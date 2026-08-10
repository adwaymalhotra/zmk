class OsKey:
    """
    Represents a key or modifier whose definition changes between OS targets
    (e.g., Linux/Windows vs macOS).
    """
    def __init__(self, default: str, mac: str, default_mod: str = None, mac_mod: str = None):
        self.default_kp = default
        self.mac_kp = mac
        self.default_mod = default_mod or (f"MOD_{default}" if not default.startswith("MOD_") else default)
        self.mac_mod = mac_mod or (f"MOD_{mac}" if not mac.startswith("MOD_") else mac)

    def get_kp(self, os_target: str = "default") -> str:
        return self.mac_kp if os_target == "mac" else self.default_kp

    def get_mod(self, os_target: str = "default") -> str:
        return self.mac_mod if os_target == "mac" else self.default_mod

    def render(self, os_target: str = "default") -> str:
        val = self.get_kp(os_target)
        return val if val.startswith("&") else f"&kp {val}"

    def __call__(self, os_target: str = "default") -> str:
        return self.render(os_target)

    def __repr__(self):
        return f"OsKey({self.default_kp}/{self.mac_kp})"


# Common OS-swapping keys
CTL_GUI = OsKey(default="LCTL", mac="LGUI")
GUI_CTL = OsKey(default="LGUI", mac="LCTL")

# Standard modifier key strings
ALT = "LALT"
SFT = "LSHFT"
CTL = "LCTL"
MET = "LMETA"
GUI = "LGUI"

