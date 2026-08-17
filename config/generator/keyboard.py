"""
Keyboard definition and center-out physical layout mapping.
"""

from typing import List, Dict, Tuple, Any, Optional, Union


class Keyboard:
  """
  Physical matrix definition and position index calculator for a keyboard.
  """

  _registry: List["Keyboard"] = []

  def __init__(
      self,
      name: str,
      max_cols: int,
      layout: List[List[str]],
      register: bool = True,
  ):
    self.name = name
    self.max_cols = max_cols
    self.layout = layout
    self.pos_map = self._build_pos_map()
    if register and self not in Keyboard._registry:
      Keyboard._registry.append(self)

  @classmethod
  def all(cls) -> List["Keyboard"]:
    return list(cls._registry)

  @classmethod
  def clear_registry(cls) -> None:
    cls._registry.clear()

  def _build_pos_map(self) -> Dict[str, int]:
    pos = {}
    idx = 0
    for row in self.layout:
      for key_alias in row:
        pos[key_alias] = idx
        idx += 1
    return pos

  def resolve_index(self, pos: Union[str, int]) -> int:
    """
    Resolves a single key alias (e.g. 'LT3') or numeric position to its 0-based matrix index.
    """
    pos_str = str(pos)
    if pos_str in self.pos_map:
      return self.pos_map[pos_str]
    try:
      return int(pos_str)
    except ValueError:
      raise KeyError(f"Position '{pos}' not found in layout for keyboard '{self.name}'")

  def resolve_indices(self, positions: List[Union[str, int]]) -> List[int]:
    """
    Resolves a list of position aliases or numbers to their 0-based matrix indices on this keyboard.
    """
    return [self.resolve_index(p) for p in positions]

  def get_keys_l(self) -> List[int]:
    """Returns 0-based indices for all left-hand non-thumb keys (LT, LM, LB)."""
    return [
        idx
        for key_name, idx in self.pos_map.items()
        if key_name.startswith("L") and not key_name.startswith("LH")
    ]

  def get_keys_r(self) -> List[int]:
    """Returns 0-based indices for all right-hand non-thumb keys (RT, RM, RB)."""
    return [
        idx
        for key_name, idx in self.pos_map.items()
        if key_name.startswith("R") and not key_name.startswith("RH")
    ]

  def get_thumbs(self) -> List[int]:
    """Returns 0-based indices for all thumb keys (LH, RH)."""
    return [
        idx
        for key_name, idx in self.pos_map.items()
        if key_name.startswith("LH") or key_name.startswith("RH")
    ]

  def map_row(
      self,
      left_items: List[Any],
      right_items: List[Any],
      row_prefix: str,
  ) -> Dict[str, Any]:
    """
    Maps left items (center-out: reverse order) and right items (center-out: normal order)
    to the keyboard's physical aliases (L<prefix>k, R<prefix>k).
    """
    mapping: Dict[str, Any] = {}
    # Left side: items[-1] is center (index 0), items[-2] is index 1, etc.
    for idx, item in enumerate(reversed(left_items)):
      alias = f"L{row_prefix}{idx}"
      if alias in self.pos_map:
        mapping[alias] = item

    # Right side: items[0] is center (index 0), items[1] is index 1, etc.
    for idx, item in enumerate(right_items):
      alias = f"R{row_prefix}{idx}"
      if alias in self.pos_map:
        mapping[alias] = item

    return mapping

  def map_thumbs(
      self,
      left_thumbs: List[Any],
      right_thumbs: List[Any],
  ) -> Dict[str, Any]:
    """
    Maps left thumbs (center-out: reverse order) and right thumbs (center-out: normal order)
    to LH0, LH1, ..., RH0, RH1, ...
    """
    return self.map_row(left_thumbs, right_thumbs, "H")

  def __repr__(self) -> str:
    return f"Keyboard({self.name}, keys={len(self.pos_map)})"
