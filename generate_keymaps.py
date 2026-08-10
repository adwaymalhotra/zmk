#!/usr/bin/env python3
"""
Python ZMK Keymap Generator Script
Generates keymaps for all defined keyboards into a separate directory ('generated_config/').
"""

import sys
import os

# Add workspace directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zmk_gen import *

# ---------------------------------------------------------------------------
# 0. Global Timing & Behavior Constants
# ---------------------------------------------------------------------------
PRIOR_IDLE_MS = 160
QUICK_TAP_MS = 175
TAPPING_TERM = 200
COMBO_TERM = 50

# ---------------------------------------------------------------------------
# 1. Macro & Behavior Definitions (Automatically registered)
# ---------------------------------------------------------------------------
uc_deg   = Macro("uc_deg", ["&kp RALT", "&kp O", "&kp O"])
uc_gbp   = Macro("uc_gbp", ["&kp RALT", "&kp LS(L)", "&kp EQL"])
uc_eur   = Macro("uc_eur", ["&kp RALT", "&kp C", "&kp EQL"])
uc_rup   = Macro("uc_rup", ["&kp RALT", "&kp R", "&kp EQL"])

vi_sav   = Macro("vi_sav", ["&kp ESC", "&kp COLON", "&kp W", "&kp RET"], wait_ms=20)
find     = Macro("find", ["&kp LC(F)"])
pre_wor  = Macro("pre_wor", ["&kp LC(LEFT)"])
nex_wor  = Macro("nex_wor", ["&kp LC(RIGHT)"])
pre_tab  = Macro("pre_tab", ["&kp LC(LS(TAB))"])
nex_tab  = Macro("nex_tab", ["&kp LC(TAB)"])
pre_dsk  = Macro("pre_dsk", ["&kp LC(LG(LEFT))"])
nex_dsk  = Macro("nex_dsk", ["&kp LC(LG(RIGHT))"])
cut      = Macro("cut", ["&kp LC(X)"])
copy     = Macro("copy", ["&kp LC(C)"])
paste    = Macro("paste", ["&kp LC(V)"])
half_dn  = Macro("half_dn", ["&kp LC(D)"])
half_up  = Macro("half_up", ["&kp LC(U)"])
del_wor  = Macro("del_wor", ["&kp LC(BSPC)"])

# Mod Morphs (OS-Aware using GUI_CTL / CTL_GUI / SFT / ALT)
bsdel    = ModMorph("bsdel", "&kp BACKSPACE", "&kp DELETE", mods=[ALT, GUI_CTL, SFT])
dlr_gbp  = ModMorph("dlr_gbp", "&kp DLLR", "&uc_gbp", mods=["MOD_LSFT", "MOD_RSFT"])
amps_eur = ModMorph("amps_eur", "&kp AMPS", "&uc_eur", mods=["MOD_LSFT", "MOD_RSFT"])
star_rup = ModMorph("star_rup", "&kp STAR", "&uc_rup", mods=["MOD_LSFT", "MOD_RSFT"])
dot_col  = ModMorph("dot_col", "&kp DOT", "&kp COLON", mods=[SFT])
com_sem  = ModMorph("com_sem", "&kp COMMA", "&kp SEMICOLON", mods=[SFT])
sqt_dqt  = ModMorph("sqt_dqt", "&kp SQT", "&kp GB_DQT", mods=[SFT])
lpar_lt  = ModMorph("lpar_lt", "&kp LPAR", "&kp LT", mods=[SFT])
rpar_gt  = ModMorph("rpar_gt", "&kp RPAR", "&kp GT", mods=[SFT])

# NumMorphs (using GUI_CTL and ALT)
eql_left = NumMorph("eql_left", "EQUAL", "LEFT", mods=[GUI_CTL, ALT])
n4_down  = NumMorph("n4_down", "N4", "DOWN", mods=[GUI_CTL, ALT])
n5_up    = NumMorph("n5_up", "N5", "UP", mods=[GUI_CTL, ALT])
n6_right = NumMorph("n6_right", "N6", "RIGHT", mods=[GUI_CTL, ALT])
n0_ret   = NumMorph("n0_ret", "N0", "RET", mods=[GUI_CTL, ALT])
n7_pgdn  = NumMorph("n7_pgdn", "N7", "PG_DN", mods=[GUI_CTL, ALT])
n8_pgup  = NumMorph("n8_pgup", "N8", "PG_UP", mods=[GUI_CTL, ALT])
dot_home = NumMorph("dot_home", "DOT", "HOME", mods=[GUI_CTL, ALT])
n9_end   = NumMorph("n9_end", "N9", "END", mods=[GUI_CTL, ALT])

# Tri States
alt_tab  = TriState("alt_tab", start="&kt_on LALT", tap="&kp TAB", end="&kt_off LALT", ignored_positions=["LT3"])
ctl_tab  = TriState("ctl_tab", start="&kt_on LCTL", tap="&kp TAB", end="&kt_off LCTL", ignored_positions=["LT3"])
gui_tab  = TriState("gui_tab", start="&kt_on LGUI", tap="&kp TAB", end="&kt_off LGUI", ignored_positions=["LT3"])
win_switch = OsKey(default="&alt_tab", mac="&gui_tab")

# ---------------------------------------------------------------------------
# 2. Keyboard Physical Layout Definitions (Automatically registered)
# ---------------------------------------------------------------------------
thumb_base = (
    [mo("Nav"), "SFT"],
    [thm(CTL_GUI, "SPC"), mo("Sym")]
)
thumb_extras = {
    "left":  {"left": [mt("MET", "TAB"), lt("SYS", "GRAVE")], "right": [mt("LALT", "ESC")]},
    "right": {"left": [mt("LALT", "RET")], "right": [lt("SYS", "FSLH"), mt("SFT", "BSPC")]},
}

limoncello = Keyboard(
    name="limoncello",
    max_cols=5,
    layout=[
        ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
        ["LM4", "LM3", "LM2", "LM1", "LM0", "RM0", "RM1", "RM2", "RM3", "RM4"],
        ["LB4", "LB3", "LB2", "LB1", "LB0", "RB0", "RB1", "RB2", "RB3", "RB4"],
        ["LH3", "LH4", "LH0", "LH1", "LH2", "RH2", "RH1", "RH0", "RH4", "RH3"],
    ],
)

totem = Keyboard(
    name="totem",
    max_cols=6,
    layout=[
        ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
        ["LM4", "LM3", "LM2", "LM1", "LM0", "RM0", "RM1", "RM2", "RM3", "RM4"],
        ["LB5", "LB4", "LB3", "LB2", "LB1", "LB0", "RB0", "RB1", "RB2", "RB3", "RB4", "RB5"],
        ["LH2", "LH1", "LH0",               "RH0", "RH1", "RH2"],
    ],
)

cygnus = Keyboard(
    name="cygnus",
    max_cols=5,
    layout=[
        ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
        ["LM4", "LM3", "LM2", "LM1", "LM0", "RM0", "RM1", "RM2", "RM3", "RM4"],
        ["LB4", "LB3", "LB2", "LB1", "LB0", "RB0", "RB1", "RB2", "RB3", "RB4"],
        ["LH2", "LH1", "LH0",               "RH0", "RH1", "RH2"],
    ],
)

discworld = Keyboard(
    name="discworld",
    max_cols=5,
    layout=[
        ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
        ["LM4", "LM3", "LM2", "LM1", "LM0", "RM0", "RM1", "RM2", "RM3", "RM4"],
        ["LB4", "LB3", "LB2", "LB1", "LB0", "RB0", "RB1", "RB2", "RB3", "RB4"],
        ["LH1", "LH0",               "RH0", "RH1"],
    ],
)

endgame = Keyboard(
    name="endgame",
    max_cols=5,
    layout=[
        ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
        ["LM4", "LM3", "LM2", "LM1", "LM0", "RM0", "RM1", "RM2", "RM3", "RM4"],
        ["LB4", "LB3", "LB2", "LB1", "LB0", "RB0", "RB1", "RB2", "RB3", "RB4"],
        ["LH2", "LH1", "LH0",               "RH0", "RH1", "RH2"],
    ],
)

atreus = Keyboard(
    name="atreus",
    max_cols=5,
    layout=[
        ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
        ["LM4", "LM3", "LM2", "LM1", "LM0", "RM0", "RM1", "RM2", "RM3", "RM4"],
        ["LB4", "LB3", "LB2", "LB1", "LB0", "RB0", "RB1", "RB2", "RB3", "RB4"],
        ["LH5", "LH4", "LH3", "LH2", "LH1", "LH0", "RH0", "RH1", "RH2", "RH3", "RH4", "RH5"],
    ],
)

pica40 = Keyboard(
    name="pica40",
    max_cols=5,
    layout=[
        ["LT4", "LT3", "LT2", "LT1", "LT0", "RT0", "RT1", "RT2", "RT3", "RT4"],
        ["LM5", "LM4", "LM3", "LM2", "LM1", "LM0", "RM0", "RM1", "RM2", "RM3", "RM4", "RM5"],
        ["LB5", "LB4", "LB3", "LB2", "LB1", "LB0", "RB0", "RB1", "RB2", "RB3", "RB4", "RB5"],
        ["LH2", "LH1", "LH0",               "RH0", "RH1", "RH2"],
    ],
)

# ---------------------------------------------------------------------------
# 3. Shared Layer Definitions (Automatically registered)
# ---------------------------------------------------------------------------
graphite = Layer(
    name="Graphite",
    rows=[
        (["B", "L", "D", "W", "Z"], [sqt_dqt, "F", "O",     "U",     "J"]),
        (["N", "R", "T", "S", "G"], ["Y",     "H", "A",     "E",     "I"]),
        (["Q", "X", "M", "C", "V"], ["K",     "P", dot_col, "MINUS", com_sem]),
    ],
)

qwerty = Layer(
    name="Qwerty",
    rows=[
        (["Q", "W", "E", "R", "T"], ["Y", "U", "I",     "O",   "P"]),
        (["A", "S", "D", "F", "G"], ["H", "J", "K",     "L",   "SEMI"]),
        (["Z", "X", "C", "V", "B"], ["N", "M", "COMMA", "DOT", "FSLH"]),
    ],
)

nav = Layer(
    name="Nav",
    rows=[
        ([win_switch, S("TAB"),   pre_tab,     nex_tab,     "PRCNT"], [dot_home, n7_pgdn, n8_pgup, n9_end,   "FSLH"]),
        ([sk(SFT),    sk(ALT),    sk(GUI_CTL), sk(CTL_GUI), "STAR"],  [eql_left, n4_down, n5_up,   n6_right, n0_ret]),
        ([vi_sav,     key_repeat, "TAB",       "ESC",       "QMARK"], ["MINUS",  "N1",    "N2",    "N3",     "PLUS"]),
    ],
)

sym = Layer(
    name="Sym",
    rows=[
        (["GRAVE",    "LT",        "LBKT",     "RBKT",     "GT"],      ["HOME",  "PG_DN", "PG_UP", "END",   sk("RALT")]),
        ([SL("EXCL"), AL("GB_AT"), ML("LPAR"), CL("RPAR"), "GB_HASH"], ["LEFT",  "DOWN",  "UP",    "RIGHT", "RET"]),
        (["AMPS",     "DLLR",      "LBRC",     "RBRC",     "CARET"],   [del_wor, "BSPC",  "DEL",   "INS",   "GB_BSLH"]),
    ],
)

fn = Layer(
    name="Fn",
    rows=[
        (["F1",       "F2",    "F3",        "F4",        "F5"],  ["F6",   "F7",       "F8",       "F9",     "F10"]),
        ([sk(SFT),    sk(ALT), sk(GUI_CTL), sk(CTL_GUI), "F11"], ["F12",  "C_VOL_DN", "C_VOL_UP", "C_MUTE", vi_sav]),
        ([tog("SYS"), none,    none,        none,        none],  ["CAPS", "C_BRI_DN", "C_BRI_UP", none,     "PSCRN"]),
    ],
)

sys_layer = Layer(
    name="sys",
    rows=[
        ([bt_sel(0),  bt_sel(1),  bt_sel(2),  bt_sel(3),  bt_clr()],   [bt_clr_all(), none, none, none,       tog("GAME")]),
        ([none,       none,       "C_BRI_UP", "C_BRI_DN", sys_reset],  [sys_reset,    none, none, tog("QWM"), tog("QW")]),
        ([out("BLE"), out("USB"), none,       none,       bootloader], [bootloader,   none, none, none,       tog("GRM")]),
    ],
    generate_mac=False,
)

# ---------------------------------------------------------------------------
# 4. Mod Layer Combos & Simple Combos (Automatically registered)
# ---------------------------------------------------------------------------
Combo("degree", "&uc_deg", ["LT4", "LM4"])
Combo("bootloader", "&bootloader", ["LT0", "LT1", "RT1", "RT0"])
Combo("reset", "&sys_reset", ["LT0", "RT0"])

# OsKey mods (CTL_GUI, GUI_CTL) auto-generate both linux and mac combos+macros.
# Plain string mods (ALT, SFT) are identical across OSs → only one combo is generated.
ModLayerCombo(CTL_GUI, nav, ["LH1", "LM1"])
ModLayerCombo(GUI_CTL, nav, ["LH1", "LM2"])
ModLayerCombo(ALT,     nav, ["LH1", "LM3"])
ModLayerCombo(SFT,     nav, ["LH1", "LM4"])

ModLayerCombo([GUI_CTL, CTL_GUI], nav, ["LH1", "LM2", "LM1"])
ModLayerCombo([GUI_CTL, ALT],     nav, ["LH1", "LM2", "LM3"])
ModLayerCombo([GUI_CTL, SFT],     nav, ["LH1", "LM2", "LM4"])
ModLayerCombo([CTL_GUI, ALT],     nav, ["LH1", "LM1", "LM3"])
ModLayerCombo([CTL_GUI, SFT],     nav, ["LH1", "LM1", "LM4"])

ModLayerCombo(CTL_GUI, sym, ["RH1", "LM1"])
ModLayerCombo(GUI_CTL, sym, ["RH1", "LM2"])
ModLayerCombo(ALT,     sym, ["RH1", "LM3"])
ModLayerCombo(SFT,     sym, ["RH1", "LM4"])

ModLayerCombo([GUI_CTL, CTL_GUI], sym, ["RH1", "LM2", "LM1"])
ModLayerCombo([GUI_CTL, ALT],     sym, ["RH1", "LM2", "LM3"])
ModLayerCombo([GUI_CTL, SFT],     sym, ["RH1", "LM2", "LM4"])
ModLayerCombo([CTL_GUI, ALT],     sym, ["RH1", "LM1", "LM3"])
ModLayerCombo([CTL_GUI, SFT],     sym, ["RH1", "LM1", "LM4"])

# ---------------------------------------------------------------------------
# 5. Execute Keymap Generation
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    output_directory = os.path.join(os.path.dirname(__file__), "generated_config")
    generator = KeymapGenerator(
        thumbs=(thumb_base, thumb_extras),
        prior_idle_ms=PRIOR_IDLE_MS,
        quick_tap_ms=QUICK_TAP_MS,
        tapping_term=TAPPING_TERM,
        combo_term=COMBO_TERM,
    )
    generator.generate_all(output_dir=output_directory)
    print(f"\nAll keymaps successfully generated into: '{output_directory}'")
