import os
from typing import List, Dict, Union, Optional, Tuple, Any
from .layout import Keyboard
from .layer import Layer
from .os_key import OsKey
from .behaviors import Behavior, Macro, ModMorph, TriState, HoldTap
from .combo import SimpleCombo, ModLayerCombo

class KeymapGenerator:
    def __init__(
        self,
        keyboards: List[Keyboard],
        layers: List[Layer],
        thumbs: Optional[Union[Tuple, List, Dict]] = None,
        combos: Optional[List[Union[SimpleCombo, ModLayerCombo]]] = None,
        behaviors: Optional[List[Union[Behavior, Macro, ModMorph, TriState, HoldTap]]] = None,
        thumb_base: Optional[Union[Tuple, List, Dict]] = None,
        thumb_extras: Optional[Dict] = None,
    ):
        self.keyboards = keyboards
        self.layers = layers
        self.combos = combos or []
        self.behaviors = behaviors or []
        self.registered_behaviors = {b.name: b for b in self.behaviors}
        
        if thumb_base is not None or thumb_extras is not None:
            self.thumb_base = thumb_base
            self.thumb_extras = thumb_extras
        elif isinstance(thumbs, (list, tuple)) and len(thumbs) >= 2:
            self.thumb_base = thumbs[0]
            self.thumb_extras = thumbs[1]
        elif isinstance(thumbs, dict):
            self.thumb_base = thumbs.get("base", thumbs.get("thumb_base"))
            self.thumb_extras = thumbs.get("extras", thumbs.get("thumb_extras"))
        else:
            self.thumb_base = None
            self.thumb_extras = None

    def build_pos_map(self, keyboard: Keyboard) -> Dict[str, int]:
        pos_map = {}
        idx = 0
        for row in keyboard.layout:
            for key_name in row:
                pos_map[key_name] = idx
                idx += 1
        return pos_map

    def build_layer_indices(self) -> Dict[str, int]:
        layer_indices = {}
        idx = 0
        for l in self.layers:
            layer_indices[l.name] = idx
            idx += 1
            if l.generate_mac and l.name in ["Nav", "Sym", "Fn", "Graphite", "Qwerty"]:
                mac_name = f"{l.name}M" if l.name in ["Nav", "Sym", "Fn"] else f"{l.name}_mac"
                layer_indices[mac_name] = idx
                idx += 1
        return layer_indices

    def render_keyboard_keymap(self, keyboard: Keyboard) -> str:
        pos_map = self.build_pos_map(keyboard)
        layer_indices = self.build_layer_indices()

        lines = [
            "// Auto-generated ZMK Keymap by Python zmk_gen system. DO NOT EDIT DIRECTLY.",
            "#include <dt-bindings/zmk/keys.h>",
            "#include <behaviors.dtsi>",
            "#include <dt-bindings/zmk/bt.h>",
            "#include <dt-bindings/zmk/outputs.h>",
            "#include <zmk-helpers/helper.h>",
            "",
            "/* Layer ID Definitions */",
        ]

        # Emit #define layer ID constants at the top of the file
        for name, idx in layer_indices.items():
            lines.append(f"#define {name} {idx}")
        lines.append("")

        # 1. Macros Section
        lines.append("/ {")
        lines.append("    macros {")
        emitted_macros = set()
        for b in self.behaviors:
            if isinstance(b, Macro):
                if b.name not in emitted_macros:
                    lines.append(b.render_dts("default", wrap_root=False))
                    emitted_macros.add(b.name)
                
        for c in self.combos:
            if isinstance(c, ModLayerCombo):
                for macro_name, macro_dts in zip(c.all_macro_names(layer_indices), c.render_all_macros(layer_indices)):
                    if macro_name not in emitted_macros:
                        lines.append(macro_dts)
                        emitted_macros.add(macro_name)
        lines.append("    };")
        lines.append("};")
        lines.append("")

        # 2. Behaviors Section
        lines.append("/ {")
        lines.append("    behaviors {")
        emitted_behaviors = set()
        for b in self.behaviors:
            if isinstance(b, HoldTap):
                if b.name not in emitted_behaviors:
                    lines.append(b.render_dts("default", wrap_root=False))
                    emitted_behaviors.add(b.name)
            elif isinstance(b, TriState):
                if b.name not in emitted_behaviors:
                    lines.append(b.render_dts("default", pos_map=pos_map, wrap_root=False))
                    emitted_behaviors.add(b.name)
            elif isinstance(b, ModMorph):
                if b.name not in emitted_behaviors:
                    lines.append(b.render_dts("default", wrap_root=False))
                    emitted_behaviors.add(b.name)
                if any(isinstance(m, OsKey) for m in b.mods):
                    mac_name = f"{b.name}_mac"
                    if mac_name not in emitted_behaviors:
                        lines.append(b.render_dts("mac", name_suffix="_mac", wrap_root=False))
                        emitted_behaviors.add(mac_name)
            elif isinstance(b, Behavior) and not isinstance(b, Macro):
                if b.name not in emitted_behaviors:
                    lines.append(b.render_dts("default", wrap_root=False))
                    emitted_behaviors.add(b.name)
        lines.append("    };")
        lines.append("};")
        lines.append("")

        # 3. Combos Section
        lines.append("/ {")
        lines.append("    combos {")
        lines.append('        compatible = "zmk,combos";')
        emitted_combos = set()
        for c in self.combos:
            if isinstance(c, SimpleCombo):
                if c.name not in emitted_combos:
                    lines.append(c.render_dts("default", pos_map, layer_indices, self.registered_behaviors))
                    emitted_combos.add(c.name)
            elif isinstance(c, ModLayerCombo):
                for macro_name, combo_dts in zip(c.all_macro_names(layer_indices), c.render_all_combos(pos_map, layer_indices)):
                    combo_key = f"combo_{macro_name.replace('macro_', '', 1)}"
                    if combo_key not in emitted_combos:
                        lines.append(combo_dts)
                        emitted_combos.add(combo_key)
        lines.append("    };")
        lines.append("};")
        lines.append("")

        # 4. Keymap Section
        lines.append("/ {")
        lines.append("    keymap {")
        lines.append('        compatible = "zmk,keymap";')
        lines.append("")

        for l in self.layers:
            lines.append(l.render_dts(keyboard, "default", self.registered_behaviors, layer_indices, default_thumb_base=self.thumb_base, default_thumb_extras=self.thumb_extras))
            if l.generate_mac and l.name in ["Nav", "Sym", "Fn", "Graphite", "Qwerty"]:
                lines.append(l.render_dts(keyboard, "mac", self.registered_behaviors, layer_indices, default_thumb_base=self.thumb_base, default_thumb_extras=self.thumb_extras))

        lines.append("    };")
        lines.append("};")
        return "\n".join(lines)

    def generate_all(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        for kb in self.keyboards:
            content = self.render_keyboard_keymap(kb)
            out_path = os.path.join(output_dir, f"{kb.name}.keymap")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Generated keymap for {kb.name} -> {out_path}")
