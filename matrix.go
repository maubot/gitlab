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

var mxbot *mautrix.MatrixBot

func startMatrix() func() {
	mxbot = mautrix.Create(config.Matrix.Homeserver)

	if len(config.Matrix.AuthToken) == 0 {
		err := mxbot.PasswordLogin(config.Matrix.Username, config.Matrix.Password)
		if err != nil {
			panic(err)
		}
		config.Matrix.AuthToken = mxbot.AccessToken
		saveConfig(*configPath)
	} else {
		mxbot.SetToken(config.Matrix.Username, config.Matrix.AuthToken)
		mxbot.TxnID = config.Matrix.TransactionID
	}

	fmt.Println("Connected to Matrix homeserver at", config.Matrix.Homeserver, "as", config.Matrix.Username)

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
					lines := strings.Split(msg, "\n")
					parts := strings.Split(lines[0], " ")
					if len(lines) > 1 {
						lines = lines[1:]
					} else {
						lines = []string{}
					}
					cmd := parts[0]
					var args []string
					if len(parts) > 1 {
						args = parts[1:]
					}
					handleCommand(evt.Room, evt.Sender, cmd, args, lines)
				}
			case roomID := <-mxbot.InviteChan:
				invite := mxbot.Invites[roomID]
				fmt.Printf("%s invited me to %s (%s)\n", invite.Sender, invite.Name, invite.ID)
				err := invite.Accept()
				if err != nil {
					fmt.Println("Unexpected error:", err)
				}
			}
		}
		mxbot.Stop()
	}()

	return func() {
		stop <- true
		config.Matrix.TransactionID = mxbot.TxnID
		saveConfig(*configPath)
	}
}
