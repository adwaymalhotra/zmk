from typing import List, Union, Optional, Dict, Any
from .os_key import OsKey, CTL_CMD, CMD_CTL, ALT, SFT

class Behavior:
    """
    Base class for all ZMK Devicetree behaviors.
    Supports self-contained top-level DTSI block definitions (/ { <section> { <node> { ... }; }; };).
    """
    def __init__(
        self,
        name: str,
        compatible: str,
        section: str = "behaviors",
        binding_cells: int = 0,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.compatible = compatible
        self.section = section
        self.binding_cells = binding_cells
        self.properties = properties or {}

    def render_node_dts(self, node_name_override: Optional[str] = None, indent: str = "        ") -> str:
        name = node_name_override or self.name
        lines = [f"{indent}{name}: {name} {{"]
        lines.append(f'{indent}    compatible = "{self.compatible}";')
        lines.append(f'{indent}    #binding-cells = <{self.binding_cells}>;')
        
        for k, v in self.properties.items():
            if v is None:
                continue
            v_str = str(v)
            if v_str.startswith("<") and v_str.endswith(">"):
                lines.append(f'{indent}    {k} = {v_str};')
            elif v_str.startswith('"') and v_str.endswith('"'):
                lines.append(f'{indent}    {k} = {v_str};')
            elif isinstance(v, int):
                lines.append(f'{indent}    {k} = <{v}>;')
            else:
                lines.append(f'{indent}    {k} = {v_str};')
                
        lines.append(f"{indent}}};")
        return "\n".join(lines)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
    ) -> str:
        node_dts = self.render_node_dts(node_name_override=node_name_override)
        if not wrap_root:
            return node_dts
        return f"/ {{\n    {self.section} {{\n{node_dts}\n    }};\n}};\n"


class Macro(Behavior):
    def __init__(
        self,
        name: str,
        bindings: List[Union[str, OsKey]],
        wait_ms: Optional[int] = None,
        tap_ms: Optional[int] = None,
    ):
        self.raw_bindings = bindings
        props = {}
        if wait_ms is not None:
            props["wait-ms"] = f"<{wait_ms}>"
        if tap_ms is not None:
            props["tap-ms"] = f"<{tap_ms}>"
            
        super().__init__(name=name, compatible="zmk,behavior-macro", section="macros", binding_cells=0, properties=props)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
    ) -> str:
        resolved_bindings = []
        for b in self.raw_bindings:
            if isinstance(b, OsKey):
                resolved_bindings.append(f"&kp {b.get_kp(os_target)}")
            else:
                resolved_bindings.append(str(b))
                
        self.properties["bindings"] = f"<{', '.join(resolved_bindings)}>"
        return super().render_dts(os_target=os_target, node_name_override=node_name_override, pos_map=pos_map, wrap_root=wrap_root)


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
        super().__init__(name=name, compatible="zmk,behavior-mod-morph", section="behaviors", binding_cells=0)

    def format_key(self, val: Union[str, OsKey], os_target: str) -> str:
        if isinstance(val, OsKey):
            return f"&kp {val.get_kp(os_target)}"
        val_str = str(val)
        if not val_str.startswith("&"):
            return f"&kp {val_str}"
        return val_str

    def format_mods(self, mod_list: List[Union[str, OsKey]], os_target: str) -> str:
        items = [m.get_mod(os_target) if isinstance(m, OsKey) else str(m) for m in mod_list]
        return "|".join(items)

    def render_dts(
        self,
        os_target: str = "default",
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
    ) -> str:
        node_name = f"{self.name}{name_suffix}"
        normal_str = self.format_key(self.normal, os_target)
        morph_str = self.format_key(self.morph, os_target)
        mods_str = self.format_mods(self.mods, os_target)
        
        self.properties["bindings"] = f"<{normal_str}>, <{morph_str}>"
        self.properties["mods"] = f"<({mods_str})>"
        if self.keep_mods:
            self.properties["keep-mods"] = f"<({self.format_mods(self.keep_mods, os_target)})>"
            
        return super().render_dts(os_target=os_target, node_name_override=node_name, pos_map=pos_map, wrap_root=wrap_root)


class NumMorph(ModMorph):
    """
    Standard ZMK NUM_MORPH behavior (mod morph activated on MOD_LGUI/MOD_LALT).
    """
    def __init__(self, name: str, normal: str, morph: str, mods: Optional[List[Union[str, OsKey]]] = None):
        if mods is None:
            mods = [CMD_CTL, ALT]
        super().__init__(name=name, normal=normal, morph=morph, mods=mods, keep_mods=mods)


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

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
    ) -> str:
        self.properties["bindings"] = f"<{self.start}>, <{self.tap}>, <{self.end}>"
        if self.ignored_positions:
            pos_strs = [str(pos_map.get(p, p) if pos_map else p) for p in self.ignored_positions]
            self.properties["ignored-key-positions"] = f"<{' '.join(pos_strs)}>"
        return super().render_dts(os_target=os_target, node_name_override=node_name_override, pos_map=pos_map, wrap_root=wrap_root)


class HoldTap(Behavior):
    def __init__(
        self,
        name: str,
        flavor: str,
        hold: str,
        tap: str,
        trigger_pos: str = "",
        tapping_term_ms: int = 200,
        quick_tap_ms: int = 175,
        require_prior_idle_ms: Optional[int] = None,
    ):
        props = {
            "flavor": f'"{flavor}"',
            "tapping-term-ms": f"<{tapping_term_ms}>",
            "quick-tap-ms": f"<{quick_tap_ms}>",
            "bindings": f"<{hold}>, <{tap}>",
        }
        if require_prior_idle_ms is not None:
            props["require-prior-idle-ms"] = f"<{require_prior_idle_ms}>"
        if trigger_pos:
            props["hold-trigger-key-positions"] = f"<{trigger_pos}>"
            
        super().__init__(name=name, compatible="zmk,behavior-hold-tap", section="behaviors", binding_cells=2, properties=props)


class HRMCall:
    """
    Represents a Home Row Mod call inside a layer binding, e.g. SL(EXCL), CL(RPAR).
    """
    def __init__(self, hand: str, mod: Union[str, OsKey], key: str, is_layer: bool = False):
        self.hand = hand
        self.mod = mod
        self.key = key
        self.is_layer = is_layer

    def render(self, os_target: str = "default") -> str:
        behavior_name = f"hr{'l' if self.is_layer else 'm'}_{self.hand}"
        mod_str = self.mod.get_kp(os_target) if isinstance(self.mod, OsKey) else str(self.mod)
        return f"&{behavior_name} {mod_str} {self.key}"

    def __str__(self):
        return self.render("default")


# Helper Functions for Layer Formatting
def SL(key: str) -> HRMCall: return HRMCall("left", SFT, key)
def CL(key: str) -> HRMCall: return HRMCall("left", CTL_CMD, key)
def AL(key: str) -> HRMCall: return HRMCall("left", ALT, key)
def ML(key: str) -> HRMCall: return HRMCall("left", CMD_CTL, key)

def SR(key: str) -> HRMCall: return HRMCall("right", SFT, key)
def CR(key: str) -> HRMCall: return HRMCall("right", CTL_CMD, key)
def AR(key: str) -> HRMCall: return HRMCall("right", ALT, key)
def MR(key: str) -> HRMCall: return HRMCall("right", CMD_CTL, key)

def SYL(key: str) -> HRMCall: return HRMCall("left", "SYS", key, is_layer=True)
def SYR(key: str) -> HRMCall: return HRMCall("right", "SYS", key, is_layer=True)
