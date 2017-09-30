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
	"time"

	flag "maunium.net/go/mauflag"
)

var wantHelp, _ = flag.MakeHelpFlag()
var configPath = flag.MakeFull("c", "config", "The path to the config file.", "config.json").String()

func main() {
	flag.SetHelpTitles("maulabbot - A GitLab bot for Matrix", "maulabbot [-h] [-c /path/to/config]")
	err := flag.Parse()
	if err != nil {
		fmt.Println(err)
		*wantHelp = true
	}
	if *wantHelp {
		flag.PrintHelp()
		return
	}

	err = loadConfig(*configPath)
	if err != nil {
		fmt.Println("Error loading config:", err)
		return
	}

	// Initialize everything
	stopMatrix := startMatrix()
	stopWebhook := startWebhook()
	loadGitlabTokens()

	// Wait for interrupts
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c

	// Stop everything
	stopMatrix()
	stopWebhook()
	time.Sleep(1 * time.Second)
}
