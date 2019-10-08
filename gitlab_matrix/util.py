from typing import Tuple, Any
from maubot import MessageEvent
from maubot.handlers.command import Argument


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
            return " ".join(vals[1:]), vals[0]
        return val, None
