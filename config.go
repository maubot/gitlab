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
	"io/ioutil"
)

// Config is the config for Maunium GitLab bot.
type Config struct {
	Webhook struct {
		Listen string `json:"listen"`
		Path   string `json:"path"`
		Secret string `json:"secret"`
	} `json:"webhook"`

	Matrix struct {
		Homeserver string `json:"homeserver"`
		Username   string `json:"username"`
		Password   string `json:"password"`
		AuthToken  string `json:"authtoken"`
	}

	GitLab struct {
		Domain string `json:"domain"`
	} `json:"gitlab"`

	Options struct {
		IRCCompatibility bool `json:"irc-compatibility"`
	} `json:"options"`
}

var config Config

func loadConfig(path string) error {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return err
	}

	return json.Unmarshal(data, &config)
}

func saveConfig(path string) error {
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return err
	}

	return ioutil.WriteFile(path, data, 0600)
}
