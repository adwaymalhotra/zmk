# ZMK Gen
## Key
This is the basic building block of a layer. This can be either a String, or a behavior along with its parameters (if any). This should be fully resolved. `none` and `trans` are special keys which correspond to none and transparent respectively.

Behaviors should be passed as functions (which when invoked will spit out a string). They can also be called at definition to spit out a string which will result in it being treated like a normal raw keycode. This string should begin with an `&` and the string parsing will ignore these. 

`Key("F")` will return a string like `&kp F` and `Key("&beh")` will return `&beh`.

## Layer
A collection of keys. These keys should be fully resolved - therefore should all be strings. When a layer is defined any CtxKey or BehaviorCall should be resolved. So, it rarely makes sense to define a layer directly.

Each layer accepts an array of strings, each corresponding to a keycode. The size of this array should be equal to the size of the keyboard being generated. So, if one were to try and define this directly, each keyboard will have to define its own layer. A layer cannot be translated easily to another keyboard with a different layout.

There should be a layer registry which holds the layer object and its index. This index will be used when evaluating things like conditional layers, hold taps etc. When rendering, a constant is defined with the name of the layer, equal to this index. This constant should be defined at the top of the keymap and used in the fully resolved key. 

## Node
ZMK uses DTSI which accepts a series of nodes which make up the config. Each node has a name. Beyond that there are some fields which can be different for each type of node. A node will also have a section field which identifies if this node goes into one of `[behaviors, combos, macros]`. 

Each subclass of Node should define an array of `properties` containing the name of the property mapped to a NodeProperty object.

The base node class should use the name, binding-cells and properties to output a behavior definition.

Combos, ConditionalLayers, Macros, Keymap etc. are all nodes and we just need to use the correct properties to build our dtsi with these. 

We should be able to register nodes in a registry and at the final step, all parts of the keymap should be included by just iterating on this registry.
A node call can be made for some special directives like `&lt` for configuration of a general purpose behavior.

Subclasses should not define the rendering logic for the final output. The `properties` array should govern this completely.

### NodeProperty
There is a variety of fields for which we'll need to create an enum so that these can be easily defined and used.

Each of these objects should take one or more arguments, and output a string representation of the property which will be understood by ZMK.

This enum represents the place where each user-definable property is defined and all behaviors should use this to populate their properties field.

## Keyboard
A keyboard is a mapping of how the keys on a keyboard are arranged. This is defined using an indexing scheme which assigns a symbol to each key position. These indexes can be used in nodes like Combos, HoldTap and TriState which can define positions where the behavior is active or behaves differently somehow. A sample keyboard definition is:
```python
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
```
Notice that the left and right indexing is separate and starts at the center and increments outwards. The rows are labeled `T=Top, M=Middle, B=Bottom, H=tHumb (or Home)`.

## CtxKey (Contextual Key)
These will be the foundation of everything in this layout. This is the reason why I'm going the generator route. 

An CtxKey is defined like `CTL_CMD = CtxKey(["LCTRL", "LCMD", "LCTRL"])`. When the context is 0, it spits out `LCTRL`, when the context is 1, it spits out `LCMD`. Essentially, it should output the key based on the index passed. 

Behaviors can use CtxKeys. e.g. if I define a tri-state behavior using the above CtxKey, then it should generate three keys: 
``` python
  new_tab = TriState("new_tab", start=kt_on(CTL_CMD), tap="TAB", end=kt_off(CTL_CMD))

  # generates new_tab0 new_tab1 new_tab2. which are used like new_tab() in CtxLayer and &new_tab0 in the output.
```
In the above example, the expected behavior is to use `new_tab()` in a `CtxLayer`. So, the behavior class should contain a method which should return a method which accepts n parameters equal to the number of binding-cells of the behavior. For TriState, this is 0. But for things like `HoldTap` this would be 2.

## CtxLayer (Contextual Layer)
These are layers which can use CtxKeys and know about the keyboard. Usually, we would want to use these for the most part. These will pass a context to each function defined in the rows or thumbs, so that these functions can spit out an array of results, based on which index of context is needed.

Each CtxLayer will have a rows array which takes three tuples of arrays which each have some elements. Each row is filled from the center, so the left array should be evaluated starting at the last element. If there are extra elements in the row, these are ignored. If there are fewer elements than required by the keyboard, then `none` should be used to fill these positions.

For thumbs, we have a tuple like: 
``` python
thumbs = (
    [mt("LGUI", "TAB"), lt("sys", "GRAVE"), mt("LALT", "ESC"), "LSHFT", mo(Nav)],
    [mo(Sym), thm(CTL_GUI, "SPACE"), mt("LALT", "RET"), lt(sys, "FSLH"), mt("SFT", "BSPC")],
)
```
The indexes defined in the keyboard layout govern which index in the thumbs arrays correspond to which key. Similarly to the rows, these are filled in reverse order for the left side. So, the last item here will be LH0, second-last LH1 and so on. For right, the first item is RH0, second RH1 and so on. 

A CtxLayer will be applied to a keyboard to generate a Layer. This layer is specific to the keyboard in question, so this needs to be done for each registered keyboard.

A CtxLayer should parse through its elements to check if there are actually any CtxKeys. If yes, then it will register each output layer in the Layer registry and remember the indices returned. The number of output layers will be governed by max() of the array passed to a CtxKey.  

A CtxLayer also has an optional condition field which is an array of layers. If the layers have multiple outputs then the condition should be applied to each output. e.g. for a `condition = [nav, sym]`, we should output directives like `conditional_layer { if_layers = <nav0, sym0>, then_layers = <layer0>}; conditional_layer { if_layers = <nav1, sym1>, then_layers = <layer1>}; `

## Generator
A Generator will be created for each Keyboard and an array of layers. This also points to an output file where the result should be written. A generator will also have some hardcoded lines at the top for things like includes. 

In each keymap, the layer indices should be defined first, then the directives and constants, then the behaviors, macros and combos, then the keymap in the end. The challenge here is to calculate the resolution of the CtxKeys and then using the correct indices etc. 

The best way to do this is to define the layers first, and then assign the fields to each. So, a sequence like:
```python
graphite = CtxLayer("Graphite")
nav = CtxLayer("Navigation")
# now we can use the layers as needed.

# ... behaviors definition
# ... thumbs definition

graphite.init(
  rows = [...],
  thumbs = (thumbs_base,thumbs_extras),
)
```
