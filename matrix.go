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

	flag "maunium.net/go/mauflag"
	"maunium.net/go/mautrix"
)

var homeserver = flag.MakeFull("s", "homeserver", "Matrix homeserver", "https://matrix.org").String()
var username = flag.MakeFull("u", "username", "Matrix username", "").String()
var password = flag.MakeFull("p", "password", "Matrix password", "").String()
var mxbot *mautrix.MatrixBot

func startMatrix() func() {
	mxbot = mautrix.Create(*homeserver)

	err := mxbot.PasswordLogin(*username, *password)
	if err != nil {
		panic(err)
	}
	fmt.Println("Connected to Matrix homeserver at", *homeserver, "as", *username)

	stop := make(chan bool, 1)

	go mxbot.Listen()
	go func() {
	Loop:
		for {
			select {
			case <-stop:
				break Loop
			case evt := <-mxbot.Timeline:
				switch evt.Type {
				case mautrix.EvtRoomMessage:
					evt.MarkRead()
					msg := evt.Content["body"].(string)
					if !strings.HasPrefix(msg, "!gitlab") {
						continue Loop
					}
					msg = strings.TrimPrefix(msg, "!gitlab ")
					parts := strings.Split(msg, " ")
					cmd := parts[0]
					var args []string
					if len(parts) > 1 {
						args = parts[1:]
					}
					handleGitlabCommand(evt.Room, evt.Sender, cmd, args...)
				}
			case roomID := <-mxbot.InviteChan:
				invite := mxbot.Invites[roomID]
				fmt.Printf("%s invited me to %s (%s)\n", invite.Sender, invite.Name, invite.ID)
				fmt.Println(invite.Accept())
			}
		}
		mxbot.Stop()
	}()

	return func() {
		stop <- true
	}
}
