"""
KeyToggle behavior definition.
"""

from typing import Optional
from ..node import Node
from ..property import Prop


class KeyToggle(Node):
  """
  ZMK Key-Toggle behavior (zmk,behavior-key-toggle).
  """

  def __init__(
      self,
      name: str,
      toggle_mode: Optional[str] = None,
      register: bool = True,
  ):
    self.toggle_mode = toggle_mode
    props = []
    if toggle_mode:
      props.append(Prop.str("toggle-mode", toggle_mode))

    super().__init__(
        name=name,
        compatible="zmk,behavior-key-toggle",
        binding_cells=1,
        section="behaviors",
        properties=props,
        has_label=True,
        is_callable=True,
        register=register,
    )


# Standard KeyToggle instances
kt_off = KeyToggle("kt_off", toggle_mode="off")
kt_on = KeyToggle("kt_on", toggle_mode="on")
