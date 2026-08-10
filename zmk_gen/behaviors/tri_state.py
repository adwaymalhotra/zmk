"""
Tri-State behavior definition.
"""
from typing import List, Optional, Union, Dict, Any
from .base import Behavior


class TriState(Behavior):
    def __init__(
        self,
        name: str,
        start: str,
        tap: str,
        end: str,
        ignored_positions: Optional[List[Union[str, int]]] = None,
    ):
        self.start = start
        self.tap = tap
        self.end = end
        self.ignored_positions = ignored_positions or []
        super().__init__(name=name, compatible="zmk,behavior-tri-state", section="behaviors", binding_cells=0)

    def get_properties(self, os_target: str = "default", context: Optional[Any] = None) -> Dict[str, Any]:
        props = {
            "bindings": f"<{self.start}>, <{self.tap}>, <{self.end}>"
        }
        if self.ignored_positions:
            pos_map = context.get("pos_map") if isinstance(context, dict) else context
            pos_map = pos_map if isinstance(pos_map, dict) else {}
            pos_strs = [str(pos_map.get(p, p)) for p in self.ignored_positions]
            props["ignored-key-positions"] = f"<{' '.join(pos_strs)}>"
        return props
