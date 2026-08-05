from __future__ import annotations
from typing import TYPE_CHECKING, List, Union, Optional, Dict
from .os_key import OsKey

if TYPE_CHECKING:
    from .layer import Layer


class SimpleCombo:
    def __init__(
        self,
        name: str,
        key: str,
        positions: List[str],
        layers: Optional[List[str]] = None,
        timeout_ms: int = 50,
        slow_release: bool = False,
    ):
        self.name = name
        self.key = key
        self.positions = positions
        self.layers = layers
        self.timeout_ms = timeout_ms
        self.slow_release = slow_release

    def render_dts(
        self,
        os_target: str,
        pos_map: Dict[str, int],
        layer_indices: Dict[str, int],
        registered_behaviors: Optional[Dict[str, object]] = None,
    ) -> str:
        indices = [str(pos_map.get(p, p)) for p in self.positions]
        lines = [f"        combo_{self.name} {{"]
        lines.append(f'            timeout-ms = <{self.timeout_ms}>;')
        lines.append(f'            key-positions = <{" ".join(indices)}>;')

        key_str = self.key if self.key.startswith("&") else f"&{self.key}"
        lines.append(f'            bindings = <{key_str}>;')

        if self.layers:
            layer_nums = []
            for l in self.layers:
                target_l = f"{l}M" if (os_target == "mac" and f"{l}M" in layer_indices) else (f"{l}_mac" if (os_target == "mac" and f"{l}_mac" in layer_indices) else l)
                if target_l in layer_indices:
                    layer_nums.append(str(layer_indices[target_l]))
            if layer_nums:
                lines.append(f'            layers = <{" ".join(layer_nums)}>;')

        if self.slow_release:
            lines.append('            slow-release;')

        lines.append('        };')
        return "\n".join(lines)


class ModLayerCombo:
    """
    Unified OS-aware Mod Layer Combo for 1 or more modifiers.

    - `layer` is a Layer object. The combo activates `layer.name` for linux/default
      and the mac variant (e.g. `NavM` or `Nav_mac`) for mac targets.
    - If ANY mod is an OsKey whose `default_kp != mac_kp`, separate macros and combos
      are emitted for each OS target. Otherwise only one shared combo is emitted.
    - Combos are scoped to the base (non-functional) layers of the relevant OS.
    """

    def __init__(
        self,
        mods: Union[Union[str, OsKey], List[Union[str, OsKey]]],
        layer: "Layer",
        positions: List[str],
        timeout_ms: int = 50,
    ):
        self.mods: List[Union[str, OsKey]] = mods if isinstance(mods, list) else [mods]
        self.layer = layer
        self.positions = positions
        self.timeout_ms = timeout_ms

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

    def get_target_layer_name(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        base = self.layer.name
        if os_target == "mac":
            for candidate in (f"{base}M", f"{base}_mac"):
                if candidate in layer_indices:
                    return candidate
        return base

    def get_macro_name(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        m_strs = self.get_mod_strs(os_target)
        target_layer = self.get_target_layer_name(os_target, layer_indices)
        return f"macro_{'_'.join(m_strs)}_{target_layer}"

    def _os_targets(self) -> List[str]:
        """Return the list of OS targets to generate for this combo."""
        return ["default", "mac"] if self._has_os_split() else ["default"]

    def get_scoped_layers(self, os_target: str, layer_indices: Dict[str, int]) -> List[str]:
        """
        Scope the combo to base (non-functional) layers for the given OS.
        'Base' layers are those with generate_mac=True that serve as the top-level
        layout layers (Graphite, Qwerty, Game, etc.).
        """
        base_layer_names = ["Graphite", "Qwerty", "Game"]
        scoped = []
        for name in base_layer_names:
            if os_target == "mac":
                candidate = f"{name}_mac" if f"{name}_mac" in layer_indices else name
            else:
                candidate = name
            if candidate in layer_indices:
                scoped.append(str(layer_indices[candidate]))
        return scoped

    # ------------------------------------------------------------------ rendering

    def render_macro_dts(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        m_strs = self.get_mod_strs(os_target)
        target_layer = self.get_target_layer_name(os_target, layer_indices)
        macro_name = self.get_macro_name(os_target, layer_indices)

        lines = [f"        {macro_name}: {macro_name} {{"]
        lines.append('            compatible = "zmk,behavior-macro";')
        lines.append('            #binding-cells = <0>;')
        lines.append('            wait-ms = <0>;')
        lines.append('            tap-ms = <0>;')
        lines.append('            bindings')
        lines.append(f'                = <&macro_press &mo {target_layer}>')
        for m in m_strs:
            lines.append(f'                , <&macro_press &sk {m}>')
        lines.append('                , <&macro_pause_for_release>')
        for m in reversed(m_strs):
            lines.append(f'                , <&macro_release &sk {m}>')
        lines.append(f'                , <&macro_release &mo {target_layer}>')
        lines.append('                ;')
        lines.append('        };')
        return "\n".join(lines)

    def render_combo_dts(
        self,
        os_target: str,
        pos_map: Dict[str, int],
        layer_indices: Dict[str, int],
    ) -> str:
        macro_name = self.get_macro_name(os_target, layer_indices)
        combo_name = f"combo_{macro_name.replace('macro_', '', 1)}"

        indices = [str(pos_map.get(p, p)) for p in self.positions]
        scoped_layers = self.get_scoped_layers(os_target, layer_indices)

        lines = [f"        {combo_name} {{"]
        lines.append(f'            timeout-ms = <{self.timeout_ms}>;')
        lines.append(f'            key-positions = <{" ".join(indices)}>;')
        lines.append(f'            bindings = <&{macro_name}>;')
        if scoped_layers:
            lines.append(f'            layers = <{" ".join(scoped_layers)}>;')
        lines.append('            slow-release;')
        lines.append('        };')
        return "\n".join(lines)

    def render_all_macros(self, layer_indices: Dict[str, int]) -> List[str]:
        """Return all macro DTS nodes needed for this combo (1 or 2 depending on OS split)."""
        return [self.render_macro_dts(t, layer_indices) for t in self._os_targets()]

    def render_all_combos(
        self,
        pos_map: Dict[str, int],
        layer_indices: Dict[str, int],
    ) -> List[str]:
        """Return all combo DTS nodes needed for this combo (1 or 2 depending on OS split)."""
        return [self.render_combo_dts(t, pos_map, layer_indices) for t in self._os_targets()]

    def all_macro_names(self, layer_indices: Dict[str, int]) -> List[str]:
        return [self.get_macro_name(t, layer_indices) for t in self._os_targets()]
