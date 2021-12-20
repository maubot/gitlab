# gitlab

A GitLab client and webhook receiver for maubot.

## Usage

### Set up the plugin like any other maubot plugin

Upload [the plugin](https://mau.dev/maubot/gitlab/-/pipelines) in Maubot Manager,
and then create an instance (an association of a plugin and a client).

Give this new instance an **ID** / name, for example `my_gitlab_bot`.
We will refer to this identifier later as `instance_id`.

## Logging into your GitLab account

Create a personal access token, as explained in Gitlab's documentation.

> You can create as many personal access tokens as you like from your GitLab profile.
>
> - 1. Sign in to GitLab.
> - 2. In the upper-right corner, click your avatar and select **Settings**.
> - 3. On the **User Settings** menu, select **Access Tokens**.
> - 4. Choose a name and optional expiry date for the token.
> - 5. Choose the [desired scopes](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#limiting-scopes-of-a-personal-access-token).
> - 6. Click the **Create personal access token** button.
> - 7. Save the personal access token somewhere safe. If you navigate away or refresh your page, and you did not save the token, you must create a new one.
>
> _Source: <https://docs.gitlab.com/ee/user/profile/personal_access_tokens>._

Invite the bot to a Matrix room.

Assuming the base command to invoke the bot is `gitlab`, adapt the following command and invoke the bot with:

**Warning: Make sure not to enter this command in a public room!**

```txt
!gitlab server login https://gitlab.example.org PERSONAL_ACCESS_TOKEN
```

You should now be logged in your Gitlab account. Use `!gitlab` to view the list of commands and `!gitlab <command>` to
view help for subcommands (e.g. `!gitlab webhook`).

## Setting up webhooks

**The instructions below are for adding webhooks manually. You can also simply use `!gitlab webhook add <repo>`, but
that requires logging into the bot using your GitLab token first.**

Go to the desired repository's webhooks settings, in Gitlab, under **Your repo** > **Settings** > **Webhooks**.

Configure the **URL** as follows:

```sh
https://${server_name}/${plugin_base_path}/${instance_id}/webhooks?room=${room_id}
```

Where

- `${server_name}` is an ip address or domain name where your Maubot instance is reachable
- `${base_path}` is the base path for plugin endpoint as configured under `server.plugin_base_path` in `config.yaml`
- `${instance_id}` is the identifier you previously defined while setting up the plugin instance, here `my_gitlab_bot`
- `${room_id}` is the Matrix room identifier as defined in its URL, or under **Room Settings** > **Advanced** > **Internal room identifier**

Which gives for example, with the default configuration: <https://maubot.example.org/_matrix/maubot/plugin/my_gitlab_bot/webhooks?room=!XXXXXXXXXXXX>.

As `secret`, set the token shown in Maubot's **Instances** > **my_gitlab_bot** > **secret:**

Afterwhile, configure the desired permissions, [enable SSL verification if needed](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#ssl-verification) and create the webhook.

Finally, test your webhook and fix the configuration until you get a return status like `2xx`.

_Gitlab webhooks documentation: <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html>._
