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
	"net/http"

	"maubot.xyz"
)

type MauLabBot struct {
	client maubot.MatrixClient
	log    maubot.Logger
	server *http.Server
}

// Active commands
const (
	CommandPing           = "gitlab ping"
	CommandShowCommit     = "gitlab show $repo $hash"
	CommandShowCommitDiff = "gitlab diff $repo $hash"
	CommandLog            = "gitlab log $repo $num $page"
	CommandWhoami         = "gitlab whoami"
	CommandLogout         = "gitlab logout"
	CommandLogin          = "gitlab login $token"
)

// Passive commands
const (
	CommandIssueExpansion        = "issue_expansion"
	CommandMergeRequestExpansion = "merge_request_expansion"
)

var spec = &maubot.CommandSpec{
	Commands: []maubot.Command{{
		Syntax:      CommandPing,
		Description: "Ping the bot",
	}, {
		Syntax:      CommandShowCommit,
		Description: "Get details about a specific commit",
		Arguments: maubot.ArgumentMap{
			"$repo": {
				Matches:     `\w+/\w+`,
				Required:    false,
				Description: "The GitLab repository owner and name",
			},
			"$hash": {
				Matches:     "[a-z0-9]{5,40}",
				Required:    true,
				Description: "The commit hash to get",
			},
		},
	}, {
		Syntax:      CommandShowCommitDiff,
		Description: "Get the diff of a specific commit",
		Arguments: maubot.ArgumentMap{
			"$repo": {
				Matches:     `\w+/\w+`,
				Required:    false,
				Description: "The GitLab repository owner and name",
			},
			"$hash": {
				Matches:     "[a-z0-9]{5,40}",
				Required:    true,
				Description: "The commit hash to get",
			},
		},
	}, {
		Syntax:      CommandLog,
		Description: "Get the log of a specific repo",
		Arguments: maubot.ArgumentMap{
			"$repo": {
				Matches:     `\w+/\w+`,
				Required:    false,
				Description: "The GitLab repository owner and name",
			},
			"$num": {
				Matches:     "[0-9]{1,2}",
				Required:    false,
				Description: "The number of commits to show per page",
			},
			"$page": {
				Matches:     "[0-9]+",
				Required:    false,
				Description: "The page to show",
			},
		},
	}, {
		Syntax:      CommandWhoami,
		Description: "Check who you're logged in as",
	}, {
		Syntax:      CommandLogout,
		Description: "Remove your GitLab access token from storage",
	}, {
		Syntax:      CommandLogin,
		Description: "Add a GitLab access token to storage",
		Arguments: maubot.ArgumentMap{
			"$token": {
				Matches:     "[A-Za-z0-9]+",
				Required:    true,
				Description: "Your GitLab access token",
			},
		},
	}},
	PassiveCommands: []maubot.PassiveCommand{{
		Name:         CommandIssueExpansion,
		Matches:      `((\w+?/)?(\w+?))?0#([0-9]+)`,
		MatchAgainst: maubot.MatchAgainstBody,
	}, {
		Name:         CommandMergeRequestExpansion,
		Matches:      `((\w+?/)?(\w+?))?0!([0-9]+)`,
		MatchAgainst: maubot.MatchAgainstBody,
	}},
}

func (bot *MauLabBot) Start() {
	bot.client.SetCommandSpec(spec)
	go bot.startWebhook()
}

func (bot *MauLabBot) Stop() {
	bot.stopWebhook()
}

var Plugin = maubot.PluginCreator{
	Create: func(client maubot.MatrixClient, log maubot.Logger) maubot.Plugin {
		return &MauLabBot{
			client: client,
			log:    log,
		}
	},
	Name:    "maubot.xyz/gitlab",
	Version: "0.1.0",
}
