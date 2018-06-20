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

	"github.com/xanzy/go-gitlab"
	"maubot.xyz"
)

var gitlabTokens = make(map[string]string)

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
	err := git.SetBaseURL(fmt.Sprintf("%s/api/v4", config.GitLab.Domain))
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

func logoutGitlab(userID string) {
	delete(gitlabTokens, userID)
	saveGitlabTokens()
}

type GitLabCommandHandler func(evt *maubot.Event, client *gitlab.Client) maubot.CommandHandlerResult

func gitlabClientMiddleware(fn GitLabCommandHandler) maubot.CommandHandler {
	return func(evt *maubot.Event) maubot.CommandHandlerResult {
		return fn(evt, getGitlabClient(evt.Sender))
	}
}

func getGitlabClient(userID string) *gitlab.Client {
	token, ok := gitlabTokens[userID]
	if !ok {
		return nil
	}

	git := gitlab.NewClient(nil, token)
	err := git.SetBaseURL(fmt.Sprintf("%s/api/v4", config.GitLab.Domain))
	if err != nil {
		return nil
	}

	return git
}
