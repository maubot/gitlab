// maulabbot - A Gitlab bot for Matrix
// Copyright (C) 2017 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

package main

import (
	"bytes"
	"fmt"
	"net/http"
	"strings"

	"gopkg.in/go-playground/webhooks.v3"
	"gopkg.in/go-playground/webhooks.v3/gitlab"
	flag "maunium.net/go/mauflag"
)

var gitlabListenAddr = flag.MakeFull("l", "gitlab", "GitLab listen address", ":8080").String()
var gitlabListenPath = flag.MakeFull("g", "gitlab-path", "GitLab listen path", "/webhooks").String()
var gitlabSecret = flag.MakeFull("e", "secret", "GitLab secret", "").String()

func addRoomToHeaders(handler http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		room := r.URL.Query().Get("room")
		if len(room) == 0 {
			w.WriteHeader(400)
			w.Write([]byte("No room specified."))
			return
		}
		r.Header.Set("X-Room-Id", room)
		handler.ServeHTTP(w, r)
	})
}

func startWebhook() func() {
	hook := gitlab.New(&gitlab.Config{Secret: *gitlabSecret})
	hook.RegisterEvents(handlePushEvent, gitlab.PushEvents)
	hook.RegisterEvents(handleIssueEvent, gitlab.IssuesEvents)
	hook.RegisterEvents(handleMergeRequestEvent, gitlab.MergeRequestEvents)
	hook.RegisterEvents(handleCommentEvent, gitlab.CommentEvents)

	server := &http.Server{Addr: *gitlabListenAddr}
	go func() {
		mux := http.NewServeMux()
		mux.Handle(*gitlabListenPath, addRoomToHeaders(webhooks.Handler(hook)))

		server.Handler = mux

		err := server.ListenAndServe()
		if err != nil {
			fmt.Println(err)
		}
	}()
	return func() {
		server.Shutdown(nil)
	}
}

func handlePushEvent(payload interface{}, header webhooks.Header) {
	data := payload.(gitlab.PushEventPayload)
	roomID := header["X-Room-Id"][0]
	room := mxbot.GetRoom(roomID)

	branch := strings.TrimPrefix(data.Ref, "refs/heads/")
	if data.TotalCommitsCount == 0 {
		room.SendHTML(fmt.Sprintf(
			"[%[3]s/%[4]s] %[5]s force pushed to or deleted branch <a href='%[1]s/tree/%[2]s'>%[2]s</a>",
			data.Project.WebURL,
			branch,
			data.Project.Namespace,
			data.Project.Name,
			data.UserName))
		return
	}

	var pluralizer = ""
	if data.TotalCommitsCount != 1 {
		pluralizer = "s"
	}
	room.SendHTML(fmt.Sprintf(
		"[<a href='%[1]s/tree/%[2]s'>%[3]s/%[4]s#%[2]s</a>] %[5]d new commit%[7]s by %[6]s",
		data.Project.WebURL,
		branch,
		data.Project.Namespace,
		data.Project.Name,
		data.TotalCommitsCount,
		data.UserName,
		pluralizer))
	// IRC compatibility: Allow up to 4 commits to be displayed through the IRC bridge without
	// 					  having the bridge turn the message into a link.
	if data.TotalCommitsCount > 4 {
		var msg bytes.Buffer
		fmt.Fprintln(&msg, "<ul>")
		for i := len(data.Commits) - 1; i >= 0; i-- {
			commit := data.Commits[i]
			fmt.Fprintf(&msg, "<li>%s (%s)</li>\n", strings.Split(commit.Message, "\n")[0], commit.ID[:8])
		}
		fmt.Fprintln(&msg, "</ul>")
		room.SendHTML(msg.String())
	} else {
		for i := len(data.Commits) - 1; i >= 0; i-- {
			commit := data.Commits[i]
			room.SendHTML(fmt.Sprintf("<ul><li>%s (%s)</li></ul>", strings.Split(commit.Message, "\n")[0], commit.ID[:8]))
		}
	}
}

func handleIssueEvent(payload interface{}, header webhooks.Header) {
	data := payload.(gitlab.IssueEventPayload)
	roomID := header["X-Room-Id"][0]
	room := mxbot.GetRoom(roomID)

	var action = data.ObjectAttributes.Action
	if action == "update" {
		return
	} else if !strings.HasSuffix(action, "e") {
		action += "e"
	}
	room.SendHTML(fmt.Sprintf(
		"[%[1]s/%[2]s] %[3]s %[4]sd issue <a href='%[5]s'>%[6]s (#%[7]d)</a>",
		data.Project.Namespace,
		data.Project.Name,
		data.User.Name,
		action,
		data.ObjectAttributes.URL,
		data.ObjectAttributes.Title,
		data.ObjectAttributes.IID))
}

func handleMergeRequestEvent(payload interface{}, header webhooks.Header) {
	data := payload.(gitlab.MergeRequestEventPayload)
	roomID := header["X-Room-Id"][0]
	room := mxbot.GetRoom(roomID)

	var action = data.ObjectAttributes.Action
	if action == "update" {
		return
	} else if !strings.HasSuffix(action, "e") {
		action += "e"
	}
	room.SendHTML(fmt.Sprintf(
		"[%[1]s/%[2]s] %[3]s %[4]sd merge request <a href='%[5]s'>%[6]s (#%[7]d)</a>",
		data.ObjectAttributes.Target.Namespace,
		data.ObjectAttributes.Target.Name,
		data.User.Name,
		action,
		data.ObjectAttributes.URL,
		data.ObjectAttributes.Title,
		data.ObjectAttributes.IID))
}

func handleCommentEvent(payload interface{}, header webhooks.Header) {
	data := payload.(gitlab.CommentEventPayload)
	roomID := header["X-Room-Id"][0]
	room := mxbot.GetRoom(roomID)

	var notebookType, title string
	var id int64
	switch data.ObjectAttributes.NotebookType {
	case "Issue":
		notebookType = "issue"
		title = data.Issue.Title
		id = data.Issue.IID
	case "MergeRequest":
		notebookType = "merge request"
		title = data.MergeRequest.Title
		id = data.MergeRequest.IID
	}

	room.SendHTML(fmt.Sprintf(
		"[%[1]s/%[2]s] %[3]s <a href='%[5]s'>commented</a> on %[4]s %[6]s (#%[7]d)",
		data.Project.Namespace,
		data.Project.Name,
		data.User.Name,
		notebookType,
		data.ObjectAttributes.URL,
		title,
		id))
}
