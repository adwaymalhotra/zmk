import os
from typing import List, Dict, Union
from .layout import Keyboard
from .layer import Layer
from .os_key import OsKey
from .behaviors import Behavior, Macro, ModMorph, TriState, HoldTap
from .combo import SimpleCombo, ModLayerCombo, ModLayerCombo2

class KeymapGenerator:
    def __init__(
        self,
        keyboards: List[Keyboard],
        layers: List[Layer],
        combos: List[Union[SimpleCombo, ModLayerCombo, ModLayerCombo2]],
        behaviors: List[Union[Behavior, Macro, ModMorph, TriState, HoldTap]],
    ):
        self.keyboards = keyboards
        self.layers = layers
        self.combos = combos
        self.behaviors = behaviors
        self.registered_behaviors = {b.name: b for b in behaviors}

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
        ]

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
            if isinstance(c, (ModLayerCombo, ModLayerCombo2)):
                m_def = c.render_macro_dts("default", layer_indices)
                m_def_name = c.get_macro_name("default", layer_indices)
                if m_def_name not in emitted_macros:
                    lines.append(m_def)
                    emitted_macros.add(m_def_name)
                    
                m_mac = c.render_macro_dts("mac", layer_indices)
                m_mac_name = c.get_macro_name("mac", layer_indices)
                if m_mac_name not in emitted_macros:
                    lines.append(m_mac)
                    emitted_macros.add(m_mac_name)
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
            elif isinstance(c, (ModLayerCombo, ModLayerCombo2)):
                m_def_name = f"combo_{c.get_macro_name('default', layer_indices)}"
                if m_def_name not in emitted_combos:
                    lines.append(c.render_combo_dts("default", pos_map, layer_indices))
                    emitted_combos.add(m_def_name)
                m_mac_name = f"combo_{c.get_macro_name('mac', layer_indices)}"
                if m_mac_name not in emitted_combos:
                    lines.append(c.render_combo_dts("mac", pos_map, layer_indices))
                    emitted_combos.add(m_mac_name)
        lines.append("    };")
        lines.append("};")
        lines.append("")

        # 4. Keymap Section
        lines.append("/ {")
        lines.append("    keymap {")
        lines.append('        compatible = "zmk,keymap";')
        lines.append("")

        for l in self.layers:
            lines.append(l.render_dts(keyboard, "default", self.registered_behaviors, layer_indices))
            if l.generate_mac and l.name in ["Nav", "Sym", "Fn", "Graphite", "Qwerty"]:
                lines.append(l.render_dts(keyboard, "mac", self.registered_behaviors, layer_indices))

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
