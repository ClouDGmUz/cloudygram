from android_utils import copy_to_clipboard
from base_plugin import MenuItemData, MenuItemType
from elyx import strings
from ui.bulletin import BulletinHelper
from ui.settings import Header, Text

from .base import Feature

# Channel/supergroup dialog ids are -(1000000000000 + channel_id).
CHANNEL_ID_OFFSET = 1000000000000


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
        else:
            BulletinHelper.show_error(strings("copy_link_unavailable"))

    def _build_link(self, ctx):
        # Only channels/supergroups have message links; private chats and
        # basic groups don't, so those return None.
        try:
            message = ctx.get("message")
            if message is None:
                return None
            msg_id = message.getId()

            dialog_id = None
            try:
                dialog_id = int(message.getDialogId())
            except Exception:
                raw = ctx.get("dialog_id") or ctx.get("dialogId")
                dialog_id = int(raw) if raw else None
            if dialog_id is None or dialog_id > -CHANNEL_ID_OFFSET:
                return None

            chat = ctx.get("chat")
            username = getattr(chat, "username", None) if chat is not None else None
            if username:
                return f"https://t.me/{username}/{msg_id}"
            return f"https://t.me/c/{-dialog_id - CHANNEL_ID_OFFSET}/{msg_id}"
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
