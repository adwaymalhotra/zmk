"""
Layer, CtxLayer, and ConditionalLayer definitions.
"""
from typing import List, Dict, Tuple, Any, Optional, Union
from .key import Key, CtxKey, BehaviorCall, none, trans
from .keyboard import Keyboard
from .node import Node
from .property import Prop


class Layer:
    """
    Concrete resolved layer for a specific keyboard and context.
    """
    def __init__(self, name: str, keyboard: Keyboard, key_map: Dict[str, Key], display_name: str = ""):
        self.name = name
        self.keyboard = keyboard
        self.key_map = key_map
        self.display_name = display_name or name

    def render_dts(self, indent: str = "        ") -> str:
        lines = [
            f"{indent}{self.name} {{",
            f'{indent}    display-name = "{self.display_name}";',
            f"{indent}    bindings = <",
        ]
        
        for row_idx, row in enumerate(self.keyboard.layout):
            left_keys = []
            right_keys = []
            for alias in row:
                key_obj = self.key_map.get(alias, none)
                code = key_obj.code if isinstance(key_obj, Key) else str(key_obj)
                if alias.startswith("L"):
                    left_keys.append(code)
                else:
                    right_keys.append(code)
            
            if left_keys and right_keys:
                row_str = f"{' '.join(left_keys)} /**/ {' '.join(right_keys)}"
            else:
                row_str = " ".join(left_keys + right_keys)
            
            lines.append(f"{indent}        {row_str}")

        lines.append(f"{indent}    >;")
        lines.append(f"{indent}}};")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Layer({self.name}, keys={len(self.key_map)})"


class ConditionalLayer(Node):
    """
    Represents a ZMK Conditional Layer (tri-layer) node.
    """
    _registry: List["ConditionalLayer"] = []

    def __init__(
        self,
        then_layer: Union["CtxLayer", str],
        if_layers: List[Union["CtxLayer", str]],
        name: Optional[str] = None,
        ctx_idx: int = 0,
        total_contexts: int = 1,
        register: bool = True,
    ):
        self.then_layer = then_layer
        self.if_layers = list(if_layers)
        self.ctx_idx = ctx_idx
        self.total_contexts = total_contexts

        then_name = self._resolve_name(self.then_layer, ctx_idx, total_contexts)
        if_names = [self._resolve_name(l, ctx_idx, total_contexts) for l in self.if_layers]

        node_name = name or f"tri_layer_{then_name}"
        props = [
            Prop.layers("if-layers", if_names),
            Prop.layers("then-layer", [then_name]),
        ]
        super().__init__(
            name=node_name,
            compatible=None,
            binding_cells=None,
            section="conditional_layers",
            properties=props,
            has_label=False,
            is_callable=False,
            register=False,
        )
        if register and self not in ConditionalLayer._registry:
            ConditionalLayer._registry.append(self)

    @classmethod
    def all(cls) -> List["ConditionalLayer"]:
        return list(cls._registry)

    @classmethod
    def clear_registry(cls) -> None:
        cls._registry.clear()

    @staticmethod
    def _resolve_name(layer: Union["CtxLayer", str], ctx_idx: int, total_contexts: int) -> str:
        if hasattr(layer, "get_layer_name"):
            return layer.get_layer_name(ctx_idx, total_contexts=total_contexts)
        return str(layer)


class CtxLayer:
    """
    Contextual Layer template. Can be defined in 1 step or 2 steps (init).
    """
    _registry: List["CtxLayer"] = []

    def __init__(
        self,
        name: str,
        rows: Optional[List[Tuple[List[Any], List[Any]]]] = None,
        thumbs: Optional[Tuple[List[Any], List[Any]]] = None,
        condition: Optional[List[Union["CtxLayer", str]]] = None,
        transparent_thumbs: bool = False,
        register: bool = True,
    ):
        self.name = name
        self.rows: List[Tuple[List[Any], List[Any]]] = rows or []
        self.thumbs: Optional[Tuple[List[Any], List[Any]]] = thumbs
        self.condition = condition
        self.transparent_thumbs = transparent_thumbs
        if register and self not in CtxLayer._registry:
            CtxLayer._registry.append(self)

    @classmethod
    def all(cls) -> List["CtxLayer"]:
        return list(cls._registry)

    @classmethod
    def clear_registry(cls) -> None:
        cls._registry.clear()

    def init(
        self,
        rows: Optional[List[Tuple[List[Any], List[Any]]]] = None,
        thumbs: Optional[Tuple[List[Any], List[Any]]] = None,
        condition: Optional[List[Union["CtxLayer", str]]] = None,
        transparent_thumbs: bool = False,
    ) -> "CtxLayer":
        if rows is not None:
            self.rows = rows
        if thumbs is not None:
            self.thumbs = thumbs
        if condition is not None:
            self.condition = condition
        if transparent_thumbs:
            self.transparent_thumbs = transparent_thumbs
        return self

    def get_layer_name(self, ctx_idx: int = 0, total_contexts: int = 1) -> str:
        return f"{self.name}_{ctx_idx}" if total_contexts > 1 else self.name

    def max_contexts(self) -> int:
        max_c = 1
        # Inspect rows
        for left, right in self.rows:
            for item in (left + right):
                max_c = max(max_c, self._get_item_contexts(item))
        # Inspect thumbs
        if self.thumbs:
            left_th, right_th = self.thumbs
            for item in (left_th + right_th):
                max_c = max(max_c, self._get_item_contexts(item))
        return max_c

    def _get_item_contexts(self, item: Any) -> int:
        if isinstance(item, CtxKey):
            return item.max_contexts()
        if hasattr(item, "max_contexts") and callable(getattr(item, "max_contexts")):
            return item.max_contexts()
        if isinstance(item, BehaviorCall):
            return max((self._get_item_contexts(a) for a in item.args), default=1)
        return 1

    def resolve(
        self,
        keyboard: Keyboard,
        ctx_idx: int = 0,
        total_contexts: int = 1,
        layer_indices: Optional[Dict[str, int]] = None,
    ) -> Layer:
        key_map: Dict[str, Key] = {}

        # 1. Map rows
        row_prefixes = ["T", "M", "B"]
        for row_idx, (left_items, right_items) in enumerate(self.rows):
            if row_idx < len(row_prefixes):
                prefix = row_prefixes[row_idx]
                row_mapping = keyboard.map_row(left_items, right_items, prefix)
                for alias, val in row_mapping.items():
                    key_map[alias] = self._resolve_val(val, ctx_idx, layer_indices, total_contexts)

        # 2. Map thumbs
        if self.transparent_thumbs:
            for alias in keyboard.pos_map:
                if alias.startswith("LH") or alias.startswith("RH"):
                    key_map[alias] = trans
        elif self.thumbs:
            left_th, right_th = self.thumbs
            thumb_mapping = keyboard.map_thumbs(left_th, right_th)
            for alias, val in thumb_mapping.items():
                key_map[alias] = self._resolve_val(val, ctx_idx, layer_indices, total_contexts)

        # 3. Fill any unmapped positions with &none
        for alias in keyboard.pos_map:
            if alias not in key_map:
                key_map[alias] = none

        layer_name = self.get_layer_name(ctx_idx, total_contexts)
        display_name = f"{self.name} {ctx_idx}" if total_contexts > 1 else self.name
        return Layer(
            name=layer_name,
            keyboard=keyboard,
            key_map=key_map,
            display_name=display_name,
        )

    def _resolve_val(
        self,
        val: Any,
        ctx_idx: int,
        layer_indices: Optional[Dict[str, int]],
        total_contexts: int,
    ) -> Key:
        if isinstance(val, CtxKey):
            return val.resolve(ctx_idx)
        if isinstance(val, BehaviorCall):
            return val.resolve(ctx_idx, layer_indices=layer_indices, total_contexts=total_contexts)
        if isinstance(val, Key):
            return val
        if hasattr(val, "name"):
            # A Node or Layer instance
            if hasattr(val, "max_contexts") and callable(getattr(val, "max_contexts")) and val.max_contexts() > 1:
                return Key(f"&{val.name}_{ctx_idx}")
            if hasattr(val, "get_layer_name") and callable(getattr(val, "get_layer_name")):
                return Key(f"&{val.get_layer_name(ctx_idx, total_contexts)}")
            return Key(f"&{val.name}")
        return Key(str(val))

    def __repr__(self) -> str:
        return f"CtxLayer({self.name})"
