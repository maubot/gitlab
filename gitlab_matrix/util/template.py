# gitlab - A GitLab client and webhook receiver for maubot
# Copyright (C) 2021 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import Dict, Any, Tuple, Callable, Iterable, List, Union
import os.path

from jinja2 import Environment as JinjaEnvironment, Template, BaseLoader, TemplateNotFound

from mautrix.util import markdown

from maubot.loader import BasePluginLoader


class TemplateUtil:
    # FIXME remove
    @staticmethod
    def debug(msg: str) -> str:
        print(msg)
        return "debuggeth"

    @staticmethod
    def bold_scope(label: str) -> str:
        try:
            scope, label = label.rsplit("::", 1)
            return f"{scope}::<strong>{label}</strong>"
        except ValueError:
            return label

    @staticmethod
    def pluralize(val: int, unit: str) -> str:
        if val == 1:
            return f"{val} {unit}"
        return f"{val} {unit}s"

    @classmethod
    def format_time(cls, seconds: Union[int, float], enable_days: bool = False) -> str:
        seconds = abs(seconds)
        frac_seconds = round(seconds - int(seconds), 1)
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if enable_days:
            days, hours = divmod(hours, 24)
        else:
            days = 0
        parts = []
        if days > 0:
            parts.append(cls.pluralize(days, "day"))
        if hours > 0:
            parts.append(cls.pluralize(hours, "hour"))
        if minutes > 0:
            parts.append(cls.pluralize(minutes, "minute"))
        if seconds > 0 or len(parts) == 0:
            parts.append(cls.pluralize(seconds + frac_seconds, "second"))

        if len(parts) == 1:
            return parts[0]
        return ", ".join(parts[:-1]) + f" and {parts[-1]}"

    @staticmethod
    def join_human_list(data: List[str], *, joiner: str = ", ", final_joiner: str = " and ",
                        mutate: Callable[[str], str] = lambda val: val) -> str:
        if not data:
            return ""
        elif len(data) == 1:
            return mutate(data[0])
        return joiner.join(mutate(val) for val in data[:-1]) + final_joiner + mutate(data[-1])


class TemplateProxy:
    _env: JinjaEnvironment
    _args: Dict[str, Any]

    def __init__(self, env: JinjaEnvironment, args: Dict[str, Any]) -> None:
        self._env = env
        self._args = args

    def __getattr__(self, item: str) -> str:
        try:
            tpl = self._env.get_template(item)
        except TemplateNotFound:
            raise AttributeError(item)
        return tpl.render(**self._args)


class PluginTemplateLoader(BaseLoader):
    plugin_loader: BasePluginLoader
    directory: str
    macros: str

    def __init__(self, loader: BasePluginLoader, directory: str) -> None:
        self.plugin_loader = loader
        self.directory = directory
        self.macros = loader.sync_read_file("templates/macros.html").decode("utf-8")

    def get_source(self, environment: Any, name: str) -> Tuple[str, str, Callable[[], bool]]:
        path = f"{os.path.join(self.directory, name)}.html"
        try:
            tpl = self.plugin_loader.sync_read_file(path)
        except KeyError:
            raise TemplateNotFound(name)
        return self.macros + tpl.decode("utf-8"), name, lambda: True

    def list_templates(self) -> Iterable[str]:
        return [os.path.splitext(os.path.basename(path))[1]
                for path in self.plugin_loader.sync_list_files(self.directory)
                if path.endswith(".html")]


class TemplateManager:
    _env: JinjaEnvironment
    _loader: PluginTemplateLoader

    def __init__(self, loader: BasePluginLoader, directory: str) -> None:
        self._loader = PluginTemplateLoader(loader, directory)
        self._env = JinjaEnvironment(loader=self._loader, lstrip_blocks=True, trim_blocks=True,
                                     extensions=["jinja2.ext.do"])
        self._env.filters["markdown"] = markdown.render

    def __getitem__(self, item: str) -> Template:
        return self._env.get_template(item)

    def proxy(self, args: Dict[str, Any]) -> TemplateProxy:
        return TemplateProxy(self._env, args)
