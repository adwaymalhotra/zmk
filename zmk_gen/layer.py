import re
from typing import List, Dict, Union, Optional, Tuple, Any
from .os_key import *
from .layout import normalize_tokens
from .primitives.binding import LayerRef

def tokenize_line(line: str) -> List[str]:
    """
    Tokenizes a line of layer bindings, grouping multi-word ZMK behaviors
    (e.g., &sk SFT, &bt BT_SEL 0, &out OUT_BLE, &tog SYS) into single binding strings.
    """
    line_clean = re.sub(r'/\*.*?\*/', ' ', line)
    raw_words = line_clean.split()
    tokens = []
    i = 0
    while i < len(raw_words):
        w = raw_words[i]
        if w.startswith("&"):
            beh = w.lower()
            if beh in ["&lt", "&mt", "&thl", "&thm"]:
                args = raw_words[i+1 : i+3]
                tokens.append(" ".join([w] + args))
                i += 1 + len(args)
            elif beh in ["&sk", "&mo", "&tog", "&out", "&kp", "&kt_on", "&kt_off"]:
                if i + 1 < len(raw_words):
                    tokens.append(f"{w} {raw_words[i+1]}")
                    i += 2
                else:
                    tokens.append(w)
                    i += 1
            elif beh == "&bt":
                if i + 1 < len(raw_words):
                    next_w = raw_words[i+1]
                    if next_w == "BT_SEL" and i + 2 < len(raw_words):
                        tokens.append(f"{w} {next_w} {raw_words[i+2]}")
                        i += 3
                    else:
                        tokens.append(f"{w} {next_w}")
                        i += 2
                else:
                    tokens.append(w)
                    i += 1
            else:
                tokens.append(w)
                i += 1
        else:
            tokens.append(w)
            i += 1
    return tokens


def normalize_layer_row(row: Any) -> Dict[str, List[Any]]:
    """
    Normalizes a layer row into {'left': [...], 'right': [...]}.
    Supports:
      - dict: {'left': [...], 'right': [...]}
      - tuple/list of two lists: ([left...], [right...])
      - flat list of keys: splits evenly in half
    """
    if isinstance(row, dict):
        return {
            "left": list(row.get("left", [])),
            "right": list(row.get("right", [])),
        }
    if isinstance(row, (list, tuple)):
        if len(row) == 2 and isinstance(row[0], (list, tuple)) and isinstance(row[1], (list, tuple)):
            return {
                "left": list(row[0]),
                "right": list(row[1]),
            }
        mid = len(row) // 2
        return {
            "left": list(row[:mid]),
            "right": list(row[mid:]),
        }
    return {"left": [], "right": []}


class ConditionalLayer:
    """
    Represents a ZMK Conditional Layer (tri-layer) configuration.
    Activates `then_layer` when all `if_layers` are active.
    """
    _registry: List["ConditionalLayer"] = []

    def __init__(
        self,
        then_layer: Union[str, "Layer", Any],
        if_layers: List[Union[str, "Layer", Any]],
        name: Optional[str] = None,
        generate_mac: bool = True,
    ):
        self.then_layer = then_layer
        self.if_layers = if_layers
        self.name = name
        self.generate_mac = generate_mac
        if self not in ConditionalLayer._registry:
            ConditionalLayer._registry.append(self)

    @classmethod
    def all(cls) -> List["ConditionalLayer"]:
        return list(cls._registry)

    @classmethod
    def clear_registry(cls) -> None:
        cls._registry.clear()

    def get_node_name(self, os_target: str = "default") -> str:
        if self.name:
            suffix = "M" if os_target == "mac" else ""
            return f"{self.name}{suffix}"
        then_name = LayerRef(self.then_layer).get_layer_name(os_target)
        return f"tri_layer_{then_name}"

    def render_dts(
        self,
        os_target: str = "default",
        layer_indices: Optional[Dict[str, int]] = None,
        indent: str = "        ",
    ) -> str:
        node_name = self.get_node_name(os_target)
        then_name = LayerRef(self.then_layer).get_layer_name(os_target)
        if_names = [LayerRef(l).get_layer_name(os_target) for l in self.if_layers]

        lines = [
            f"{indent}{node_name} {{",
            f"{indent}    if-layers = <{' '.join(if_names)}>;",
            f"{indent}    then-layer = <{then_name}>;",
            f"{indent}}};",
        ]
        return "\n".join(lines)


class Layer:
    _registry: List["Layer"] = []

    def __init__(
        self,
        name: str,
        rows: Optional[List[Any]] = None,
        thumbs: Optional[Any] = None,
        thumb_base: Optional[Union[Tuple, List, Dict]] = None,
        thumb_extras: Optional[Dict] = None,
        transparent_thumbs: bool = False,
        generate_mac: bool = True,
        is_raw_devicetree: bool = False,
        raw_content: str = "",
        layout: Optional[Union[str, List[Any]]] = None,
        condition: Optional[List[Union[str, "Layer", Any]]] = None,
        if_layers: Optional[List[Union[str, "Layer", Any]]] = None,
    ):
        self.name = name
        self.thumbs = thumbs
        self.thumb_base = thumb_base
        self.thumb_extras = thumb_extras
        self.transparent_thumbs = transparent_thumbs
        self.generate_mac = generate_mac
        self.is_raw_devicetree = is_raw_devicetree
        self.raw_content = raw_content
        self.condition = condition or if_layers

        if self.condition:
            ConditionalLayer(
                then_layer=self,
                if_layers=self.condition,
                generate_mac=self.generate_mac,
            )

        if rows is not None:
            self.rows = [normalize_layer_row(r) for r in rows]
        elif layout is not None:
            if isinstance(layout, str):
                self.rows = self._parse_text_layout(layout)
            elif isinstance(layout, list):
                self.rows = [normalize_layer_row(r) for r in layout]
            else:
                self.rows = []
        else:
            self.rows = []

        if self not in Layer._registry:
            Layer._registry.append(self)

    @classmethod
    def all(cls) -> List["Layer"]:
        return list(cls._registry)

    @classmethod
    def clear_registry(cls) -> None:
        cls._registry.clear()

    @staticmethod
    def _parse_text_layout(layout: str) -> List[Dict[str, List[str]]]:
        lines = [
            line.strip()
            for line in layout.strip().split("\n")
            if line.strip() and not line.strip().startswith("//")
        ]
        parsed_rows = []
        for line in lines:
            left_raw, _, right_raw = line.partition("|")
            left_half = tokenize_line(left_raw)
            right_half = tokenize_line(right_raw)
            parsed_rows.append({"left": left_half, "right": right_half})
        return parsed_rows

    @classmethod
    def from_text(
        cls,
        name: str,
        layout: str,
        thumbs: Optional[Union[List[Any], Tuple[Any, ...]]] = None,
        thumb_base: Optional[Union[Tuple, List, Dict]] = None,
        thumb_extras: Optional[Dict] = None,
        generate_mac: bool = True,
    ) -> "Layer":
        return cls(
            name=name,
            layout=layout,
            thumbs=thumbs,
            thumb_base=thumb_base,
            thumb_extras=thumb_extras,
            generate_mac=generate_mac,
        )

    @classmethod
    def raw_layer(cls, name: str, raw_content: str) -> "Layer":
        """
        Creates a raw devicetree layer (e.g. for game layer or custom bindings).
        """
        return cls(name=name, rows=[], is_raw_devicetree=True, raw_content=raw_content)

    def format_token(
        self,
        token: Any,
        os_target: str = "default",
        registered_behaviors: Optional[Dict[str, object]] = None,
    ) -> str:
        """
        Formats a key binding token:
          - If string starting with '&': returns raw binding with OS substitutions if needed.
          - If plain string keycode: prepends '&kp '.
          - If OsKey: resolves kp/behavior for the OS target.
          - If BehaviorCall / HRMCall / callable / object: evaluates/renders it to a string.
        """
        if isinstance(token, str):
            t_str = token.strip()
            if not t_str:
                return "&none"
            if t_str.startswith("&"):
                parts = t_str.split()
                if len(parts) > 1:
                    new_parts = [parts[0]]
                    for p in parts[1:]:
                        new_parts.append(LayerRef(p).get_layer_name(os_target))
                    return " ".join(new_parts)
                return t_str
            
            # Check registered behaviors (ModMorph, Macro, etc.) by string name
            if registered_behaviors and t_str in registered_behaviors:
                beh = registered_behaviors[t_str]
                if hasattr(beh, "render_call"):
                    return beh.render_call(os_target)
                if hasattr(beh, "render"):
                    return beh.render(os_target)
                suffix = "_mac" if (os_target == "mac" and getattr(beh, "has_mac_variant", False)) else ""
                return f"&{t_str}{suffix}"
            
            if "(" in t_str and ")" in t_str:
                return f"&kp {t_str}" if not t_str.startswith("&") else t_str
            
            return f"&kp {t_str}"

        if isinstance(token, OsKey):
            val = token.get_kp(os_target)
            return val if val.startswith("&") else f"&kp {val}"

        if hasattr(token, "render_call") and callable(getattr(token, "render_call")):
            return token.render_call(os_target)

        if hasattr(token, "render") and callable(getattr(token, "render")):
            return token.render(os_target)

        if callable(token):
            try:
                res = token(os_target)
            except TypeError:
                res = token()
            return self.format_token(res, os_target, registered_behaviors)

        if hasattr(token, "name"):
            suffix = "_mac" if (os_target == "mac" and getattr(token, "has_mac_variant", False)) else ""
            return f"&{token.name}{suffix}"

        return f"&kp {token}"

    def render_layer_bindings(
        self,
        keyboard,
        os_target: str,
        registered_behaviors: Optional[Dict[str, object]] = None,
        default_thumb_base: Optional[Any] = None,
        default_thumb_extras: Optional[Any] = None,
    ) -> Tuple[List[Tuple[List[str], List[str]]], List[str]]:
        if self.is_raw_devicetree:
            return [], [self.raw_content]

        rows_bindings = []
        max_cols = keyboard.max_cols

        # Process 3 main rows (Top, Mid, Bot)
        for row_idx, row in enumerate(self.rows[:3]):
            left_tokens = row["left"]
            right_tokens = row["right"]

            # Column index 0 = innermost (adjacent to center).
            # Left half written left-to-right: left_tokens[-1] is innermost (col 0).
            # Right half written left-to-right: right_tokens[0] is innermost (col 0).
            left_cols = {}
            for idx, token in enumerate(reversed(left_tokens)):
                col_idx = idx
                if col_idx < max_cols:
                    left_cols[col_idx] = token

            right_cols = {}
            for idx, token in enumerate(right_tokens):
                col_idx = idx
                if col_idx < max_cols:
                    right_cols[col_idx] = token

            left_row_bindings = []
            right_row_bindings = []

            # Left half: emit from outermost (max_cols-1) down to innermost (0)
            for c in range(max_cols - 1, -1, -1):
                if c in keyboard.column_overrides:
                    ov = keyboard.column_overrides[c]
                    side_overrides = ov.get("left", [])
                    if row_idx < len(side_overrides):
                        left_row_bindings.append(self.format_token(side_overrides[row_idx], os_target, registered_behaviors))
                        continue

                tok = left_cols.get(c, "&none")
                left_row_bindings.append(self.format_token(tok, os_target, registered_behaviors))

            # Right half: emit from innermost (0) up to outermost (max_cols-1)
            for c in range(max_cols):
                if c in keyboard.column_overrides:
                    ov = keyboard.column_overrides[c]
                    side_overrides = ov.get("right", [])
                    if row_idx < len(side_overrides):
                        right_row_bindings.append(self.format_token(side_overrides[row_idx], os_target, registered_behaviors))
                        continue

                tok = right_cols.get(c, "&none")
                right_row_bindings.append(self.format_token(tok, os_target, registered_behaviors))

            rows_bindings.append((left_row_bindings, right_row_bindings))

        # Thumbs
        if self.transparent_thumbs:
            lh_keys = [k for row in keyboard.layout for k in row if k.startswith("LH")]
            rh_keys = [k for row in keyboard.layout for k in row if k.startswith("RH")]
            left_thumb_tokens = ["&trans"] * len(lh_keys)
            right_thumb_tokens = ["&trans"] * len(rh_keys)
        elif self.thumbs is not None:
            if isinstance(self.thumbs, (tuple, list)) and len(self.thumbs) == 2 and isinstance(self.thumbs[1], dict):
                t_base, t_extras = self.thumbs[0], self.thumbs[1]
                left_thumb_tokens, right_thumb_tokens = keyboard.get_thumb_halves(os_target=os_target, thumb_base=t_base, thumb_extras=t_extras)
            elif isinstance(self.thumbs, dict) and ("left" in self.thumbs or "right" in self.thumbs):
                left_thumb_tokens = normalize_tokens(self.thumbs.get("left", []))
                right_thumb_tokens = normalize_tokens(self.thumbs.get("right", []))
            elif isinstance(self.thumbs, (list, tuple)) and len(self.thumbs) == 2 and isinstance(self.thumbs[0], (list, tuple)):
                left_thumb_tokens = normalize_tokens(self.thumbs[0])
                right_thumb_tokens = normalize_tokens(self.thumbs[1])
            elif self.thumbs in ["trans", "&trans"]:
                lh_keys = [k for row in keyboard.layout for k in row if k.startswith("LH")]
                rh_keys = [k for row in keyboard.layout for k in row if k.startswith("RH")]
                left_thumb_tokens = ["&trans"] * len(lh_keys)
                right_thumb_tokens = ["&trans"] * len(rh_keys)
            else:
                all_t = normalize_tokens(self.thumbs)
                mid = len(all_t) // 2
                left_thumb_tokens = all_t[:mid]
                right_thumb_tokens = all_t[mid:]
        elif self.thumb_base is not None or self.thumb_extras is not None:
            left_thumb_tokens, right_thumb_tokens = keyboard.get_thumb_halves(os_target=os_target, thumb_base=self.thumb_base, thumb_extras=self.thumb_extras)
        elif default_thumb_base is not None or default_thumb_extras is not None:
            left_thumb_tokens, right_thumb_tokens = keyboard.get_thumb_halves(os_target=os_target, thumb_base=default_thumb_base, thumb_extras=default_thumb_extras)
        else:
            lh_keys = [k for row in keyboard.layout for k in row if k.startswith("LH")]
            rh_keys = [k for row in keyboard.layout for k in row if k.startswith("RH")]
            left_thumb_tokens = ["&trans"] * len(lh_keys)
            right_thumb_tokens = ["&trans"] * len(rh_keys)

        left_thumb_bindings = [self.format_token(t, os_target, registered_behaviors) for t in left_thumb_tokens]
        right_thumb_bindings = [self.format_token(t, os_target, registered_behaviors) for t in right_thumb_tokens]

        return rows_bindings, (left_thumb_bindings, right_thumb_bindings)

    def render_dts(
        self,
        keyboard,
        os_target: str,
        registered_behaviors: Optional[Dict[str, object]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        default_thumb_base: Optional[Any] = None,
        default_thumb_extras: Optional[Any] = None,
    ) -> str:
        layer_name = f"{self.name}M" if (os_target == "mac" and self.name in ["Nav", "Sym", "Fn"]) else (f"{self.name}_mac" if os_target == "mac" else self.name)

        lines = [f"        {layer_name} {{"]
        lines.append('            bindings = <')
        
        rows_bindings, (left_thumb_bindings, right_thumb_bindings) = self.render_layer_bindings(
            keyboard,
            os_target,
            registered_behaviors,
            default_thumb_base=default_thumb_base,
            default_thumb_extras=default_thumb_extras,
        )
        
        if self.is_raw_devicetree:
            for b in left_thumb_bindings + right_thumb_bindings:
                lines.append(f'                {b}')
        else:
            # Calculate column widths across all rows for alignment
            max_cols = keyboard.max_cols
            col_widths_left = [0] * max_cols
            col_widths_right = [0] * max_cols

            for left_row, right_row in rows_bindings:
                for c, tok in enumerate(left_row):
                    col_widths_left[c] = max(col_widths_left[c], len(tok))
                for c, tok in enumerate(right_row):
                    col_widths_right[c] = max(col_widths_right[c], len(tok))

            for left_row, right_row in rows_bindings:
                left_str = " ".join(tok.ljust(col_widths_left[c]) for c, tok in enumerate(left_row))
                right_str = " ".join(tok.ljust(col_widths_right[c]) for c, tok in enumerate(right_row))
                lines.append(f'                {left_str} /**/ {right_str}')

            if left_thumb_bindings or right_thumb_bindings:
                if left_thumb_bindings and right_thumb_bindings:
                    lines.append(f'                {" ".join(left_thumb_bindings)} /**/ {" ".join(right_thumb_bindings)}')
                else:
                    lines.append(f'                {" ".join(left_thumb_bindings + right_thumb_bindings)}')

        lines.append('            >;')
        lines.append('        };')
        return "\n".join(lines)

    def render(
        self,
        keyboard,
        os_target: str = "default",
        registered_behaviors: Optional[Dict[str, object]] = None,
        layer_indices: Optional[Dict[str, int]] = None,
        default_thumb_base: Optional[Any] = None,
        default_thumb_extras: Optional[Any] = None,
    ) -> str:
        """
        Directly returns the layer DTS definition string.
        """
        return self.render_dts(
            keyboard=keyboard,
            os_target=os_target,
            registered_behaviors=registered_behaviors,
            layer_indices=layer_indices,
            default_thumb_base=default_thumb_base,
            default_thumb_extras=default_thumb_extras,
        )
