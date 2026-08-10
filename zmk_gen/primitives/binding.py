"""
Lower-level domain building blocks for keymap bindings in ZMK.
"""
from typing import Protocol, Any, Optional, Union, List, Dict
from ..os_key import OsKey, CTL_GUI, GUI_CTL


class Binding(Protocol):
    def render(self, os_target: str = "default", context: Optional[Any] = None) -> str:
        """Renders the Devicetree binding string (e.g. \x27&kp A\x27, \x27&mo NavM\x27)."""
        ...


class Key:
    """
    Represents a plain keycode or full &binding string.
    """
    def __init__(self, code: str):
        self.code = str(code).strip()

    def render(self, os_target: str = "default", context: Optional[Any] = None) -> str:
        if not self.code:
            return "&none"
        if self.code.startswith("&"):
            return self.code
        return f"&kp {self.code}"

    def __str__(self) -> str:
        return self.render("default")

    def __call__(self, os_target: str = "default") -> str:
        return self.render(os_target)


class LayerRef:
    """
    Encapsulates an OS-aware Layer reference (e.g., Nav -> NavM on mac).
    """
    def __init__(self, layer: Union[str, Any], is_momentary: bool = False):
        self.layer = layer
        self.is_momentary = is_momentary

    def get_layer_name(self, os_target: str = "default") -> str:
        if hasattr(self.layer, "name"):
            name = self.layer.name
            generate_mac = getattr(self.layer, "generate_mac", True)
        else:
            name = str(self.layer)
            generate_mac = name.lower() not in ["sys", "system", "game"]

        if os_target == "mac" and generate_mac:
            if name in ["Nav", "Sym", "Fn", "NAV", "SYM", "FN"]:
                return f"{name}M"
            elif name in ["Graphite", "Qwerty"]:
                return f"{name}_mac"
            elif hasattr(self.layer, "generate_mac") and getattr(self.layer, "generate_mac"):
                return f"{name}_mac" if "_" in name or len(name) > 4 else f"{name}M"
        return name

    def render(self, os_target: str = "default", context: Optional[Any] = None) -> str:
        name = self.get_layer_name(os_target)
        return f"&mo {name}" if self.is_momentary else name

    def __str__(self) -> str:
        return self.get_layer_name("default")

    def __call__(self, os_target: str = "default") -> str:
        return self.render(os_target)


class BehaviorCall:
    """
    Represents a ZMK behavior call in a layer binding (e.g. &mt LCTL RET, &mo Nav, &bt BT_SEL 0).
    Can be evaluated with an OS target (default/mac) to produce a ZMK binding string.
    """
    def __init__(self, behavior_name: str, *args: Any):
        self.behavior_name = behavior_name
        self.args = list(args)

    def render(self, os_target: str = "default", context: Optional[Any] = None) -> str:
        rendered_args = []
        for a in self.args:
            if isinstance(a, OsKey):
                rendered_args.append(a.get_kp(os_target))
            elif isinstance(a, LayerRef):
                rendered_args.append(a.get_layer_name(os_target))
            elif isinstance(a, BehaviorCall):
                rendered_args.append(a.render(os_target, context))
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
                rendered_args.append(LayerRef(a).get_layer_name(os_target))
            elif isinstance(a, str):
                if a == "CTL_GUI":
                    rendered_args.append(CTL_GUI.get_kp(os_target))
                elif a == "GUI_CTL":
                    rendered_args.append(GUI_CTL.get_kp(os_target))
                else:
                    rendered_args.append(str(a))
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
    return BehaviorCall("lt", LayerRef(layer), tap)

def mo(layer: Union[str, Any]) -> BehaviorCall:
    return BehaviorCall("mo", LayerRef(layer))

def tog(layer: Union[str, Any]) -> BehaviorCall:
    return BehaviorCall("tog", LayerRef(layer))

def sk(mod: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("sk", mod)

def thl(layer: Union[str, Any], tap: Union[str, OsKey, Any]) -> BehaviorCall:
    return BehaviorCall("thl", LayerRef(layer), tap)

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
