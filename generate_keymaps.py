#!/usr/bin/env python3
"""
Python ZMK Keymap Generator Script
Generates keymaps for all defined keyboards into a separate directory ('generated_config/').
"""

import sys
import os

# Add workspace directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zmk_gen import (
    Keyboard, Layer, OsKey, ModLayerCombo, SimpleCombo,
    Macro, ModMorph, NumMorph, TriState, KeymapGenerator,
    CTL_CMD, CMD_CTL, ALT, SFT,
    SL, CL, AL, ML, SR, CR, AR, MR, SYL, SYR
)

# ---------------------------------------------------------------------------
# 1. Macro & Behavior Definitions
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

# Mod Morphs (OS-Aware using CMD_CTL / CTL_CMD / SFT / ALT)
bsdel    = ModMorph("bsdel", "&kp BACKSPACE", "&kp DELETE", mods=[ALT, CMD_CTL, SFT])
dlr_gbp  = ModMorph("dlr_gbp", "&kp DLLR", "&uc_gbp", mods=["MOD_LSFT", "MOD_RSFT"])
amps_eur = ModMorph("amps_eur", "&kp AMPS", "&uc_eur", mods=["MOD_LSFT", "MOD_RSFT"])
star_rup = ModMorph("star_rup", "&kp STAR", "&uc_rup", mods=["MOD_LSFT", "MOD_RSFT"])
dot_col  = ModMorph("dot_col", "&kp DOT", "&kp COLON", mods=[SFT])
com_sem  = ModMorph("com_sem", "&kp COMMA", "&kp SEMICOLON", mods=[SFT])
sqt_dqt  = ModMorph("sqt_dqt", "&kp SQT", "&kp GB_DQT", mods=[SFT])
lpar_lt  = ModMorph("lpar_lt", "&kp LPAR", "&kp LT", mods=[SFT])
rpar_gt  = ModMorph("rpar_gt", "&kp RPAR", "&kp GT", mods=[SFT])

# NumMorphs (using CMD_CTL and ALT)
eql_left = NumMorph("eql_left", "EQUAL", "LEFT", mods=[CMD_CTL, ALT])
n4_down  = NumMorph("n4_down", "N4", "DOWN", mods=[CMD_CTL, ALT])
n5_up    = NumMorph("n5_up", "N5", "UP", mods=[CMD_CTL, ALT])
n6_right = NumMorph("n6_right", "N6", "RIGHT", mods=[CMD_CTL, ALT])
n0_ret   = NumMorph("n0_ret", "N0", "RET", mods=[CMD_CTL, ALT])
n7_pgdn  = NumMorph("n7_pgdn", "N7", "PG_DN", mods=[CMD_CTL, ALT])
n8_pgup  = NumMorph("n8_pgup", "N8", "PG_UP", mods=[CMD_CTL, ALT])
dot_home = NumMorph("dot_home", "DOT", "HOME", mods=[CMD_CTL, ALT])
n9_end   = NumMorph("n9_end", "N9", "END", mods=[CMD_CTL, ALT])

# Tri States
alt_tab  = TriState("alt_tab", start="&kt_on LALT", tap="&kp TAB", end="&kt_off LALT", ignored_positions=["LT3"])
ctl_tab  = TriState("ctl_tab", start="&kt_on LCTL", tap="&kp TAB", end="&kt_off LCTL", ignored_positions=["LT3"])
gui_tab  = TriState("gui_tab", start="&kt_on LGUI", tap="&kp TAB", end="&kt_off LGUI", ignored_positions=["LT3"])
win_switch = OsKey(default="&alt_tab", mac="&gui_tab")

all_behaviors = [
    uc_deg, uc_gbp, uc_eur, uc_rup, vi_sav, find, pre_wor, nex_wor,
    pre_tab, nex_tab, pre_dsk, nex_dsk, cut, copy, paste, half_dn, half_up, del_wor,
    bsdel, dlr_gbp, amps_eur, star_rup, dot_col, com_sem, sqt_dqt, lpar_lt, rpar_gt,
    eql_left, n4_down, n5_up, n6_right, n0_ret, n7_pgdn, n8_pgup, dot_home, n9_end,
    alt_tab, ctl_tab, gui_tab
]

# ---------------------------------------------------------------------------
# 2. Keyboard Physical Layout Definitions
# ---------------------------------------------------------------------------
thumb_base = ("&mo Nav &kp SFT", "&thm CTL_CMD SPC &mo Sym")
thumb_extras = {
    "left":  {"left": ["&mt MET TAB", "&lt SYS GRAVE"], "right": ["&mt LALT ESC"]},
    "right": {"left": ["&mt LALT RET"], "right": ["&lt SYS FSLH", "&mt SFT BSPC"]},
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

all_keyboards = [limoncello, totem, cygnus, discworld, endgame, atreus, pica40]

# ---------------------------------------------------------------------------
# 3. Shared Layer Definitions
# ---------------------------------------------------------------------------
graphite = Layer.from_text(
    name="Graphite",
    layout="""
        B  L  D  W  Z | sqt_dqt F  O       U     J
        N  R  T  S  G | Y       H  A       E     I
        Q  X  M  C  V | K       P  dot_col MINUS com_sem
    """
)

qwerty = Layer.from_text(
    name="Qwerty",
    layout="""
        Q  W  E  R  T | Y  U  I     O   P
        A  S  D  F  G | H  J  K     L   SEMI
        Z  X  C  V  B | N  M  COMMA DOT FSLH
    """
)

nav = Layer.from_text(
    name="Nav",
    layout="""
        win_switch  LS(TAB)    pre_tab     nex_tab     PRCNT | dot_home n7_pgdn n8_pgup n9_end   FSLH
        &sk SFT     &sk ALT    &sk CMD_CTL &sk CTL_CMD STAR  | eql_left n4_down n5_up   n6_right n0_ret
        vi_sav      key_repeat TAB         ESC         QMARK | MINUS    N1      N2      N3       PLUS
    """
)

sym = Layer.from_text(
    name="Sym",
    layout="""
        GRAVE    LT        LBKT     RBKT     GT      | HOME    PG_DN PG_UP END   &sk RALT
        SL(EXCL) AL(GB_AT) ML(LPAR) CL(RPAR) GB_HASH | LEFT    DOWN  UP    RIGHT RET
        AMPS     DLLR      LBRC     RBRC     CARET   | del_wor BSPC  DEL   INS   GB_BSLH
    """
)

fn = Layer.from_text(
    name="Fn",
    layout="""
        F1       F2      F3          F4          F5   | F6   F7       F8       F9     F10
        &sk SFT  &sk ALT &sk CMD_CTL &sk CTL_CMD F11  | F12  C_VOL_DN C_VOL_UP C_MUTE vi_sav
        &tog SYS none    none        none        none | CAPS C_BRI_DN C_BRI_UP none   PSCRN
    """
)

sys_layer = Layer.from_text(
    name="sys",
    layout="""
        &bt BT_SEL 0 &bt BT_SEL 1 &bt BT_SEL 2 &bt BT_SEL 3 &bt BT_CLR | &bt BT_CLR_ALL none none none     &tog GAME
        none         none         C_BRI_UP     C_BRI_DN     sys_reset  | sys_reset      none none &tog QWM &tog QW
        &out OUT_BLE &out OUT_USB none         none         bootloader | bootloader     none none none     &tog GRM
    """,
    generate_mac=False
)

all_layers = [graphite, qwerty, nav, sym, fn, sys_layer]

# ---------------------------------------------------------------------------
# 4. Mod Layer Combos & Simple Combos
# ---------------------------------------------------------------------------
combos = [
    SimpleCombo("degree", "&uc_deg", ["LT4", "LM4"]),
    SimpleCombo("bootloader", "&bootloader", ["LT0", "LT1", "RT1", "RT0"]),
    SimpleCombo("reset", "&sys_reset", ["LT0", "RT0"]),

    # OsKey mods (CTL_CMD, CMD_CTL) auto-generate both linux and mac combos+macros.
    # Plain string mods (ALT, SFT) are identical across OSs → only one combo is generated.
    ModLayerCombo(CTL_CMD, nav, ["LH1", "LM1"]),
    ModLayerCombo(CMD_CTL, nav, ["LH1", "LM2"]),
    ModLayerCombo(ALT,     nav, ["LH1", "LM3"]),
    ModLayerCombo(SFT,     nav, ["LH1", "LM4"]),

    ModLayerCombo([CMD_CTL, CTL_CMD], nav, ["LH1", "LM2", "LM1"]),
    ModLayerCombo([CMD_CTL, ALT],     nav, ["LH1", "LM2", "LM3"]),
    ModLayerCombo([CMD_CTL, SFT],     nav, ["LH1", "LM2", "LM4"]),
    ModLayerCombo([CTL_CMD, ALT],     nav, ["LH1", "LM1", "LM3"]),
    ModLayerCombo([CTL_CMD, SFT],     nav, ["LH1", "LM1", "LM4"]),

    ModLayerCombo(CTL_CMD, sym, ["RH1", "LM1"]),
    ModLayerCombo(CMD_CTL, sym, ["RH1", "LM2"]),
    ModLayerCombo(ALT,     sym, ["RH1", "LM3"]),
    ModLayerCombo(SFT,     sym, ["RH1", "LM4"]),

    ModLayerCombo([CMD_CTL, CTL_CMD], sym, ["RH1", "LM2", "LM1"]),
    ModLayerCombo([CMD_CTL, ALT],     sym, ["RH1", "LM2", "LM3"]),
    ModLayerCombo([CMD_CTL, SFT],     sym, ["RH1", "LM2", "LM4"]),
    ModLayerCombo([CTL_CMD, ALT],     sym, ["RH1", "LM1", "LM3"]),
    ModLayerCombo([CTL_CMD, SFT],     sym, ["RH1", "LM1", "LM4"]),
]

# ---------------------------------------------------------------------------
# 5. Execute Keymap Generation
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    output_directory = os.path.join(os.path.dirname(__file__), "generated_config")
    generator = KeymapGenerator(
        keyboards=all_keyboards,
        layers=all_layers,
        thumbs=(thumb_base, thumb_extras),
        combos=combos,
        behaviors=all_behaviors
    )
    generator.generate_all(output_dir=output_directory)
    print(f"\nAll keymaps successfully generated into: '{output_directory}'")
