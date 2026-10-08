from typing import Any, List

from android_utils import copy_to_clipboard
from base_plugin import BasePlugin, HookResult, HookStrategy
from elyx import assets, settings, strings
from ui.settings import Header, Input, Switch, Text

from .compact_bottom_nav import CompactBottomNav
from .features.registry import FEATURES
from .greeting import build_greeting

DEVELOPER = "@cloudgmuz"
CHANNEL_URL = "https://t.me/cloudyextera"
UPDATE_CHANNEL_ID = -1004466296728
UPDATE_MESSAGE_ID = 4

CLOUDYLIB_MIN_VERSION = max(
    (spec["min_cloudylib"] for spec in FEATURES if spec.get("min_cloudylib")),
    default=None,
)


class CloudygramPlugin(BasePlugin):
    def on_plugin_load(self):
        self.nav = CompactBottomNav(self)
        self._features = {}
        self.logger.info(strings("loaded"))

        wave_icon = assets.wave
        self.logger.info(f"Bundled icon: {wave_icon.path_str}")

        self._load_features()

        if self.get_setting("compact_nav_enabled", False):
            self.nav.load()

        self._register_autoupdate()

    def on_plugin_unload(self):
        if getattr(self, "nav", None) is not None:
            self.nav.unload()

        for fid in list(getattr(self, "_features", {}).keys()):
            self._stop_feature(fid)

    def _feature_modules(self):
        modules = {}
        try:
            from .features import endless_folders

            modules["endless_folders"] = endless_folders
        except Exception as e:
            self.logger.error(f"[feature] endless_folders import failed: {e}")
        try:
            from .features import user_info_saver

            modules["user_info_saver"] = user_info_saver
        except Exception as e:
            self.logger.error(f"[feature] user_info_saver import failed: {e}")
        try:
            from .features import recent_actions_plus

            modules["recent_actions_plus"] = recent_actions_plus
        except Exception as e:
            self.logger.error(f"[feature] recent_actions_plus import failed: {e}")
        try:
            from .features import admin_tools

            modules["admin_tools"] = admin_tools
        except Exception as e:
            self.logger.error(f"[feature] admin_tools import failed: {e}")
        try:
            from .features import no_forward_limit

            modules["no_forward_limit"] = no_forward_limit
        except Exception as e:
            self.logger.error(f"[feature] no_forward_limit import failed: {e}")
        try:
            from .features import ghost_mode

            modules["ghost_mode"] = ghost_mode
        except Exception as e:
            self.logger.error(f"[feature] ghost_mode import failed: {e}")
        try:
            from .features import chat_ids

            modules["chat_ids"] = chat_ids
        except Exception as e:
            self.logger.error(f"[feature] chat_ids import failed: {e}")
        try:
            from .features import read_receipts

            modules["read_receipts"] = read_receipts
        except Exception as e:
            self.logger.error(f"[feature] read_receipts import failed: {e}")
        try:
            from .features import copy_link

            modules["copy_link"] = copy_link
        except Exception as e:
            self.logger.error(f"[feature] copy_link import failed: {e}")
        try:
            from .features import anti_delete

            modules["anti_delete"] = anti_delete
        except Exception as e:
            self.logger.error(f"[feature] anti_delete import failed: {e}")
        try:
            from .features import auto_delete

            modules["auto_delete"] = auto_delete
        except Exception as e:
            self.logger.error(f"[feature] auto_delete import failed: {e}")
        try:
            from .features import chat_export

            modules["chat_export"] = chat_export
        except Exception as e:
            self.logger.error(f"[feature] chat_export import failed: {e}")
        return modules

    def _load_features(self):
        modules = self._feature_modules()
        for spec in FEATURES:
            module = modules.get(spec["module"])
            if module is None:
                continue

            fid = spec["id"]
            try:
                feature = module.build(self)
            except Exception as e:
                self.logger.error(f"[feature] {fid} build failed: {e}")
                continue

            self._features[fid] = feature

            if self.get_setting(f"feature_{fid}_enabled", False):
                self._start_feature(fid)

    def _start_feature(self, fid):
        feature = self._features.get(fid)
        if feature is None:
            return
        try:
            feature.on_plugin_load()
        except Exception as e:
            self.logger.error(f"[feature] {fid} load failed: {e}")

    def _stop_feature(self, fid):
        feature = self._features.get(fid)
        if feature is None:
            return
        try:
            feature.on_plugin_unload()
        except Exception as e:
            self.logger.error(f"[feature] {fid} unload failed: {e}")

    def _notify_reload(self, fid, enabled):
        try:
            from ui.bulletin import BulletinHelper

            BulletinHelper.show_info(strings("feature_reload_note"))
        except Exception as e:
            self.logger.debug(f"[feature] reload notice failed: {e}")

    def _register_autoupdate(self):
        try:
            import cloudylib

            cloudylib.add_autoupdater_task(UPDATE_CHANNEL_ID, UPDATE_MESSAGE_ID)
        except Exception as e:
            self.logger.debug(f"CloudyLib autoupdate not available: {e}")

    def _cloudylib_status(self):
        try:
            import cloudylib
        except Exception:
            return "missing", None

        version = str(getattr(cloudylib, "__version__", "") or "")
        checker = getattr(cloudylib, "is_zwylib_version_sufficient", None)
        if checker is None:
            checker = getattr(cloudylib, "is_cloudylib_version_sufficient", None)
        if checker is not None:
            try:
                if not checker("Cloudygram", CLOUDYLIB_MIN_VERSION, notify=False):
                    return "outdated", version
            except Exception:
                pass
        return "ok", version

    def _reload_plugin(self, _=None):
        try:
            import cloudylib

            cloudylib.PluginUtils.reload_plugin("cloudygram")
        except Exception as e:
            self.logger.error(f"[reload] {e}")

    def pre_request_hook(self, request_name, account, request):
        return self._dispatch("pre_request_hook", request_name, account, request)

    def post_request_hook(self, request_name, account, response, error):
        return self._dispatch("post_request_hook", request_name, account, response, error)

    def on_send_message_hook(self, account, params):
        return self._dispatch("on_send_message_hook", account, params)

    def on_update_hook(self, update_name, account, update):
        return self._dispatch("on_update_hook", update_name, account, update)

    def on_updates_hook(self, container_name, account, updates):
        return self._dispatch("on_updates_hook", container_name, account, updates)

    def _dispatch(self, method_name, *args):
        for feature in getattr(self, "_features", {}).values():
            fn = getattr(type(feature), method_name, None)
            if fn is None:
                continue
            try:
                result = fn(feature, *args)
            except Exception as e:
                self.logger.error(f"[feature] {method_name} failed: {e}")
                continue
            if result is not None and getattr(result, "strategy", HookStrategy.DEFAULT) != HookStrategy.DEFAULT:
                return result
        return HookResult()

    def create_settings(self) -> List[Any]:
        name = settings.get("name", "Alice")
        status, version = self._cloudylib_status()
        features_subtext = strings("features_hint")
        features_red = False
        if status != "ok":
            features_subtext = strings("cloudylib_missing_short")
            features_red = True
        return [
            Header(text=strings("settings_title")),
            Input(
                key="name",
                text=strings("name_label"),
                subtext=strings("name_hint"),
                default="Alice",
                icon="msg_edit",
            ),
            Text(
                text=build_greeting(name),
                subtext="This row is generated from two project files.",
                icon="msg_info",
            ),
            Text(
                text=strings("compact_nav_title"),
                subtext=strings("compact_nav_folder_hint"),
                icon="msg_arrow_forward",
                create_sub_fragment=self._create_compact_page,
            ),
            Text(
                text=strings("features_title"),
                subtext=features_subtext,
                icon="msg_arrow_forward",
                red=features_red,
                create_sub_fragment=self._create_features_page,
            ),
            Header(text=strings("about_title")),
            Text(
                text=strings("about_developer"),
                subtext=DEVELOPER,
                icon="msg_openprofile",
                on_click=lambda _=None: copy_to_clipboard(DEVELOPER),
            ),
            Text(
                text=strings("about_channel"),
                subtext=CHANNEL_URL,
                icon="msg_info",
                on_click=lambda _=None: copy_to_clipboard(CHANNEL_URL),
            ),
        ]

    def _create_features_page(self) -> List[Any]:
        status, version = self._cloudylib_status()
        items: List[Any] = [Header(text=strings("features_title"))]
        if status == "missing":
            items.append(
                Text(
                    text=strings("cloudylib_missing"),
                    subtext=strings("cloudylib_missing_hint"),
                    icon="msg_error",
                    red=True,
                )
            )
        elif status == "outdated":
            items.append(
                Text(
                    text=strings("cloudylib_outdated"),
                    subtext=strings("cloudylib_outdated_hint", version=CLOUDYLIB_MIN_VERSION),
                    icon="msg_error",
                    red=True,
                )
            )
        if status == "ok":
            items.append(
                Text(
                    text=strings("reload_now"),
                    subtext=strings("reload_now_hint"),
                    icon="msg_photo_switch2",
                    accent=True,
                    on_click=self._reload_plugin,
                )
            )
        for spec in FEATURES:
            fid = spec["id"]
            items.append(
                Text(
                    text=strings(spec["title"]),
                    subtext=strings("feature_configure_hint"),
                    icon="msg_arrow_forward",
                    create_sub_fragment=(lambda fid=fid: self._create_feature_page(fid)),
                )
            )
        return items

    def _create_feature_page(self, fid: str) -> List[Any]:
        spec = next((s for s in FEATURES if s["id"] == fid), None)
        title = spec["title"] if spec else fid
        credit = spec.get("credit", "") if spec else ""
        feature = getattr(self, "_features", {}).get(fid)
        items: List[Any] = [
            Header(text=strings(title)),
            Switch(
                key=f"feature_{fid}_enabled",
                text=strings("feature_enable"),
                default=False,
                on_change=(lambda val, fid=fid: self._notify_reload(fid, val)),
            ),
            Text(
                text=strings("feature_reload_note"),
                icon="msg_info",
            ),
        ]

        if feature is not None and getattr(type(feature), "create_settings", None) is not None:
            try:
                items.extend(feature.create_settings())
            except Exception as e:
                items.append(Text(text=f"{e}", icon="msg_error", red=True))

        items.append(
            Text(
                text=strings("feature_credit"),
                subtext=credit,
                icon="msg_info",
            )
        )
        return items

    def _create_compact_page(self) -> List[Any]:
        return [
            Header(text=strings("compact_nav_title")),
            Switch(
                key="compact_nav_enabled",
                text=strings("compact_nav_enabled"),
                subtext=strings("compact_nav_enabled_hint"),
                default=False,
                icon="msg_edit",
                on_change=lambda val: self._toggle_compact_nav(val),
            ),
            Switch(
                key="compact_nav_hide_labels",
                text=strings("compact_nav_hide_labels"),
                subtext=strings("compact_nav_hide_labels_hint"),
                default=True,
                icon="msg_edit",
                on_change=lambda val: self.nav.apply_settings(),
            ),
            Switch(
                key="compact_nav_add_search_button",
                text=strings("compact_nav_add_search_button"),
                subtext=strings("compact_nav_add_search_button_hint"),
                default=True,
                icon="msg_search",
                on_change=lambda val: self.nav.apply_settings(),
            ),
            Header(text=strings("compact_nav_actionbar_title")),
            Switch(
                key="compact_nav_hide_actionbar_search",
                text=strings("compact_nav_hide_actionbar_search"),
                subtext=strings("compact_nav_hide_actionbar_search_hint"),
                default=False,
                icon="msg_search",
                on_change=lambda val: self.nav.apply_settings(),
            ),
            Text(
                text=strings("compact_nav_credit"),
                subtext=strings("compact_nav_credit_hint"),
                icon="msg_openprofile",
                on_click=lambda _=None: self.nav.show_author_sheet(),
            ),
        ]

    def _toggle_compact_nav(self, enabled):
        if enabled:
            self.nav.load()
        else:
            self.nav.unload()
