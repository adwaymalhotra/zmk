"""
Macro behavior definition.
"""
from typing import List, Optional, Any, Union
from ..node import Node
from ..property import Prop
from ..key import Key, CtxKey, BehaviorCall


class Macro(Node):
    """
    ZMK Macro behavior (zmk,behavior-macro).
    """
    def __init__(
        self,
        name: str,
        bindings: List[Any],
        wait_ms: Optional[int] = None,
        tap_ms: Optional[int] = None,
        ctx_idx: int = 0,
        register: bool = True,
    ):
        self.raw_bindings = list(bindings)
        self.wait_ms = wait_ms
        self.tap_ms = tap_ms
        self.ctx_idx = ctx_idx

        props = []
        if wait_ms is not None:
            props.append(Prop.int("wait-ms", wait_ms))
        if tap_ms is not None:
            props.append(Prop.int("tap-ms", tap_ms))

        # Format bindings for single-line Devicetree output
        resolved_bindings = []
        for b in self.raw_bindings:
            if isinstance(b, CtxKey):
                resolved_bindings.append(b.resolve(ctx_idx).code)
            elif isinstance(b, BehaviorCall):
                resolved_bindings.append(b.resolve(ctx_idx).code)
            elif isinstance(b, Key):
                resolved_bindings.append(b.code)
            elif hasattr(b, "name"):
                if hasattr(b, "max_contexts") and callable(getattr(b, "max_contexts")) and b.max_contexts() > 1:
                    resolved_bindings.append(f"&{b.name}_{ctx_idx}")
                else:
                    resolved_bindings.append(f"&{b.name}")
            else:
                k = Key(b)
                resolved_bindings.append(k.code)

        props.append(Prop.bindings("bindings", resolved_bindings))

        super().__init__(
            name=name,
            compatible="zmk,behavior-macro",
            binding_cells=0,
            section="macros",
            properties=props,
            has_label=True,
            is_callable=True,
            register=register,
        )

    def max_contexts(self) -> int:
        max_c = 1
        for b in self.raw_bindings:
            if isinstance(b, CtxKey):
                max_c = max(max_c, b.max_contexts())
            elif isinstance(b, BehaviorCall):
                for a in b.args:
                    if isinstance(a, CtxKey):
                        max_c = max(max_c, a.max_contexts())
        return max_c

    def resolve_variants(self) -> List["Macro"]:
        n = self.max_contexts()
        if n <= 1:
            return [self]
        variants = []
        for i in range(n):
            v_name = f"{self.name}_{i}"
            m = Macro(
                name=v_name,
                bindings=self.raw_bindings,
                wait_ms=self.wait_ms,
                tap_ms=self.tap_ms,
                ctx_idx=i,
                register=False,
            )
            variants.append(m)
        return variants
