from typing import List, Tuple, Union, Optional, Dict, Any
from .os_key import OsKey, CTL_GUI, GUI_CTL, ALT, SFT

class Behavior:
    """
    Base class for all ZMK Devicetree behaviors.
    Supports self-contained top-level DTSI block definitions (/ { <section> { <node> { ... }; }; };).
    Automatically registers instances for keymap generation.
    """
    _registry: List["Behavior"] = []

    def __init__(
        self,
        name: str,
        compatible: str,
        section: str = "behaviors",
        binding_cells: int = 0,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.compatible = compatible
        self.section = section
        self.binding_cells = binding_cells
        self.properties = properties or {}
        if self not in Behavior._registry:
            Behavior._registry.append(self)

    @classmethod
    def all(cls) -> List["Behavior"]:
        return list(cls._registry)

    @classmethod
    def get_all(cls) -> List["Behavior"]:
        return list(cls._registry)

    @classmethod
    def clear_registry(cls) -> None:
        cls._registry.clear()

    def render_node_dts(
        self,
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        indent: str = "        ",
    ) -> str:
        name = node_name_override if node_name_override is not None else f"{self.name}{name_suffix}"
        lines = [f"{indent}{name}: {name} {{"]
        lines.append(f'{indent}    compatible = "{self.compatible}";')
        lines.append(f'{indent}    #binding-cells = <{self.binding_cells}>;')
        
        for k, v in self.properties.items():
            if v is None:
                continue
            v_str = str(v)
            if v_str.startswith("<") and v_str.endswith(">"):
                lines.append(f'{indent}    {k} = {v_str};')
            elif v_str.startswith('"') and v_str.endswith('"'):
                lines.append(f'{indent}    {k} = {v_str};')
            elif isinstance(v, int):
                lines.append(f'{indent}    {k} = <{v}>;')
            else:
                lines.append(f'{indent}    {k} = {v_str};')
                
        lines.append(f"{indent}}};")
        return "\n".join(lines)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        node_dts = self.render_node_dts(
            node_name_override=node_name_override,
            name_suffix=name_suffix,
            indent=indent,
        )
        if not wrap_root:
            return node_dts
        return f"/ {{\n    {self.section} {{\n{node_dts}\n    }};\n}};\n"

    def render_all_dts(
        self,
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = False,
        indent: str = "        ",
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        return [(self.name, self.render_dts(
            os_target="default",
            pos_map=pos_map,
            wrap_root=wrap_root,
            indent=indent,
            **kwargs,
        ))]

    def render_call(self, os_target: str = "default") -> str:
        return f"&{self.name}"

    def __call__(self, os_target: str = "default") -> str:
        return self.render_call(os_target)


class Macro(Behavior):
    def __init__(
        self,
        name: str,
        bindings: List[Union[str, OsKey]],
        wait_ms: Optional[int] = None,
        tap_ms: Optional[int] = None,
    ):
        self.raw_bindings = bindings
        props = {}
        if wait_ms is not None:
            props["wait-ms"] = f"<{wait_ms}>"
        if tap_ms is not None:
            props["tap-ms"] = f"<{tap_ms}>"
            
        super().__init__(name=name, compatible="zmk,behavior-macro", section="macros", binding_cells=0, properties=props)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        resolved_bindings = []
        for b in self.raw_bindings:
            if isinstance(b, OsKey):
                resolved_bindings.append(f"&kp {b.get_kp(os_target)}")
            else:
                resolved_bindings.append(str(b))
                
        self.properties["bindings"] = f"<{', '.join(resolved_bindings)}>"
        return super().render_dts(
            os_target=os_target,
            node_name_override=node_name_override,
            name_suffix=name_suffix,
            pos_map=pos_map,
            wrap_root=wrap_root,
            indent=indent,
            **kwargs,
        )


class ModMorph(Behavior):
    def __init__(
        self,
        name: str,
        normal: Union[str, OsKey],
        morph: Union[str, OsKey],
        mods: List[Union[str, OsKey]],
        keep_mods: Optional[List[Union[str, OsKey]]] = None,
    ):
        self.normal = normal
        self.morph = morph
        self.mods = mods
        self.keep_mods = keep_mods
        super().__init__(name=name, compatible="zmk,behavior-mod-morph", section="behaviors", binding_cells=0)

    @property
    def has_mac_variant(self) -> bool:
        return any(isinstance(m, OsKey) for m in self.mods)

    def format_key(self, val: Union[str, OsKey], os_target: str) -> str:
        if isinstance(val, OsKey):
            return f"&kp {val.get_kp(os_target)}"
        val_str = str(val)
        if not val_str.startswith("&"):
            return f"&kp {val_str}"
        return val_str

    def format_mods(self, mod_list: List[Union[str, OsKey]], os_target: str) -> str:
        items = [m.get_mod(os_target) if isinstance(m, OsKey) else str(m) for m in mod_list]
        return "|".join(items)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        normal_str = self.format_key(self.normal, os_target)
        morph_str = self.format_key(self.morph, os_target)
        mods_str = self.format_mods(self.mods, os_target)
        
        self.properties["bindings"] = f"<{normal_str}>, <{morph_str}>"
        self.properties["mods"] = f"<({mods_str})>"
        if self.keep_mods:
            self.properties["keep-mods"] = f"<({self.format_mods(self.keep_mods, os_target)})>"
            
        return super().render_dts(
            os_target=os_target,
            node_name_override=node_name_override,
            name_suffix=name_suffix,
            pos_map=pos_map,
            wrap_root=wrap_root,
            indent=indent,
            **kwargs,
        )

    def render_all_dts(
        self,
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = False,
        indent: str = "        ",
        **kwargs: Any,
    ) -> List[Tuple[str, str]]:
        results = [
            (self.name, self.render_dts(
                os_target="default",
                pos_map=pos_map,
                wrap_root=wrap_root,
                indent=indent,
                **kwargs,
            ))
        ]
        if self.has_mac_variant:
            mac_name = f"{self.name}_mac"
            results.append(
                (mac_name, self.render_dts(
                    os_target="mac",
                    name_suffix="_mac",
                    pos_map=pos_map,
                    wrap_root=wrap_root,
                    indent=indent,
                    **kwargs,
                ))
            )
        return results

    def render_call(self, os_target: str = "default") -> str:
        suffix = "_mac" if (os_target == "mac" and self.has_mac_variant) else ""
        return f"&{self.name}{suffix}"

    def __call__(self, os_target: str = "default") -> str:
        return self.render_call(os_target)


class NumMorph(ModMorph):
    """
    Standard ZMK NUM_MORPH behavior (mod morph activated on MOD_LGUI/MOD_LALT).
    """
    def __init__(self, name: str, normal: str, morph: str, mods: Optional[List[Union[str, OsKey]]] = None):
        if mods is None:
            mods = [GUI_CTL, ALT]
        super().__init__(name=name, normal=normal, morph=morph, mods=mods, keep_mods=mods)


class TriState(Behavior):
    def __init__(
        self,
        name: str,
        start: str,
        tap: str,
        end: str,
        ignored_positions: Optional[List[Union[str, int]]] = None,
    ):
        self.start = start
        self.tap = tap
        self.end = end
        self.ignored_positions = ignored_positions or []
        super().__init__(name=name, compatible="zmk,behavior-tri-state", section="behaviors", binding_cells=0)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        self.properties["bindings"] = f"<{self.start}>, <{self.tap}>, <{self.end}>"
        if self.ignored_positions:
            pos_strs = [str(pos_map.get(p, p) if pos_map else p) for p in self.ignored_positions]
            self.properties["ignored-key-positions"] = f"<{' '.join(pos_strs)}>"
        return super().render_dts(
            os_target=os_target,
            node_name_override=node_name_override,
            name_suffix=name_suffix,
            pos_map=pos_map,
            wrap_root=wrap_root,
            indent=indent,
            **kwargs,
        )


class HoldTap(Behavior):
    def __init__(
        self,
        name: str,
        flavor: str = "tap-preferred",
        hold: str = "&kp",
        tap: str = "&kp",
        trigger_pos: Union[str, List[str], List[int]] = "",
        tapping_term_ms: int = 200,
        quick_tap_ms: int = 175,
        require_prior_idle_ms: Optional[int] = 150,
        bindings: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.flavor = flavor
        self.hold = hold if hold.startswith("&") else f"&{hold}"
        self.tap = tap if tap.startswith("&") else f"&{tap}"
        self.trigger_pos = trigger_pos
        self.tapping_term_ms = tapping_term_ms
        self.quick_tap_ms = quick_tap_ms
        self.require_prior_idle_ms = require_prior_idle_ms
        self.custom_bindings = bindings

        props = properties.copy() if properties else {}
        props["flavor"] = f'"{self.flavor}"'
        props["tapping-term-ms"] = f"<{self.tapping_term_ms}>"
        props["quick-tap-ms"] = f"<{self.quick_tap_ms}>"
        if self.require_prior_idle_ms is not None:
            props["require-prior-idle-ms"] = f"<{self.require_prior_idle_ms}>"
        props["bindings"] = self.custom_bindings or f"<{self.hold}>, <{self.tap}>"

        super().__init__(
            name=name,
            compatible="zmk,behavior-hold-tap",
            section="behaviors",
            binding_cells=2,
            properties=props,
        )

    def resolve_trigger_pos(
        self,
        keyboard: Optional[Any] = None,
        pos_map: Optional[Dict[str, int]] = None,
    ) -> str:
        if not self.trigger_pos:
            return ""
        if isinstance(self.trigger_pos, (list, tuple)):
            if pos_map:
                resolved = [str(pos_map.get(p, p)) for p in self.trigger_pos]
            else:
                resolved = [str(p) for p in self.trigger_pos]
            return " ".join(resolved)
        if isinstance(self.trigger_pos, str):
            tp = self.trigger_pos.strip()
            if keyboard is not None or pos_map is not None:
                keys_l = keyboard.get_keys_l(pos_map) if keyboard and hasattr(keyboard, "get_keys_l") else []
                keys_r = keyboard.get_keys_r(pos_map) if keyboard and hasattr(keyboard, "get_keys_r") else []
                thumbs = keyboard.get_thumbs_pos(pos_map) if keyboard and hasattr(keyboard, "get_thumbs_pos") else []

                parts = tp.split()
                resolved_indices = []
                for p in parts:
                    if p in ["KEYS_L", "L"]:
                        resolved_indices.extend(keys_l)
                    elif p in ["KEYS_R", "R"]:
                        resolved_indices.extend(keys_r)
                    elif p in ["THUMBS", "T"]:
                        resolved_indices.extend(thumbs)
                    elif pos_map and p in pos_map:
                        resolved_indices.append(pos_map[p])
                    elif p.isdigit():
                        resolved_indices.append(int(p))
                    else:
                        resolved_indices.append(p)
                if resolved_indices:
                    return " ".join(str(x) for x in resolved_indices)
            return tp
        return str(self.trigger_pos)

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        keyboard: Optional[Any] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        tp_str = self.resolve_trigger_pos(keyboard=keyboard, pos_map=pos_map)
        if tp_str:
            self.properties["hold-trigger-key-positions"] = f"<{tp_str}>"
        elif "hold-trigger-key-positions" in self.properties:
            del self.properties["hold-trigger-key-positions"]

        return super().render_dts(
            os_target=os_target,
            node_name_override=node_name_override,
            name_suffix=name_suffix,
            pos_map=pos_map,
            keyboard=keyboard,
            wrap_root=wrap_root,
            indent=indent,
            **kwargs,
        )


class HRMCall:
    """
    Represents a Home Row Mod call inside a layer binding, e.g. SL("EXCL"), CL("RPAR").
    Targets hrm_l / hrm_r (for keys) or hrl_l / hrl_r (for layers).
    """
    def __init__(self, hand: str, mod: Union[str, OsKey], key: str, is_layer: bool = False):
        self.hand = "l" if hand in ["l", "L", "left", "Left"] else "r"
        self.mod = mod
        self.key = key
        self.is_layer = is_layer

    def render(self, os_target: str = "default") -> str:
        prefix = "hrl" if self.is_layer else "hrm"
        behavior_name = f"{prefix}_{self.hand}"

        if isinstance(self.mod, OsKey):
            mod_str = self.mod.get_kp(os_target)
        else:
            mod_str = str(self.mod)
            if self.is_layer:
                if os_target == "mac" and mod_str in ["Nav", "Sym", "Fn"]:
                    mod_str = f"{mod_str}M"
                elif os_target == "mac" and mod_str in ["NAV", "SYM", "FN"]:
                    mod_str = f"{mod_str}M"
                elif os_target == "mac" and mod_str in ["Graphite", "Qwerty"]:
                    mod_str = f"{mod_str}_mac"

        return f"&{behavior_name} {mod_str} {self.key}"

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        return self.render(os_target)

    def __call__(self, os_target: str = "default") -> str:
        return self.render(os_target)

    def __str__(self):
        return self.render("default")


class BehaviorCall:
    """
    Represents a ZMK behavior call in a layer binding (e.g. &mt LCTL RET, &mo Nav, &bt BT_SEL 0).
    Can be evaluated with an OS target (default/mac) to produce a ZMK binding string.
    """
    def __init__(self, behavior_name: str, *args: Any):
        self.behavior_name = behavior_name
        self.args = list(args)

    def render(self, os_target: str = "default") -> str:
        rendered_args = []
        for a in self.args:
            if isinstance(a, OsKey):
                rendered_args.append(a.get_kp(os_target))
            elif isinstance(a, BehaviorCall):
                rendered_args.append(a.render(os_target))
            elif hasattr(a, "render_call") and callable(getattr(a, "render_call")):
                rendered_args.append(a.render_call(os_target))
            elif hasattr(a, "render") and callable(getattr(a, "render")):
                rendered_args.append(a.render(os_target))
            elif callable(a):
                try:
                    rendered_args.append(str(a(os_target)))
                except TypeError:
                    rendered_args.append(str(a()))
            elif hasattr(a, "name"):
                # E.g. Layer instance
                layer_name = a.name
                if os_target == "mac" and layer_name in ["Nav", "Sym", "Fn"]:
                    rendered_args.append(f"{layer_name}M")
                elif os_target == "mac" and layer_name in ["Graphite", "Qwerty"]:
                    rendered_args.append(f"{layer_name}_mac")
                else:
                    rendered_args.append(layer_name)
            elif isinstance(a, str):
                if a == "CTL_GUI":
                    rendered_args.append(CTL_GUI.get_kp(os_target))
                elif a == "GUI_CTL":
                    rendered_args.append(GUI_CTL.get_kp(os_target))
                elif os_target == "mac" and a in ["Nav", "Sym", "Fn"]:
                    rendered_args.append(f"{a}M")
                elif os_target == "mac" and a in ["NAV", "SYM", "FN"]:
                    rendered_args.append(f"{a}M")
                elif os_target == "mac" and a in ["Graphite", "Qwerty"]:
                    rendered_args.append(f"{a}_mac")
                else:
                    rendered_args.append(a)
            else:
                rendered_args.append(str(a))

        beh = self.behavior_name if self.behavior_name.startswith("&") else f"&{self.behavior_name}"
        if rendered_args:
            return f"{beh} {' '.join(rendered_args)}"
        return beh

    def render_dts(
        self,
        os_target: str = "default",
        node_name_override: Optional[str] = None,
        name_suffix: str = "",
        pos_map: Optional[Dict[str, int]] = None,
        wrap_root: bool = True,
        indent: str = "        ",
        **kwargs: Any,
    ) -> str:
        return self.render(os_target)

    def __call__(self, *call_args: Any, **kwargs: Any) -> Union[str, "BehaviorCall"]:
        if not call_args and not kwargs:
            return self.render("default")
        if len(call_args) == 1 and call_args[0] in ["default", "mac"]:
            return self.render(call_args[0])
        return BehaviorCall(self.behavior_name, *(self.args + list(call_args)))

    def __str__(self) -> str:
        return self.render("default")

    def __repr__(self) -> str:
        return f"BehaviorCall({self.behavior_name}, {self.args})"


# Standardized Behavior Factory Functions
def mt(hold: Union[str, OsKey, Any], tap: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("mt", hold, tap)

def lt(layer: Union[str, Any], tap: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("lt", layer, tap)

def mo(layer: Union[str, Any]) -> BehaviorCall:
    return BehaviorCall("mo", layer)

def tog(layer: Union[str, Any]) -> BehaviorCall:
    return BehaviorCall("tog", layer)

def sk(mod: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("sk", mod)

def thl(layer: Union[str, Any], tap: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("thl", layer, tap)

def thm(mod: Union[str, OsKey, Any], tap: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("thm", mod, tap)

def out(endpoint: str) -> BehaviorCall:
    ep = endpoint if endpoint.startswith("OUT_") else f"OUT_{endpoint}"
    return BehaviorCall("out", ep)

def bt(command: str, *args: Any) -> BehaviorCall:
    cmd = command if command.startswith("BT_") else f"BT_{command}"
    return BehaviorCall("bt", cmd, *args)

def bt_sel(index: Union[int, str]) -> BehaviorCall:
    return bt("BT_SEL", str(index))

def bt_clr() -> BehaviorCall:
    return bt("BT_CLR")

def bt_clr_all() -> BehaviorCall:
    return bt("BT_CLR_ALL")

def kt_on(key: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("kt_on", key)

def kt_off(key: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("kt_off", key)

def kp(key: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("kp", key)

# Predefined 0-argument behaviors
none = BehaviorCall("none")
trans = BehaviorCall("trans")
bootloader = BehaviorCall("bootloader")
sys_reset = BehaviorCall("sys_reset")
caps_word = BehaviorCall("caps_word")
key_repeat = BehaviorCall("key_repeat")

# Mod key helpers
def S(key: str) -> str: return f"LS({key})"
def C(key: str) -> str: return f"LC({key})"
def A(key: str) -> str: return f"LA({key})"
def G(key: str) -> str: return f"LG({key})"

# Standard HoldTap behaviors
hrm_l = HoldTap("hrm_l", flavor="tap-preferred", hold="&kp", tap="&kp", trigger_pos="KEYS_R THUMBS", tapping_term_ms=200, quick_tap_ms=175, require_prior_idle_ms=150)
hrm_r = HoldTap("hrm_r", flavor="tap-preferred", hold="&kp", tap="&kp", trigger_pos="KEYS_L THUMBS", tapping_term_ms=200, quick_tap_ms=175, require_prior_idle_ms=150)
hrl_l = HoldTap("hrl_l", flavor="tap-preferred", hold="&mo", tap="&kp", trigger_pos="KEYS_R THUMBS", tapping_term_ms=200, quick_tap_ms=175, require_prior_idle_ms=150)
hrl_r = HoldTap("hrl_r", flavor="tap-preferred", hold="&mo", tap="&kp", trigger_pos="KEYS_L THUMBS", tapping_term_ms=200, quick_tap_ms=175, require_prior_idle_ms=150)
thm_ht = HoldTap("thm", flavor="balanced", hold="&kp", tap="&kp", trigger_pos="KEYS_L KEYS_R", tapping_term_ms=200, quick_tap_ms=175, require_prior_idle_ms=150)
thl_ht = HoldTap("thl", flavor="balanced", hold="&mo", tap="&kp", trigger_pos="KEYS_L KEYS_R", tapping_term_ms=200, quick_tap_ms=175, require_prior_idle_ms=150)

# Home Row Mod Call Helpers
def SL(key: str) -> HRMCall: return HRMCall("l", SFT, key)
def CL(key: str) -> HRMCall: return HRMCall("l", CTL_GUI, key)
def AL(key: str) -> HRMCall: return HRMCall("l", ALT, key)
def ML(key: str) -> HRMCall: return HRMCall("l", GUI_CTL, key)

def SR(key: str) -> HRMCall: return HRMCall("r", SFT, key)
def CR(key: str) -> HRMCall: return HRMCall("r", CTL_GUI, key)
def AR(key: str) -> HRMCall: return HRMCall("r", ALT, key)
def MR(key: str) -> HRMCall: return HRMCall("r", GUI_CTL, key)

def SYL(key: str) -> HRMCall: return HRMCall("l", "SYS", key, is_layer=True)
def SYR(key: str) -> HRMCall: return HRMCall("r", "SYS", key, is_layer=True)
