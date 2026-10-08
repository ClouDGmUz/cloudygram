import base64
import traceback

from android_utils import run_on_ui_thread
from dalvik.system import InMemoryDexClassLoader
from java.nio import ByteBuffer
from org.telegram.messenger import ApplicationLoader

from .compact_nav_dex import DEX_B64


class CompactBottomNav:
    def __init__(self, plugin):
        self.plugin = plugin
        self.dex_class = None
        self.dex_loader = None
        self.author_sheet_class = None

    @property
    def is_loaded(self) -> bool:
        return self.dex_class is not None

    def load(self):
        if self.is_loaded:
            self.apply_settings()
            return
        try:
            dex_bytes = base64.b64decode(DEX_B64)
            buffer = ByteBuffer.wrap(dex_bytes)
            parent_cl = ApplicationLoader.applicationContext.getClassLoader()
            self.dex_loader = InMemoryDexClassLoader(buffer, parent_cl)
            self.dex_class = self.dex_loader.loadClass(
                "dev.rooni.compactbottomnav.CompactBottomNav"
            )
            self.author_sheet_class = self.dex_loader.loadClass(
                "dev.rooni.author.AuthorBottomSheet"
            )

            self.dex_class.getMethod("start").invoke(None)

            self.apply_settings()
            run_on_ui_thread(self.check_author_promo, delay=700)
        except Exception as e:
            self.plugin.logger.error(
                f"[Cloudygram] Failed to load Java CompactBottomNav module: {e}\n{traceback.format_exc()}"
            )

    def unload(self):
        if not self.is_loaded:
            return
        try:
            self.dex_class.getMethod("stop").invoke(None)
        except Exception as e:
            self.plugin.logger.error(
                f"[Cloudygram] Failed to unload Java CompactBottomNav module: {e}"
            )
        finally:
            self.dex_class = None
            self.author_sheet_class = None
            self.dex_loader = None

    def apply_settings(self):
        if not self.is_loaded:
            return
        try:
            hide_labels = bool(self.plugin.get_setting("compact_nav_hide_labels", True))
            add_search_button = bool(
                self.plugin.get_setting("compact_nav_add_search_button", True)
            )
            hide_actionbar_search = bool(
                self.plugin.get_setting("compact_nav_hide_actionbar_search", False)
            )

            for method in self.dex_class.getMethods():
                if method.getName() == "updateSettings" and len(method.getParameterTypes()) == 3:
                    method.invoke(None, hide_labels, add_search_button, hide_actionbar_search)
                    break
        except Exception as e:
            self.plugin.logger.error(
                f"[Cloudygram] Apply settings error: {e}\n{traceback.format_exc()}"
            )

    def check_author_promo(self):
        try:
            if self.plugin.get_setting("compact_nav_author_promo_shown", False):
                return

            if self.author_sheet_class is None:
                return

            is_sub = self.author_sheet_class.getMethod("isSubscribedToAuthor").invoke(None)
            if is_sub:
                self.plugin.set_setting("compact_nav_author_promo_shown", True)
                return

            shown = self.author_sheet_class.getMethod("showFromCurrentActivity").invoke(None)
            if shown:
                self.plugin.set_setting("compact_nav_author_promo_shown", True)
        except Exception as e:
            self.plugin.logger.error(
                f"[Cloudygram] Error in check_author_promo: {e}\n{traceback.format_exc()}"
            )

    def show_author_sheet(self):
        try:
            if self.author_sheet_class is not None:
                self.author_sheet_class.getMethod("showFromCurrentActivity").invoke(None)
        except Exception as e:
            self.plugin.logger.error(
                f"[Cloudygram] Error showing author sheet: {e}\n{traceback.format_exc()}"
            )
