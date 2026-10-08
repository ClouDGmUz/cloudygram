from android_utils import copy_to_clipboard
from base_plugin import MenuItemData, MenuItemType
from elyx import strings
from ui.settings import Header, Text

from .base import Feature


class ChatIdsFeature(Feature):
    def __init__(self, host):
        super().__init__(host)
        self._items = []

    def on_plugin_load(self):
        self._items = [
            self.host.add_menu_item(
                MenuItemData(
                    menu_type=MenuItemType.CHAT_ACTION_MENU,
                    text=strings("ids_copy_chat"),
                    icon="msg_copy",
                    on_click=lambda ctx: self._copy(ctx.get("chatId")),
                )
            ),
            self.host.add_menu_item(
                MenuItemData(
                    menu_type=MenuItemType.MESSAGE_CONTEXT_MENU,
                    text=strings("ids_copy_message"),
                    icon="msg_copy",
                    on_click=lambda ctx: self._copy_message(ctx),
                )
            ),
            self.host.add_menu_item(
                MenuItemData(
                    menu_type=MenuItemType.PROFILE_ACTION_MENU,
                    text=strings("ids_copy_user"),
                    icon="msg_copy",
                    on_click=lambda ctx: self._copy(ctx.get("userId")),
                )
            ),
        ]

    def on_plugin_unload(self):
        for item_id in self._items:
            if item_id:
                self.host.remove_menu_item(item_id)
        self._items = []

    def _copy(self, value):
        if value:
            copy_to_clipboard(str(value))

    def _copy_message(self, ctx):
        message = ctx.get("message")
        if message is not None:
            self._copy(message.getId())

    def create_settings(self):
        return [
            Header(text=strings("ids_title")),
            Text(
                text=strings("ids_hint"),
                subtext=strings("ids_hint_sub"),
                icon="msg_info",
            ),
        ]


def build(host):
    return ChatIdsFeature(host)
