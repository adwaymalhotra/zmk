"""
Mod-Morph and Num-Morph behavior definitions.
"""
from typing import Union, List, Optional, Dict, Any, Tuple
from .base import Behavior
from ..os_key import OsKey


class ModMorph(Behavior):
    def __init__(
        self,
        name: str,
        normal: Union[str, OsKey],
        morph: Union[str, OsKey],
        mods: List[Union[str, OsKey]],
        keep_mods: Optional[List[Union[str, OsKey]]] = None,
    ):
        self.normal = normal
        self.morph = morph
        self.mods = mods
        self.keep_mods = keep_mods
        has_mac = any(isinstance(m, OsKey) for m in mods)
        super().__init__(
            name=name,
            compatible="zmk,behavior-mod-morph",
            section="behaviors",
            binding_cells=0,
            has_mac_variant=has_mac,
        )

    def _format_key(self, val: Union[str, OsKey], os_target: str) -> str:
        if isinstance(val, OsKey):
            return f"&kp {val.get_kp(os_target)}"
        val_str = str(val)
        if not val_str.startswith("&"):
            return f"&kp {val_str}"
        return val_str

    def _format_mods(self, mod_list: List[Union[str, OsKey]], os_target: str) -> str:
        items = [m.get_mod(os_target) if isinstance(m, OsKey) else (m if m.startswith("MOD_") else f"MOD_{m}") for m in mod_list]
        return "|".join(items)

    def get_properties(self, os_target: str = "default", context: Optional[Any] = None) -> Dict[str, Any]:
        norm_str = self._format_key(self.normal, os_target)
        morph_str = self._format_key(self.morph, os_target)
        mods_str = self._format_mods(self.mods, os_target)
        props = {
            "bindings": f"<{norm_str}>, <{morph_str}>",
            "mods": f"<({mods_str})>",
        }
        if self.keep_mods:
            props["keep-mods"] = f"<({self._format_mods(self.keep_mods, os_target)})>"
        return props


class NumMorph(ModMorph):
    """
    Standard ZMK NUM_MORPH behavior (mod morph activated on MOD_LGUI/MOD_LALT).
    """
    def __init__(self, name: str, normal: str, morph: str, mods: Optional[List[Union[str, OsKey]]] = None):
        if mods is None:
            mods = ["MOD_LGUI", "LALT"]
        super().__init__(name=name, normal=normal, morph=morph, mods=mods, keep_mods=mods)
