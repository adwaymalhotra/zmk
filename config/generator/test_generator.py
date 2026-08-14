"""
Unit tests for the new generator package.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator import (
    Node, NodeProperty, PropertyType, Prop,
    Key, CtxKey, BehaviorCall, none, trans,
    Keyboard, Layer, CtxLayer, ConditionalLayer,
    HoldTap, Macro, ModMorph, NumMorph, TriState, KeyToggle, Combo, ModLayerCombo,
    KeymapGenerator, KeymapContext,
    kp, mo, lt, mt, sk, tog, kt_on, kt_off, thm, thl,
    SFT, ALT, CTL, GUI, SL, CL, AL, ML, SR, CR, AR, MR, SYL, SYR,
)


class TestProperty(unittest.TestCase):
    def test_property_rendering(self):
        self.assertEqual(Prop.int("timeout-ms", 50).render().strip(), "timeout-ms = <50>;")
        self.assertEqual(Prop.str("flavor", "tap-preferred").render().strip(), 'flavor = "tap-preferred";')
        self.assertEqual(Prop.bindings("bindings", "&kp A", "&kp B").render().strip(), "bindings = <&kp A>, <&kp B>;")
        self.assertEqual(Prop.positions("key-positions", [0, 1, 2]).render().strip(), "key-positions = <0 1 2>;")
        self.assertEqual(Prop.mods("mods", ["MOD_LGUI", "LALT"]).render().strip(), "mods = <(MOD_LGUI|MOD_LALT)>;")
        self.assertEqual(Prop.mods("mods", ["LCTRL", "LSHFT"]).render().strip(), "mods = <(MOD_LCTL|MOD_LSFT)>;")
        self.assertEqual(Prop.flag("slow-release").render().strip(), "slow-release;")
        self.assertEqual(Prop.delete("ignore-modifiers").render().strip(), "/delete-property/ ignore-modifiers;")

    def test_mod_morph_with_ctx_key(self):
        cmd_ctl = CtxKey(["LGUI", "LCTRL"])
        mm = ModMorph("test_mm", "BACKSPACE", "DELETE", mods=["LALT", cmd_ctl, "LSFT"], register=False)
        self.assertEqual(mm.max_contexts(), 2)
        variants = mm.resolve_variants()
        self.assertEqual(len(variants), 2)
        self.assertIn("mods = <(MOD_LALT|MOD_LGUI|MOD_LSFT)>;", variants[0].render_node_dts())
        self.assertIn("mods = <(MOD_LALT|MOD_LCTL|MOD_LSFT)>;", variants[1].render_node_dts())


class TestNodeAndCallables(unittest.TestCase):
    def test_callable_node_hold_tap(self):
        ht = HoldTap("my_ht", flavor="tap-preferred", hold="&kp", tap="&kp", register=False)
        self.assertTrue(ht.is_callable)
        self.assertEqual(ht.binding_cells, 2)
        call = ht("LSHFT", "A")
        self.assertIsInstance(call, BehaviorCall)
        self.assertEqual(call.resolve(0).code, "&my_ht LSHFT A")

    def test_callable_node_key_toggle(self):
        kt = KeyToggle("my_kt", toggle_mode="on", register=False)
        self.assertTrue(kt.is_callable)
        self.assertEqual(kt.binding_cells, 1)
        call = kt("LALT")
        self.assertEqual(call.resolve(0).code, "&my_kt LALT")

    def test_callable_node_macro(self):
        m = Macro("my_macro", bindings=["&kp A", "&kp B"], register=False)
        self.assertTrue(m.is_callable)
        self.assertEqual(m.binding_cells, 0)
        call = m()
        self.assertEqual(call.resolve(0).code, "&my_macro")

    def test_callable_arity_mismatch(self):
        ht = HoldTap("my_ht", register=False)
        with self.assertRaises(ValueError):
            ht("LSHFT")  # Missing 2nd arg

    def test_non_callable_node(self):
        combo = Combo("my_combo", key="&caps_word", positions=[0, 1], register=False)
        self.assertFalse(combo.is_callable)
        with self.assertRaises(TypeError):
            combo()


class TestCtxKey(unittest.TestCase):
    def test_ctx_key_resolution(self):
        ctl_cmd = CtxKey(["LCTRL", "LGUI", "LCTRL"])
        self.assertEqual(ctl_cmd.max_contexts(), 3)
        self.assertEqual(ctl_cmd.resolve(0).code, "&kp LCTRL")
        self.assertEqual(ctl_cmd.resolve(1).code, "&kp LGUI")
        self.assertEqual(ctl_cmd.resolve(2).code, "&kp LCTRL")
        self.assertEqual(ctl_cmd.resolve(3).code, "&kp LCTRL")  # Wraps around


class TestKeyboardCenterOutMapping(unittest.TestCase):
    def test_center_out_mapping(self):
        kb = Keyboard(
            name="test_kb",
            max_cols=5,
            layout=[
                ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
                ["LH2", "LH1", "LH0",               "RH0", "RH1", "RH2"],
            ],
            register=False,
        )
        # Left: ["B", "L", "D", "W", "Z"] -> Z is center (LT0), W is LT1, D is LT2, L is LT3, B is LT4
        # Right: ["F", "O", "U", "J", "Q"] -> F is center (RT0), O is RT1, U is RT2, J is RT3, Q is RT4
        row_map = kb.map_row(["B", "L", "D", "W", "Z"], ["F", "O", "U", "J", "Q"], "T")
        self.assertEqual(row_map["LT0"], "Z")
        self.assertEqual(row_map["LT1"], "W")
        self.assertEqual(row_map["LT2"], "D")
        self.assertEqual(row_map["LT3"], "L")
        self.assertEqual(row_map["LT4"], "B")

        self.assertEqual(row_map["RT0"], "F")
        self.assertEqual(row_map["RT1"], "O")
        self.assertEqual(row_map["RT2"], "U")
        self.assertEqual(row_map["RT3"], "J")
        self.assertEqual(row_map["RT4"], "Q")

    def test_resolve_indices(self):
        kb = Keyboard(
            name="test_kb",
            max_cols=5,
            layout=[
                ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
                ["LH2", "LH1", "LH0",               "RH0", "RH1", "RH2"],
            ],
            register=False,
        )
        self.assertEqual(kb.resolve_index("LT0"), 4)
        self.assertEqual(kb.resolve_index("RT0"), 5)
        self.assertEqual(kb.resolve_index(10), 10)
        self.assertEqual(kb.resolve_indices(["LT4", "RT4", "LH0"]), [0, 9, 12])
        with self.assertRaises(KeyError):
            kb.resolve_index("INVALID_POS")

    def test_extra_and_missing_keys(self):
        kb = Keyboard(
            name="test_kb",
            max_cols=3,
            layout=[
                ["LT2", "LT1", "LT0", "RT0", "RT1", "RT2"],
            ],
            register=False,
        )
        # Pass 4 keys on left: ["A", "B", "C", "D"] -> D is LT0, C is LT1, B is LT2, A is extra and ignored
        row_map = kb.map_row(["A", "B", "C", "D"], ["E", "F"], "T")
        self.assertEqual(row_map["LT0"], "D")
        self.assertEqual(row_map["LT1"], "C")
        self.assertEqual(row_map["LT2"], "B")
        self.assertNotIn("A", row_map.values())
        self.assertEqual(row_map["RT0"], "E")
        self.assertEqual(row_map["RT1"], "F")
        self.assertNotIn("RT2", row_map)  # Missing key


class TestCtxLayer(unittest.TestCase):
    def test_two_phase_init(self):
        graphite = CtxLayer("Graphite", register=False)
        graphite.init(
            rows=[
                (["B", "L", "D", "W", "Z"], ["F", "O", "U", "J", "Q"]),
            ],
            thumbs=(["mo_Nav", "SFT"], ["CTL_SPACE", "mo_Sym"]),
        )
        self.assertEqual(graphite.name, "Graphite")
        self.assertEqual(len(graphite.rows), 1)

    def test_contextual_layer_resolution(self):
        ctl_cmd = CtxKey(["LCTRL", "LGUI"])
        kb = Keyboard(
            name="test_kb",
            max_cols=2,
            layout=[
                ["LT1", "LT0", "RT0", "RT1"],
                ["LH0",        "RH0"],
            ],
            register=False,
        )
        layer = CtxLayer(
            "Nav",
            rows=[
                (["A", "B"], ["C", "D"]),
            ],
            thumbs=(
                [thm(ctl_cmd, "SPACE")],
                [mo("Sym")],
            ),
            register=False,
        )
        self.assertEqual(layer.max_contexts(), 2)

        # Context 0: ctl_cmd -> LCTRL
        l0 = layer.resolve(kb, ctx_idx=0, total_contexts=2)
        self.assertEqual(l0.name, "Nav_0")
        self.assertEqual(l0.key_map["LH0"].code, "&thm LCTRL SPACE")

        # Context 1: ctl_cmd -> LGUI
        l1 = layer.resolve(kb, ctx_idx=1, total_contexts=2)
        self.assertEqual(l1.name, "Nav_1")
        self.assertEqual(l1.key_map["LH0"].code, "&thm LGUI SPACE")


class TestEndToEndGenerator(unittest.TestCase):
    def test_keymap_generation(self):
        ctl_cmd = CtxKey(["LCTRL", "LGUI"])
        kb = Keyboard(
            name="mini",
            max_cols=2,
            layout=[
                ["LT1", "LT0", "RT0", "RT1"],
                ["LH0",        "RH0"],
            ],
            register=False,
        )
        base = CtxLayer(
            "Base",
            rows=[(["A", "B"], ["C", "D"])],
            thumbs=([mo("Nav")], [mo("Sym")]),
            register=False,
        )
        nav = CtxLayer(
            "Nav",
            rows=[(["E", "F"], ["G", "H"])],
            transparent_thumbs=True,
            register=False,
        )
        sym = CtxLayer(
            "Sym",
            rows=[(["I", "J"], ["K", "L"])],
            transparent_thumbs=True,
            register=False,
        )
        fn = CtxLayer(
            "Fn",
            rows=[(["1", "2"], ["3", "4"])],
            condition=[nav, sym],
            transparent_thumbs=True,
            register=False,
        )

        gen = KeymapGenerator(
            keyboards=[kb],
            layers=[base, nav, sym, fn],
            nodes=[
                HoldTap("hrm_l", flavor="tap-preferred", register=False),
                Macro("test_macro", bindings=["&kp A", "&kp B"], register=False),
                Combo("test_combo", key="&caps_word", positions=["LT0", "RT0"], register=False),
            ],
        )
        dts = gen.render_keyboard_keymap(kb)
        self.assertIn("#define Base 0", dts)
        self.assertIn("#define Nav 1", dts)
        self.assertIn("#define Sym 2", dts)
        self.assertIn("#define Fn 3", dts)
        self.assertIn('display-name = "Base";', dts)
        self.assertIn('display-name = "Nav";', dts)
        self.assertIn("conditional_layers {", dts)
        self.assertIn("tri_layer_Fn {", dts)
        self.assertIn("if-layers = <Nav Sym>;", dts)
        self.assertIn("then-layer = <Fn>;", dts)
        self.assertIn("test_macro: test_macro {", dts)
        self.assertIn("bindings = <&kp A>, <&kp B>;", dts)
        self.assertIn("combo_test_combo {", dts)
        self.assertIn("key-positions = <1 2>;", dts)


if __name__ == "__main__":
    unittest.main()
