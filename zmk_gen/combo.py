from typing import List, Union, Optional, Dict
from .os_key import OsKey

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
        # Convert position names (e.g. LT4) to physical key position indices
        indices = []
        for p in self.positions:
            if p in pos_map:
                indices.append(str(pos_map[p]))
            else:
                indices.append(str(p))
                
        lines = [f"        combo_{self.name} {{"]
        lines.append(f'            timeout-ms = <{self.timeout_ms}>;')
        lines.append(f'            key-positions = <{" ".join(indices)}>;')
        
        # Render key reference
        key_str = self.key
        if not key_str.startswith("&"):
            key_str = f"&{key_str}"
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
    OS-aware Mod Layer Combo. Generates macro and combo nodes.
    Scoped strictly to the layers of the target OS environment.
    """
    def __init__(
        self,
        mod: Union[str, OsKey],
        layer: str,
        positions: List[str],
        timeout_ms: int = 50,
    ):
        self.mod = mod
        self.layer = layer
        self.positions = positions
        self.timeout_ms = timeout_ms

    def get_mod_str(self, os_target: str) -> str:
        if isinstance(self.mod, OsKey):
            return self.mod.get_kp(os_target)
        return str(self.mod)

    def get_target_layer(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        if os_target == "mac":
            mac_name = f"{self.layer}M" if f"{self.layer}M" in layer_indices else f"{self.layer}_mac"
            if mac_name in layer_indices:
                return mac_name
        return self.layer

    def get_macro_name(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        mod_str = self.get_mod_str(os_target)
        target_layer = self.get_target_layer(os_target, layer_indices)
        return f"macro_{mod_str}_{target_layer}"

    def get_scoped_layers(self, os_target: str, layer_indices: Dict[str, int]) -> List[str]:
        scoped = []
        for name, idx in layer_indices.items():
            is_mac = name.endswith("_mac") or name.endswith("M")
            if os_target == "mac":
                if is_mac or name.lower() in ["game", "sys"]:
                    scoped.append(str(idx))
            else:
                if not is_mac or name.lower() in ["game", "sys"]:
                    scoped.append(str(idx))
        return scoped

    def render_macro_dts(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        mod_str = self.get_mod_str(os_target)
        target_layer = self.get_target_layer(os_target, layer_indices)
        macro_name = self.get_macro_name(os_target, layer_indices)
        
        lines = [f"        {macro_name}: {macro_name} {{"]
        lines.append('            compatible = "zmk,behavior-macro";')
        lines.append('            #binding-cells = <0>;')
        lines.append('            wait-ms = <0>;')
        lines.append('            tap-ms = <0>;')
        lines.append('            bindings')
        lines.append(f'                = <&macro_press &mo {target_layer}>')
        lines.append(f'                , <&macro_press &sk {mod_str}>')
        lines.append('                , <&macro_pause_for_release>')
        lines.append(f'                , <&macro_release &sk {mod_str}>')
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
        mod_str = self.get_mod_str(os_target)
        target_layer = self.get_target_layer(os_target, layer_indices)
        macro_name = f"macro_{mod_str}_{target_layer}"
        combo_name = f"combo_{mod_str}_{target_layer}"
        
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


class ModLayerCombo2:
    """
    OS-aware Mod Layer Combo with 2 modifiers.
    Scoped strictly to the layers of the target OS environment.
    """
    def __init__(
        self,
        mod1: Union[str, OsKey],
        mod2: Union[str, OsKey],
        layer: str,
        positions: List[str],
        timeout_ms: int = 50,
    ):
        self.mod1 = mod1
        self.mod2 = mod2
        self.layer = layer
        self.positions = positions
        self.timeout_ms = timeout_ms

    def get_mod_str(self, mod: Union[str, OsKey], os_target: str) -> str:
        if isinstance(mod, OsKey):
            return mod.get_kp(os_target)
        return str(mod)

    def get_target_layer(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        if os_target == "mac":
            mac_name = f"{self.layer}M" if f"{self.layer}M" in layer_indices else f"{self.layer}_mac"
            if mac_name in layer_indices:
                return mac_name
        return self.layer

    def get_macro_name(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        m1 = self.get_mod_str(self.mod1, os_target)
        m2 = self.get_mod_str(self.mod2, os_target)
        target_layer = self.get_target_layer(os_target, layer_indices)
        return f"macro_{m1}_{m2}_{target_layer}"

    def get_scoped_layers(self, os_target: str, layer_indices: Dict[str, int]) -> List[str]:
        scoped = []
        for name, idx in layer_indices.items():
            is_mac = name.endswith("_mac") or name.endswith("M")
            if os_target == "mac":
                if is_mac or name.lower() in ["game", "sys"]:
                    scoped.append(str(idx))
            else:
                if not is_mac or name.lower() in ["game", "sys"]:
                    scoped.append(str(idx))
        return scoped

    def render_macro_dts(self, os_target: str, layer_indices: Dict[str, int]) -> str:
        macro_name = self.get_macro_name(os_target, layer_indices)
        m1 = self.get_mod_str(self.mod1, os_target)
        m2 = self.get_mod_str(self.mod2, os_target)
        target_layer = self.get_target_layer(os_target, layer_indices)
        
        lines = [f"        {macro_name}: {macro_name} {{"]
        lines.append('            compatible = "zmk,behavior-macro";')
        lines.append('            #binding-cells = <0>;')
        lines.append('            wait-ms = <0>;')
        lines.append('            tap-ms = <0>;')
        lines.append('            bindings')
        lines.append(f'                = <&macro_press &mo {target_layer}>')
        lines.append(f'                , <&macro_press &sk {m1}>')
        lines.append(f'                , <&macro_press &sk {m2}>')
        lines.append('                , <&macro_pause_for_release>')
        lines.append(f'                , <&macro_release &sk {m2}>')
        lines.append(f'                , <&macro_release &sk {m1}>')
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
        m1 = self.get_mod_str(self.mod1, os_target)
        m2 = self.get_mod_str(self.mod2, os_target)
        target_layer = self.get_target_layer(os_target, layer_indices)
        macro_name = f"macro_{m1}_{m2}_{target_layer}"
        combo_name = f"combo_{m1}_{m2}_{target_layer}"
        
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
