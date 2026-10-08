from android_utils import copy_to_clipboard
from base_plugin import MenuItemData, MenuItemType
from elyx import strings
from ui.settings import Header, Text

from .base import Feature


class CopyLinkFeature(Feature):
    def __init__(self, host):
        super().__init__(host)
        self._item = None

    def on_plugin_load(self):
        self._item = self.host.add_menu_item(
            MenuItemData(
                menu_type=MenuItemType.MESSAGE_CONTEXT_MENU,
                text=strings("copy_link_action"),
                icon="msg_link",
                on_click=self._on_click,
            )
        )

    def on_plugin_unload(self):
        if self._item:
            self.host.remove_menu_item(self._item)
            self._item = None

    def _on_click(self, ctx):
        link = self._build_link(ctx)
        if link:
            copy_to_clipboard(link)

    def _build_link(self, ctx):
        try:
            message = ctx.get("message")
            if message is None:
                return None
            msg_id = message.getId()

            username = None
            chat = ctx.get("chat")
            user = ctx.get("user")
            if chat is not None:
                username = getattr(chat, "username", None)
            elif user is not None:
                username = getattr(user, "username", None)
            if username:
                return f"https://t.me/{username}/{msg_id}"

            dialog_id = ctx.get("dialog_id") or ctx.get("dialogId") or ctx.get("chatId")
            if not dialog_id:
                return None
            internal = int(dialog_id)
            if internal < 0:
                internal = -internal
            if str(internal).startswith("100"):
                internal = int(str(internal)[3:])
            return f"https://t.me/c/{internal}/{msg_id}"
        except Exception as e:
            self.host.logger.debug(f"copy_link: {e}")
            return None

    def create_settings(self):
        return [
            Header(text=strings("copy_link_title")),
            Text(text=strings("copy_link_hint"), icon="msg_info"),
        ]


def build(host):
    return CopyLinkFeature(host)
