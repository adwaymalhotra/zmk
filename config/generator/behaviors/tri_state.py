"""
TriState behavior definition.
"""

from typing import List, Optional, Any, Union, Dict
from ..node import Node
from ..property import Prop
from ..key import Key, CtxKey, BehaviorCall
from ..keyboard import Keyboard


class TriState(Node):
  """
  ZMK Tri-State behavior (zmk,behavior-tri-state).
  """

  def __init__(
      self,
      name: str,
      start: Any,
      tap: Any,
      end: Any,
      ignored_positions: Optional[List[Union[str, int]]] = None,
      ctx_idx: int = 0,
      register: bool = True,
  ):
    self.raw_start = start
    self.raw_tap = tap
    self.raw_end = end
    self.ignored_positions = list(ignored_positions) if ignored_positions else []
    self.ctx_idx = ctx_idx

    s_str = self._format_key(start, ctx_idx)
    t_str = self._format_key(tap, ctx_idx)
    e_str = self._format_key(end, ctx_idx)

    props = [Prop.bindings("bindings", [s_str, t_str, e_str])]
    if self.ignored_positions:
      props.append(Prop.positions("ignored-key-positions", self.ignored_positions))

    super().__init__(
        name=name,
        compatible="zmk,behavior-tri-state",
        binding_cells=0,
        section="behaviors",
        properties=props,
        has_label=True,
        is_callable=True,
        register=register,
    )

  def resolve_with_keyboard(self, keyboard: Keyboard) -> "TriState":
    """
    Resolves symbolic position names (e.g. 'LT3') into physical matrix indices.
    """
    if not self.ignored_positions:
      return self
    resolved_indices = keyboard.resolve_indices(self.ignored_positions)
    return TriState(
        name=self.name,
        start=self.raw_start,
        tap=self.raw_tap,
        end=self.raw_end,
        ignored_positions=resolved_indices,
        ctx_idx=self.ctx_idx,
        register=False,
    )

  def max_contexts(self) -> int:
    max_c = 1
    for item in [self.raw_start, self.raw_tap, self.raw_end]:
      if isinstance(item, CtxKey):
        max_c = max(max_c, item.max_contexts())
      elif isinstance(item, BehaviorCall):
        for a in item.args:
          if isinstance(a, CtxKey):
            max_c = max(max_c, a.max_contexts())
    return max_c

  def resolve_variants(self) -> List["TriState"]:
    n = self.max_contexts()
    if n <= 1:
      return [self]
    variants = []
    for i in range(n):
      v_name = f"{self.name}_{i}"
      t = TriState(
          name=v_name,
          start=self.raw_start,
          tap=self.raw_tap,
          end=self.raw_end,
          ignored_positions=self.ignored_positions,
          ctx_idx=i,
          register=False,
      )
      variants.append(t)
    return variants

  @staticmethod
  def _format_key(val: Any, ctx_idx: int = 0) -> str:
    if isinstance(val, CtxKey):
      return val.resolve(ctx_idx).code
    if isinstance(val, BehaviorCall):
      return val.resolve(ctx_idx).code
    if isinstance(val, Key):
      return val.code
    if hasattr(val, "name"):
      return f"&{val.name}"
    v = str(val).strip()
    return v if v.startswith("&") else f"&kp {v}"
