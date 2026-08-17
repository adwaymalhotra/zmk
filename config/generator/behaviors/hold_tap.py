"""
HoldTap behavior and Home Row Mod (HRM) helper definitions.
"""

from typing import Union, List, Optional, Any
from ..node import Node
from ..property import Prop


class HoldTap(Node):
  """
  ZMK Hold-Tap behavior (zmk,behavior-hold-tap).
  """

  def __init__(
      self,
      name: str,
      flavor: str = "tap-preferred",
      hold: str = "&kp",
      tap: str = "&kp",
      trigger_pos: Union[str, List[Any]] = "",
      tapping_term_ms: Union[int, str] = "TAPPING_TERM",
      quick_tap_ms: Union[int, str] = "QUICK_TAP_MS",
      require_prior_idle_ms: Optional[Union[int, str]] = "PRIOR_IDLE_MS",
      bindings: Optional[str] = None,
      register: bool = True,
  ):
    self.flavor = flavor
    self.hold = hold if hold.startswith("&") else f"&{hold}"
    self.tap = tap if tap.startswith("&") else f"&{tap}"
    self.trigger_pos = trigger_pos
    self.tapping_term_ms = tapping_term_ms
    self.quick_tap_ms = quick_tap_ms
    self.require_prior_idle_ms = require_prior_idle_ms

    props = [
        Prop.str("flavor", self.flavor),
        Prop.int("tapping-term-ms", self.tapping_term_ms),
        Prop.int("quick-tap-ms", self.quick_tap_ms),
    ]
    if self.require_prior_idle_ms is not None:
      props.append(Prop.int("require-prior-idle-ms", self.require_prior_idle_ms))

    bindings_val = bindings if bindings else [self.hold, self.tap]
    props.append(Prop.bindings("bindings", bindings_val))

    if self.trigger_pos:
      props.append(Prop.positions("hold-trigger-key-positions", self.trigger_pos))

    super().__init__(
        name=name,
        compatible="zmk,behavior-hold-tap",
        binding_cells=2,
        section="behaviors",
        properties=props,
        has_label=True,
        is_callable=True,
        register=register,
    )


# Standard HoldTap behaviors
hrm_l = HoldTap(
    "hrm_l",
    flavor="tap-preferred",
    hold="&kp",
    tap="&kp",
    trigger_pos="KEYS_R THUMBS",
    tapping_term_ms="TAPPING_TERM",
    quick_tap_ms="QUICK_TAP_MS",
    require_prior_idle_ms="PRIOR_IDLE_MS",
)
hrm_r = HoldTap(
    "hrm_r",
    flavor="tap-preferred",
    hold="&kp",
    tap="&kp",
    trigger_pos="KEYS_L THUMBS",
    tapping_term_ms="TAPPING_TERM",
    quick_tap_ms="QUICK_TAP_MS",
    require_prior_idle_ms="PRIOR_IDLE_MS",
)
hrl_l = HoldTap(
    "hrl_l",
    flavor="tap-preferred",
    hold="&mo",
    tap="&kp",
    trigger_pos="KEYS_R THUMBS",
    tapping_term_ms="TAPPING_TERM",
    quick_tap_ms="QUICK_TAP_MS",
    require_prior_idle_ms="PRIOR_IDLE_MS",
)
hrl_r = HoldTap(
    "hrl_r",
    flavor="tap-preferred",
    hold="&mo",
    tap="&kp",
    trigger_pos="KEYS_L THUMBS",
    tapping_term_ms="TAPPING_TERM",
    quick_tap_ms="QUICK_TAP_MS",
    require_prior_idle_ms="PRIOR_IDLE_MS",
)
thm_ht = HoldTap(
    "thm",
    flavor="tap-preferred",
    hold="&kp",
    tap="&kp",
    trigger_pos="KEYS_L KEYS_R THUMBS",
    tapping_term_ms="TAPPING_TERM",
    quick_tap_ms="QUICK_TAP_MS",
    require_prior_idle_ms="PRIOR_IDLE_MS",
)
thl_ht = HoldTap(
    "thl",
    flavor="tap-preferred",
    hold="&mo",
    tap="&kp",
    trigger_pos="KEYS_L KEYS_R THUMBS",
    tapping_term_ms="TAPPING_TERM",
    quick_tap_ms="QUICK_TAP_MS",
    require_prior_idle_ms="PRIOR_IDLE_MS",
)
