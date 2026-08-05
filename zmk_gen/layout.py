from typing import List, Dict, Union, Tuple, Optional

class Keyboard:
    """
    Defines a physical keyboard layout, including position names, column counts,
    thumb clusters, and column index overrides.
    """
    def __init__(
        self,
        name: str,
        max_cols: int,
        layout: List[List[str]],
        thumbs: Optional[Dict[str, Union[List[str], Tuple[str, ...]]]] = None,
        column_overrides: Optional[Dict[int, Dict[str, List[str]]]] = None,
        keys_l: Optional[List[int]] = None,
        keys_r: Optional[List[int]] = None,
        thumbs_pos: Optional[List[int]] = None,
    ):
        self.name = name
        self.max_cols = max_cols
        self.layout = layout
        self.thumbs = thumbs or {}
        self.column_overrides = column_overrides or {}
        self.keys_l = keys_l
        self.keys_r = keys_r
        self.thumbs_pos = thumbs_pos

    def get_thumb_bindings(self, os_target: str = "default") -> List[str]:
        if os_target in self.thumbs:
            val = self.thumbs[os_target]
        elif "default" in self.thumbs:
            val = self.thumbs["default"]
        else:
            return []
        
        if isinstance(val, (list, tuple)):
            return list(val)
        return [val]
