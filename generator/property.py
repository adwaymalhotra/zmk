"""
NodeProperty and PropertyType definitions for the ZMK Devicetree generator.
"""
from enum import Enum, auto
from typing import Any, List, Union, Optional


class PropertyType(Enum):
    INT = auto()           # <50> or <TAPPING_TERM>
    STRING = auto()        # "tap-preferred"
    BINDINGS = auto()      # <&kp A>, <&kp B>
    POSITIONS = auto()     # <0 1 2> or <KEYS_L THUMBS>
    MODS = auto()          # <(MOD_LGUI|MOD_LALT)>
    LAYERS = auto()        # <1 2> or <Nav_0 Sym_0>
    FLAG = auto()          # slow-release; / quick-release;
    DELETE = auto()        # /delete-property/ ignore-modifiers;
    RAW = auto()           # unquoted / unformatted string


class NodeProperty:
    """
    Represents a single property inside a Devicetree node.
    """
    def __init__(self, name: str, prop_type: PropertyType, value: Any = None):
        self.name = name
        self.prop_type = prop_type
        self.value = value

    def render(self, indent: str = "        ") -> str:
        if self.prop_type == PropertyType.FLAG:
            return f"{indent}{self.name};"
        if self.prop_type == PropertyType.DELETE:
            return f"{indent}/delete-property/ {self.name};"
        if self.prop_type == PropertyType.INT:
            return f"{indent}{self.name} = <{self.value}>;"
        if self.prop_type == PropertyType.STRING:
            return f'{indent}{self.name} = "{self.value}";'
        if self.prop_type == PropertyType.POSITIONS:
            items = " ".join(str(p) for p in self.value) if isinstance(self.value, (list, tuple)) else str(self.value)
            return f"{indent}{self.name} = <{items}>;"
        if self.prop_type == PropertyType.LAYERS:
            items = " ".join(str(l) for l in self.value) if isinstance(self.value, (list, tuple)) else str(self.value)
            return f"{indent}{self.name} = <{items}>;"
        if self.prop_type == PropertyType.MODS:
            if isinstance(self.value, (list, tuple)):
                items = []
                for m in self.value:
                    m_str = str(m).strip()
                    if m_str.startswith("MOD_"):
                        items.append(m_str)
                    else:
                        mod_map = {
                            "LCTRL": "LCTL",
                            "RCTRL": "RCTL",
                            "LSHFT": "LSFT",
                            "RSHFT": "RSFT",
                            "CTL": "LCTL",
                            "SFT": "LSFT",
                            "ALT": "LALT",
                            "GUI": "LGUI",
                            "MET": "LGUI",
                        }
                        canonical = mod_map.get(m_str, m_str)
                        items.append(f"MOD_{canonical}")
                return f"{indent}{self.name} = <({'|'.join(items)})>;"
            else:
                return f"{indent}{self.name} = <({self.value})>;"
        if self.prop_type == PropertyType.BINDINGS:
            if isinstance(self.value, (list, tuple)):
                b_strs = [f"<{b}>" if not str(b).startswith("<") else str(b) for b in self.value]
                return f"{indent}{self.name} = {', '.join(b_strs)};"
            val = str(self.value)
            return f"{indent}{self.name} = {val if val.startswith('<') else f'<{val}>'};"
        return f"{indent}{self.name} = {self.value};"

    def __repr__(self) -> str:
        return f"NodeProperty({self.name}, {self.prop_type.name}, {self.value})"


class Prop:
    """
    Convenience factory methods for constructing NodeProperty instances.
    """
    @staticmethod
    def int(name: str, val: Any) -> NodeProperty:
        return NodeProperty(name, PropertyType.INT, val)

    @staticmethod
    def str(name: str, val: str) -> NodeProperty:
        return NodeProperty(name, PropertyType.STRING, val)

    @staticmethod
    def bindings(name: str, *bindings: Any) -> NodeProperty:
        if len(bindings) == 1 and isinstance(bindings[0], (list, tuple)):
            items = list(bindings[0])
        else:
            items = list(bindings)
        return NodeProperty(name, PropertyType.BINDINGS, items)

    @staticmethod
    def positions(name: str, positions: Any) -> NodeProperty:
        return NodeProperty(name, PropertyType.POSITIONS, positions)

    @staticmethod
    def mods(name: str, mods: Any) -> NodeProperty:
        return NodeProperty(name, PropertyType.MODS, mods)

    @staticmethod
    def layers(name: str, layers: Any) -> NodeProperty:
        return NodeProperty(name, PropertyType.LAYERS, layers)

    @staticmethod
    def flag(name: str) -> NodeProperty:
        return NodeProperty(name, PropertyType.FLAG)

    @staticmethod
    def delete(name: str) -> NodeProperty:
        return NodeProperty(name, PropertyType.DELETE)

    @staticmethod
    def raw(name: str, val: str) -> NodeProperty:
        return NodeProperty(name, PropertyType.RAW, val)
