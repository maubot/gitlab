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

	"gopkg.in/go-playground/webhooks.v5/gitlab"
	"maunium.net/go/mautrix"
)

func handlePayload(hook *gitlab.Webhook) func(w http.ResponseWriter, r *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		payload, err := hook.Parse(
			r,
			gitlab.PushEvents,
			gitlab.TagEvents,
			gitlab.IssuesEvents,
			gitlab.CommentEvents,
			gitlab.MergeRequestEvents,
			gitlab.PipelineEvents,
			//gitlab.ConfidentialIssuesEvents,
			//gitlab.WikiPageEvents,
			//gitlab.BuildEvents,
		)
		if err != nil {
			if err == gitlab.ErrEventNotFound {
				w.WriteHeader(500)
				w.Write([]byte("Event not found"))
				return
			}
		}

		roomID := r.URL.Query().Get("room")
		if len(roomID) == 0 {
			w.WriteHeader(400)
			w.Write([]byte("No room specified."))
			return
		}
		room := mxbot.GetRoom(roomID)
		switch payload.(type) {
		case gitlab.PushEventPayload:
			handlePushEvent(payload, *room)
		case gitlab.TagEventPayload:
			handleTagEvent(payload, *room)
		case gitlab.IssueEventPayload:
			handleIssueEvent(payload, *room)
		case gitlab.CommentEventPayload:
			handleCommentEvent(payload, *room)
		case gitlab.MergeRequestEventPayload:
			handleMergeRequestEvent(payload, *room)
		case gitlab.PipelineEventPayload:
			handlePipelineEvent(payload, *room)
		case gitlab.WikiPageEventPayload:
			handleWikiPageEvent(payload, *room)
			//case gitlab.ConfidentialIssueEventPayload:
			//case gitlab.BuildEventPayload:
		}

		w.WriteHeader(204)
		return
	}
}

func startWebhook() func() {
	hook, _ := gitlab.New(gitlab.Options.Secret(config.Webhook.Secret))

	server := &http.Server{Addr: config.Webhook.Listen}
	go func() {
		mux := http.NewServeMux()
		mux.Handle(config.Webhook.Path, http.HandlerFunc(handlePayload(hook)))

		server.Handler = mux

		fmt.Println("Listening to GitLab webhooks at", config.Webhook.Listen+config.Webhook.Path)
		err := server.ListenAndServe()
		if err != nil {
			fmt.Println(err)
		}
	}()
	return func() {
		server.Shutdown(nil)
	}
}

func handlePushEvent(payload interface{}, room mautrix.Room) {
	data := payload.(gitlab.PushEventPayload)

	branch := strings.TrimPrefix(data.Ref, "refs/heads/")
	if data.TotalCommitsCount == 0 {
		room.SendfHTML(
			"[%[3]s/%[4]s] %[5]s force pushed to or deleted branch <a href='%[1]s/tree/%[2]s'>%[2]s</a>",
			data.Project.WebURL,
			branch,
			data.Project.Namespace,
			data.Project.Name,
			data.UserName)
		return
	}

	var pluralizer = ""
	if data.TotalCommitsCount != 1 {
		pluralizer = "s"
	}
	room.SendfHTML(
		"[<a href='%[1]s/tree/%[2]s'>%[3]s/%[4]s#%[2]s</a>] %[5]d new commit%[7]s by %[6]s",
		data.Project.WebURL,
		branch,
		data.Project.Namespace,
		data.Project.Name,
		data.TotalCommitsCount,
		data.UserName,
		pluralizer)
	// IRC compatibility: Allow up to 4 commits to be displayed through the IRC bridge without
	// 					  having the bridge turn the message into a link.
	if data.TotalCommitsCount > 4 || !config.Options.IRCCompatibility {
		var msg bytes.Buffer
		fmt.Fprint(&msg, "<ul>")
		for i := len(data.Commits) - 1; i >= 0; i-- {
			commit := data.Commits[i]
			lines := strings.Split(commit.Message, "\n")
			message := lines[0]
			if len(lines) > 1 && len(strings.Join(lines[1:], "")) > 0 {
				message += " (...)"
			}
			fmt.Fprintf(&msg, "<li>%s (%s)</li>\n", message, commit.ID[:8])
		}
		fmt.Fprint(&msg, "</ul>")
		room.SendHTML(msg.String())
	} else {
		for i := len(data.Commits) - 1; i >= 0; i-- {
			commit := data.Commits[i]
			lines := strings.Split(commit.Message, "\n")
			message := lines[0]
			if len(lines) > 1 && len(strings.Join(lines[1:], "")) > 0 {
				message += " (...)"
			}
			room.SendfHTML("<ul><li>%s (%s)</li></ul>", message, commit.ID[:8])
		}
	}
}

func handleTagEvent(payload interface{}, room mautrix.Room) {
	data := payload.(gitlab.TagEventPayload)
	if data.ObjectKind != "tag_push" {
		return
	}
	tag := strings.TrimPrefix(data.Ref, "refs/tags/")
	room.SendfHTML("[%[1]s/%[2]s] %[3]s created tag <a href='%[4]s/tags/%[5]s'>%[5]s</a>",
		data.Project.Namespace,
		data.Project.Name,
		data.UserName,
		data.Project.WebURL,
		tag)
}

func handleIssueEvent(payload interface{}, room mautrix.Room) {
	data, ok := payload.(gitlab.IssueEventPayload)
	confidential := ""
	if !ok {
		data2, ok := payload.(gitlab.ConfidentialIssueEventPayload)
		if !ok {
			fmt.Println("Unexpected error: Received issue event with incorrect payload type.")
			return
		}
		confidential = "confidential "
		data = data2.IssueEventPayload
	}

	action := data.ObjectAttributes.Action
	if action == "update" || len(action) == 0 {
		return
	} else if !strings.HasSuffix(action, "e") {
		action += "e"
	}
	room.SendfHTML(
		"[%[1]s/%[2]s] %[3]s %[4]sd %[5]sissue <a href='%[6]s'>%[7]s (#%[8]d)</a>",
		data.Project.Namespace,
		data.Project.Name,
		data.User.Name,
		action,
		confidential,
		data.ObjectAttributes.URL,
		data.ObjectAttributes.Title,
		data.ObjectAttributes.IID)
}

func handleMergeRequestEvent(payload interface{}, room mautrix.Room) {
	data := payload.(gitlab.MergeRequestEventPayload)

	action := data.ObjectAttributes.Action
	if action == "update" {
		return
	} else if !strings.HasSuffix(action, "e") {
		action += "e"
	}
	room.SendfHTML(
		"[%[1]s/%[2]s] %[3]s %[4]sd merge request <a href='%[5]s'>%[6]s (!%[7]d)</a>",
		data.ObjectAttributes.Target.Namespace,
		data.ObjectAttributes.Target.Name,
		data.User.Name,
		action,
		data.ObjectAttributes.URL,
		data.ObjectAttributes.Title,
		data.ObjectAttributes.IID)
}

func handleCommentEvent(payload interface{}, room mautrix.Room) {
	data := payload.(gitlab.CommentEventPayload)

	var notebookType, title string
	var notebookIdentifier rune
	var id int64
	switch data.ObjectAttributes.NotebookType {
	case "Issue":
		notebookType = "issue"
		notebookIdentifier = '#'
		title = data.Issue.Title
		id = data.Issue.IID
	case "MergeRequest":
		notebookType = "merge request"
		notebookIdentifier = '!'
		title = data.MergeRequest.Title
		id = data.MergeRequest.IID
	}

	room.SendfHTML(
		"[%[1]s/%[2]s] %[3]s <a href='%[5]s'>commented</a> on %[4]s %[6]s (%[8]c%[7]d)",
		data.Project.Namespace,
		data.Project.Name,
		data.User.Name,
		notebookType,
		data.ObjectAttributes.URL,
		title,
		id,
		notebookIdentifier)
}

func handlePipelineEvent(payload interface{}, room mautrix.Room) {
	data := payload.(gitlab.PipelineEventPayload)

	room.SendfHTML(
		"[<a href='%[5]s'>%[1]s/%[2]s</a>] pipeline %[7]d complete, %[3]s in %[4]d seconds %[6]s",
		data.Project.Namespace,
		data.Project.Name,
		data.ObjectAttributes.Status,
		data.ObjectAttributes.Duration,
		data.ObjectAttributes.URL,
		data.ObjectAttributes.Title,
		data.ObjectAttributes.IID)
}

func handleWikiPageEvent(payload interface{}, room mautrix.Room) {
	data := payload.(gitlab.WikiPageEventPayload)

	action := data.ObjectAttributes.Action

	if !strings.HasSuffix(action, "e") {
		action += "e"
	}
	room.SendfHTML(
		"[%[1]s/%[2]s] %[3]s %[4]sd page on wiki <a href='%[5]s'>%[6]s (#%[7]d)</a>",
		data.Project.Namespace,
		data.Project.Name,
		data.User.Name,
		action,
		data.ObjectAttributes.URL,
		data.ObjectAttributes.Title,
		data.ObjectAttributes.IID)
}
