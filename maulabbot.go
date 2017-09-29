// maulabbot - A GitLab bot for Matrix
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
	"os"
	"os/signal"
	"syscall"

	flag "maunium.net/go/mauflag"
)

var wantHelp, _ = flag.MakeHelpFlag()

func main() {
	flag.SetHelpTitles("maulabbot - A GitLab bot for Matrix", "maulabbot [-h] [-s hs] [-u user] [-p passwd] [-l listen addr] [-g listen path] [-e secret]")
	err := flag.Parse()
	if err != nil {
		fmt.Println(err)
		*wantHelp = true
	}
	if *wantHelp {
		flag.PrintHelp()
		return
	}
	stopMatrix := startMatrix()
	stopWebhook := startWebhook()

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c
	stopMatrix()
	stopWebhook()
}
