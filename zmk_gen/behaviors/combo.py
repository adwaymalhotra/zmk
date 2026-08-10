from __future__ import annotations
from typing import TYPE_CHECKING, List, Union, Optional, Dict, Tuple, Any
from ..os_key import OsKey
from .base import Behavior
from .macro import Macro
from ..primitives.binding import BehaviorCall, LayerRef

if TYPE_CHECKING:
    from ..layer import Layer


class Combo(Behavior):
    """
    ZMK Devicetree Combo Behavior (/ { combos { <node> { ... }; }; };).
    """
    def __init__(
        self,
        name: str,
        key: Union[str, BehaviorCall, Behavior, OsKey, Any],
        positions: List[str],
        layers: Optional[List[str]] = None,
        timeout_ms: Union[int, str] = "COMBO_TERM",
        slow_release: bool = False,
        register: bool = True,
    ):
        self.key = key
        self.positions = positions
        self.layers = layers
        self.timeout_ms = timeout_ms
        self.slow_release = slow_release
        super().__init__(
            name=name,
            compatible="",
            section="combos",
            binding_cells=0,
        )
        if not register and self in Behavior._registry:
            Behavior._registry.remove(self)

    def render_node_dts(
        self,
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        os_target: str = "default",
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        base_name = self.name if self.name.startswith("combo_") else f"combo_{self.name}"
        node_name = node_name_override if node_name_override is not None else f"{base_name}{name_suffix}"

        pos_map = pos_map or {}
        layer_indices = layer_indices or {}

        indices = [str(pos_map.get(p, p)) for p in self.positions]
        lines = [f"{indent}{node_name} {{"]
        timeout_val = "<COMBO_TERM>" if self.timeout_ms in [50, "50", "COMBO_TERM"] else f"<{self.timeout_ms}>"
        lines.append(f'{indent}    timeout-ms = {timeout_val};')
        lines.append(f'{indent}    key-positions = <{" ".join(indices)}>;')

        if isinstance(self.key, OsKey):
            key_str = self.key.render(os_target)
        elif hasattr(self.key, "render_call") and callable(getattr(self.key, "render_call")):
            key_str = self.key.render_call(os_target)
        elif hasattr(self.key, "render") and callable(getattr(self.key, "render")):
            key_str = self.key.render(os_target)
        elif callable(self.key):
            try:
                key_str = str(self.key(os_target))
            except TypeError:
                key_str = str(self.key())
        else:
            k = str(self.key).strip()
            key_str = k if k.startswith("&") else f"&{k}"

        lines.append(f'{indent}    bindings = <{key_str}>;')

        if self.layers:
            layer_nums = []
            for l in self.layers:
                l_str = str(l)
                if l_str.isdigit():
                    layer_nums.append(l_str)
                else:
                    target_l = LayerRef(l).get_layer_name(os_target)
                    if target_l in layer_indices:
                        layer_nums.append(str(layer_indices[target_l]))
            if layer_nums:
                lines.append(f'{indent}    layers = <{" ".join(layer_nums)}>;')

        if self.slow_release:
            lines.append(f'{indent}    slow-release;')

        lines.append(f"{indent}}};")
        return "\n".join(lines)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        node_dts = self.render_node_dts(
            node_name_override=node_name_override,
            name_suffix=name_suffix,
            pos_map=pos_map,
            layer_indices=layer_indices,
            os_target=os_target,
            indent=indent,
            **kwargs,
        )
        if not wrap_root:
            return node_dts
        return f"/ {{\n    {self.section} {{\n        compatible = \"zmk,combos\";\n{node_dts}\n    }};\n}};\n"

    def render_all_dts(
        self,
        pos_map: Optional[Dict[str, int]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        wrap_root: bool = False,
        indent: str = "        ",
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        base_name = self.name if self.name.startswith("combo_") else f"combo_{self.name}"
        return [(base_name, self.render_dts(
            os_target="default",
            pos_map=pos_map,
            layer_indices=layer_indices,
            wrap_root=wrap_root,
            indent=indent,
            **kwargs,
        ))]


# Backward-compatible alias
SimpleCombo = Combo


class ModLayerCombo(Behavior):
    """
    Unified OS-aware Mod Layer Combo for 1 or more modifiers.
    Subclass of Behavior. Emits associated macros and combos.
    """
    def __init__(
        self,
        mods: Union[Union[str, OsKey], List[Union[str, OsKey]]],
        layer: "Layer",
        positions: List[str],
        timeout_ms: Union[int, str] = "COMBO_TERM",
        name: Optional[str] = None,
    ):
        self.mods: List[Union[str, OsKey]] = mods if isinstance(mods, list) else [mods]
        self.layer = layer
        self.positions = positions
        self.timeout_ms = timeout_ms
        combo_name = name or f"modlayer_{self.layer.name}"
        super().__init__(
            name=combo_name,
            compatible="",
            section="combos",
            binding_cells=0,
        )

    # ------------------------------------------------------------------ helpers
    def _has_os_split(self) -> bool:
        """True if any mod produces different keys on linux vs mac."""
        return any(
            isinstance(m, OsKey) and m.default_kp != m.mac_kp
            for m in self.mods
        )

    def get_mod_strs(self, os_target: str) -> List[str]:
        return [
            m.get_kp(os_target) if isinstance(m, OsKey) else str(m)
            for m in self.mods
        ]

    def get_target_layer_name(self, os_target: str, layer_indices: Optional[Dict[str, int]] = None) -> str:
        layer_indices = layer_indices or {}
        base = self.layer.name
        if os_target == "mac":
            for candidate in (f"{base}M", f"{base}_mac"):
                if candidate in layer_indices:
                    return candidate
        return base

    def get_macro_name(self, os_target: str, layer_indices: Optional[Dict[str, int]] = None) -> str:
        m_strs = self.get_mod_strs(os_target)
        target_layer = self.get_target_layer_name(os_target, layer_indices)
        return f"macro_{'_'.join(m_strs)}_{target_layer}"

    def _os_targets(self) -> List[str]:
        """Return the list of OS targets to generate for this combo."""
        return ["default", "mac"] if self._has_os_split() else ["default"]

    def get_scoped_layers(self, os_target: str, layer_indices: Optional[Dict[str, int]] = None) -> List[str]:
        base_layer_names = ["Graphite", "Qwerty", "Game"]
        layer_indices = layer_indices or {}
        scoped = []
        for name in base_layer_names:
            if os_target == "mac":
                candidate = f"{name}_mac" if f"{name}_mac" in layer_indices else name
            else:
                candidate = name
            if candidate in layer_indices:
                scoped.append(str(layer_indices[candidate]))
        return scoped

    # ------------------------------------------------------------------ composed types
    def get_macro(self, os_target: str, layer_indices: Optional[Dict[str, int]] = None) -> Macro:
        macro_name = self.get_macro_name(os_target, layer_indices)
        m_strs = self.get_mod_strs(os_target)
        target_layer = self.get_target_layer_name(os_target, layer_indices)

        bindings = [
            f"&macro_press &mo {target_layer}",
            *(f"&macro_press &sk {m}" for m in m_strs),
            "&macro_pause_for_release",
            *(f"&macro_release &sk {m}" for m in reversed(m_strs)),
            f"&macro_release &mo {target_layer}",
        ]
        return Macro(
            name=macro_name,
            bindings=bindings,
            wait_ms=0,
            tap_ms=0,
            multi_line=True,
            register=False,
        )

    def get_combo(self, os_target: str, layer_indices: Optional[Dict[str, int]] = None) -> Combo:
        macro_name = self.get_macro_name(os_target, layer_indices)
        combo_name = macro_name.replace("macro_", "", 1)
        scoped_layers = self.get_scoped_layers(os_target, layer_indices)
        return Combo(
            name=combo_name,
            key=f"&{macro_name}",
            positions=self.positions,
            layers=scoped_layers,
            timeout_ms=self.timeout_ms,
            slow_release=True,
            register=False,
        )

    # ------------------------------------------------------------------ rendering
    def render_macro_dts(
        self,
        os_target: str,
        layer_indices: Optional[Dict[str, int]] = None,
        indent: str = "        ",
    ) -> str:
        macro = self.get_macro(os_target, layer_indices)
        return macro.render_node_dts(os_target=os_target, indent=indent)

    def render_combo_dts(
        self,
        os_target: str,
        pos_map: Optional[Dict[str, int]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        indent: str = "        ",
    ) -> str:
        combo = self.get_combo(os_target, layer_indices)
        return combo.render_node_dts(
            os_target=os_target,
            pos_map=pos_map,
            layer_indices=layer_indices,
            indent=indent,
        )

    def render_all_macros(self, layer_indices: Optional[Dict[str, int]] = None) -> List[Tuple[str, str]]:
        return [
            (self.get_macro_name(t, layer_indices), self.render_macro_dts(t, layer_indices))
            for t in self._os_targets()
        ]

    def render_all_combos(
        self,
        pos_map: Optional[Dict[str, int]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        indent: str = "        ",
    ) -> List[Tuple[str, str]]:
        return [
            (f"combo_{self.get_macro_name(t, layer_indices).replace('macro_', '', 1)}",
             self.render_combo_dts(t, pos_map, layer_indices, indent=indent))
            for t in self._os_targets()
        ]

    def render_all_dts(
        self,
        pos_map: Optional[Dict[str, int]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        wrap_root: bool = False,
        indent: str = "        ",
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        return self.render_all_combos(pos_map=pos_map, layer_indices=layer_indices, indent=indent)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        combo_dts = self.render_combo_dts(os_target=os_target, pos_map=pos_map, layer_indices=layer_indices, indent=indent)
        if not wrap_root:
            return combo_dts
        return f"/ {{\n    {self.section} {{\n        compatible = \"zmk,combos\";\n{combo_dts}\n    }};\n}};\n"

    def all_macro_names(self, layer_indices: Optional[Dict[str, int]] = None) -> List[str]:
        return [self.get_macro_name(t, layer_indices) for t in self._os_targets()]

