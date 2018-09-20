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
	"maubot.xyz"
)

type MauLabBot struct {
	client maubot.MatrixClient
}

const (
	CommandIssueExpansion = "issue_expansion"
)

var spec = &maubot.CommandSpec{
	Commands: []maubot.Command{{
		Syntax:      "gitlab ping",
		Description: "Ping the bot",
	}, {
		Syntax:      "gitlab show $repo $hash",
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
		Syntax:      "gitlab diff $repo $hash",
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
		Syntax:      "gitlab log $repo $num $page",
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
		Syntax:      "gitlab whoami",
		Description: "Check who you're logged in as",
	}, {
		Syntax:      "gitlab logout",
		Description: "Remove your GitLab access token from storage",
	}, {
		Syntax:      "gitlab login $token",
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
	}},
}

func (bot *MauLabBot) Start() {
	bot.client.SetCommandSpec(spec)
}

func (bot *MauLabBot) Stop() {

}

var Plugin = maubot.PluginCreator{
	Create: func(client maubot.MatrixClient, log maubot.Logger) maubot.Plugin {
		return &MauLabBot{
			client: client,
		}
	},
	Name:    "maubot.xyz/gitlab",
	Version: "0.1.0",
}
