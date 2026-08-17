"""
KeymapGenerator and KeymapContext compilation engine.
"""

import os
from typing import List, Dict, Optional, Callable
from .node import Node, NodeRegistry
from .keyboard import Keyboard
from .layer import CtxLayer, ConditionalLayer
from .behaviors.combo import Combo, ModLayerCombo
from .behaviors.tri_state import TriState

# Timing Defaults
PRIOR_IDLE_MS = 160
QUICK_TAP_MS = 175
TAPPING_TERM = 200
COMBO_TERM = 50


class KeymapContext:
  """
  Context for configuring keymaps in an isolated, pure environment.
  """

  def __init__(
      self,
      keyboard: Keyboard,
      prior_idle_ms: int = PRIOR_IDLE_MS,
      quick_tap_ms: int = QUICK_TAP_MS,
      tapping_term: int = TAPPING_TERM,
      combo_term: int = COMBO_TERM,
  ):
    self.keyboard = keyboard
    self.prior_idle_ms = prior_idle_ms
    self.quick_tap_ms = quick_tap_ms
    self.tapping_term = tapping_term
    self.combo_term = combo_term

    self.layers: List[CtxLayer] = []
    self.nodes: List[Node] = []
    self.mod_layer_combos: List[ModLayerCombo] = []

  def add_layer(self, layer: CtxLayer) -> CtxLayer:
    if layer not in self.layers:
      self.layers.append(layer)
    return layer

  def add_layers(self, *layers: CtxLayer) -> List[CtxLayer]:
    for l in layers:
      self.add_layer(l)
    return self.layers

  def add_node(self, node: Node) -> Node:
    if node not in self.nodes:
      self.nodes.append(node)
    return node

  def add_nodes(self, *nodes: Node) -> List[Node]:
    for n in nodes:
      self.add_node(n)
    return self.nodes

  def add_mod_layer_combo(self, mlc: ModLayerCombo) -> ModLayerCombo:
    if mlc not in self.mod_layer_combos:
      self.mod_layer_combos.append(mlc)
    return mlc


class KeymapGenerator:
  """
  Evaluates keymap specifications against Keyboard hardware matrices
  and emits deterministic ZMK Devicetree .keymap files.
  """

  def __init__(
      self,
      keyboards: Optional[List[Keyboard]] = None,
      layers: Optional[List[CtxLayer]] = None,
      nodes: Optional[List[Node]] = None,
      mod_layer_combos: Optional[List[ModLayerCombo]] = None,
      recipe: Optional[Callable[[KeymapContext], None]] = None,
      prior_idle_ms: int = PRIOR_IDLE_MS,
      quick_tap_ms: int = QUICK_TAP_MS,
      tapping_term: int = TAPPING_TERM,
      combo_term: int = COMBO_TERM,
  ):
    self.keyboards = list(keyboards) if keyboards is not None else Keyboard.all()
    self.layers = list(layers) if layers is not None else CtxLayer.all()
    self.nodes = list(nodes) if nodes is not None else NodeRegistry.get_default().get_nodes()
    self.mod_layer_combos = list(mod_layer_combos) if mod_layer_combos is not None else ModLayerCombo.all()
    self.recipe = recipe
    self.prior_idle_ms = prior_idle_ms
    self.quick_tap_ms = quick_tap_ms
    self.tapping_term = tapping_term
    self.combo_term = combo_term

  def create_context(self, keyboard: Keyboard) -> KeymapContext:
    ctx = KeymapContext(
        keyboard=keyboard,
        prior_idle_ms=self.prior_idle_ms,
        quick_tap_ms=self.quick_tap_ms,
        tapping_term=self.tapping_term,
        combo_term=self.combo_term,
    )
    if self.recipe:
      self.recipe(ctx)
    else:
      ctx.layers = list(self.layers)
      ctx.nodes = list(self.nodes)
      ctx.mod_layer_combos = list(self.mod_layer_combos)
    return ctx

  def render_keyboard_keymap(self, keyboard: Keyboard) -> str:
    ctx = self.create_context(keyboard)

    # 1. Determine total contexts
    total_contexts = 1
    for l in ctx.layers:
      total_contexts = max(total_contexts, l.max_contexts())
    for n in ctx.nodes:
      if hasattr(n, "max_contexts") and callable(getattr(n, "max_contexts")):
        total_contexts = max(total_contexts, n.max_contexts())
    for mlc in ctx.mod_layer_combos:
      total_contexts = max(total_contexts, mlc.max_contexts())

    # 2. Build layer index mapping (#define <LayerName> <Index>)
    layer_indices: Dict[str, int] = {}
    idx = 0
    for l in ctx.layers:
      for c in range(total_contexts):
        layer_name = l.get_layer_name(c, total_contexts)
        if layer_name not in layer_indices:
          layer_indices[layer_name] = idx
          idx += 1

    # 3. Position alias lists
    keys_l_strs = [str(x) for x in keyboard.get_keys_l()]
    keys_r_strs = [str(x) for x in keyboard.get_keys_r()]
    thumbs_strs = [str(x) for x in keyboard.get_thumbs()]

    lines = [
        "// Auto-generated ZMK Keymap by Python generator system. DO NOT EDIT DIRECTLY.",
        "#include <dt-bindings/zmk/keys.h>",
        "#include <behaviors.dtsi>",
        "#include <dt-bindings/zmk/bt.h>",
        "#include <dt-bindings/zmk/outputs.h>",
        "#include <zmk-helpers/helper.h>",
        '#include "keys_en_gb_extended.h"',
        "",
        f"#define PRIOR_IDLE_MS {ctx.prior_idle_ms}",
        f"#define QUICK_TAP_MS {ctx.quick_tap_ms}",
        f"#define TAPPING_TERM {ctx.tapping_term}",
        "",
        "#undef COMBO_TERM",
        f"#define COMBO_TERM {ctx.combo_term}",
        "",
        f"#define KEYS_L {' '.join(keys_l_strs)}",
        f"#define KEYS_R {' '.join(keys_r_strs)}",
        f"#define THUMBS {' '.join(thumbs_strs)}",
        "",
    ]

    # Dynamic Top-Level Override Nodes (&sk, &lt, &mt, &caps_word, etc.)
    override_nodes = [n for n in ctx.nodes if n.section in ("overrides", "root", "root_nodes")]
    if override_nodes:
      lines.append("/* Base Behavior Config */")
      for on in override_nodes:
        lines.append(on.render_node_dts(indent=""))
        lines.append("")

    lines.append("/* Layer Ids */")

    for name, l_idx in layer_indices.items():
      lines.append(f"#define {name} {l_idx}")
    lines.append("")

    # 4. Resolve Nodes by section
    # Generate composite ModLayerCombos
    extra_macros = []
    extra_combos = []
    for mlc in ctx.mod_layer_combos:
      for c in range(total_contexts):
        macro, combo = mlc.generate_nodes(ctx_idx=c, total_contexts=total_contexts, keyboard=keyboard)
        extra_macros.append(macro)
        extra_combos.append(combo)

    all_macros = [n for n in ctx.nodes if n.section == "macros"] + extra_macros
    all_behaviors = [n for n in ctx.nodes if n.section == "behaviors"]
    all_combos = [n for n in ctx.nodes if n.section == "combos"] + extra_combos

    # Single Root / { ... }; containing all sections
    lines.append("/ {")

    # Macros Section
    if all_macros:
      lines.append("    macros {")
      emitted_macros = set()
      for m in all_macros:
        if hasattr(m, "resolve_variants"):
          variants = m.resolve_variants()
        else:
          variants = [m]
        for var in variants:
          if var.name not in emitted_macros:
            lines.append(var.render_node_dts())
            emitted_macros.add(var.name)
      lines.append("    };")
      lines.append("")

    # Behaviors Section
    if all_behaviors:
      lines.append("    behaviors {")
      emitted_behaviors = set()
      for b in all_behaviors:
        if isinstance(b, TriState):
          resolved_b = b.resolve_with_keyboard(keyboard)
          variants = resolved_b.resolve_variants()
        elif hasattr(b, "resolve_variants"):
          variants = b.resolve_variants()
        else:
          variants = [b]
        for var in variants:
          if var.name not in emitted_behaviors:
            lines.append(var.render_node_dts())
            emitted_behaviors.add(var.name)
      lines.append("    };")
      lines.append("")

    # Combos Section
    if all_combos:
      lines.append("    combos {")
      lines.append('        compatible = "zmk,combos";')
      emitted_combos = set()
      for c in all_combos:
        if isinstance(c, Combo):
          resolved_c = c.resolve_with_keyboard(
              keyboard,
              layer_indices=layer_indices,
              total_contexts=total_contexts,
          )
        else:
          resolved_c = c
        if resolved_c.name not in emitted_combos:
          lines.append(resolved_c.render_node_dts())
          emitted_combos.add(resolved_c.name)
      lines.append("    };")
      lines.append("")

    # Conditional Layers Section
    conditional_layers = []
    for l in ctx.layers:
      if l.condition:
        for c in range(total_contexts):
          cl = ConditionalLayer(
              then_layer=l,
              if_layers=l.condition,
              ctx_idx=c,
              total_contexts=total_contexts,
              register=False,
          )
          conditional_layers.append(cl)

    if conditional_layers:
      lines.append("    conditional_layers {")
      lines.append('        compatible = "zmk,conditional-layers";')
      for cl in conditional_layers:
        lines.append(cl.render_node_dts())
      lines.append("    };")
      lines.append("")

    # Keymap Section
    lines.append("    keymap {")
    lines.append('        compatible = "zmk,keymap";')
    lines.append("")
    for l in ctx.layers:
      for c in range(total_contexts):
        concrete_layer = l.resolve(
            keyboard=keyboard,
            ctx_idx=c,
            total_contexts=total_contexts,
            layer_indices=layer_indices,
        )
        lines.append(concrete_layer.render_dts())
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
