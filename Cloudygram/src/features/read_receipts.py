from base_plugin import HookResult, HookStrategy
from elyx import strings
from ui.settings import Header, Switch

from .base import Feature

READ_REQUESTS = (
    "TL_messages_readHistory",
    "TL_messages_readMessageContents",
    "TL_messages_readEncryptedHistory",
)


class ReadReceiptsFeature(Feature):
    def on_plugin_load(self):
        for name in READ_REQUESTS:
            self.host.add_hook(name)

    def pre_request_hook(self, request_name, account, request):
        if request_name in READ_REQUESTS and self.host.get_setting("hide_read_receipts", True):
            return HookResult(strategy=HookStrategy.CANCEL)
        return HookResult()

    def create_settings(self):
        return [
            Header(text=strings("read_receipts_title")),
            Switch(
                key="hide_read_receipts",
                text=strings("hide_read_receipts"),
                subtext=strings("hide_read_receipts_hint"),
                default=True,
                icon="msg_edit",
            ),
        ]


def build(host):
    return ReadReceiptsFeature(host)
