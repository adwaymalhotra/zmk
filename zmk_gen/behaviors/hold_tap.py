"""
Hold-Tap behavior and Home Row Mod (HRM) definitions.
"""
from typing import Union, List, Optional, Dict, Any
from .base import Behavior
from ..os_key import OsKey, CTL_GUI, GUI_CTL, ALT, SFT
from ..primitives.binding import LayerRef


class HoldTap(Behavior):
    def __init__(
        self,
        name: str,
        flavor: str = "tap-preferred",
        hold: str = "&kp",
        tap: str = "&kp",
        trigger_pos: Union[str, List[str], List[int]] = "",
        tapping_term_ms: Union[int, str] = "TAPPING_TERM",
        quick_tap_ms: Union[int, str] = "QUICK_TAP_MS",
        require_prior_idle_ms: Optional[Union[int, str]] = "PRIOR_IDLE_MS",
        bindings: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.flavor = flavor
        self.hold = hold if hold.startswith("&") else f"&{hold}"
        self.tap = tap if tap.startswith("&") else f"&{tap}"
        self.trigger_pos = trigger_pos
        self.tapping_term_ms = tapping_term_ms
        self.quick_tap_ms = quick_tap_ms
        self.require_prior_idle_ms = require_prior_idle_ms
        self.custom_bindings = bindings

        props = properties.copy() if properties else {}
        props["flavor"] = f'"{self.flavor}"'
        props["tapping-term-ms"] = f"<{self.tapping_term_ms}>"
        props["quick-tap-ms"] = f"<{self.quick_tap_ms}>"
        if self.require_prior_idle_ms is not None:
            props["require-prior-idle-ms"] = f"<{self.require_prior_idle_ms}>"
        props["bindings"] = self.custom_bindings or f"<{self.hold}>, <{self.tap}>"

        super().__init__(
            name=name,
            compatible="zmk,behavior-hold-tap",
            section="behaviors",
            binding_cells=2,
            properties=props,
        )

    def resolve_trigger_pos(
        self,
        keyboard: Optional[Any] = None,
        pos_map: Optional[Dict[str, int]] = None,
    ) -> str:
        if not self.trigger_pos:
            return ""
        if isinstance(self.trigger_pos, (list, tuple)):
            return " ".join(str(p) for p in self.trigger_pos)
        if isinstance(self.trigger_pos, str):
            return self.trigger_pos.strip()
        return str(self.trigger_pos)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        keyboard: Optional[Any] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        tp_str = self.resolve_trigger_pos(keyboard=keyboard, pos_map=pos_map)
        if tp_str:
            self.properties["hold-trigger-key-positions"] = f"<{tp_str}>"
        elif "hold-trigger-key-positions" in self.properties:
            del self.properties["hold-trigger-key-positions"]

        return super().render_dts(
            os_target=os_target,
            node_name_override=node_name_override,
            name_suffix=name_suffix,
            pos_map=pos_map,
            keyboard=keyboard,
            wrap_root=wrap_root,
            indent=indent,
            **kwargs,
        )


class HRMCall:
    """
    Represents a Home Row Mod call inside a layer binding, e.g. SL("EXCL"), CL("RPAR").
    Targets hrm_l / hrm_r (for keys) or hrl_l / hrl_r (for layers).
    """
    def __init__(self, hand: str, mod: Union[str, OsKey, Any], key: str, is_layer: bool = False):
        self.hand = "l" if hand in ["l", "L", "left", "Left"] else "r"
        self.mod = mod
        self.key = key
        self.is_layer = is_layer

    def render(self, os_target: str = "default", context: Optional[Any] = None) -> str:
        prefix = "hrl" if self.is_layer else "hrm"
        behavior_name = f"{prefix}_{self.hand}"

        if isinstance(self.mod, OsKey):
            mod_str = self.mod.get_kp(os_target)
        elif self.is_layer:
            mod_str = LayerRef(self.mod).get_layer_name(os_target)
        else:
            mod_str = str(self.mod)

        return f"&{behavior_name} {mod_str} {self.key}"

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        return self.render(os_target)

    def __call__(self, os_target: str = "default") -> str:
        return self.render(os_target)

    def __str__(self) -> str:
        return self.render("default")


# Standard HoldTap behaviors
hrm_l = HoldTap("hrm_l", flavor="tap-preferred", hold="&kp", tap="&kp", trigger_pos="KEYS_R THUMBS", tapping_term_ms="TAPPING_TERM", quick_tap_ms="QUICK_TAP_MS", require_prior_idle_ms="PRIOR_IDLE_MS")
hrm_r = HoldTap("hrm_r", flavor="tap-preferred", hold="&kp", tap="&kp", trigger_pos="KEYS_L THUMBS", tapping_term_ms="TAPPING_TERM", quick_tap_ms="QUICK_TAP_MS", require_prior_idle_ms="PRIOR_IDLE_MS")
hrl_l = HoldTap("hrl_l", flavor="tap-preferred", hold="&mo", tap="&kp", trigger_pos="KEYS_R THUMBS", tapping_term_ms="TAPPING_TERM", quick_tap_ms="QUICK_TAP_MS", require_prior_idle_ms="PRIOR_IDLE_MS")
hrl_r = HoldTap("hrl_r", flavor="tap-preferred", hold="&mo", tap="&kp", trigger_pos="KEYS_L THUMBS", tapping_term_ms="TAPPING_TERM", quick_tap_ms="QUICK_TAP_MS", require_prior_idle_ms="PRIOR_IDLE_MS")
thm_ht = HoldTap("thm", flavor="tap-preferred", hold="&kp", tap="&kp", trigger_pos="KEYS_L KEYS_R", tapping_term_ms="TAPPING_TERM", quick_tap_ms="QUICK_TAP_MS", require_prior_idle_ms="PRIOR_IDLE_MS")
thl_ht = HoldTap("thl", flavor="tap-preferred", hold="&mo", tap="&kp", trigger_pos="KEYS_L KEYS_R", tapping_term_ms="TAPPING_TERM", quick_tap_ms="QUICK_TAP_MS", require_prior_idle_ms="PRIOR_IDLE_MS")

# Home Row Mod Call Helpers
def SL(key: str) -> HRMCall: return HRMCall("l", SFT, key)
def CL(key: str) -> HRMCall: return HRMCall("l", CTL_GUI, key)
def AL(key: str) -> HRMCall: return HRMCall("l", ALT, key)
def ML(key: str) -> HRMCall: return HRMCall("l", GUI_CTL, key)

def SR(key: str) -> HRMCall: return HRMCall("r", SFT, key)
def CR(key: str) -> HRMCall: return HRMCall("r", CTL_GUI, key)
def AR(key: str) -> HRMCall: return HRMCall("r", ALT, key)
def MR(key: str) -> HRMCall: return HRMCall("r", GUI_CTL, key)

def SYL(key: str) -> HRMCall: return HRMCall("l", "SYS", key, is_layer=True)
def SYR(key: str) -> HRMCall: return HRMCall("r", "SYS", key, is_layer=True)
