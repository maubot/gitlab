from typing import Tuple, Any
from maubot import MessageEvent
from maubot.handlers.command import Argument
from gitlab import Gitlab
from gitlab.exceptions import GitlabAuthenticationError
from typing import Dict


class OptUrlAliasArgument(Argument):
    def __init__(self, name: str, label: str = None,
                 arg_num: int = 1, *, required: bool = False):
        super().__init__(name, label=label, required=required, pass_raw=True)
        self.arg_num = arg_num

    def match(self, val: str, evt: MessageEvent, instance: 'Gitlab',
              **kwargs) -> Tuple[str, Any]:
        vals = val.split(" ")

        if (len(vals) > self.arg_num
                and (vals[0] in instance.db.get_servers(evt.sender)
                     or vals[0] in instance.db.get_aliases(evt.sender))):
            return " ".join(vals[1:]), instance.db.get_login(evt.sender,
                                                             url_alias=val[0])
        return val, instance.db.get_login(evt.sender)


def GitlabLogin(func):
    async def wrapper(self, evt: MessageEvent,
                      login: Dict[str, str], **kwargs):
        try:
            with Gitlab(login['gitlab_server'],
                        login['api_token']) as gl:
                await func(self, evt, gl=gl, **kwargs)
        except GitlabAuthenticationError as e:
            await evt.reply("Invalid Access Token.\n\n{0}".format(e))
        except Exception as e:
            self.log.info("Failed to handle Command.", exc_info=True)
            self.log.debug(e)
    return wrapper
