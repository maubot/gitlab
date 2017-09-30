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
	"encoding/json"
	"fmt"
	"io/ioutil"
	"strings"

	"github.com/xanzy/go-gitlab"
	flag "maunium.net/go/mauflag"
	"maunium.net/go/mautrix"
)

var gitlabTokens = make(map[string]string)
var gitlabDomain = flag.MakeFull("d", "gitlab-domain", "GitLab domain", "https://gitlab.com").String()

func saveGitlabTokens() {
	data, _ := json.MarshalIndent(gitlabTokens, "", "  ")
	ioutil.WriteFile("tokens.json", data, 0600)
}

func loadGitlabTokens() {
	data, err := ioutil.ReadFile("tokens.json")
	if err != nil {
		return
	}
	err = json.Unmarshal(data, &gitlabTokens)
	if err != nil {
		panic(err)
	}
}

func loginGitlab(userID, token string) string {
	git := gitlab.NewClient(nil, token)
	err := git.SetBaseURL(fmt.Sprintf("%s/api/v4", *gitlabDomain))
	if err != nil {
		return err.Error()
	}

	user, resp, err := git.Users.CurrentUser()
	if resp.StatusCode == 401 {
		return fmt.Sprintf("Invalid access token!")
	} else if err != nil {
		return fmt.Sprintf("GitLab login failed: %s", err)
	}

	gitlabTokens[userID] = token
	saveGitlabTokens()
	return fmt.Sprintf("Successfully logged into GitLab at %s as %s\n", git.BaseURL().Hostname(), user.Name)
}

func getGitlabClient(userID string) *gitlab.Client {
	token, ok := gitlabTokens[userID]
	if !ok {
		return nil
	}

	git := gitlab.NewClient(nil, token)
	err := git.SetBaseURL(fmt.Sprintf("%s/api/v4", *gitlabDomain))
	if err != nil {
		return nil
	}

	return git
}

func handlePreloginGitlabCommand(room *mautrix.Room, sender, command string, args ...string) {
	switch command {
	case "ping":
		room.Send("Pong.")
	case "server":
		room.Send(fmt.Sprintf("I'm using the GitLab server at %s", *gitlabDomain))
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
		room.Send(fmt.Sprintf("I'm using the GitLab server at %s", *gitlabDomain))
	case "login":
		room.Send("You're already logged in.")
	case "logout":
		delete(gitlabTokens, sender)
		saveGitlabTokens()
		room.Send("Access token removed successfully.")
	case "whoami":
		user, _, err := git.Users.CurrentUser()
		if err != nil {
			room.Send(fmt.Sprintf("Unexpected error: %s", err))
			return
		}
		room.SendHTML(fmt.Sprintf(
			"You're logged into %[1]s as <a href='%[2]s/%[3]s'>%[4]s</a>",
			git.BaseURL().Hostname(),
			*gitlabDomain,
			user.Username,
			user.Name))
	case "commit":
		if len(args) < 2 {
			room.SendHTML("Usage: <code>!gitlab commit &lt;repo&gt; &lt;hash&gt;</code>")
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
