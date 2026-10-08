from base_plugin import HookResult, HookStrategy
from elyx import strings
from ui.settings import Header, Input, Switch

from .base import Feature


class AutoDeleteFeature(Feature):
    def on_plugin_load(self):
        self.host.add_on_send_message_hook()

    def on_send_message_hook(self, account, params):
        if not self.host.get_setting("auto_delete_enabled", False):
            return HookResult()
        try:
            seconds = int(self.host.get_setting("auto_delete_seconds", 60))
        except Exception:
            seconds = 60
        if seconds <= 0:
            return HookResult()
        try:
            params.ttl = seconds
            return HookResult(strategy=HookStrategy.MODIFY, params=params)
        except Exception as e:
            self.host.logger.debug(f"auto_delete: {e}")
            return HookResult()

    def create_settings(self):
        return [
            Header(text=strings("auto_delete_title")),
            Switch(
                key="auto_delete_enabled",
                text=strings("auto_delete_enabled"),
                subtext=strings("auto_delete_hint"),
                default=False,
                icon="msg_edit",
            ),
            Input(
                key="auto_delete_seconds",
                text=strings("auto_delete_seconds"),
                subtext=strings("auto_delete_seconds_hint"),
                default="60",
                icon="msg_edit",
            ),
        ]


def build(host):
    return AutoDeleteFeature(host)
