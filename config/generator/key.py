"""
Key, CtxKey, BehaviorCall, and standard key factory definitions.
"""

from typing import Any, List, Optional, Dict, Union


class Key:
  """
  Represents a fully resolved ZMK key binding (e.g. '&kp F', '&none', '&mo Nav_0').
  """

  def __init__(self, code: Any):
    if hasattr(code, "name"):
      self.code = f"&{code.name}"
    else:
      c = str(code).strip()
      if not c:
        self.code = "&none"
      elif c.startswith("&"):
        self.code = c
      else:
        self.code = f"&kp {c}"

  def __str__(self) -> str:
    return self.code

  def __repr__(self) -> str:
    return f"Key({self.code})"

  def __eq__(self, other: Any) -> bool:
    if isinstance(other, Key):
      return self.code == other.code
    return self.code == str(other)

  def __hash__(self) -> int:
    return hash(self.code)


class CtxKey:
  """
  Contextual key that resolves to different keys based on the context index.
  e.g. CTL_CMD = CtxKey(["LCTRL", "LGUI", "LCTRL"])
  """

  def __init__(self, variants: List[Any]):
    if not variants:
      raise ValueError("CtxKey requires at least one variant.")
    self.variants = list(variants)

  def resolve(self, ctx_idx: int = 0) -> Key:
    val = self.variants[ctx_idx % len(self.variants)]
    if isinstance(val, Key):
      return val
    if isinstance(val, BehaviorCall):
      return val.resolve(ctx_idx)
    if hasattr(val, "name"):
      if (
          hasattr(val, "max_contexts")
          and callable(getattr(val, "max_contexts"))
          and val.max_contexts() > 1
      ):
        return Key(f"&{val.name}_{ctx_idx}")
      return Key(f"&{val.name}")
    return Key(val)

  def max_contexts(self) -> int:
    return len(self.variants)

  def __repr__(self) -> str:
    return f"CtxKey({self.variants})"


class BehaviorCall:
  """
  Represents an invocation of a ZMK behavior with arguments (e.g. &lt Nav_0 SPACE, &mo Sym_0).
  Resolves to a concrete Key when given a context index.
  """

  def __init__(self, behavior_name: str, *args: Any):
    self.behavior_name = behavior_name.lstrip("&")
    self.args = list(args)

  def resolve(
      self,
      ctx_idx: int = 0,
      layer_indices: Optional[Dict[str, int]] = None,
      total_contexts: int = 1,
  ) -> Key:
    rendered_args = []
    for a in self.args:
      if isinstance(a, CtxKey):
        k = a.resolve(ctx_idx)
        # If kp, extract the raw key code for argument position
        code = k.code
        rendered_args.append(code.replace("&kp ", "") if code.startswith("&kp ") else code)
      elif hasattr(a, "get_layer_name") and callable(getattr(a, "get_layer_name")):
        rendered_args.append(a.get_layer_name(ctx_idx, total_contexts=total_contexts))
      elif hasattr(a, "name"):
        if (
            hasattr(a, "max_contexts")
            and callable(getattr(a, "max_contexts"))
            and a.max_contexts() > 1
        ):
          rendered_args.append(f"{a.name}_{ctx_idx}")
        else:
          rendered_args.append(str(a.name))
      elif isinstance(a, BehaviorCall):
        k = a.resolve(ctx_idx, layer_indices=layer_indices, total_contexts=total_contexts)
        rendered_args.append(k.code)
      elif isinstance(a, Key):
        rendered_args.append(a.code)
      else:
        rendered_args.append(str(a))

    arg_str = f" {' '.join(rendered_args)}" if rendered_args else ""
    return Key(f"&{self.behavior_name}{arg_str}")

  def __repr__(self) -> str:
    return f"BehaviorCall({self.behavior_name}, {self.args})"

  def __str__(self) -> str:
    return self.resolve(0).code


# Standard key factory functions
def kp(key: Union[str, Key, CtxKey]) -> Union[Key, BehaviorCall]:
  if isinstance(key, CtxKey):
    return BehaviorCall("kp", key)
  return Key(str(key))


def mo(layer: Any) -> BehaviorCall:
  return BehaviorCall("mo", layer)


def lt(layer: Any, tap: Any) -> BehaviorCall:
  return BehaviorCall("lt", layer, tap)


def mt(mod: Any, tap: Any) -> BehaviorCall:
  return BehaviorCall("mt", mod, tap)


def sk(mod: Any) -> BehaviorCall:
  return BehaviorCall("sk", mod)


def tog(layer: Any) -> BehaviorCall:
  return BehaviorCall("tog", layer)


def kt_on(key: Any) -> BehaviorCall:
  return BehaviorCall("kt_on", key)


def kt_off(key: Any) -> BehaviorCall:
  return BehaviorCall("kt_off", key)


def thm(mod: Any, tap: Any) -> BehaviorCall:
  return BehaviorCall("thm", mod, tap)


def thl(layer: Any, tap: Any) -> BehaviorCall:
  return BehaviorCall("thl", layer, tap)


def out(endpoint: str) -> BehaviorCall:
  ep = endpoint if endpoint.startswith("OUT_") else f"OUT_{endpoint}"
  return BehaviorCall("out", ep)


def bt(command: str, *args: Any) -> BehaviorCall:
  cmd = command if command.startswith("BT_") else f"BT_{command}"
  return BehaviorCall("bt", cmd, *args)


def bt_sel(index: Union[int, str]) -> BehaviorCall:
  return bt("BT_SEL", str(index))


def bt_clr() -> BehaviorCall:
  return bt("BT_CLR")


def bt_clr_all() -> BehaviorCall:
  return bt("BT_CLR_ALL")


# Standard 0-argument Keys
none = Key("&none")
trans = Key("&trans")
bootloader = Key("&bootloader")
sys_reset = Key("&sys_reset")
caps_word = Key("&caps_word")
key_repeat = Key("&key_repeat")
