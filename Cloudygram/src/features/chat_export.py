import os

from android_utils import copy_to_clipboard
from base_plugin import MenuItemData, MenuItemType
from client_utils import get_messages_controller, send_request
from elyx import strings
from file_utils import ensure_dir_exists, get_plugins_dir, write_file
from org.telegram.tgnet import TLRPC
from ui.bulletin import BulletinHelper
from ui.settings import Header, Input

from .base import Feature


class ChatExportFeature(Feature):
    def __init__(self, host):
        super().__init__(host)
        self._item = None

    def on_plugin_load(self):
        self._item = self.host.add_menu_item(
            MenuItemData(
                menu_type=MenuItemType.CHAT_ACTION_MENU,
                text=strings("chat_export_action"),
                icon="msg_archive",
                on_click=self._export,
            )
        )

    def on_plugin_unload(self):
        if self._item:
            self.host.remove_menu_item(self._item)
            self._item = None

    def _export(self, ctx):
        try:
            chat_id = ctx.get("chatId") or ctx.get("dialog_id") or ctx.get("dialogId")
            if not chat_id:
                return
            chat_id = int(chat_id)

            request = TLRPC.TL_messages_getHistory()
            request.peer = get_messages_controller().getInputPeer(chat_id)
            if request.peer is None:
                return
            request.limit = int(self.host.get_setting("chat_export_limit", 100))

            send_request(request, lambda response, error: self._on_history(chat_id, response, error))
            BulletinHelper.show_info(strings("chat_export_started"))
        except Exception as e:
            self.host.logger.debug(f"chat_export: {e}")

    def _on_history(self, chat_id, response, error):
        try:
            if error or response is None:
                return
            messages = getattr(response, "messages", None)
            if messages is None:
                return
            lines = []
            for index in range(messages.size()):
                message = messages.get(index)
                text = getattr(message, "message", "") or ""
                lines.append(f"[{message.id}] {text}")

            dir_path = os.path.join(get_plugins_dir(), "cloudygram_exports")
            ensure_dir_exists(dir_path)
            path = os.path.join(dir_path, f"chat_{chat_id}.txt")
            write_file(path, "\n".join(lines))
            copy_to_clipboard(path)
            BulletinHelper.show_info(strings("chat_export_done"))
        except Exception as e:
            self.host.logger.debug(f"chat_export write: {e}")

    def create_settings(self):
        return [
            Header(text=strings("chat_export_title")),
            Input(
                key="chat_export_limit",
                text=strings("chat_export_limit"),
                subtext=strings("chat_export_limit_hint"),
                default="100",
                icon="msg_edit",
            ),
        ]


def build(host):
    return ChatExportFeature(host)
