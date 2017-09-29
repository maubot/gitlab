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
	"fmt"
	"strings"

	"github.com/xanzy/go-gitlab"
	flag "maunium.net/go/mauflag"
	"maunium.net/go/mautrix"
)

var gitlabToken = flag.MakeFull("t", "token", "GitLab access token", "").String()
var gitlabDomain = flag.MakeFull("d", "gitlab-domain", "GitLab domain", "https://gitlab.com").String()
var git *gitlab.Client

func initGitlabClient() {
	git = gitlab.NewClient(nil, *gitlabToken)
	err := git.SetBaseURL(fmt.Sprintf("%s/api/v4", *gitlabDomain))
	if err != nil {
		panic(err)
	}
}

func handleGitlabCommand(room *mautrix.Room, command string, args ...string) {
	switch command {
	case "ping":
		room.Send("Pong.")
	case "commit":
		if len(args) < 2 {
			room.Send("Usage: !gitlab commit <repo> <hash>")
			return
		}

		commit, _, err := git.Commits.GetCommit(args[0], args[1])
		if err != nil {
			room.Send(fmt.Sprintf("An error occurred: %s", err))
			return
		}
		room.SendHTML(fmt.Sprintf(
			"<a href='%s'>Commit %s</a> by %s at %s:<br/><blockquote>%s</blockquote>",
			fmt.Sprintf("%s/%s/commit/%s", *gitlabDomain, args[0], commit.ID),
			commit.ShortID,
			commit.AuthorName,
			commit.CommittedDate.Format("Jan _2, 2006 15:04:05"),
			strings.Replace(commit.Message, "\n", "<br/>", -1)))
	}
}
