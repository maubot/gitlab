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

	"maunium.net/go/mautrix"
)

func handlePreloginGitlabCommand(room *mautrix.Room, sender, command string, args ...string) {
	switch command {
	case "ping":
		room.Send("Pong.")
	case "server":
		room.Sendf("I'm using the GitLab server at %s", config.GitLab.Domain)
	case "login":
		if len(args) == 0 {
			room.SendHTML("Usage: <code>!gitlab login &lt;access token&gt;</code>")
			return
		}
		room.Send(loginGitlab(sender, args[0]))
	case "help":
		room.SendHTML(`<b>You're not logged in.</b><br/>
<pre>
Commands are prefixed with !gitlab
- ping          - Ping the bot.
- server        - Get the server this bot uses.
- login &lt;token&gt; - Add a GitLab access token to storage.
- help          - Show this help page.
</pre>`)
	case "commit":
		fallthrough
	case "whoami":
		fallthrough
	case "logout":
		room.SendHTML("That command can only be used if you're logged in.\nTry <code>!gitlab login &lt;access token&gt;</code>")
	default:
		room.SendHTML("Unknown command. Type <code>!gitlab help</code> for help.")
	}
}

func handleGitlabCommand(room *mautrix.Room, sender, command string, args ...string) {
	git := getGitlabClient(sender)
	if git == nil {
		handlePreloginGitlabCommand(room, sender, command, args...)
		return
	}
	switch command {
	case "ping":
		room.Send("Pong.")
	case "server":
		room.Sendf("I'm using the GitLab server at %s", config.GitLab.Domain)
	case "login":
		room.Send("You're already logged in.")
	case "logout":
		logoutGitlab(sender)
		room.Send("Access token removed successfully.")
	case "whoami":
		user, _, err := git.Users.CurrentUser()
		if err != nil {
			room.Sendf("Unexpected error: %s", err)
			return
		}
		room.SendfHTML(
			"You're logged into %[1]s as <a href='%[2]s/%[3]s'>%[4]s</a>",
			git.BaseURL().Hostname(),
			config.GitLab.Domain,
			user.Username,
			user.Name)
	case "commit":
		if len(args) < 2 {
			room.SendHTML("Usage: <code>!gitlab commit &lt;repo&gt; &lt;hash&gt;</code>")
			return
		}

		commit, _, err := git.Commits.GetCommit(args[0], args[1])
		if err != nil {
			room.Sendf("An error occurred: %s", err)
			return
		}
		room.SendfHTML(
			"<a href='%s'>Commit %s</a> by %s at %s:<br/><blockquote>%s</blockquote>",
			fmt.Sprintf("%s/%s/commit/%s", config.GitLab.Domain, args[0], commit.ID),
			commit.ShortID,
			commit.AuthorName,
			commit.CommittedDate.Format("Jan _2, 2006 15:04:05"),
			strings.Replace(commit.Message, "\n", "<br/>", -1))
	case "help":
		room.SendHTML(`<pre>
Commands are prefixed with !gitlab
- ping                 - Ping the bot.
- commit &lt;repo&gt; &lt;hash&gt; - Get details about a specific commit.
- whoami               - Check who you're logged in as.
- logout               - Remove your GitLab access token from storage.
- login        &lt;token&gt; - Add a GitLab access token to storage.
- help                 - Show this help page.
</pre>`)
	default:
		room.SendHTML("Unknown command. Type <code>!gitlab help</code> for help.")
	}
}
