"""
Key-Toggle behavior definition and standard instances.
"""
from typing import Optional
from .base import Behavior


class KeyToggle(Behavior):
    def __init__(
        self,
        name: str, 
        toggle_mode: Optional[str] = None,
    ):
        self.name = name
        properties = {}
        if toggle_mode:
            properties["toggle-mode"] = f'"{toggle_mode}"'
        super().__init__(
            name=name,
            compatible="zmk,behavior-key-toggle",
            section="behaviors",
            binding_cells=1,
            properties=properties,
        )


kt_off = KeyToggle("kt_off", toggle_mode="off")
kt_on = KeyToggle("kt_on", toggle_mode="on")
