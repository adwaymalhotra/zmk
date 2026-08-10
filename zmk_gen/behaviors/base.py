"""
Base Behavior class for all ZMK Devicetree behaviors.
"""
from typing import List, Tuple, Union, Optional, Dict, Any


class Behavior:
    """
    Base class for all ZMK Devicetree behaviors.
    Supports self-contained top-level DTSI block definitions (/ { <section> { <node> { ... }; }; };).
    Automatically registers instances for keymap generation.
    """
    _registry: List["Behavior"] = []

    def __init__(
        self,
        name: str,
        compatible: str,
        section: str = "behaviors",
        binding_cells: int = 0,
        properties: Optional[Dict[str, Any]] = None,
        has_mac_variant: bool = False,
    ):
        self.name = name
        self.compatible = compatible
        self.section = section
        self.binding_cells = binding_cells
        self.properties = properties or {}
        self.has_mac_variant = has_mac_variant
        if self not in Behavior._registry:
            Behavior._registry.append(self)

    @classmethod
    def all(cls) -> List["Behavior"]:
        return list(cls._registry)

    @classmethod
    def clear_registry(cls) -> None:
        cls._registry.clear()

    def get_properties(self, os_target: str = "default", context: Optional[Any] = None) -> Dict[str, Any]:
        """
        Override to return dynamically evaluated properties for a given OS target or keyboard context.
        """
        return self.properties

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
            v_str = str(v)
            if v_str.startswith("<") and v_str.endswith(">"):  # inside <>
                lines.append(f'{indent}    {k} = {v_str};')
            elif v_str.startswith('"') and v_str.endswith('"'):  # quoted string
                lines.append(f'{indent}    {k} = {v_str};')
            elif isinstance(v, int):  # integer
                lines.append(f'{indent}    {k} = <{v}>;')
            else:  # plain string
                lines.append(f'{indent}    {k} = "{v_str}";')
                
        lines.append(f"{indent}}};")
        return "\n".join(lines)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        ctx = {"pos_map": pos_map, "keyboard": kwargs.get("keyboard")}
        node_dts = self.render_node_dts(
            os_target=os_target,
            node_name_override=node_name_override,
            name_suffix=name_suffix,
            indent=indent,
            context=ctx,
        )
        if not wrap_root:
            return node_dts
        return f"/ {{\n    {self.section} {{\n{node_dts}\n    }};\n}};\n"

    def render_all_dts(
        self,
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = False,
        indent: str = "        ",
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        results = [(self.name, self.render_dts(
            os_target="default",
            pos_map=pos_map,
            wrap_root=wrap_root,
            indent=indent,
            **kwargs,
        ))]
        if self.has_mac_variant:
            mac_name = f"{self.name}_mac"
            results.append((mac_name, self.render_dts(
                os_target="mac",
                name_suffix="_mac",
                pos_map=pos_map,
                wrap_root=wrap_root,
                indent=indent,
                **kwargs,
            )))
        return results

    def render_call(self, os_target: str = "default") -> str:
        suffix = "_mac" if (os_target == "mac" and self.has_mac_variant) else ""
        return f"&{self.name}{suffix}"

    def __call__(self, os_target: str = "default") -> str:
        return self.render_call(os_target)
