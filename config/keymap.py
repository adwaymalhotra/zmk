#!/usr/bin/env python3
"""
Migrated Keymap Generation Script using the new pure generator architecture.
"""
import sys
import os

# Add config directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generator import *

PRIOR_IDLE_MS = 160
QUICK_TAP_MS = 175
TAPPING_TERM = 200
COMBO_TERM = 50

# Default Behavior Config
Node(
    name="&sk",
    properties=[Prop.int("release-after-ms", 1000), Prop.flag("quick-release")],
    has_label=False,
    is_callable=False,
    section="overrides",
)

Node(
    name="&lt",
    properties=[
        Prop.int("tapping-term-ms", "TAPPING_TERM"),
        Prop.int("quick-tap-ms", "QUICK_TAP_MS"),
        Prop.str("flavor", "hold-preferred"),
    ],
    has_label=False,
    is_callable=False,
    section="overrides",
)

Node(
    name="&mt",
    properties=[
        Prop.int("tapping-term-ms", "TAPPING_TERM"),
        Prop.int("quick-tap-ms", "QUICK_TAP_MS"),
        Prop.str("flavor", "hold-preferred"),
    ],
    has_label=False,
    is_callable=False,
    section="overrides",
)

Node(
    name="&caps_word",
    properties=[
        Prop.positions("continue-list", ["UNDERSCORE", "MINUS", "BACKSPACE", "DELETE"]),
        Prop.delete("ignore-modifiers"),
    ],
    has_label=False,
    is_callable=False,
    section="overrides",
)

# Modifiers
ALT = "LALT"
SFT = "LSHFT"
CTL = "LCTRL"
GUI = "LGUI"
CTL_GUI = CtxKey([CTL,GUI])
GUI_CTL = CtxKey([GUI,CTL])

# Home Row Mod Call Helpers
def SL(key: str): return hrm_l(SFT, key)
def CL(key: str): return hrm_l(CTL_GUI, key)
def AL(key: str): return hrm_l(ALT, key)
def ML(key: str): return hrm_l(GUI_CTL, key)

def SR(key: str): return hrm_r(SFT, key)
def CR(key: str): return hrm_r(CTL_GUI, key)
def AR(key: str): return hrm_r(ALT, key)
def MR(key: str): return hrm_r(GUI_CTL, key)

# Macros
uc_deg   = Macro("uc_deg", ["RALT", "O", "O"])
uc_gbp   = Macro("uc_gbp", ["RALT", S("L"), "EQL"])
uc_eur   = Macro("uc_eur", ["RALT", "C", "EQL"])
uc_rup   = Macro("uc_rup", ["RALT", "R", "EQL"])

vi_sav   = Macro("vi_sav", ["ESC", "COLON", "W", "RET"], wait_ms=20)
find     = Macro("find", [C("F")])
pre_wor  = Macro("pre_wor", [C("LEFT")])
nex_wor  = Macro("nex_wor", [C("RIGHT")])
pre_tab  = Macro("pre_tab", [C(S("TAB"))])
nex_tab  = Macro("nex_tab", [C("TAB")])
pre_dsk  = Macro("pre_dsk", [C(G("LEFT"))])
nex_dsk  = Macro("nex_dsk", [C(G("RIGHT"))])
cut      = Macro("cut", [C("X")])
copy     = Macro("copy", [C("C")])
paste    = Macro("paste", [C("V")])
half_dn  = Macro("half_dn", [C("D")])
half_up  = Macro("half_up", [C("U")])
del_wor  = Macro("del_wor", [C("BSPC")])

# Mod Morphs
bsdel    = ModMorph("bsdel", "BACKSPACE", "DELETE", mods=[ALT, GUI_CTL, "LSFT"])
dlr_gbp  = ModMorph("dlr_gbp", "DLLR", uc_gbp, mods=["LSFT", "RSFT"])
amps_eur = ModMorph("amps_eur", "AMPS", uc_eur, mods=["LSFT", "RSFT"])
star_rup = ModMorph("star_rup", "STAR", uc_rup, mods=["LSFT", "RSFT"])
dot_col  = ModMorph("dot_col", "DOT", "COLON", mods=["LSFT"])
com_sem  = ModMorph("com_sem", "COMMA", "SEMICOLON", mods=["LSFT"])
sqt_dqt  = ModMorph("sqt_dqt", "SQT", "GB_DQT", mods=["LSFT"])
lpar_lt  = ModMorph("lpar_lt", "LPAR", "LT", mods=["LSFT"])
rpar_gt  = ModMorph("rpar_gt", "RPAR", "GT", mods=["LSFT"])

# NumMorphs
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
alt_tab  = TriState("alt_tab", start=kt_on(ALT), tap="TAB", end=kt_off(ALT), ignored_positions=["LT3"])
ctl_tab  = TriState("ctl_tab", start=kt_on(CTL), tap="TAB", end=kt_off(CTL), ignored_positions=["LT3"])
gui_tab  = TriState("gui_tab", start=kt_on(GUI), tap="TAB", end=kt_off(GUI), ignored_positions=["LT3"])
win_switch = CtxKey([alt_tab, gui_tab])

# Keyboards
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

KEYBOARDS = [limoncello, totem, cygnus, discworld, endgame, atreus, pica40]

# Layers
graphite = CtxLayer("Graphite")
qwerty = CtxLayer("Qwerty")
nav = CtxLayer("Nav")
sym = CtxLayer("Sym")
fn = CtxLayer("Fn")
sys_layer = CtxLayer("sys")

thumbs = (
    [mt(GUI_CTL, "TAB"), lt(sys_layer, "GRAVE"), mt(ALT, "ESC"), SFT, mo(nav)],
    [mo(sym), thm(CTL_GUI, "SPACE"), mt(ALT, "RET"), lt(sys_layer, "FSLH"), mt(SFT, "BSPC")],
)

graphite.init(
    rows=[
        (["B", "L", "D", "W", "Z"], [sqt_dqt, "F", "O",     "U",     "J"]),
        (["N", "R", "T", "S", "G"], ["Y",     "H", "A",     "E",     "I"]),
        (["Q", "X", "M", "C", "V"], ["K",     "P", dot_col, "MINUS", com_sem]),
    ],
    thumbs=thumbs,
)

qwerty.init(
    rows=[
        (["Q", "W", "E", "R", "T"], ["Y", "U", "I",     "O",   "P"]),
        (["A", "S", "D", "F", "G"], ["H", "J", "K",     "L",   "SEMI"]),
        (["Z", "X", "C", "V", "B"], ["N", "M", "COMMA", "DOT", "FSLH"]),
    ],
    thumbs=thumbs,
)

nav.init(
    rows=[
        ([win_switch, S("TAB"),   pre_tab,     nex_tab,     "PRCNT"], [dot_home, n7_pgdn, n8_pgup, n9_end,   "FSLH"]),
        ([sk(SFT),    sk(ALT),    sk(GUI_CTL), sk(CTL_GUI), "STAR"],  [eql_left, n4_down, n5_up,   n6_right, n0_ret]),
        ([vi_sav,     key_repeat, "TAB",       "ESC",       "QMARK"], ["MINUS",  "N1",    "N2",    "N3",     "PLUS"]),
    ],
    transparent_thumbs=True,
)

sym.init(
    rows=[
        (["GRAVE",    "LT",        "LBKT",     "RBKT",     "GT"],      ["HOME",  "PG_DN", "PG_UP", "END",   sk("RALT")]),
        ([SL("EXCL"), AL("GB_AT"), ML("LPAR"), CL("RPAR"), "GB_HASH"], ["LEFT",  "DOWN",  "UP",    "RIGHT", "RET"]),
        (["AMPS",     "DLLR",      "LBRC",     "RBRC",     "CARET"],   [del_wor, "BSPC",  "DEL",   "INS",   "GB_BSLH"]),
    ],
    transparent_thumbs=True,
)

fn.init(
    rows=[
        (["F1",          "F2",    "F3",         "F4",         "F5"],  ["F6",   "F7",       "F8",       "F9",     "F10"]),
        ([sk(SFT),       sk(ALT), sk(GUI_CTL),  sk(CTL_GUI),  "F11"], ["F12",  "C_VOL_DN", "C_VOL_UP", "C_MUTE", vi_sav]),
        ([tog(sys_layer), none,    none,         none,         none],  ["CAPS", "C_BRI_DN", "C_BRI_UP", none,     "PSCRN"]),
    ],
    condition=[nav, sym],
    transparent_thumbs=True,
)

sys_layer.init(
    rows=[
        ([bt_sel(0),  bt_sel(1),  bt_sel(2),  bt_sel(3),  bt_clr()],   [bt_clr_all(), none, none, none, tog("Graphite_1")]),
        ([none,       none,       "C_BRI_UP", "C_BRI_DN", sys_reset],  [sys_reset,    none, none, none, tog("Qwerty_0")]),
        ([out("BLE"), out("USB"), none,       none,       bootloader], [bootloader,   none, none, none, tog("Qwerty_1")]),
    ],
    transparent_thumbs=True,
)

# Combos
Combo("degree", uc_deg, ["LT4", "LM4"])
Combo("bootloader", bootloader, ["LT0", "LT1", "RT1", "RT0"])
Combo("reset", sys_reset, ["LT0", "RT0"])

# Mod Layer Combos
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

# Generator call
if __name__ == "__main__":
    generator = KeymapGenerator(
        keyboards=KEYBOARDS,
        prior_idle_ms=PRIOR_IDLE_MS,
        quick_tap_ms=QUICK_TAP_MS,
        tapping_term=TAPPING_TERM,
        combo_term=COMBO_TERM,
    )
    output_directory = os.path.dirname(os.path.abspath(__file__))
    generator.generate_all(output_directory)
