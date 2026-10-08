from base_plugin import HookResult, HookStrategy
from elyx import strings
from ui.settings import Header, Switch

from .base import Feature


class GhostModeFeature(Feature):
    def on_plugin_load(self):
        self.host.add_hook("TL_messages_setTyping")
        self.host.add_hook("TL_messages_setEncryptedTyping")
        self.host.add_hook("TL_account_updateStatus")

    def pre_request_hook(self, request_name, account, request):
        if request_name in ("TL_messages_setTyping", "TL_messages_setEncryptedTyping"):
            if self.host.get_setting("ghost_no_typing", True):
                return HookResult(strategy=HookStrategy.CANCEL)
        elif request_name == "TL_account_updateStatus":
            if self.host.get_setting("ghost_always_offline", True):
                request.offline = True
                return HookResult(strategy=HookStrategy.MODIFY, request=request)
        return HookResult()

    def create_settings(self):
        return [
            Header(text=strings("ghost_title")),
            Switch(
                key="ghost_no_typing",
                text=strings("ghost_no_typing"),
                subtext=strings("ghost_no_typing_hint"),
                default=True,
                icon="msg_edit",
            ),
            Switch(
                key="ghost_always_offline",
                text=strings("ghost_always_offline"),
                subtext=strings("ghost_always_offline_hint"),
                default=True,
                icon="msg_edit",
            ),
        ]


def build(host):
    return GhostModeFeature(host)
