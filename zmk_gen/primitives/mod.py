"""
Modifier helper functions (LS, LC, LA, LG).
"""
from typing import Union, Any

def S(key: Any) -> str: return f"LS({key})"
def C(key: Any) -> str: return f"LC({key})"
def A(key: Any) -> str: return f"LA({key})"
def G(key: Any) -> str: return f"LG({key})"
