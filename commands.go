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
	"maunium.net/go/mautrix"
)

// UnknownCommand handles unknown !gitlab commands.
func UnknownCommand(git *gitlab.Client, room *mautrix.Room, sender, command string, args ...string) {
	room.SendHTML("Unknown command. Type <code>!gitlab help</code> for help.")
}

// AuthOnlyCommand handles !gitlab commands that require authentication when the user hasn't logged in.
func AuthOnlyCommand(room *mautrix.Room, sender, command string, args ...string) {
	room.SendHTML("That command can only be used if you're logged in.\nTry <code>!gitlab login &lt;access token&gt;</code>")
}

// GitlabCommand is a function that handles a !gitlab command.
type GitlabCommand func(git *gitlab.Client, room *mautrix.Room, sender string, args ...string)

// Commands contains all the normal !gitlab commands.
var Commands = map[string]GitlabCommand{
	"ping":   commandPing,
	"server": commandServer,
	"login":  commandLogin,
	"logout": commandLogout,
	"show":   commandShow,
	"whoami": commandWhoami,
	"help":   commandHelp,
}

func commandPing(git *gitlab.Client, room *mautrix.Room, sender string, args ...string) {
	room.Send("Pong.")
}

func commandServer(git *gitlab.Client, room *mautrix.Room, sender string, args ...string) {
	room.Sendf("I'm using the GitLab server at %s", config.GitLab.Domain)
}

func commandLogin(git *gitlab.Client, room *mautrix.Room, sender string, args ...string) {
	if git != nil {
		room.Send("You're already logged in.")
		return
	} else if len(args) == 0 {
		room.SendHTML("Usage: <code>!gitlab login &lt;access token&gt;</code>")
		return
	}
	room.Send(loginGitlab(sender, args[0]))
}

func commandLogout(git *gitlab.Client, room *mautrix.Room, sender string, args ...string) {
	logoutGitlab(sender)
	room.Send("Access token removed successfully.")
}

func commandHelp(git *gitlab.Client, room *mautrix.Room, sender string, args ...string) {
	if git != nil {
		room.SendHTML(`<pre>
Commands are prefixed with !gitlab
- ping               - Ping the bot.
- show &lt;repo&gt; &lt;hash&gt; - Get details about a specific commit.
- whoami             - Check who you're logged in as.
- logout             - Remove your GitLab access token from storage.
- login      &lt;token&gt; - Add a GitLab access token to storage.
- help               - Show this help page.
</pre>`)
	} else {
		room.SendHTML(`<b>You're not logged in.</b><br/>
<pre>
Commands are prefixed with !gitlab
- ping          - Ping the bot.
- server        - Get the server this bot uses.
- login &lt;token&gt; - Add a GitLab access token to storage.
- help          - Show this help page.
</pre>`)
	}
}

func commandWhoami(git *gitlab.Client, room *mautrix.Room, sender string, args ...string) {
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
}

func commandShow(git *gitlab.Client, room *mautrix.Room, sender string, args ...string) {
	if len(args) < 2 {
		room.SendHTML("Usage: <code>!gitlab show &lt;repo&gt; &lt;hash&gt;</code>")
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
}
