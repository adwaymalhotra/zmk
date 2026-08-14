"""
Node and NodeRegistry base definitions.
"""
from typing import Optional, List, Any, Dict
from .property import NodeProperty


class Node:
    """
    Base class for all ZMK Devicetree nodes (behaviors, macros, combos, conditional layers, etc.).
    Rendering is 100% driven by self.properties without subclass overrides.
    """
    def __init__(
        self,
        name: str,
        compatible: Optional[str] = None,
        binding_cells: Optional[int] = None,
        section: str = "behaviors",
        properties: Optional[List[NodeProperty]] = None,
        has_label: bool = True,
        is_callable: bool = True,
        register: bool = True,
    ):
        self.name = name
        self.compatible = compatible
        self.binding_cells = binding_cells
        self.section = section
        self.properties: List[NodeProperty] = list(properties) if properties else []
        self.has_label = has_label
        self.is_callable = is_callable
        if register:
            NodeRegistry.get_default().register(self)

    def __call__(self, *args: Any) -> Any:
        if not self.is_callable:
            raise TypeError(f"Node '{self.name}' is not callable.")
        if self.binding_cells is not None and len(args) != self.binding_cells:
            raise ValueError(
                f"Node '{self.name}' (#binding-cells={self.binding_cells}) expects {self.binding_cells} arguments, got {len(args)}: {args}"
            )
        from .key import BehaviorCall
        return BehaviorCall(self.name, *args)

    def render_node_dts(self, indent: str = "        ") -> str:
        header = f"{indent}{self.name}: {self.name} {{" if self.has_label else f"{indent}{self.name} {{"
        lines = [header]
        if self.compatible:
            lines.append(f'{indent}    compatible = "{self.compatible}";')
        if self.binding_cells is not None:
            lines.append(f'{indent}    #binding-cells = <{self.binding_cells}>;')
        for prop in self.properties:
            lines.append(prop.render(indent=indent + "    "))
        lines.append(f"{indent}}};")
        return "\n".join(lines)

    def __str__(self) -> str:
        return f"&{self.name}"

    def __repr__(self) -> str:
        return f"Node({self.name}, section={self.section})"


class NodeRegistry:
    """
    Registry for managing Node instances.
    """
    _default: Optional["NodeRegistry"] = None

    def __init__(self):
        self._nodes: List[Node] = []

    @classmethod
    def get_default(cls) -> "NodeRegistry":
        if cls._default is None:
            cls._default = NodeRegistry()
        return cls._default

    @classmethod
    def reset_default(cls) -> None:
        cls._default = NodeRegistry()

    def register(self, node: Node) -> Node:
        if node not in self._nodes:
            self._nodes.append(node)
        return node

    def get_nodes(self, section: Optional[str] = None) -> List[Node]:
        if section is None:
            return list(self._nodes)
        return [n for n in self._nodes if n.section == section]

    def clear(self) -> None:
        self._nodes.clear()
