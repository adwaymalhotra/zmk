"""
ModMorph and NumMorph behavior definitions.
"""

from typing import List, Optional, Any, Union
from ..node import Node
from ..property import Prop
from ..key import Key, CtxKey, BehaviorCall


class ModMorph(Node):
  """
  ZMK Mod-Morph behavior (zmk,behavior-mod-morph).
  """

  def __init__(
      self,
      name: str,
      normal: Any,
      morph: Any,
      mods: List[Any],
      keep_mods: Optional[List[Any]] = None,
      ctx_idx: int = 0,
      register: bool = True,
  ):
    self.raw_normal = normal
    self.raw_morph = morph
    self.raw_mods = list(mods)
    self.raw_keep_mods = list(keep_mods) if keep_mods else None
    self.ctx_idx = ctx_idx

    norm_str = self._format_key(normal, ctx_idx)
    morph_str = self._format_key(morph, ctx_idx)

    resolved_mods = self._resolve_mods(self.raw_mods, ctx_idx)
    props = [
        Prop.bindings("bindings", [norm_str, morph_str]),
        Prop.mods("mods", resolved_mods),
    ]
    if self.raw_keep_mods:
      resolved_keep_mods = self._resolve_mods(self.raw_keep_mods, ctx_idx)
      props.append(Prop.mods("keep-mods", resolved_keep_mods))

    super().__init__(
        name=name,
        compatible="zmk,behavior-mod-morph",
        binding_cells=0,
        section="behaviors",
        properties=props,
        has_label=True,
        is_callable=True,
        register=register,
    )

  @classmethod
  def _resolve_mods(cls, mods_list: List[Any], ctx_idx: int) -> List[str]:
    resolved = []
    for m in mods_list:
      if isinstance(m, CtxKey):
        k = m.resolve(ctx_idx)
        raw = k.code.replace("&kp ", "")
      elif isinstance(m, Key):
        raw = m.code.replace("&kp ", "")
      else:
        raw = str(m).strip()
      resolved.append(raw)
    return resolved

  def max_contexts(self) -> int:
    max_c = 1
    for item in [self.raw_normal, self.raw_morph]:
      if isinstance(item, CtxKey):
        max_c = max(max_c, item.max_contexts())
      elif hasattr(item, "max_contexts") and callable(getattr(item, "max_contexts")):
        max_c = max(max_c, item.max_contexts())
    for m in self.raw_mods:
      if isinstance(m, CtxKey):
        max_c = max(max_c, m.max_contexts())
    if self.raw_keep_mods:
      for m in self.raw_keep_mods:
        if isinstance(m, CtxKey):
          max_c = max(max_c, m.max_contexts())
    return max_c

  def resolve_variants(self) -> List["ModMorph"]:
    n = self.max_contexts()
    if n <= 1:
      return [self]
    variants = []
    for i in range(n):
      v_name = f"{self.name}_{i}"
      m = ModMorph(
          name=v_name,
          normal=self.raw_normal,
          morph=self.raw_morph,
          mods=self.raw_mods,
          keep_mods=self.raw_keep_mods,
          ctx_idx=i,
          register=False,
      )
      variants.append(m)
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
      if (
          hasattr(val, "max_contexts")
          and callable(getattr(val, "max_contexts"))
          and val.max_contexts() > 1
      ):
        return f"&{val.name}_{ctx_idx}"
      return f"&{val.name}"
    v = str(val).strip()
    return v if v.startswith("&") else f"&kp {v}"


class NumMorph(ModMorph):
  """
  Standard ZMK Num-Morph behavior (mod morph activated on MOD_LGUI/MOD_LALT).
  """

  def __init__(
      self,
      name: str,
      normal: Any,
      morph: Any,
      mods: Optional[List[Any]] = None,
      ctx_idx: int = 0,
      register: bool = True,
  ):
    if mods is None:
      mods = ["MOD_LGUI", "MOD_LALT"]
    super().__init__(
        name=name,
        normal=normal,
        morph=morph,
        mods=mods,
        keep_mods=mods,
        ctx_idx=ctx_idx,
        register=register,
    )

  def resolve_variants(self) -> List["NumMorph"]:
    n = self.max_contexts()
    if n <= 1:
      return [self]
    variants = []
    for i in range(n):
      v_name = f"{self.name}_{i}"
      m = NumMorph(
          name=v_name,
          normal=self.raw_normal,
          morph=self.raw_morph,
          mods=self.raw_mods,
          ctx_idx=i,
          register=False,
      )
      variants.append(m)
    return variants
