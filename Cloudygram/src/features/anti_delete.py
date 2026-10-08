import os

from base_plugin import HookResult
from client_utils import run_on_queue
from elyx import strings
from file_utils import ensure_dir_exists, get_plugins_dir, read_file, write_file
from ui.bulletin import BulletinHelper
from ui.settings import Header, Switch

from .base import Feature

DELETE_UPDATES = ("updateDeleteMessages", "updateDeleteChannelMessages")
NEW_UPDATES = ("updateNewMessage", "updateNewChannelMessage")


class AntiDeleteFeature(Feature):
    def __init__(self, host):
        super().__init__(host)
        self._cache = {}
        self._deleted = []

    def on_plugin_load(self):
        for name in NEW_UPDATES + DELETE_UPDATES:
            self.host.add_hook(name, match_substring=True)

    def on_update_hook(self, update_name, account, update):
        if not self.host.get_setting("anti_delete_enabled", True):
            return HookResult()
        try:
            if any(name in update_name for name in DELETE_UPDATES):
                self._handle_delete(account, update)
            elif any(name in update_name for name in NEW_UPDATES):
                self._handle_new(account, update)
        except Exception as e:
            self.host.logger.debug(f"anti_delete: {e}")
        return HookResult()

    def _handle_new(self, account, update):
        # update.message is a raw TLRPC.Message: plain `id` / `message` fields.
        message = getattr(update, "message", None)
        if message is None:
            return
        text = getattr(message, "message", None)
        if text:
            peer = getattr(message, "peer_id", None)
            channel_id = int(getattr(peer, "channel_id", 0) or 0) if peer is not None else 0
            self._cache[(int(account), channel_id, int(message.id))] = str(text)
            if len(self._cache) > 2000:
                self._cache.pop(next(iter(self._cache)))

    def _handle_delete(self, account, update):
        ids = getattr(update, "messages", None)
        if ids is None:
            return
        # Channel message ids are per-channel; private/basic-group ids use channel 0.
        channel_id = int(getattr(update, "channel_id", 0) or 0)
        found = False
        for index in range(ids.size()):
            text = self._cache.pop((int(account), channel_id, int(ids.get(index))), None)
            if text:
                self._deleted.append(text)
                found = True
        if len(self._deleted) > 200:
            self._deleted = self._deleted[-200:]
        if found and self._deleted:
            last = self._deleted[-1]
            run_on_queue(lambda: self._persist_and_notify(last))

    def _persist_and_notify(self, text):
        try:
            dir_path = os.path.join(get_plugins_dir(), "cloudygram_exports")
            ensure_dir_exists(dir_path)
            path = os.path.join(dir_path, "deleted.txt")
            write_file(path, (read_file(path) or "") + text + "\n")
        except Exception as e:
            self.host.logger.debug(f"anti_delete save: {e}")
        try:
            BulletinHelper.show_info(strings("anti_delete_saved"))
        except Exception:
            pass

    def create_settings(self):
        return [
            Header(text=strings("anti_delete_title")),
            Switch(
                key="anti_delete_enabled",
                text=strings("anti_delete_enabled"),
                subtext=strings("anti_delete_hint"),
                default=True,
                icon="msg_edit",
            ),
        ]


def build(host):
    return AntiDeleteFeature(host)
