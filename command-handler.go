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
	"maunium.net/go/mautrix"
)

var permittedPreloginCommands = []string{"ping", "server", "login", "help"}

func handleCommand(room *mautrix.Room, sender, command string, args []string, lines []string) {
	git := getGitlabClient(sender)
	handler, ok := Commands[command]
	if !ok {
		UnknownCommand(git, room, sender, command, args)
		return
	}
	if git == nil {
		for _, cmd := range permittedPreloginCommands {
			if cmd == command {
				handler(nil, room, sender, args, lines)
				return
			}
		}
		AuthOnlyCommand(room, sender, command, args)
		return
	}
	handler(git, room, sender, args, lines)
}
