Maunium GitLab bot
==================
A Gitlab bot for Matrix. It uses
[maubot](https://github.com/maubot/maubot),
[go-playground webhooks](https://github.com/go-playground/webhooks) and
[go-gitlab](https://github.com/xanzy/go-gitlab)

## Discussion
Matrix room: [#maulabbot:maunium.net](https://matrix.to/#/#maulabbot:maunium.net)

## Features
* [x] Spam a Matrix room using GitLab webhooks
	* [X] Issues/merge requests
		* [X] Comments
	* [X] Push events
	* [x] Tag creation
	* [ ] Pipeline events
	* [ ] Wiki page edits
* [x] Log in to GitLab accounts (per-user)
	* [ ] [Maybe] Allow logging in to multiple GitLab servers and add a per-room config of which server to use in that room by default.
* [x] Commits
	* [x] View full commit messages
	* [x] View commit diffs
	* [x] View commit history
* [x] Issue management
	* [x] Read issues
	* [x] Create/close/reopen issues
	* [x] Read comments on issues
	* [x] Comment on issues
* [ ] Shorter commands

## Usage
~~Configure the server by copying `example-config.json` to `config.json` and
filling out the fields.~~

### Webhooks
When adding a GitLab webhook, add the internal room ID as a query string in the
field `room`. For example, if the address + path is `https://example.com/webhook`,
you could add `https://example.com/webhook?room=!HweXqCwBqJzepVovYt:matrix.org`
as the webhook URL and the bot would send notifications to the room whose
internal ID is `!HweXqCwBqJzepVovYt:matrix.org`.

### Commands
You should log in with your GitLab access token, since most commands require
authentication. You can log in by sending `!gitlab login <access token>` to the
bot in a private room.

The bot only handles commands prefixed with `!gitlab`. Use `!gitlab help` for help.
