"""
Macro behavior definition.
"""
from typing import List, Union, Optional, Dict, Any
from .base import Behavior
from ..os_key import OsKey


class Macro(Behavior):
    def __init__(
        self,
        name: str,
        bindings: List[Union[str, OsKey, Any]],
        wait_ms: Optional[int] = None,
        tap_ms: Optional[int] = None,
        multi_line: bool = False,
        register: bool = True,
    ):
        self.raw_bindings = bindings
        self.multi_line = multi_line
        props = {}
        if wait_ms is not None:
            props["wait-ms"] = f"<{wait_ms}>"
        if tap_ms is not None:
            props["tap-ms"] = f"<{tap_ms}>"
            
        super().__init__(name=name, compatible="zmk,behavior-macro", section="macros", binding_cells=0, properties=props)
        if not register and self in Behavior._registry:
            Behavior._registry.remove(self)

    def get_properties(self, os_target: str = "default", context: Optional[Any] = None) -> Dict[str, Any]:
        resolved = []
        for b in self.raw_bindings:
            if isinstance(b, OsKey):
                resolved.append(f"&kp {b.get_kp(os_target)}")
            else:
                resolved.append(str(b))
        props = self.properties.copy()
        if self.multi_line:
            indent = "        "
            lines = [
                f"{indent}    bindings",
                f"{indent}        = <{resolved[0]}>",
            ]
            for b in resolved[1:]:
                lines.append(f"{indent}        , <{b}>")
            lines.append(f"{indent}        ;")
            props["bindings_raw"] = lines
        else:
            binding_strs = [f"<{b}>" for b in resolved]
            props["bindings"] = ", ".join(binding_strs)
        return props

    def render_node_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        context: Optional[Any] = None,
        indent: str = "        ",
    ) -> str:
        name = node_name_override if node_name_override is not None else f"{self.name}{name_suffix}"
        lines = [f"{indent}{name}: {name} {{"]
        if self.compatible:
            lines.append(f'{indent}    compatible = "{self.compatible}";')
        lines.append(f'{indent}    #binding-cells = <{self.binding_cells}>;')
        
        props = self.get_properties(os_target=os_target, context=context)
        for k, v in props.items():
            if v is None:
                continue
            if k == "bindings_raw":
                lines.extend(v)
                continue
            v_str = str(v)
            if v_str.startswith("<") and v_str.endswith(">"):
                lines.append(f'{indent}    {k} = {v_str};')
            elif v_str.startswith('"') and v_str.endswith('"'):
                lines.append(f'{indent}    {k} = {v_str};')
            elif isinstance(v, int):
                lines.append(f'{indent}    {k} = <{v}>;')
            else:
                lines.append(f'{indent}    {k} = "{v_str}";')
                
        lines.append(f"{indent}}};")
        return "\n".join(lines)
