from typing import Tuple, Any
from maubot.handlers.command import Argument


class OptArgument(Argument):
    def __init__(self, name: str, label: str = None, arg_num: int = 1, *,
                 required: bool = False):
        super().__init__(name, label=label, required=False, pass_raw=True)
        self.arg_num = arg_num

    def match(self, val: str, **kwargs) -> Tuple[str, Any]:
        vals = val.split(" ")
        if len(vals) > self.arg_num:
            return " ".join(vals[1:]), vals[0]
        return val, None
