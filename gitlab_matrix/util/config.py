# gitlab - A GitLab client and webhook receiver for maubot
# Copyright (C) 2019 Lorenz Steinert
# Copyright (C) 2019 Tulir Asokan
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
import secrets

from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        if not self["secret"] or self["secret"] == "put a random password here":
            helper.base["secret"] = secrets.token_urlsafe(32)
        else:
            helper.copy("secret")
        helper.copy("base_command")
        helper.copy("send_as_notice")
        helper.copy("time_format")
        helper.copy("hide_details")
