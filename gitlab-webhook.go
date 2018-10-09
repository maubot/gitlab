// maulabbot - A Gitlab bot for Matrix
// Copyright (C) 2018 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

package main

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"gopkg.in/go-playground/webhooks.v3"
	"gopkg.in/go-playground/webhooks.v3/gitlab"
)

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

func (bot *MauLabBot) startWebhook() {
	hook := gitlab.New(&gitlab.Config{Secret: config.Webhook.Secret})
	hook.RegisterEvents(bot.handlePushEvent, gitlab.PushEvents)
	hook.RegisterEvents(bot.handleTagEvent, gitlab.TagEvents)
	hook.RegisterEvents(bot.handleIssueEvent, gitlab.IssuesEvents)
	hook.RegisterEvents(bot.handleIssueEvent, gitlab.ConfidentialIssuesEvents)
	hook.RegisterEvents(bot.handleMergeRequestEvent, gitlab.MergeRequestEvents)
	hook.RegisterEvents(bot.handleCommentEvent, gitlab.CommentEvents)

	bot.server = &http.Server{Addr: config.Webhook.Listen}
	go func() {
		mux := http.NewServeMux()
		mux.Handle(config.Webhook.Path, addRoomToHeaders(webhooks.Handler(hook)))

		bot.server.Handler = mux

		bot.log.Infoln("Listening to GitLab webhooks at", config.Webhook.Listen+config.Webhook.Path)
		err := bot.server.ListenAndServe()
		if err != nil {
			bot.log.Errorln("GitLab webhook listener errored:", err)
		}
	}()
}

func (bot *MauLabBot) stopWebhook() {
	ctx, cancel := context.WithTimeout(context.Background(), 3 * time.Second)
	defer cancel()
	bot.server.Shutdown(ctx)
}

func (bot *MauLabBot) handlePushEvent(payload interface{}, header webhooks.Header) {
	data := payload.(gitlab.PushEventPayload)
	roomID := header["X-Room-Id"][0]

	branch := strings.TrimPrefix(data.Ref, "refs/heads/")
	if data.TotalCommitsCount == 0 {
		bot.client.SendMessagef(roomID,
			"[%[3]s/%[4]s] %[5]s force pushed to or deleted branch [%[2]s](%[1]s/tree/%[2]s)",
			data.Project.WebURL,
			branch,
			data.Project.Namespace,
			data.Project.Name,
			data.UserName)
		return
	}

	var commits bytes.Buffer
	for i := len(data.Commits) - 1; i >= 0; i-- {
		commit := data.Commits[i]
		lines := strings.Split(commit.Message, "\n")
		message := lines[0]
		if len(lines) > 1 && len(strings.Join(lines[1:], "")) > 0 {
			message += " (...)"
		}
		fmt.Fprintf(&commits, "* %s (%s)\n", message, commit.ID[:8])
	}

	var pluralizer = ""
	if data.TotalCommitsCount != 1 {
		pluralizer = "s"
	}

	bot.client.SendMessagef(roomID,
		"[[%[3]s/%[4]s#%[2]s](%[1]s/tree/%[2]s)] %[5]d new commit%[7]s by %[6]s\n\n%[8]s",
		data.Project.WebURL,
		branch,
		data.Project.Namespace,
		data.Project.Name,
		data.TotalCommitsCount,
		data.UserName,
		pluralizer,
		commits.String())
}

func (bot *MauLabBot) handleTagEvent(payload interface{}, header webhooks.Header) {
	data := payload.(gitlab.TagEventPayload)
	if data.ObjectKind != "tag_push" {
		return
	}
	roomID := header["X-Room-Id"][0]
	tag := strings.TrimPrefix(data.Ref, "refs/tags/")
	bot.client.SendMessagef(roomID,
		"[%[1]s/%[2]s] %[3]s created tag [%[5]s](%[4]s/tags/%[5]s)",
		data.Project.Namespace,
		data.Project.Name,
		data.UserName,
		data.Project.WebURL,
		tag)
}

func (bot *MauLabBot) handleIssueEvent(payload interface{}, header webhooks.Header) {
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
	roomID := header["X-Room-Id"][0]

	var action = data.ObjectAttributes.Action
	if action == "update" || len(action) == 0 {
		return
	} else if !strings.HasSuffix(action, "e") {
		action += "e"
	}
	bot.client.SendMessagef(roomID,
		"[%[1]s/%[2]s] %[3]s %[4]sd %[5]sissue [%[7]s (#%[8]d)](%[6]s)",
		data.Project.Namespace,
		data.Project.Name,
		data.User.Name,
		action,
		confidential,
		data.ObjectAttributes.URL,
		data.ObjectAttributes.Title,
		data.ObjectAttributes.IID)
}

func (bot *MauLabBot) handleMergeRequestEvent(payload interface{}, header webhooks.Header) {
	data := payload.(gitlab.MergeRequestEventPayload)
	roomID := header["X-Room-Id"][0]

	var action = data.ObjectAttributes.Action
	if action == "update" {
		return
	} else if !strings.HasSuffix(action, "e") {
		action += "e"
	}
	bot.client.SendMessagef(roomID,
		"[%[1]s/%[2]s] %[3]s %[4]sd merge request [%[6]s (!%[7]d)](%[5]s)",
		data.ObjectAttributes.Target.Namespace,
		data.ObjectAttributes.Target.Name,
		data.User.Name,
		action,
		data.ObjectAttributes.URL,
		data.ObjectAttributes.Title,
		data.ObjectAttributes.IID)
}

func (bot *MauLabBot) handleCommentEvent(payload interface{}, header webhooks.Header) {
	data := payload.(gitlab.CommentEventPayload)
	roomID := header["X-Room-Id"][0]

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

	bot.client.SendMessagef(roomID,
		"[%[1]s/%[2]s] %[3]s [commented](%[5]s) on %[4]s %[6]s (%[8]c%[7]d)",
		data.Project.Namespace,
		data.Project.Name,
		data.User.Name,
		notebookType,
		data.ObjectAttributes.URL,
		title,
		id,
		notebookIdentifier)
}
