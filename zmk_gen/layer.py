import re
from typing import List, Dict, Union, Optional, Tuple
from .os_key import OsKey
from .behaviors import HRMCall, ModMorph, Macro

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
            elif beh in ["&sk", "&mo", "&tog", "&out"]:
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
        generate_mac: bool = True,
        is_raw_devicetree: bool = False,
        raw_content: str = "",
    ):
        self.name = name
        self.rows = rows  # List of rows, each row has left half and right half
        self.thumbs = thumbs
        self.generate_mac = generate_mac
        self.is_raw_devicetree = is_raw_devicetree
        self.raw_content = raw_content

    @classmethod
    def from_text(
        cls,
        name: str,
        layout: str,
        thumbs: Optional[Union[List[str], Tuple[str, ...]]] = None,
        generate_mac: bool = True,
    ) -> "Layer":
        """
        Parses a multiline string layout into row structures.
        Expects 3 rows (Top, Middle, Bottom). Each line has left half and right half.
        """
        lines = [line.strip() for line in layout.strip().split("\n") if line.strip() and not line.strip().startswith("//")]
        parsed_rows = []
        
        for line in lines:
            tokens = tokenize_line(line)
            if not tokens:
                continue
            
            # Split tokens into left half and right half
            mid = len(tokens) // 2
            left_half = tokens[:mid]
            right_half = tokens[mid:]
            
            parsed_rows.append({"left": left_half, "right": right_half})

        return cls(name=name, rows=parsed_rows, thumbs=thumbs, generate_mac=generate_mac)

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
    ) -> List[str]:
        if self.is_raw_devicetree:
            return [self.raw_content]

        bindings = []
        max_cols = keyboard.max_cols

        # Process 3 main rows (Top, Mid, Bot)
        for row_idx, row in enumerate(self.rows[:3]):
            left_tokens = row["left"]
            right_tokens = row["right"]
            
            num_left = len(left_tokens)
            num_right = len(right_tokens)

            # Map center-out indices
            left_cols = {}
            for idx, token in enumerate(left_tokens):
                col_idx = (num_left - 1) - idx
                if col_idx < max_cols:
                    left_cols[col_idx] = token
                    
            right_cols = {}
            for idx, token in enumerate(right_tokens):
                col_idx = idx
                if col_idx < max_cols:
                    right_cols[col_idx] = token

            row_bindings = []
            
            # Left half: from highest col index down to 0
            for c in range(max_cols - 1, -1, -1):
                if c in keyboard.column_overrides:
                    ov = keyboard.column_overrides[c]
                    side_overrides = ov.get("left", [])
                    if row_idx < len(side_overrides):
                        row_bindings.append(self.format_token(side_overrides[row_idx], os_target, registered_behaviors))
                        continue
                
                tok = left_cols.get(c, "&none")
                row_bindings.append(self.format_token(tok, os_target, registered_behaviors))

            # Right half: from 0 up to highest col index
            for c in range(max_cols):
                if c in keyboard.column_overrides:
                    ov = keyboard.column_overrides[c]
                    side_overrides = ov.get("right", [])
                    if row_idx < len(side_overrides):
                        row_bindings.append(self.format_token(side_overrides[row_idx], os_target, registered_behaviors))
                        continue

                tok = right_cols.get(c, "&none")
                row_bindings.append(self.format_token(tok, os_target, registered_behaviors))

            bindings.extend(row_bindings)

        # Thumbs
        if self.thumbs:
            thumb_tokens = self.thumbs
        else:
            thumb_tokens = keyboard.get_thumb_bindings(os_target)
            
        for t in thumb_tokens:
            bindings.append(self.format_token(t, os_target, registered_behaviors))

        return bindings

    def render_dts(
        self,
        keyboard,
        os_target: str,
        registered_behaviors: Dict[str, object],
        layer_indices: Dict[str, int],
    ) -> str:
        layer_name = f"{self.name}M" if (os_target == "mac" and self.name in ["Nav", "Sym", "Fn"]) else (f"{self.name}_mac" if os_target == "mac" else self.name)

        lines = [f"        {layer_name} {{"]
        lines.append('            bindings = <')
        
        bindings = self.render_layer_bindings(keyboard, os_target, registered_behaviors)
        
        chunk_size = keyboard.max_cols * 2
        for i in range(0, len(bindings), chunk_size):
            chunk = bindings[i:i + chunk_size]
            lines.append(f'                {" ".join(chunk)}')
            
        lines.append('            >;')
        lines.append('        };')
        return "\n".join(lines)
