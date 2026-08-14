"""
Combo and ModLayerCombo behavior definitions.
"""
from typing import List, Optional, Any, Union, Dict, Tuple
from ..node import Node
from ..property import Prop
from ..key import Key, CtxKey, BehaviorCall
from ..keyboard import Keyboard
from .macro import Macro


class Combo(Node):
    """
    ZMK Combo behavior (zmk,combos).
    """
    def __init__(
        self,
        name: str,
        key: Any,
        positions: List[Union[str, int]],
        layers: Optional[List[Any]] = None,
        timeout_ms: Union[int, str] = "COMBO_TERM",
        slow_release: bool = False,
        ctx_idx: int = 0,
        register: bool = True,
    ):
        self.raw_key = key
        self.positions = list(positions)
        self.layers = list(layers) if layers else []
        self.timeout_ms = timeout_ms
        self.slow_release = slow_release
        self.ctx_idx = ctx_idx

        base_name = name if name.startswith("combo_") else f"combo_{name}"

        key_str = self._format_key(key, ctx_idx)
        props = [
            Prop.int("timeout-ms", timeout_ms),
            Prop.positions("key-positions", self.positions),
            Prop.bindings("bindings", [key_str]),
        ]
        if self.layers:
            props.append(Prop.layers("layers", self.layers))
        if self.slow_release:
            props.append(Prop.flag("slow-release"))

        super().__init__(
            name=base_name,
            compatible=None,
            binding_cells=None,
            section="combos",
            properties=props,
            has_label=False,
            is_callable=False,
            register=register,
        )

    def resolve_with_keyboard(
        self,
        keyboard: Keyboard,
        layer_indices: Optional[Dict[str, int]] = None,
        total_contexts: int = 1,
    ) -> "Combo":
        resolved_positions = keyboard.resolve_indices(self.positions)
        resolved_layers = []
        for l in self.layers:
            if hasattr(l, "get_layer_name"):
                l_name = l.get_layer_name(self.ctx_idx, total_contexts=total_contexts)
            else:
                l_name = str(l)
            resolved_layers.append(l_name)

        return Combo(
            name=self.name,
            key=self.raw_key,
            positions=resolved_positions,
            layers=resolved_layers,
            timeout_ms=self.timeout_ms,
            slow_release=self.slow_release,
            ctx_idx=self.ctx_idx,
            register=False,
        )

    @staticmethod
    def _format_key(val: Any, ctx_idx: int = 0) -> str:
        if isinstance(val, CtxKey):
            return val.resolve(ctx_idx).code
        if isinstance(val, BehaviorCall):
            return val.resolve(ctx_idx).code
        if isinstance(val, Key):
            return val.code
        if hasattr(val, "name"):
            return f"&{val.name}"
        v = str(val).strip()
        return v if v.startswith("&") else f"&kp {v}"


class ModLayerCombo:
    """
    Composite Mod-Layer Combo: creates an associated Macro and Combo.
    """
    _registry: List["ModLayerCombo"] = []

    def __init__(
        self,
        mods: Union[Any, List[Any]],
        layer: Any,
        positions: List[str],
        timeout_ms: Union[int, str] = "COMBO_TERM",
        name: Optional[str] = None,
        register: bool = True,
    ):
        self.mods = mods if isinstance(mods, (list, tuple)) else [mods]
        self.layer = layer
        self.positions = list(positions)
        self.timeout_ms = timeout_ms
        self.name = name
        if register and self not in ModLayerCombo._registry:
            ModLayerCombo._registry.append(self)

    @classmethod
    def all(cls) -> List["ModLayerCombo"]:
        return list(cls._registry)

    @classmethod
    def clear_registry(cls) -> None:
        cls._registry.clear()

    def max_contexts(self) -> int:
        max_c = 1
        for m in self.mods:
            if isinstance(m, CtxKey):
                max_c = max(max_c, m.max_contexts())
        return max_c

    def generate_nodes(
        self,
        ctx_idx: int = 0,
        total_contexts: int = 1,
        keyboard: Optional[Keyboard] = None,
    ) -> Tuple[Macro, Combo]:
        # 1. Resolve mods for this context
        mod_strs = []
        for m in self.mods:
            if isinstance(m, CtxKey):
                k = m.resolve(ctx_idx)
                mod_strs.append(k.code.replace("&kp ", ""))
            elif isinstance(m, Key):
                mod_strs.append(m.code.replace("&kp ", ""))
            else:
                mod_strs.append(str(m))

        # 2. Resolve layer name for this context
        if hasattr(self.layer, "get_layer_name"):
            target_layer = self.layer.get_layer_name(ctx_idx, total_contexts=total_contexts)
        else:
            target_layer = str(self.layer)

        macro_name = f"macro_{'_'.join(mod_strs)}_{target_layer}"
        bindings = [
            f"&macro_press &mo {target_layer}",
            *(f"&macro_press &sk {m}" for m in mod_strs),
            "&macro_pause_for_release",
            *(f"&macro_release &sk {m}" for m in reversed(mod_strs)),
            f"&macro_release &mo {target_layer}",
        ]

        macro = Macro(
            name=macro_name,
            bindings=bindings,
            wait_ms=0,
            tap_ms=0,
            ctx_idx=ctx_idx,
            register=False,
        )

        combo_name = macro_name.replace("macro_", "", 1)
        combo = Combo(
            name=combo_name,
            key=f"&{macro_name}",
            positions=self.positions,
            layers=[],  # Active on base layers or all layers
            timeout_ms=self.timeout_ms,
            slow_release=True,
            ctx_idx=ctx_idx,
            register=False,
        )

        return macro, combo
