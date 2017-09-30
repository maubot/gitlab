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
	"regexp"
	"strconv"
	"strings"

	"github.com/xanzy/go-gitlab"
	"maunium.net/go/mautrix"
)

// UnknownCommand handles unknown !gitlab commands.
func UnknownCommand(git *gitlab.Client, room *mautrix.Room, sender, command string, args []string) {
	room.SendHTML("Unknown command. Type <code>!gitlab help</code> for help.")
}

// AuthOnlyCommand handles !gitlab commands that require authentication when the user hasn't logged in.
func AuthOnlyCommand(room *mautrix.Room, sender, command string, args []string) {
	room.SendHTML("That command can only be used if you're logged in.\nTry <code>!gitlab login &lt;access token&gt;</code>")
}

// GitlabCommand is a function that handles a !gitlab command.
type GitlabCommand func(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string)

// Commands contains all the normal !gitlab commands.
var Commands = map[string]GitlabCommand{
	"ping":   commandPing,
	"server": commandServer,
	"login":  commandLogin,
	"logout": commandLogout,
	"show":   commandShow,
	"diff":   commandDiff,
	"log":    commandLog,
	"whoami": commandWhoami,
	"help":   commandHelp,
	"issue":  commandIssue,
	"create": commandCreateIssue,
}

func commandPing(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	room.Send("Pong.")
}

func commandServer(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	room.Sendf("I'm using the GitLab server at %s", config.GitLab.Domain)
}

func commandLogin(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	if git != nil {
		room.Send("You're already logged in.")
		return
	} else if len(args) == 0 {
		room.SendHTML("Usage: <code>!gitlab login &lt;access token&gt;</code>")
		return
	}
	room.Send(loginGitlab(sender, args[0]))
}

func commandLogout(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	logoutGitlab(sender)
	room.Send("Access token removed successfully.")
}

func commandHelp(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	if git != nil {
		if len(args) > 0 {
			if args[0] == "issue" {
				room.SendHTML(`<pre><code>Commands are prefixed with !gitlab issue
- create &lt;repo&gt; &lt;title&gt;         - Create an issue. The issue body can be placed on a new line.
- close &lt;repo&gt; &lt;id&gt;             - Close an issue.
- comment &lt;repo&gt; &lt;id&gt; &lt;message&gt; - Comment on an issue.
- read &lt;repo&gt; &lt;id&gt;              - Read an issue.
- read-comments &lt;repo&gt; &lt;id&gt;     - Read comments on an issue.
</code></pre>`)
				return
			}
		}
		fmt.Println(room.SendHTML(`<pre><code>Commands are prefixed with !gitlab
- ping                  - Ping the bot.
- show &lt;repo&gt; &lt;hash&gt;    - Get details about a specific commit.
- diff &lt;repo&gt; &lt;hash&gt;    - Get the diff of a specific commit.
- log &lt;repo&gt; [n] [page] - Get the log of a specific repo.
- whoami                - Check who you're logged in as.
- logout                - Remove your GitLab access token from storage.
- login &lt;token&gt;         - Add a GitLab access token to storage.
- issue &lt;...&gt;           - Manage issues. Type !gitlab help issue for details.
- help                  - Show this help page.
</code></pre>`))
	} else {
		room.SendHTML(`<b>You're not logged in.</b><br/>
<pre><code>Commands are prefixed with !gitlab
- ping          - Ping the bot.
- server        - Get the server this bot uses.
- login &lt;token&gt; - Add a GitLab access token to storage.
- help          - Show this help page.
</code></pre>`)
	}
}

func commandWhoami(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
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

func commandShow(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
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

var diffLocationRegex = regexp.MustCompile("(@@ -[0-9]+,[0-9]+ \\+[0-9]+,[0-9]+ @@)")

func commandDiff(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	if len(args) < 2 {
		room.SendHTML("Usage: <code>!gitlab diff &lt;repo&gt; &lt;hash&gt;</code>")
		return
	}

	diffs, _, err := git.Commits.GetCommitDiff(args[0], args[1])
	if err != nil {
		room.Sendf("An error occurred: %s", err)
		return
	}
	var buf bytes.Buffer
	for _, diff := range diffs {
		fmt.Fprintf(&buf, "<pre><code>")
		for _, line := range strings.Split(diff.Diff, "\n") {
			if strings.HasPrefix(line, "@@") {
				line = diffLocationRegex.ReplaceAllString(line, "<font color='#00A'>$1</font>")
			}
			if strings.HasPrefix(line, "+++") || strings.HasPrefix(line, "---") {
				fmt.Fprintf(&buf, "<font color='#000'>%s</font>", line)
			} else if strings.HasPrefix(line, "+") {
				fmt.Fprintf(&buf, "<font color='#0A0'>%s</font>", line)
			} else if strings.HasPrefix(line, "-") {
				fmt.Fprintf(&buf, "<font color='#A00'>%s</font>", line)
			} else {
				fmt.Fprintf(&buf, "<font color='#666'>%s</font>", line)
			}
			fmt.Fprintf(&buf, "\n")
		}
		fmt.Fprintf(&buf, "</code></pre>")
	}
	room.SendHTML(buf.String())
}

func commandLog(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	if len(args) == 0 {
		room.SendHTML("Usage: <code>!gitlab log &lt;repo&gt; [n] [page]</code>")
		return
	}

	n := 10
	page := 1
	if len(args) > 1 {
		n, _ = strconv.Atoi(args[1])
	}
	if len(args) > 2 {
		page, _ = strconv.Atoi(args[2])
	}
	commits, _, err := git.Commits.ListCommits(args[0], &gitlab.ListCommitsOptions{
		ListOptions: gitlab.ListOptions{
			PerPage: n,
			Page:    page,
		},
	})
	if err != nil {
		room.Sendf("An error occurred: %s", err)
		return
	}

	var buf bytes.Buffer
	for _, commit := range commits {
		fmt.Fprintf(&buf, "<font color='#AA0'>%s</font> %s<br/>\n",
			commit.ShortID,
			strings.Split(commit.Message, "\n")[0])
	}

	room.SendHTML(buf.String())
}

func commandReadIssue(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	if len(args) < 2 {
		room.Send("Usage: !gitlab issue read <repo> <issue id>")
		return
	}

	id, err := strconv.Atoi(args[1])
	if err != nil {
		room.Send("Usage: !gitlab issue read <repo> <issue id>")
		return
	}

	issue, _, err := git.Issues.GetIssue(args[0], id)
	if err != nil {
		room.Sendf("An error occurred: %s", err)
		return
	}

	var buf bytes.Buffer
	fmt.Fprintf(&buf, "Issue #%[2]d by %[3]s: <a href='%[1]s'>%[4]s</a>.", issue.WebURL, issue.IID, issue.Author.Name, issue.Title)
	if len(issue.Assignee.Name) > 0 {
		fmt.Fprintf(&buf, " Assigned to %s.", issue.Assignee.Name)
	}
	fmt.Fprintf(&buf, "<br/>\n<blockquote>%s</blockquote><br/>\n", strings.Replace(issue.Description, "\n", "<br/>\n", -1))
	room.SendHTML(buf.String())
}

func commandCreateIssue(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	if len(args) < 2 {
		room.Send("Usage: !gitlab issue create <repo> <title> \\n <body>")
		return
	}

	title := strings.Join(args[1:], " ")
	description := strings.Join(lines, "\n")

	_, _, err := git.Issues.CreateIssue(args[0], &gitlab.CreateIssueOptions{
		Title:       &title,
		Description: &description,
	})
	if err != nil {
		room.Sendf("Failed to create issue: %s", err)
	}
}

func commandIssue(git *gitlab.Client, room *mautrix.Room, sender string, args []string, lines []string) {
	if len(args) == 0 {
		room.SendHTML("Unknown subcommand. Try <code>!gitlab help issue</code> for help.")
		return
	}

	subcommand := args[0]
	if len(args) > 1 {
		args = args[1:]
	} else {
		args = []string{}
	}

	switch subcommand {
	case "show":
		fallthrough
	case "view":
		fallthrough
	case "read":
		commandReadIssue(git, room, sender, args, lines)
	case "open":
		fallthrough
	case "create":
		commandCreateIssue(git, room, sender, args, lines)
	case "close":
		fallthrough
	case "reopen":
		if len(args) < 2 {
			room.Sendf("Usage: !gitlab issue %s <repo> <issue number>", subcommand)
			return
		}

		issueID, err := strconv.Atoi(args[1])
		if err != nil {
			room.Sendf("Invalid issue ID: %s", args[1])
		}
		_, resp, err := git.Issues.UpdateIssue(args[0], issueID, &gitlab.UpdateIssueOptions{
			StateEvent: &subcommand,
		})
		if resp.StatusCode == 404 {
			room.Sendf("Issue #%d or repository %s not found.", issueID, args[0])
		} else if err != nil {
			room.Sendf("Failed to %s issue: %s", subcommand, err)
		}
	case "comment":
	case "read-comments":
	default:
		room.SendHTML("Unknown subcommand. Try <code>!gitlab help issue</code> for help.")
	}
}
