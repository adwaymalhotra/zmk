import re
from typing import List, Dict, Union, Tuple, Optional, Any
from .os_key import OsKey


def tokenize_thumb_str(line: str) -> List[str]:
    """
    Tokenizes a string of thumb bindings, grouping multi-word ZMK behaviors.
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


def normalize_tokens(item: Any) -> List[Any]:
    if item is None:
        return []
    if isinstance(item, (list, tuple)):
        res = []
        for x in item:
            res.extend(normalize_tokens(x))
        return res
    if isinstance(item, str):
        toks = tokenize_thumb_str(item)
        return toks if toks else [item]
    return [item]


def get_base_halves(thumb_base: Any) -> Tuple[List[Any], List[Any]]:
    if not thumb_base:
        return [], []
    if isinstance(thumb_base, dict):
        left = normalize_tokens(thumb_base.get("left", []))
        right = normalize_tokens(thumb_base.get("right", []))
        return left, right
    if hasattr(thumb_base, "left") and hasattr(thumb_base, "right"):
        left = normalize_tokens(getattr(thumb_base, "left"))
        right = normalize_tokens(getattr(thumb_base, "right"))
        return left, right
    if isinstance(thumb_base, (list, tuple)) and len(thumb_base) >= 2:
        left = normalize_tokens(thumb_base[0])
        right = normalize_tokens(thumb_base[1])
        return left, right
    toks = normalize_tokens(thumb_base)
    mid = len(toks) // 2
    return toks[:mid], toks[mid:]


def get_extras_halves(thumb_extras: Any) -> Tuple[List[Any], List[Any], List[Any], List[Any]]:
    """
    Returns (left_left, left_right, right_left, right_right).
    """
    if not thumb_extras:
        return [], [], [], []
    
    def get_side(obj, side_name):
        if isinstance(obj, dict):
            return obj.get(side_name, {})
        return getattr(obj, side_name, {})

    def get_pos(side_obj, pos_name):
        if isinstance(side_obj, dict):
            return normalize_tokens(side_obj.get(pos_name, []))
        return normalize_tokens(getattr(side_obj, pos_name, []))

    left_obj = get_side(thumb_extras, "left")
    right_obj = get_side(thumb_extras, "right")

    left_left = get_pos(left_obj, "left")
    left_right = get_pos(left_obj, "right")
    right_left = get_pos(right_obj, "left")
    right_right = get_pos(right_obj, "right")

    return left_left, left_right, right_left, right_right


def assemble_layer_thumbs(thumb_base: Any, thumb_extras: Any) -> Tuple[List[Any], List[Any]]:
    """
    Combines thumb_base and thumb_extras into (left_thumbs, right_thumbs).
    On left: thumb_extras.left.left + thumb_base.left + thumb_extras.left.right
    On right: thumb_extras.right.left + thumb_base.right + thumb_extras.right.right
    """
    base_l, base_r = get_base_halves(thumb_base)
    ll, lr, rl, rr = get_extras_halves(thumb_extras)
    
    left_thumbs = ll + base_l + lr
    right_thumbs = rl + base_r + rr
    return left_thumbs, right_thumbs


class Keyboard:
    """
    Defines a physical keyboard layout, including position names, column counts,
    thumb clusters, and column index overrides.
    """
    _registry: List["Keyboard"] = []

    def __init__(
        self,
        name: str,
        max_cols: int,
        layout: List[List[str]],
        thumbs: Optional[Dict[str, Union[List[str], Tuple[str, ...]]]] = None,
        thumb_base: Optional[Union[Tuple, List, Dict]] = None,
        thumb_extras: Optional[Dict] = None,
        column_overrides: Optional[Dict[int, Dict[str, List[str]]]] = None,
        keys_l: Optional[List[int]] = None,
        keys_r: Optional[List[int]] = None,
        thumbs_pos: Optional[List[int]] = None,
    ):
        self.name = name
        self.max_cols = max_cols
        self.layout = layout
        self.thumbs = thumbs or {}
        self.thumb_base = thumb_base
        self.thumb_extras = thumb_extras
        self.column_overrides = column_overrides or {}
        self.keys_l = keys_l
        self.keys_r = keys_r
        self.thumbs_pos = thumbs_pos
        if self not in Keyboard._registry:
            Keyboard._registry.append(self)

    @classmethod
    def all(cls) -> List["Keyboard"]:
        return list(cls._registry)

    @classmethod
    def clear_registry(cls) -> None:
        cls._registry.clear()

    def get_pos_map(self) -> Dict[str, int]:
        pos_map = {}
        idx = 0
        for row in self.layout:
            for key_name in row:
                pos_map[key_name] = idx
                idx += 1
        return pos_map

    def get_keys_l(self, pos_map: Optional[Dict[str, int]] = None) -> List[int]:
        if self.keys_l is not None:
            return list(self.keys_l)
        pos_map = pos_map or self.get_pos_map()
        res = []
        for row in self.layout:
            for k in row:
                if k.startswith("L") and not k.startswith("LH"):
                    res.append(pos_map.get(k, k))
        return [int(x) for x in res]

    def get_keys_r(self, pos_map: Optional[Dict[str, int]] = None) -> List[int]:
        if self.keys_r is not None:
            return list(self.keys_r)
        pos_map = pos_map or self.get_pos_map()
        res = []
        for row in self.layout:
            for k in row:
                if k.startswith("R") and not k.startswith("RH"):
                    res.append(pos_map.get(k, k))
        return [int(x) for x in res]

    def get_thumbs_pos(self, pos_map: Optional[Dict[str, int]] = None) -> List[int]:
        if self.thumbs_pos is not None:
            return list(self.thumbs_pos)
        pos_map = pos_map or self.get_pos_map()
        res = []
        for row in self.layout:
            for k in row:
                if k.startswith("LH") or k.startswith("RH"):
                    res.append(pos_map.get(k, k))
        return [int(x) for x in res]

    def _slice_left_thumbs(
        self,
        n_lh: int,
        ll: List[Any],
        base_l: List[Any],
        lr: List[Any],
        left_thumbs: List[Any],
    ) -> List[Any]:
        if n_lh == len(left_thumbs):
            return list(left_thumbs)
        if n_lh < len(left_thumbs):
            if n_lh <= len(base_l):
                return base_l[-n_lh:] if n_lh > 0 else []
            extra_needed = n_lh - len(base_l)
            if extra_needed <= len(ll):
                return ll[-extra_needed:] + base_l
            remaining_needed = extra_needed - len(ll)
            return ll + base_l + lr[:remaining_needed]
        return ["&none"] * (n_lh - len(left_thumbs)) + left_thumbs

    def _slice_right_thumbs(
        self,
        n_rh: int,
        rl: List[Any],
        base_r: List[Any],
        rr: List[Any],
        right_thumbs: List[Any],
    ) -> List[Any]:
        if n_rh == len(right_thumbs):
            return list(right_thumbs)
        if n_rh < len(right_thumbs):
            if n_rh <= len(base_r):
                return base_r[:n_rh]
            extra_needed = n_rh - len(base_r)
            if extra_needed <= len(rr):
                return base_r + rr[:extra_needed]
            remaining_needed = extra_needed - len(rr)
            return rl[-remaining_needed:] + base_r + rr
        return right_thumbs + ["&none"] * (n_rh - len(right_thumbs))

    def resolve_thumbs(
        self,
        thumb_base: Optional[Any] = None,
        thumb_extras: Optional[Any] = None,
        os_target: str = "default",
    ) -> List[Any]:
        t_base = thumb_base if thumb_base is not None else self.thumb_base
        t_extras = thumb_extras if thumb_extras is not None else self.thumb_extras

        left_thumbs, right_thumbs = assemble_layer_thumbs(t_base, t_extras)

        lh_positions = []
        rh_positions = []
        for row in self.layout:
            for key in row:
                if key.startswith("LH"):
                    lh_positions.append(key)
                elif key.startswith("RH"):
                    rh_positions.append(key)

        n_lh = len(lh_positions)
        n_rh = len(rh_positions)

        if n_lh == 0 and n_rh == 0:
            return left_thumbs + right_thumbs

        base_l, base_r = get_base_halves(t_base)
        ll, lr, rl, rr = get_extras_halves(t_extras)

        sel_l = self._slice_left_thumbs(n_lh, ll, base_l, lr, left_thumbs)
        sel_r = self._slice_right_thumbs(n_rh, rl, base_r, rr, right_thumbs)

        return sel_l + sel_r

    def get_thumb_halves(
        self,
        os_target: str = "default",
        thumb_base: Optional[Any] = None,
        thumb_extras: Optional[Any] = None,
    ) -> Tuple[List[Any], List[Any]]:
        if os_target in self.thumbs:
            val = self.thumbs[os_target]
            bindings = list(val) if isinstance(val, (list, tuple)) else [val]
            mid = len(bindings) // 2
            return bindings[:mid], bindings[mid:]
        elif "default" in self.thumbs:
            val = self.thumbs["default"]
            bindings = list(val) if isinstance(val, (list, tuple)) else [val]
            mid = len(bindings) // 2
            return bindings[:mid], bindings[mid:]

        t_base = thumb_base if thumb_base is not None else self.thumb_base
        t_extras = thumb_extras if thumb_extras is not None else self.thumb_extras

        left_thumbs, right_thumbs = assemble_layer_thumbs(t_base, t_extras)

        lh_positions = []
        rh_positions = []
        for row in self.layout:
            for key in row:
                if key.startswith("LH"):
                    lh_positions.append(key)
                elif key.startswith("RH"):
                    rh_positions.append(key)

        n_lh = len(lh_positions)
        n_rh = len(rh_positions)

        if n_lh == 0 and n_rh == 0:
            return left_thumbs, right_thumbs

        base_l, base_r = get_base_halves(t_base)
        ll, lr, rl, rr = get_extras_halves(t_extras)

        sel_l = self._slice_left_thumbs(n_lh, ll, base_l, lr, left_thumbs)
        sel_r = self._slice_right_thumbs(n_rh, rl, base_r, rr, right_thumbs)

        return sel_l, sel_r

    def get_thumb_bindings(
        self,
        os_target: str = "default",
        thumb_base: Optional[Any] = None,
        thumb_extras: Optional[Any] = None,
    ) -> List[Any]:
        left_h, right_h = self.get_thumb_halves(os_target=os_target, thumb_base=thumb_base, thumb_extras=thumb_extras)
        return left_h + right_h

    def _thumb_has_os_split(self) -> bool:
        """True if any mod produces different keys on linux vs mac."""
        return any(
            isinstance(m, OsKey) and m.default_kp != m.mac_kp
            for m in self.thumbs
        )

