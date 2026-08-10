import re
from typing import List, Dict, Union, Optional, Tuple, Any
from .os_key import OsKey, CTL_CMD, CMD_CTL
from .behaviors import HRMCall, ModMorph, Macro
from .layout import normalize_tokens, assemble_layer_thumbs

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


class Layer:
    def __init__(
        self,
        name: str,
        rows: List[List[Union[str, OsKey, HRMCall]]],
        thumbs: Optional[Union[List[str], Tuple[str, ...]]] = None,
        thumb_base: Optional[Union[Tuple, List, Dict]] = None,
        thumb_extras: Optional[Dict] = None,
        generate_mac: bool = True,
        is_raw_devicetree: bool = False,
        raw_content: str = "",
    ):
        self.name = name
        self.rows = rows  # List of rows, each row has left half and right half
        self.thumbs = thumbs
        self.thumb_base = thumb_base
        self.thumb_extras = thumb_extras
        self.generate_mac = generate_mac
        self.is_raw_devicetree = is_raw_devicetree
        self.raw_content = raw_content

    @classmethod
    def from_text(
        cls,
        name: str,
        layout: str,
        thumbs: Optional[Union[List[str], Tuple[str, ...]]] = None,
        thumb_base: Optional[Union[Tuple, List, Dict]] = None,
        thumb_extras: Optional[Dict] = None,
        generate_mac: bool = True,
    ) -> "Layer":
        """
        Parses a multiline string layout into row structures.
        Expects 3 rows (Top, Middle, Bottom). Each line has left and right halves
        separated by a | character.

        Column indexing is outward from center: index 0 is the innermost key on
        each half. If the layer defines more columns than the keyboard supports,
        the excess outer columns are silently skipped. If fewer, the outer
        keyboard columns are filled with &none.
        """
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

        return cls(
            name=name,
            rows=parsed_rows,
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

    def format_token(self, token: Union[str, OsKey, HRMCall], os_target: str, registered_behaviors: Dict[str, object]) -> str:
        if isinstance(token, HRMCall):
            return token.render(os_target)
        if isinstance(token, OsKey):
            return f"&kp {token.get_kp(os_target)}"
        
        t_str = str(token).strip()
        if not t_str:
            return "&none"
            
        # Already starts with &
        if t_str.startswith("&"):
            parts = t_str.split()
            if len(parts) > 1:
                new_parts = [parts[0]]
                for p in parts[1:]:
                    if p == "CTL_CMD":
                        new_parts.append(CTL_CMD.get_kp(os_target))
                    elif p == "CMD_CTL":
                        new_parts.append(CMD_CTL.get_kp(os_target))
                    elif os_target == "mac" and p in ["Nav", "Sym", "Fn"]:
                        new_parts.append(f"{p}M")
                    elif os_target == "mac" and p in ["NAV", "SYM", "FN"]:
                        new_parts.append(f"{p}M")
                    elif os_target == "mac" and p in ["Graphite", "Qwerty"]:
                        new_parts.append(f"{p}_mac")
                    else:
                        new_parts.append(p)
                return " ".join(new_parts)
            return t_str
            
        # Check if it's a registered behavior (ModMorph, Macro, etc.)
        if t_str in registered_behaviors:
            beh = registered_behaviors[t_str]
            if isinstance(beh, ModMorph) and beh.mods and any(isinstance(m, OsKey) for m in beh.mods):
                suffix = "_mac" if os_target == "mac" else ""
                return f"&{t_str}{suffix}"
            return f"&{t_str}"
            
        # Function-like helpers (e.g., SL(EXCL), CL(RPAR)) passed as text
        if "(" in t_str and ")" in t_str:
            return t_str
            
        # Plain key token -> auto prefix &kp
        return f"&kp {t_str}"

    def render_layer_bindings(
        self,
        keyboard,
        os_target: str,
        registered_behaviors: Dict[str, object],
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
            # Layer tokens are ordered inward-to-outward: token[0] -> col 0, token[1] -> col 1, ...
            # Left half written left-to-right means token[-1] is innermost, so reverse:
            #   left_tokens[-1] -> col 0, left_tokens[-2] -> col 1, ...
            # Right half written left-to-right means token[0] is innermost:
            #   right_tokens[0] -> col 0, right_tokens[1] -> col 1, ...
            # Indices >= max_cols are silently dropped; missing cols filled with &none.

            left_cols = {}
            for idx, token in enumerate(reversed(left_tokens)):
                col_idx = idx  # 0 = innermost
                if col_idx < max_cols:
                    left_cols[col_idx] = token

            right_cols = {}
            for idx, token in enumerate(right_tokens):
                col_idx = idx  # 0 = innermost
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
        if self.thumbs is not None:
            thumb_tokens = normalize_tokens(self.thumbs)
        else:
            t_base = self.thumb_base if self.thumb_base is not None else default_thumb_base
            t_extras = self.thumb_extras if self.thumb_extras is not None else default_thumb_extras
            thumb_tokens = keyboard.get_thumb_bindings(os_target=os_target, thumb_base=t_base, thumb_extras=t_extras)

        thumb_bindings = [self.format_token(t, os_target, registered_behaviors) for t in thumb_tokens]

        return rows_bindings, thumb_bindings

    def render_dts(
        self,
        keyboard,
        os_target: str,
        registered_behaviors: Dict[str, object],
        layer_indices: Dict[str, int],
        default_thumb_base: Optional[Any] = None,
        default_thumb_extras: Optional[Any] = None,
    ) -> str:
        layer_name = f"{self.name}M" if (os_target == "mac" and self.name in ["Nav", "Sym", "Fn"]) else (f"{self.name}_mac" if os_target == "mac" else self.name)

        lines = [f"        {layer_name} {{"]
        lines.append('            bindings = <')
        
        rows_bindings, thumb_bindings = self.render_layer_bindings(
            keyboard,
            os_target,
            registered_behaviors,
            default_thumb_base=default_thumb_base,
            default_thumb_extras=default_thumb_extras,
        )
        
        if self.is_raw_devicetree:
            for b in thumb_bindings:
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

            if thumb_bindings:
                lines.append(f'                {" ".join(thumb_bindings)}')

        lines.append('            >;')
        lines.append('        };')
        return "\n".join(lines)

