#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

from typing import Union

import pyrogram
from pyrogram import raw, types, utils


class GetChat:
    async def get_chat(
        self: "pyrogram.Client",
        chat_id: Union[int, str],
        force_full: bool = True
    ) -> "types.Chat":
        """Get up to date information about a chat.

        Information include current name of the user for one-on-one conversations, current username of a user, group or
        channel, etc.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                Unique identifier for the target chat in form of a *t.me/joinchat/* link, identifier (int) or username
                of the target channel/supergroup (in the format @username).

            force_full (``bool``, *optional*):
                Defaults to True.
                Pass False, if do not need to fetch the full variant.

        Returns:
            :obj:`~pyrogram.types.Chat`: On success, if you've already joined the chat, a chat object is returned,
            otherwise, a chat preview object is returned.

        Raises:
            ValueError: In case the chat invite link points to a chat you haven't joined yet.

        Example:
            .. code-block:: python

                chat = await app.get_chat("pyrogram")
                print(chat)
        """
        match = self.INVITE_LINK_RE.match(str(chat_id))

        if match:
            r = await self.invoke(
                raw.functions.messages.CheckChatInvite(
                    hash=match.group(1)
                )
            )

            if isinstance(r, raw.types.ChatInvite):
                return types.Chat._parse_chat_preview(self, r)

            await self.fetch_peers([r.chat])

            if isinstance(r.chat, raw.types.Chat):
                chat_id = -r.chat.id

            if isinstance(r.chat, raw.types.Channel):
                chat_id = utils.get_channel_id(r.chat.id)

        match2 = self.TME_PUBLIC_LINK_RE.match(str(chat_id))
        if match2:
            chat_id = match2.group(1) or match2.group(2) or chat_id

        peer = await self.resolve_peer(chat_id)

        if force_full:
            if isinstance(peer, raw.types.InputPeerChannel):
                r = await self.invoke(raw.functions.channels.GetFullChannel(channel=peer))
            elif isinstance(peer, (raw.types.InputPeerUser, raw.types.InputPeerSelf)):
                r = await self.invoke(raw.functions.users.GetFullUser(id=peer))
            else:
                r = await self.invoke(raw.functions.messages.GetFullChat(chat_id=peer.chat_id))
            return await types.Chat._parse_full(self, r)
        else:
            if isinstance(peer, (raw.types.InputPeerUser, raw.types.InputPeerSelf)):
                r = await self.invoke(raw.functions.users.GetUsers(id=[peer]))
                return types.Chat._parse_chat(self, r[0])
            else:
                if isinstance(peer, raw.types.InputPeerChannel):
                    r = await self.invoke(raw.functions.channels.GetChannels(id=[peer]))
                elif isinstance(peer, raw.types.InputPeerChat):
                    r = await self.invoke(raw.functions.messages.GetChats(id=[peer.chat_id]))
                else:
                    raise ValueError("unknown chat type")
                return types.Chat._parse_chat(self, r.chats[0])
