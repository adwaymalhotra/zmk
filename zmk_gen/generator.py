import os
from typing import List, Dict, Union, Optional, Tuple, Any
from .layout import *
from .layer import *
from .primitives import *
from .constants import *
from .behaviors import *

class KeymapGenerator:
    def __init__(
        self,
        keyboards: Optional[List[Keyboard]] = None,
        layers: Optional[List[Layer]] = None,
        thumbs: Optional[Union[Tuple, List, Dict]] = None,
        combos: Optional[List[Union[Combo, SimpleCombo, ModLayerCombo]]] = None,
        behaviors: Optional[List[Behavior]] = None,
        thumb_base: Optional[Union[Tuple, List, Dict]] = None,
        thumb_extras: Optional[Dict] = None,
        prior_idle_ms: int = PRIOR_IDLE_MS,
        quick_tap_ms: int = QUICK_TAP_MS,
        tapping_term: int = TAPPING_TERM,
        combo_term: int = COMBO_TERM,
    ):
        self.keyboards = list(keyboards) if keyboards is not None else Keyboard.all()
        self.layers = list(layers) if layers is not None else Layer.all()
        self.prior_idle_ms = prior_idle_ms
        self.quick_tap_ms = quick_tap_ms
        self.tapping_term = tapping_term
        self.combo_term = combo_term
        
        all_registered = Behavior.all()
        if behaviors is not None:
            self.behaviors = list(behaviors)
        else:
            self.behaviors = [b for b in all_registered if not isinstance(b, (Combo, ModLayerCombo))]

        if combos is not None:
            self.combos = list(combos)
        else:
            self.combos = [b for b in all_registered if isinstance(b, (Combo, ModLayerCombo))]

        self.registered_behaviors = {b.name: b for b in (self.behaviors + self.combos)}
        
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
            if l.generate_mac:
                mac_name = LayerRef(l).get_layer_name("mac")
                if mac_name != l.name:
                    layer_indices[mac_name] = idx
                    idx += 1
        return layer_indices

    def render_keyboard_keymap(self, keyboard: Keyboard) -> str:
        pos_map = self.build_pos_map(keyboard)
        layer_indices = self.build_layer_indices()

        keys_l_strs = [str(x) for x in keyboard.get_keys_l(pos_map)]
        keys_r_strs = [str(x) for x in keyboard.get_keys_r(pos_map)]
        thumbs_strs = [str(x) for x in keyboard.get_thumbs_pos(pos_map)]

        lines = [
            "// Auto-generated ZMK Keymap by Python zmk_gen system. DO NOT EDIT DIRECTLY.",
            "#include <dt-bindings/zmk/keys.h>",
            "#include <behaviors.dtsi>",
            "#include <dt-bindings/zmk/bt.h>",
            "#include <dt-bindings/zmk/outputs.h>",
            "#include <zmk-helpers/helper.h>",
            "#include \"keys_en_gb_extended.h\"",
            "",
            f"#define PRIOR_IDLE_MS {self.prior_idle_ms}",
            f"#define QUICK_TAP_MS {self.quick_tap_ms}",
            f"#define TAPPING_TERM {self.tapping_term}",
            "",
            "#undef COMBO_TERM",
            f"#define COMBO_TERM {self.combo_term}",
            "",
            f"#define KEYS_L {' '.join(keys_l_strs)}",
            f"#define KEYS_R {' '.join(keys_r_strs)}",
            f"#define THUMBS {' '.join(thumbs_strs)}",
            "",
            "/* All Other Behaviors */",
            "&sk {",
            "    release-after-ms = <1000>;",
            "    quick-release;",
            "};",
            "",
            "&lt {",
            "    tapping-term-ms = <TAPPING_TERM>;",
            "    quick-tap-ms = <QUICK_TAP_MS>;",
            "    flavor = \"hold-preferred\";",
            "};",
            "",
            "&mt {",
            "    tapping-term-ms = <TAPPING_TERM>;",
            "    quick-tap-ms = <QUICK_TAP_MS>;",
            "    flavor = \"hold-preferred\";",
            "};",
            "",
            "&caps_word {",
            "    continue-list = <UNDERSCORE MINUS BACKSPACE DELETE>;",
            "    /delete-property/ ignore-modifiers;",
            "};",
            "",
            "/* Layer ID Definitions */",
        ]

        # Emit #define layer ID constants at the top of the file
        for name, idx in layer_indices.items():
            lines.append(f"#define {name} {idx}")
        lines.append("")

        # Collect all combos
        all_combos = list(self.combos)
        for b in self.behaviors:
            if isinstance(b, (Combo, ModLayerCombo)) and b not in all_combos:
                all_combos.append(b)

        # 1. Macros Section
        lines.append("/ {")
        lines.append("    macros {")
        emitted_macros = set()
        for b in self.behaviors:
            if isinstance(b, Macro):
                if b.name not in emitted_macros:
                    lines.append(b.render_dts(os_target="default", pos_map=pos_map, wrap_root=False))
                    emitted_macros.add(b.name)
                
        for c in all_combos:
            if isinstance(c, ModLayerCombo):
                for macro_name, macro_dts in c.render_all_macros(layer_indices):
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
            if isinstance(b, (Macro, Combo, ModLayerCombo)):
                continue
            if isinstance(b, Behavior):
                for name, dts in b.render_all_dts(pos_map=pos_map, keyboard=keyboard, wrap_root=False):
                    if name not in emitted_behaviors:
                        lines.append(dts)
                        emitted_behaviors.add(name)
        lines.append("    };")
        lines.append("};")
        lines.append("")

        # 3. Combos Section
        lines.append("/ {")
        lines.append("    combos {")
        lines.append('        compatible = "zmk,combos";')
        emitted_combos = set()
        for c in all_combos:
            if isinstance(c, (Combo, ModLayerCombo)):
                for name, combo_dts in c.render_all_dts(pos_map=pos_map, layer_indices=layer_indices, wrap_root=False):
                    if name not in emitted_combos:
                        lines.append(combo_dts)
                        emitted_combos.add(name)
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
            if l.generate_mac and LayerRef(l).get_layer_name("mac") != l.name:
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
