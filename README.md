# Smode Oil API — Unofficial Reference

*[Version française](README.fr.md)*

> Smode Tech does not publish documentation for the Oil/SmodeSDK API for external control.
> Everything below comes from reverse engineering (live introspection through `dir()` / `Oil.docMe()`)
> and real-world feedback, accumulated while building features with the
> [smode-mcp MCP bridge](https://github.com/gyomh/smode-mcp). Verified on Smode Compose R13 and later versions.
> Contributions welcome — see CONTRIBUTING at the bottom of the file.

## Table of contents
- [Safe introspection](#safe-introspection)
- [Golden rule: configure before adding, never after](#golden-rule-configure-before-adding-never-after)
- [A Compo without a target is never evaluated by the engine](#a-compo-without-a-target-is-never-evaluated-by-the-engine)
- [The `.linked` trap](#the-linked-trap)
- [Resolutions](#resolutions)
- [Polymorphic pointers (OwnedPointer)](#polymorphic-pointers-ownedpointer)
- [Enums: never guess the index](#enums-never-guess-the-index)
- [Project tree map](#project-tree-map)
- [3D geometry: GeometryLayer, placement, angles (confirmed R15, 06/10/2026)](#3d-geometry-geometrylayer-placement-angles-confirmed-r15-06102026)
- [3D lights (R15, 07/10/2026)](#3d-lights-r15-07102026)
- [Lock and activation (ActivationState)](#lock-and-activation-activationstate)
- [Shared materials, references, depth (R15)](#shared-materials-references-depth-r15)
- [Compo camera (R15)](#compo-camera-r15)
- [Text (TextLayer)](#text-textlayer)
- [Parameter banks linked to a Script (R15)](#parameter-banks-linked-to-a-script-r15)
- [Checking visually (outside the API)](#checking-visually-outside-the-api)
- [Nested Scene (nested Scene layer)](#nested-scene-nested-scene-layer)
- [Parameters / Links / Cues system](#parameters--links--cues-system)
- [Timeline (TimelineCue)](#timeline-timelinecue)
- [Modifiers, generators and masks (overview)](#modifiers-generators-and-masks-overview)
- [Audio reactive](#audio-reactive)
- [Scripts created programmatically (PythonScriptTool)](#scripts-created-programmatically-pythonscripttool)
- [Imported 3D files, image textures and material compos](#imported-3d-files-image-textures-and-material-compos-r15-08102026)
- [Known UI bugs](#known-ui-bugs)
- [Observed instabilities](#observed-instabilities)
- [The MCP bridge (reminder)](#the-mcp-bridge-reminder)

---

## Safe introspection

There is no Python stub (`.pyi`): `site-packages/Smode/Oil.py` is a ~80-line wrapper around
extensions compiled into `Smode.exe`, without the real class definitions.

Reliable methods, to be used in this order:
1. `obj.getOilClassName()` — the real class name.
2. `dir(obj)` — list of attributes/methods, lightweight, no known risk.
3. `Oil.createObject("ClassName")` inside a `try/except` — test whether a class exists without
   having to guess it from the docs.
4. `Oil.docMe(obj)` — full introspection officially documented (types, hierarchy).
   **Works well on an isolated object** (just created, or cleanly read from the tree). Avoid
   calling it on an object you have just handled in a risky append/removeAt (see the
   instabilities section) — not confirmed as THE cause of a crash, but correlated once.
5. Oil `Map` (e.g. `TimelineCue.elementTracks`): no access by integer index (`map[0]` raises
   `TypeError`, it expects a key object) — iterate with `.items()` (returns ordinary Python
   key/value pairs).

## Golden rule: configure before adding, never after

The pattern that works reliably and reproducibly:

```python
obj = Oil.createObject("MyClass")
obj.property = value            # configure everything HERE
obj.subObject.property2 = ...
parent.collection.append(obj)   # append last of all
# NEVER touch `obj` again after the append
```

Two ways to break this, observed in practice:
- **Re-fetching after the append, then accessing a sub-property** (e.g. `parent.areas[0].placement`)
  → `RuntimeError: Access violation - no RTTI data!`, and a following attempt can outright
  crash Smode (HTTP connection forcibly closed). The "Owned" vector seems to transfer ownership
  of the object at append time — the original Python reference becomes invalid.
- **Configuring an object BEFORE the append, then reading it back afterwards** (e.g.
  `VideoOutput.label`, `.outputDevice.deviceName/.factory`): the configured values do NOT always
  stick — seen reverting to defaults (`"Video Output 1"` / `"Remote Video Output"`) after the
  append into `pipeline.outputs`. Confirmed on engine-linked objects (`engine.*`); not reproduced
  on scene objects (Compo/GeometryLayer/AffineCamera — those keep their configuration after the
  append). So this rule is solid for the scene tree, to be re-checked case by case on the
  `engine.*` side.

## A Compo without a target is never evaluated by the engine

General rule, independent of the Timeline/Link case where it was discovered (details and a
complete example in the [Timeline (TimelineCue)](#timeline-timelinecue) section): a `Compo`
embedded through a `TextureLayer` (`compoLayer.generator = compo`) whose
`TextureLayer.renderer.target` has **never been assigned to a rendering destination** (typically
a `ContentMap`, in `script.project.pipeline.contentMaps`) is **not evaluated by the engine** —
neither its visual rendering, nor its `Link`s, nor its internal "At Every Update" `Script`s,
**even if everything else is structurally correct**. What repeatedly looked like "object built by
script that does not activate" bugs (inert Links in particular) actually came from this. Reflex
for any script that builds a Compo meant for live behaviour (not only static):

```python
contentMaps = script.project.pipeline.contentMaps
if len(contentMaps) > 0:
    compoLayer.renderer.target.set(contentMaps[0])
```

Assigning the target at construction time (before adding content that must be live inside it,
same logic as the Timeline before/after-insertion rule) is enough; no additional manual action
is needed afterwards.

## The `.linked` trap

Every 2D size/resolution has a `.linked` flag (Boolean), **True by default**, which silently
forces `width == height` (or X == Y) as soon as only one of the two values is modified —
**no error**, just a wrong visual result. Always:

```python
obj.size.linked = False   # BEFORE
obj.size.width = 1000.0
obj.size.height = 200.0
```

Concerned: `Canvas2dSize` (placement/scale), `Size3d(PositiveMeters)` (3D geometry — **also has a
`.linked`, True by default**: on a `BoxGeometryGenerator`, `size.x = 1.0; size.y = 0.1;
size.z = 0.1` gives 0.1 / 0.1 / 0.1 without error, fixed by setting `size.linked = False` BEFORE;
fixing it afterwards on an already appended object works), `InheritableImageResolution`,
`ImageResolution`, `CheckerBoardTextureGenerator.size/.balance`.

Solid colour generator ("Uniform" layer in the UI): `UniformTextureGenerator` — `.color` is an
`HsvColor` (`.red`/`.green`/`.blue`/`.hue`/`.saturation`/`.value`/`.alpha`, each a `Percentage`
with `.get()`/`.set()`). To be assigned to `TextureLayer.generator` (not plain `"Uniform"`, that
name does not exist as an Oil class).

## Resolutions

Two different classes depending on the context:
- `InheritableImageResolution` (Compo.rasterizer, ContentArea.resolution, ContentMap.rasterizer/
  rootArea.resolution): has a `.preset` (enum `ImageResolutionPreset`, a wrapper class with
  `.get()`/`.set()`, NOT assignable with a direct `=` — `obj.preset = 40` raises
  `TypeError: invalid 'preset' variable type: expected ImageResolutionPreset, not <class 'int'>`)
  that starts at **41 = "Inherited"** — in this state, `.width`/`.height` are **completely
  ignored** (the UI shows "Inherited" even if width/height were explicitly set), the resolution
  comes from the parent. You need `.preset.set(40)` ("Custom...") BEFORE setting width/height.
  If the custom values match a named preset exactly (e.g. 1280x720 = "HD 720"), `.preset`
  automatically shows that name again — cosmetic only, the values stay correct.
- `ImageResolution` (NDI device, etc.): no "Inherited" notion, direct `.width`/`.height`
  (with `.linked` all the same).

Classic trap: setting the resolution of an internal generator (e.g. `GradientTextureGenerator.
resolution`) thinking it changes the size of the Compo shown on screen — it does not, it only
drives the internal sampling of THAT generator. The real size always comes from
`Compo.rasterizer.resolution`.

## Polymorphic pointers (OwnedPointer)

Some properties are `OwnedPointer(BaseClass)` — null/not instantiated until a concrete object is
explicitly assigned to them:
- `GeometryLayer.generator` (`OwnedPointer(GeometryGenerator)`), `.renderer`
  (`OwnedPointer(GeometryRenderer)`)
- `AffineCamera.placement`, `ContentArea.placement` (`OwnedPointer(Placement2d/3d)`)

```python
cube.generator = Oil.createObject("BoxGeometryGenerator")   # direct assignment, not .set()
cube.renderer = Oil.createObject("SurfaceGeometryRenderer")
```

`VideoOutput.outputDevice` is NOT an owned pointer to a concrete device but a
`VideoOutputDeviceSelector` (fields `deviceName`/`factory`/`hostName`/`preferredAddress`) — a
selector by name, not a direct instance.

## Enums: never guess the index

The same property name can reference **different** enums depending on the owning class. Always
check `prop.getOilClassName()` before setting an index. Confirmed values:

| Enum | Known values |
|---|---|
| `BlendingMode` (effects/renderer) | 10=screen, 12=linearDodge, 0=passThrough... |
| `TextureMaskBlendingMode` (masks) | 0=add, 1=remove, 2=multiply, 3=replace |
| `PixelateMode` | 0=downscaleFactor, 1=numPixelsWidth, 2=numPixelsHeight (`.value` remains a plain `Real` whatever the mode — set `.mode` BEFORE `.value`) |
| `NoiseFunctionShapeType` | 0=simplexNoise (default), 1=perlinNoise |
| `CuePlayParameters.launchMode` | 0=manual, 1=restartWithActivation, 2=restartWithIntensity, 3=playWithIntensity |
| `PythonScriptLaunchMode` | 0=manual, 1=atPreload, 2=atActivation, 3=atParameterChange, 4=atEveryUpdate, 5=atDeactivation, 6=atUnload |
| `FunctionWrapMode` | 0=clamp, 1=repeat, 2=mirroredRepeat |

`Oil.CustomEnumeration(("a","b"), 0)`, officially documented, **does not work**
(`AttributeError`). Fix: declare `x: Oil.createObject("CustomEnumeration")` empty, populate it in
the script body with `CustomEnumerator`s (`.label`=text, `.value`=int) through
`.enumerators.append(...)`, guarded by `if len(script.x.enumerators) == 0`. **R15 (07/10/2026):
the attribute is called `enumerators` (`OwnedVector(CustomEnumerator)`); the old names
`elements` / `CustomEnumerationElement` no longer exist** (`AttributeError` / `unknown Oil type
name`). `.set()/.get()` use the label (string), unlike native enums which use an integer.
Simpler alternative if a plain boolean is enough: `Oil.Boolean` avoids this whole bug.

`Placement3dTargetAxis` enum (`placement.target.axis`, readable through `.toString()`): 0 = xPos,
1 = xNeg, 2 = zPos (default), 3 = zNeg; 4 and 5 are not valid (values tested on a throwaway
object not added to the scene).

## Project tree map

```
script.project
├── masterScene.layers[]           # main scene, layers (TextureLayer, GeometryLayer...)
├── pipeline
│   ├── contentMaps[]              # ContentMap (screen/zone mapping) — NOT a TextureGenerator,
│   │                               # does not fit into a TextureLayer.generator
│   ├── outputs[]                  # VideoOutput (OwnedVector(VideoOutput)), links a pipeline
│   │                               # source to an outputDevice through VideoOutputDeviceSelector
│   ├── channels[]                 # OwnedVector(ChannelV9), abstract, subclasses not identified
│   └── virtualScreens[]
└── topology

Compo                                # no .masterScene: the layers are direct
├── layers[]                         # OwnedVector(Layer), like masterScene.layers
├── rasterizer.resolution            # InheritableImageResolution (Custom/Inherited trap)
└── mainAnimation                    # MainAnimationOwnedPointer, e.g. TimelineCue

engine                              # system level, NOT project (shared between open projects)
├── configuration.timing.requestedFrameRate  # VideoTimeBase (.p/.q) — global frame rate
├── devices.devices[]               # OwnedVector(Device) — detected hardware (storage, capture,
│                                    # audio...) + `deviceConfigurationDirty` (Trigger) to force
│                                    # a rescan. WARNING: an object added manually here
│                                    # disappears after a trig() of deviceConfigurationDirty
│                                    # (rebuilt from the real source of truth, not from our
│                                    # ad-hoc additions)
└── configuration
    ├── videoOutputs[]              # VideoOutputDeviceConfiguration — NOT confirmed as the real
    │                                # binding of the Preferences > Engine > Video Outputs panel
    │                                # (tested empty while a row existed on screen: real
    │                                # location still NOT found, to be investigated)
    ├── graphicsWindows[]           # window/display config, not the video outputs
    └── configurations              # NamedObjectMap, config presets (not explored in detail)
```

**Displaying a Compo in a ContentMap**: NOT through `ContentMap.currentCamera` (false lead — this
`WeakPointer(CameraV9)` does exist but is not the standard display mechanism; leave it
`.reset()`/empty). The real mechanism, visible in the UI layers panel as a "target" column (which
replaces the "Normal" blend mode for top-level layers): the **renderer** of the TextureLayer that
wraps the Compo has a `target` property (`SceneTargetWeakPointer`) to point to the `ContentMap`
(directly, no need for `.rootArea` here — unlike `VideoOutput.source`):
```python
compoLayer = Oil.createObject("TextureLayer")
compoLayer.generator = compo          # the Compo to display
parentScene.layers.append(compoLayer) # default renderer = SingleTextureRenderer

compoLayer.renderer.target.set(cm)    # cm = the ContentMap (already appended in pipeline.contentMaps)
```
A layer with an unresolved `target` is shown in red with `<Missing Target>` in the UI — a reliable
symptom to spot a layer that is supposed to feed a ContentMap but is wired wrongly.

**MAJOR LIMIT CONFIRMED (2026-07-10)**: `renderer.target.set(cm)` through the bridge UPDATES the
value (immediate read-back through `.get()` confirms the right pointer, no error), **but does NOT
trigger the actual rendering**. Tested on 3 different ContentMaps (2 created by script, 1 created
entirely by hand in the UI by Guillaume): in all 3 cases, `set()` through a script leaves the
ContentMap preview black/empty, whereas **manually re-selecting the SAME value in the UI dropdown
makes the rendering appear immediately**. Unlike the "Disconnected" Links bug (fixable by
closing/reopening the project), **closing/reopening the project does NOT fix this one** —
confirmed in real conditions. Conclusion: `.set()` on a `SceneTargetWeakPointer` changes the data
but does not trigger the internal notification that activates the rendering pipeline; only a
direct UI interaction (re-selection in the dropdown) seems to do it. Current workaround: the
script can prepare/wire the value (useful for bulk wiring), but a manual pass in the UI is still
needed to really activate each target. No alternative method found so far (no triggering
`.trig()`/`.refresh()` identified on `ContentMap`, `TextureLayer`, or `SingleTextureRenderer`).

**Linking a ContentMap to a VideoOutput**: `VideoOutput.source` is a `PipelineSourceWeakPointer`
that refuses a `ContentMap` directly (Smode error, UI popup:
`"Wrong target type for pipeline source pointer: it should point to either a Content Area or a
Video Rasterizer"` — not raised as an exception on the bridge side, only visible in the UI). It
must point to its `ContentArea` (`cm.rootArea`, not `cm`):
```python
outputVideo.source.set(cm.rootArea)   # not outputVideo.source.set(cm)
```

**ContentMap / zones** (`pipeline.contentMaps`):
```python
cm = Oil.createObject("ContentMap")
cm.rasterizer.resolution.preset.set(40)   # 40=Custom, otherwise stays on Inherited (41) and ignores width/height
cm.rasterizer.resolution.linked = False
cm.rasterizer.resolution.width = 3000
cm.rasterizer.resolution.height = 200
cm.rootArea.resolution.preset.set(40)
cm.rootArea.resolution.linked = False
cm.rootArea.resolution.width = 3000
cm.rootArea.resolution.height = 200

zone = Oil.createObject("ContentArea")
# resolution NOT touched: stays on the default Inherited (preset=41) -- see the note below,
# it is the SCALE that defines the final size of a sub-zone, not the resolution
zone.placement.scale.size.linked = False
zone.placement.scale.size.width = 0.5    # fraction of the parent (50% of rootArea's width)
zone.placement.scale.size.height = 1.0   # 100% of the height
zone.placement.position.x = 0.25         # centre of the zone, 0-1 fraction of the parent
zone.placement.position.y = 0.5
cm.rootArea.areas.append(zone)    # configure BEFORE, append last — never touch again afterwards

script.project.pipeline.contentMaps.append(cm)
```

**Resolution vs Scale on a sub-`ContentArea`**: unlike the `rootArea`/`rasterizer` of the
`ContentMap` itself (where `.resolution.preset` MUST go to 40=Custom for an explicit pixel size,
see above), a **sub-zone** (`ContentArea` added to `.areas`) must stay on the default
`.resolution.preset` (**41 = Inherited**) — do not touch it. The final pixel size of the sub-zone
is determined by **`.placement.scale.size`** (fraction of the parent, e.g. `0.5` = 50% of the
parent's width): the `resolution.width` shown in the UI for an Inherited zone is only an
EXTRACTED/computed value (parent × scale), not a value to set yourself. Confirmed by inspecting a
`ContentArea` created manually in the UI by Guillaume: `resolution.preset=41`, `scale.width=0.5`,
`scale.height=1.0`.

**Units of `Canvas2dPosition`/`Canvas2dSize`**: normalised fractions 0.0–1.0 (NOT pixels),
confirmed by reading the defaults of a fresh `ContentArea` (`position=(0.5, 0.5)`,
`anchor=(0.5, 0.5)`, `scale.size=(1.0, 1.0)` = 100%). `position` represents where the anchor
point (`anchor`) is placed INSIDE the 0–1 frame of the parent — with the default anchor at the
centre (0.5,0.5), `position=(0.5, 0.5)` = a centred zone filling the whole parent. To lay N
equal-width zones side by side, set `scale.width = 1.0/N` (scale, not resolution) and compute the
centre of each zone as a fraction of the parent: `position.x = (i + 0.5) / N`. Classic mistake:
passing "pixel-style" values (e.g. `960.0` instead of `0.75`) → accepted without error but
interpreted as a huge fraction (`960.0` becomes `96000%` in the UI), zone out of frame.

Side trap: modifying `.placement.scale`/`.position`/`.resolution` on an already **appended**
`ContentArea` (re-fetched afterwards) falls back into the crash-prone pattern documented above —
in case of a wrong value after the append, prefer `areas.clear()` + recreating the zones cleanly
rather than fixing the existing objects in place.

## 3D geometry: GeometryLayer, placement, angles (confirmed R15, 06/10/2026)

- **Python angles are in RADIANS** (`placement.orientation.z = math.radians(90)`), not degrees.
  Silent trap: writing `77.5` gives 77.5 rad modulo 2π (≈123°), without error. Verified by
  reading back `layer.worldMatrix` (`m.x.x.get()`, `m.x.y.get()` = world X axis, `m.w.x/.y/.z` =
  position).
- `GeometryLayer`: `generator` (`OwnedPointer(GeometryV9Generator)`: `BoxGeometryGenerator`
  `.size`, `SphereGeometryGenerator` `.radius`, `CylinderGeometryGenerator`), `renderer`
  (`SurfaceGeometryRenderer`), `placement` (`PositionOrientationSize3dPlacement`, already
  instantiated): `anchor` (x/y/z Meters), `position` (x/y/z Meters), `orientation` (`EulerAngles`:
  x/y/z Angle + `order` + `axisAngle`), `target` (`Placement3dTarget`: `axis`, `targetObject`,
  `upVector` = native look-at), `size` (`Size3d(Real)`). No parent/child hierarchy between
  `GeometryLayer`s (no `.layers`); `GroupLayer` only has a `Placement2d`.
- **No IK / Bone / Skeleton / Constraint class in Smode** (`createObject` fails; the keywords only
  exist in the FBX / Assimp / NatNet importers). IK has to be computed by hand.
- **Writing a placement from an "At Every Update" Script works** (≈1900 executions without error,
  reading/writing `layer.placement.position.x = v` on layers already appended, no crash). In a
  `PythonScriptTool` placed in `compo.tools`, `script.parentElement` is the **Compo** (`.layers`),
  not the scene. Find the layers by label:
  `{str(l.label.get()): l for l in (comp.layers[i] for i in range(len(comp.layers)))}`.
- The open project is `script.project` (`.masterScene`, `.pipeline`); `engine.content.
  customContent` is always empty, do not look for the project there.
- Complete example (N-bone IK/FK rig, handles, banks): see the
  [smode-ik-rig](https://github.com/gyomh/smode-ik-rig) repository.
- `PlaneGeometryGenerator`: `size.width/height` (`Size2d`, not `.x/.y`), `anchor`
  (`Canvas2dPosition`, 0.5 = centre); **the plane is born lying in the XZ plane (normal = local
  Y)**: to stand it up facing +Z, rotation `orientation.x = -π/2` (columns
  `[[1,0,0],[0,0,1],[0,-1,0]]`).
- `CircleGeometryGenerator` = **outline only**: rendered as a surface → UI error "Surface No
  Triangles information in geometry"; render it with `ThickLinesGeometryRenderer` (`map` =
  `UniformTextureGenerator` whose `.color` sets the line colour; `thickness` in px).
  `SphereGeometryGenerator.precision` = `Precision2d` (`.uniform = False` before setting `.x/.y`).
  `CapsuleGeometryGenerator`: Y axis, pivot at the base.
- `NullLayer`: **invisible and not selectable in the viewport** (only in the tree); for a
  clickable handle, use real geometry (a plane).
- `Group3dLayer`: `worldMatrix` readable (columns `m.x/.y/.z/.w`, equals 0 before the first
  evaluation); a layer outside the group does not follow its transformation unless the script
  applies it.
- World matrix: `layer.worldMatrix` → `m.x.x.get()`...; rotation = normalised columns.

## 3D lights (R15, 07/10/2026)

- Classes instantiable with `Oil.createObject` and added **directly to `layers`** (no
  `LightLayer` / wrapper): `SpotLight`, `PointLight`, `DirectionalLight`, `AmbientLight`.
  `AreaLight` is abstract (`cannot instantiate abstract class`).
- Common attributes: `intensity` (`Percentage`), `diffuse` (`LightComponentParameters`: `.color`
  `HsvColor`, `.level`, `.enable`), `specular` (`.color`, `.level`, `.shininess`, `.enable`),
  `placement` (`PositionOrientationSize3dPlacement`, like a `GeometryLayer`), `visibilityScope`
  (`LightVisibilityScope`, default 0 = `compoAndSubCompos`: **a light inside a `Group3dLayer`
  lights the whole compo**, not only the group), `volumetric`, `activation`.
- Specific ones: `SpotLight` (`attenuation`, `radialAttenuation` = `FalloffFunction(PositiveAngle)`
  with `.interval` / `.exponent`, `color`, `backgroundColor`), `PointLight` (`radius`,
  `attenuation`, `areaNoise`, `areaNumSamples`, `directionalMap`), `DirectionalLight`
  (`shadowParameters`). `AmbientLight` only has the common attributes.
- **Aiming at a point**: `light.placement.target.targetObject.set(layer)` (`WeakPointer(Layer)`, a
  `NullLayer` works) + `placement.target.axis` (enum, see "Enums"). **A Spot emits towards its
  local -Z** whereas the default `axis = zPos (2)` aligns +Z towards the target: without
  `axis.set(3)` (zNeg) the light shines the opposite way. Check by script: with zNeg, the `z`
  column of `worldMatrix` has a positive dot product with the light position (it points away from
  the target). Spherical position around the target: `x = d·cos(el)·sin(az)`, `y = d·sin(el)`,
  `z = d·cos(el)·cos(az)` (azimuth 0 = +Z side, +90° = +X).
- Intensity / colour / activation can be modified after the `append` without trouble (in-place
  update of an existing rig from a Script). Complete example: the
  [smode-light-setup](https://github.com/gyomh/smode-light-setup) repository.

## Lock and activation (ActivationState)

- `layer.editable` (the layer padlock: not selectable in the viewport), `layer.activation` (the
  eye: inactive = out of the rendering) and `solo` are **`ActivationState`**s.
- **`.set()` takes a BOOLEAN** (`True` = active / editable, `False` = inactive / locked). Passing
  an integer is read as "true" and changes nothing (silent). `.get()` returns 0 (active) or 2
  (inactive); `.toString()` gives `'active'` / `'inactive'`.
- **Do not**: `Oil.createObject('ActivationState')` nor `dir()` on one of these variables →
  complete Smode crash (observed). Reading/writing the value of an existing object is safe.
- A `MaterialBank`, a `ParameterBank` and a text layer are locked the same way
  (`obj.editable.set(False)`), before or after the `append`.

## Shared materials, references, depth (R15)

- `Group3dLayer.tools` accepts a `MaterialBank` (`Oil.createObject('MaterialBank')`) whose
  `.materials` is an `OwnedVector(GeometryLayerUser)`: you put a `SurfaceGeometryRenderer` in it
  (the material, `label` = its name). Useful settings: `side` (0 front, 1 back, 2 both),
  `autoIlluminate`, `depthBuffer.test` / `.write`, `components[0]` = `DiffuseSurfaceComponent`
  (`map` = any `TextureGenerator`, including a 1024² `Compo` with a transparent background holding
  a `ShapeLayer` → vector icon; `masks` = `GeometryMask`). A new `SurfaceGeometryRenderer` has 2
  components (Diffuse + Specular).
- **Referencing a material from a layer** (`layer.renderer = ...`):
  ```python
  r = Oil.createObject('ReferenceGeometryLayerUser')
  ad = r.referencer.address
  ad.directPointer.set(material)      # the material object read from bank.materials[j]
  ad.location.set(1)                  # 1 = direct pointer; the default value 0 gives
                                      # "Unspecified reference" and the layer disappears
  layer.renderer = r
  ```
  `ad.target.get()` is only non-None when the reference is resolved. **A reference keeps a cached
  state**: after modifying the material (e.g. `depthBuffer.test`), do
  `layer.renderer.referencer.reloadInstance.trig()` on every layer that references it, or recreate
  the reference. A reference set from outside the group that contains the bank can report
  "No direct pointer".
- A plane **rotated to face the camera cuts the other planes**: the depth test hides the half that
  passes behind ("L-cut" handle). For an always-visible handle: material with
  `depthBuffer.test = False` + `reloadInstance` on the references.
- `SphereGeometryMask` (in `components[0].masks`) made the plane invisible in our tests; the
  reliable way to draw a circle/icon on a plane is a texture with alpha (Compo + ShapeLayer).
- Creating a material by script (no UI call): see `make_icon_material` in the
  [smode-ik-rig](https://github.com/gyomh/smode-ik-rig) scripts (`GroupShapeGenerator.shapes` ←
  `LineShapeGenerator` with `segment.begin/end` in 0-1 coordinates; `DefaultShapeRenderer`:
  `fill.enabled`, `stroke.enabled/.color/.thickness` in pixels of the texture).

## Compo camera (R15)

- `compo.currentCamera.get()` (the current camera, the one from the elements list) can be
  **different** from `compo.defaultCamera` (the internal camera of a fresh Compo). Read
  `currentCamera` first.
- `TargetOrientationDistance3dPlacement` placement ("orbital" camera): `target` (`Position3d`),
  `orientation` (`EulerAngles`, order 0), `distance`; **no `position`** (AttributeError).
  `FieldOfViewPerspectiveFrustum` frustum: `horizontal` / `vertical` in radians.
- World rotation of the camera = `Rz·Ry·Rx(orientation)` (no transpose), position =
  `target + R·(0,0,distance)`. Verified by projecting known points (perspective, 60° FOV) and
  comparing with the pixels of a capture: 4.7 px RMS against 36 px for the following convention.
  A billboard plane = `R_cam · Rx(-90°)`.

## Text (TextLayer)

- `TextLayer` = `generator` `LocalTextGenerator` (`text` MultiLineString `.set('...')`, accents OK;
  `style.size`, `style.foreground` `HsvColor` in 0-1, **`style.background` = `Option(HsvColor)`:
  `.enabled` + `.value` (alpha = opacity of the background)**) + `renderer` `DefaultTextRenderer`:
  `placement.position` (0-1 fractions of the compo), `size.width.type` (0 auto, **1 wordWrap**,
  2 shrinkToFit) + `size.width.size` (px), `size.height.type` (0 auto), `style.alignment` (0
  middleCenter, 1 middleLeft, 2 middleRight, 3 topCenter, 4 topLeft). Compo resolution:
  `compo.rasterizer.resolution.width.get()`.
- To keep a warning text out of the rendering: `layer.activation.set(False)` and an empty text
  when there is nothing to say.

## Parameter banks linked to a Script (R15)

- A `Parameter(Boolean)` / `Parameter(Angle)` / ... (`Oil.createObject('Parameter(Angle)')`)
  carries `label`, `value`, `expose`, `modifiers` and **`targets`: `OwnedVector(LinkTarget)`** — no
  need for a `LinkBank`: `lt = Oil.createObject('ParameterLinkTarget');
  lt.target.set(script.myVariable); p.targets.append(lt); bank.parameters.append(p)`. Initial
  value of the Parameter = current value of the variable. The Parameter takes the colour of its
  bank (`colorLabel`). See also the "Self-installing Scripts" section: the linked Parameter pushes
  its own value back onto the script.
- The `colorLabel` of any element: `c = o.colorLabel; c.red.set(r/255)` (values 0-1, `SrgbColor`).

## Checking visually (outside the API)

The rendering cannot be read by script. Technique that works: PowerShell, `GetWindowRect` of the
Smode process + `Graphics.CopyFromScreen` on that rectangle only (never the whole screen), then
reading the PNG. Crop on the viewport to read an icon; the status bar at the bottom of the window
gives the rendering errors ("No direct pointer", "Unspecified reference", "No Triangles...").
Beware: if the Smode window sits on another screen with other windows over it, the capture will
include them.

## Nested Scene (nested Scene layer)

`Scene` is an Oil class in its own right (confirmed `getOilClassName() == "Scene"`), not just the
informal name of `masterScene`. A layer of `masterScene.layers` (or of `Scene.layers`, recursive)
can be directly of class `Scene` (not only `TextureLayer`/`GeometryLayer`) — it then has its own
`layers[]`, `mainAnimation` (`OwnedPointer`, like `Compo.mainAnimation`) and `tools`
(`OwnedVector(Tool)`, like `compo.tools`). This is exactly what the UI shows as "Scene" with its
children "Main Timeline" / "Parameters" / "Animations" / "Links" / (layers).

A freshly created `Scene` (`Oil.createObject("Scene")`) is completely empty: `mainAnimation=None`,
`tools` and `layers` of size 0 — nothing is created by default, everything has to be built by hand.

The 3 banks visible in the UI under a Scene/Compo are 3 different Oil classes, not just labels of
the same `ParameterBank`: `ParameterBank` ("Parameters"), `AnimationBank` ("Animations"),
`LinkBank` ("Links") — all added through `.tools.append(...)`. Their `.label` stays an empty
string even in normal use (the name shown in the UI comes from the type, not from `.label`).

Complete verified pattern (golden rule: configure everything before the last append):
```python
scene = Oil.createObject("Scene")
scene.label = "Scene"

tc = Oil.createObject("TimelineCue")
scene.mainAnimation = tc                       # OwnedPointer, direct assignment like Compo

scene.tools.append(Oil.createObject("ParameterBank"))
scene.tools.append(Oil.createObject("AnimationBank"))
scene.tools.append(Oil.createObject("LinkBank"))

compo = Oil.createObject("Compo")
compoLayer = Oil.createObject("TextureLayer")
compoLayer.generator = compo
compoLayer.label = "Compo"
scene.layers.append(compoLayer)

script.project.masterScene.layers.append(scene)   # last append
```
`label` (on `Scene`/`TextureLayer`, wrapped as `_cppSmodeOil.String`) accepts direct assignment
`obj.label = "text"` as well as `.set()`/`.get()` — both work, unlike enums which require `.set()`.
(Ready-made Script: [smode-new-scene](https://github.com/gyomh/smode-new-scene).)

## Parameters / Links / Cues system

- `ParameterBank` (in `compo.tools`) + `Parameter(Type)` (e.g. `Parameter(Angle)`,
  `Parameter(SpeedFactor)`, `Parameter(Boolean)`) expose controls in the Smode UI.
- Linking a parameter to a target property: create a `ParameterLinkTarget`, `.target.set(var)`,
  then `sourceWithTargets.targets.append(lt)`.
- `FunctionCue(Type)` (e.g. `Angle`) + `ParametricScalarFunction({input=Seconds, output=Angle})`
  + a `shape` (`LinearRampFunctionShape`, `NoiseFunctionShape`...) for looping animations.
  **Always set explicitly** `minimum`/`maximum`/`period`/`wrapMode`/`phase`/`offset`/
  `repetitions` — the silent defaults (often `maximum=minimum=0`) give a flat output without any
  error.
- For targets with different output ranges from a single source: do not link directly (same raw
  value everywhere) — give each `ParameterLinkTarget.modifiers` its own
  `FunctionLinkModifier({input=Percentage, output=Percentage})` with a `KeyframeFunction`
  (2 `Keyframe`s minimum, default interpolators = `StepKeyframeInterpolator` → explicitly force
  `LinearKeyframeInterpolator` on `.inputInterpolator`/`.outputInterpolator`).
- **Mirroring a live field into another (e.g. `TimelineCue.transport.position` → `Text` of a
  `LocalTextGenerator`, for a timecode display)**: the right method is **"Expose As..."** (UI
  right-click on the source field) then drag the result onto the target field — Smode creates a
  `Link` in a `LinkBank` (in `compo.tools`) with `.source` = `ParameterLinkSource` (`.target` =
  WeakPointer to the SOURCE field, e.g. `transport.position`; `.modifiers` holds a
  `ToStringLinkModifier` that converts `Seconds` → text formatted as `H:MM:SS:FF` timecode) and
  `.targets` = a `ParameterLinkTarget` (`.target` = WeakPointer to the DESTINATION field, e.g.
  `textGenerator.text`; `.modifiers` empty).
  **Rebuilding this structure by script seemed not to work** on the first try, even when
  faithfully reproducing the complete structure (`Oil.createObject("Link")` +
  `ParameterLinkSource`/`ParameterLinkTarget` + `ToStringLinkModifier` on the source's
  `.modifiers` + `.target.set(prop)` on both ends + `linkBank.links.append()`): the `Link` is
  created without error, structure identical in introspection (classes, resolved targets,
  modifier present) to a native Link, but stayed frozen on its placeholder value.
  **Root cause found: it is not the Link, it is the absence of a `target` on the Compo.** A
  `Compo` embedded through a `TextureLayer` (`compoLayer.generator = compo`) without
  `compoLayer.renderer.target` pointing to a `ContentMap` (or another rendering destination) is
  **never evaluated by the engine** — neither its rendering, nor its `Link`s, nor anything else
  inside, native or script-created. As soon as a target is assigned
  (`compoLayer.renderer.target.set(contentMap)`, with `contentMap` taken from
  `script.project.pipeline.contentMaps`), a scripted `Link` identical to the one described above
  updates continuously **without any manual action**, from its creation — confirmed in active
  reading (`text` following `transport.position` frame by frame). Toggling `link.activation`
  (tried before finding the real cause) gave at best a one-off frozen evaluation — lead
  abandoned, useless once the real problem (missing target) was identified.
  **General rule, not specific to Links**: any Compo built by script and meant for "live"
  behaviour (Links, internal Scripts, animations) must receive a target at construction time,
  otherwise nothing animates inside it, even if everything is structurally correct. Note: this
  does not cancel the limit documented above on `renderer.target.set()` not necessarily
  reactivating the DISPLAY of a ContentMap already used elsewhere (a distinct bug) — here we are
  talking about the evaluation/execution of the Compo's own content, which does work as soon as
  the target is assigned, without any additional manual step.

## Timeline (TimelineCue)

- `Compo.mainAnimation` (`MainAnimationOwnedPointer`) accepts an `Oil.createObject("TimelineCue")`
  — direct assignment (`compo.mainAnimation = tc`), not `.set()` (usual OwnedPointer rule).
- `TimelineCue.createBlock(element)` → `(ElementTrack, ElementTrackBlock)`: creates the track AND
  the block for a given layer in one go, positioned at the cursor. Then reposition by hand:
  `block.autoLength.set(False)` then `block.position.set(seconds)` / `block.length.set(
  seconds)` (both in `Seconds`, not frames — convert through the frame rate, see below).
- Underlying structure (visible in clear text in a saved `.compo`/`.project`):
  `TimelineCue.elementTracks` = `Map({key = WeakPointer(Element), value = ElementTrack})`,
  `ElementTrack.blocks` = `OwnedVector(ElementTrackBlock)`.
- Walking the clips: `for element, track in timeline.elementTracks.items()`; `element.get()` gives
  the layer, `track.blocks[0]` the first block (`.position` / `.length` in seconds).
  `elt.isChildOf(layer)` is **true for the layer itself too** (`elt == layer` works as well). For a
  Scene, the owner of the timeline is the layer (`scene.layers` + `scene.mainAnimation`); for a
  Compo layer, it is `layer.generator`. Every created timeline is called "Main Timeline" (cannot
  be renamed).
- **Display bug linked to the construction order** → see "Known UI bugs": building the whole
  timeline (`createBlock` + settings) BEFORE the `Compo` is inserted in the document tree breaks
  the sync of the Timeline panel (invisible layers, playback still correct). Always insert the
  `Compo` into the scene first, build the `TimelineCue` afterwards.
- Global frame rate of the project, to convert frames → seconds:
  `engine.configuration.timing.requestedFrameRate` (`VideoTimeBase` with `.p`/`.q`, e.g. 60/1 =
  60fps). No framerate property on `Compo`/`Pipeline` — it is an engine setting, shared between
  open projects.
- **Parameter animation (R15)**: animating a position with keys creates, in the main timeline
  (`project.masterScene.mainAnimation`, not `compo.mainAnimation`), an entry of
  `TimelineCue.parameterTracks` = `Map(ObjectWeakPointer → ParameterTrack(Seconds, Meters))`; the
  track has `targetParameter` and `function` = `KeyframeFunction` (`.keyframes`, `len()`, time in
  `.input`). One track per axis (`x`, `y`) of each `Placement`. Playback by script:
  `ma.transport.position.set(t)`, `ma.transport.play.trig()` / `pause.trig()`,
  `ma.transport.playing.get()`.
- **Two writers on the same value**: the timeline **rewrites every frame** the parameters it
  animates, including the value held after the last key. An "At Every Update" Script that also
  writes these parameters conflicts; if it compares "position read" with "position I wrote" to
  detect a manual manipulation, it takes the timeline's rewrite for a drag (symptom: animation
  that skips 1 frame out of 2 after the last key). Remedy: only conclude to a manual action if
  the value read changes **also compared to the previous frame** (the timeline rewrites
  identically, a drag changes every frame), or do not write to animated parameters.
- Frame-by-frame diagnosis: make the Script write one line per execution into a file
  (`open(path, 'a')`), play the timeline by script, then analyse the file (bridge calls are not
  synchronous with the frames).

## Modifiers, generators and masks (overview)

Usage findings (R13-R15), classes seen while building scripts:
- **Post-processing effects of a Compo** (`PixelateTextureModifier`, `FeedbackTextureModifier`...):
  are added to `compo.modifiers` (Compo level), not to `renderer.effects`. A sibling layer placed
  outside the Compo does not receive these effects.
- **Gradient mask**: an inner Compo containing a shape serves as `TextureLayerTextureMask.generator`
  on a `MaskTextureModifier` applied to a `GradientTextureGenerator`; multicolour gradient through
  `QuadritoneColorFunction` (4 colours + 2 intermediate positions).
- **Point-by-point shape**: `PathShapeGenerator.path.points`, each `Path2dControlPoint` has
  `position.x/.y`. Three points at the same X (fixed bottom / oscillating / fixed bottom) give bars
  with flat transitions; alternating fixed/oscillating gives rounded peaks. A point can be the
  target (`ParameterLinkTarget.target.set(cp.position.y)`) of an audio Link.
- **Proportionality**: `ParameterLinkSource` + `MultiplyLinkModifier` (factor per target) links a
  single `Parameter` to N targets at different scales (see also `FunctionLinkModifier` above).
- `TestPatternTextureGenerator`: each component (`grid`, `horizontalBar`, `verticalBar`,
  `diagonals`, `corners`, `cornerCircles`, `centeredCircles`, `edges`, `logo`,
  `coloredCheckerBoard`, `resolutionText`, `tileLabels`, `labelText`; `labelText` and `tileLabels`
  are two distinct components) has its `.enabled`, all active by default depending on the preset:
  to show only one, explicitly disable all the others. The generator also has its own
  `.background` (colour with alpha).
- `UpscaleTextureModifier` (native): `algorithm` 0 = SimpleUpscale, 1 = SuperRes (2 and more
  invalid), `upscaleFactor`, `outputResolution`, `enhence` (sharpness), `intensity`, `strong`,
  `withoutMaxine`. In SimpleUpscale it is **not** AI (nor Maxine): a plain enlargement plus a
  little sharpening, almost no performance cost.
- `StreamDiffusionTextureModifier` (SmodeTech StreamDiffusion-R15 package): `mode` and
  `acceleration` (enum `StreamDiffusionAcceleration`: 0 = none, 1 = torchCompile, 2 = tensorRT)
  are **locked in the UI** as soon as the process is connected, but remain modifiable through
  `.set()` by script and trigger a pipeline reload (`isStreamRecreating = 1`). `modelName` accepts
  a Hugging Face identifier absent from the presets (e.g. `IDKiro/sdxs-512-0.9`). A crashed Python
  process does not restart (`execute.trig()`, `activation` toggle, `resetEvent`: no effect): the
  modifier has to be deleted and recreated. Find it by **name** (recursive search) because its
  index moves when other modifiers are added. Ready-made Script:
  [smode-streamdiff-ctrl](https://github.com/gyomh/smode-streamdiff-ctrl).

## Audio reactive

`AudioSpectrumLinkSource` — native class to continuously inject the intensity of a frequency band
into any parameter through a Link.
- `.extractor` (`AudioSpectrumExtractor`): `.audioChannel` (`WeakPointer(AudioDeviceChannel)`,
  `.set(channelObj)`), `.frequencyInterval`/`.amplitudeInterval` (`Interval(Percentage)` with
  `.begin`/`.end`/`.center`/`.size`).
- Audio devices: `engine.devices.devices`, each `JuceAudioDevice` has `.inputChannels`
  (e.g. "Left"/"Right" in DirectSound, 8 named channels in ASIO Voicemeeter).
  Examples: [smode-vizualiser](https://github.com/gyomh/smode-vizualiser),
  [smode-oscilloscope](https://github.com/gyomh/smode-oscilloscope).

## Scripts created programmatically (PythonScriptTool)

**Script engine.** Embedded Python = full CPython 3.12 (`python312.dll` + `python\` folder, whole
stdlib: `http.server`, `socketserver`, `threading`, `json`), in R13 as in R15, a single
interpreter. It is the **only family of script** (no Lua nor JavaScript: the analysis of
`Plugins/*.dll` only shows `Python.dll`, `PythonScriptTool`, `PythonEngineComponent`,
`PythonFileScriptToolConverter`; the other "code" plugins are third-party integrations like
Notch, Substance, TouchDesigner). Consequence: an external syntax checker in Python 3.11 rejects
nested f-strings that Smode accepts (3.12). `Oil` is already injected in a Script's context:
`import Oil` is useless. `site-packages/Smode/` (`Oil.py`, `SmodeSDK.py`, `Sys.py`) wraps
extensions compiled into `Smode.exe`: no `import Smode` from an external interpreter. The
official docs (doc.smode.io, Python scripting section) state that the API is not published.

Confirmed reliable:
```python
tool = Oil.createObject("PythonScriptTool")
tool.script.sourceCode.set(codeString)
tool.launchMode.set(4)   # atEveryUpdate
```
Debug: `.script.numExecutions.get()` (counter, running or not), `.script.lastExecuteResult.
status.state/.message` (error), `.script.lastExecuteResult.printed` (stdout of the last run).
`tool.script.parentElement` points to its DIRECT container, not the root scene — a trap if you
assume the same structure as the MCP bridge script itself.

**Declared parameters (`name: Oil.Type(...)`) — CORRECTED R15 (06/10/2026)**: the previous
version of this reference claimed they could not be introspected from the outside
(`.dynamicVariables` empty). That is false **once the script is compiled** (`tool.execute.trig()`
after `sourceCode.set`): `tool.dynamicVariables` lists the parameters **in declaration order**
and each one is readable AND modifiable: `dv[i].get()`, `dv[i].set(v)`, `dv[i].getFriendlyName()`
(displayed label), `WeakPointer` slots (`dv[i].set(layer)`), vectors (`dv[0][k].set(layer)`),
Boolean buttons (`.set(True)`). Wiring slots by script is therefore possible. Values and links
(Parameter bank → parameter) **survive a recompilation** as long as the variable name does not
change; renaming a variable destroys the old parameter (new object, default value).
- Displayed label = variable name: camelCase split into words, **space inserted before a digit**
  (`bone3Rotation` → "Bone 3Rotation", `boneRotation3` → "Bone Rotation 3", `BONE3Rotation` →
  unchanged). Impossible to get "Bone3 Rotation" or a dynamic number on the Script side; the
  label of a bank `Parameter`, on the other hand, is free (`p.label = ...`).
- Types seen: `Oil.Boolean`, `Oil.Meters`, `Oil.PositiveMeters`, `Oil.PositiveInteger`,
  `Oil.String`, `Oil.createObject("Angle")`, `Oil.createObject("WeakPointer(Layer)")`,
  `Oil.createObject("OwnedVector(WeakPointer(Layer))")` (list of slots whose size the script sets
  itself with `append` / `removeAt`, e.g. from an integer "number of bones").
- **Parameter declarations must precede any other statement, `import` included**
  (`ScriptStatementOrderException: Parameter declarations should be placed before any other
  statement`): put `import math` etc. after the declaration block.
- **Reserved names**: any script variable that carries the name of a native element attribute
  (e.g. `preset`, `label`, `tools`, `activation`) conflicts: `script.preset` returns the native
  `ElementPresetSelector`, not your variable (`'ElementPresetSelector' object has no attribute
  'enumerators'`). Prefix it (`lightPreset`).
- Verified declaration types: `Oil.HsvColor()`, `Oil.Percentage(x)`, `Oil.PositiveMeters(x)`,
  `Oil.Boolean(x)`, `Oil.PositiveInteger(x)`, `Oil.createObject("Angle")`; `Oil.Angle` and
  `Oil.Color` do not exist. Angles in radians (`.set(math.radians(d))`).
- **Installing and running a Script from the bridge**: `sourceCode.set(src)` +
  `parent.tools.append(t)` does compile (`dynamicVariables` filled) but does not execute; do
  `t.execute.trig()` in one call, then read `script.lastExecuteResult` / `numExecutions` in the
  **next** call (the execution happens after the bridge returns). To change a parameter:
  `t.dynamicVariables[i].set(v)` then `execute.trig()`. A `print` from the Script appears in the
  output of the call that triggered the execution.
- A `Real` refuses a Python `int` (`TypeError ... expected Real or float`): always `float(...)`.
- A Script can also wire itself / recolour itself (`script.colorLabel`, `script.x.set(...)`).
- **Scripts share the same global namespace (R15, 06/10/2026).** Two copies of the same script
  in a project (e.g. an arm rig and a leg rig) read and write the **same** `globals()`: an
  "import initialisation done" flag set by the first prevents the second from creating its
  objects (parameter banks never created), a shared label cache blocks the second one's `label`
  update, and any state remembered from one frame to the next (previous pose, etc.) is mixed
  between the two. **Never store per-script state in `globals()` directly**: keep the state in a
  registry indexed by the object that distinguishes the script, for example its compo:
  ```python
  def S():
      reg = globals().setdefault('_REGISTRY', [])
      comp = script.parentElement
      for c, d in reg:
          if c is comp: return d          # the same Smode element always gives the same Python object
      d = {}; reg.append((comp, d)); return d
  ```
- **A Script can live in a `Group3dLayer`** (`group.tools.append(tool)`): `script.parentElement`
  is then the group (`.layers`, `.tools`, `.placement`, `.worldMatrix`), not the Compo. Parent
  chain verified: script → `Group3dLayer` → (nested groups…) → `Compo` → `TextureLayer` → `Scene` →
  `Project` (`element.parentElement`, `AttributeError` at the top). `rasterizer`, `currentCamera`
  and `defaultCamera` only exist on the **Compo**: find it by walking up the parents until
  `getOilClassName() == 'Compo'`. `Group3dLayer.tools` accepts `PythonScriptTool`,
  `ParameterBank` and `MaterialBank`. The `worldMatrix` of a group **inherits from the parent
  groups** (rotation / position accumulated): a rig in a group itself inside a rotated group
  works if you work in the group's local coordinates and read the group's `worldMatrix` for any
  world orientation (e.g. a handle facing the camera). It allows nested rigs (body > arms, legs)
  with one script per group (see per-script state above). Verified: `comp_a is comp_b` is true
  for two reads of the same element, even after `gc.collect()`. (`getUniqueIdentifier()` raises
  an exception, `WeakPointer.toString()` returns an empty string: not usable as identifiers.) A
  script pasted from a Windows file can have `\r\n` line endings: no effect on execution, but
  `sourceCode.get() == file` is then false.

**Activation cascade**: a root layer with `activation="inactive"` freezes everything below it
(including nested "At Every Update" Scripts), without any error or message. Debug reflex if a
script "no longer runs": check `layer.activation.get()` going up the whole hierarchy, not just the
script itself.

### Triggering a Script from another Script (slots) — confirmed R15 (30/09/2026)

- Declaring a slot where the user drops a Script: `slot1: Oil.createObject("WeakPointer(PythonScriptTool)")`.
  `script.slot1.get()` returns the `PythonScriptTool` (or `None`).
- Executing that Script: `tool.execute.trig()` (`execute` is a `Trigger` object, not a function:
  `tool.execute()` raises `'Trigger' object is not callable`). Synchronous, increments
  `numExecutions`.
- `Oil.createObject("Trigger")` can be declared as a Script parameter, but has no read method (only
  `.trig()`): no way found to detect a click from the Script. An `Oil.Boolean(False)` that the
  script resets to `False` acts as a button.
- `tool.getUniqueIdentifier()` **crashes**: `TypeError: Unable to convert function return value
  ... juce::Uuid`. Do not use it. An uncaught exception in an "At Every Update" Script stops it
  completely (the MCP bridge then answers 504).
- A Script's `globals()` namespace **survives re-pasting the code**: a function removed from the
  source stays callable until Smode restarts. An HTTP server created with
  `if "x" not in globals()` also keeps the old handler class. The bridge's solution: a
  `restartServer` checkbox (purges functions absent from the source through `ast` +
  `script.script.sourceCode.get()`, then restarts the server in a thread — `shutdown()` would
  block the main thread).

### Reloading a script / clearing the Python cache — confirmed R15 (06/10/2026)

- Smode R15 has **a single embedded Python interpreter** (`sys.prefix` = the `python` folder of
  Smode Compose), ~170 modules loaded at startup (stdlib, `Smode`, `Smode.Oil`, `_cppSmode*`). A
  user module imported by a Script stays in `sys.modules`: modifying it on disk is not enough, it
  has to be purged (user modules only, sparing `__main__`, `Smode*`, `_cpp*`, stdlib and
  site-packages) then `importlib.invalidate_caches()`, and the `__pycache__` deleted if needed.
  The Oil API exposes no script cache (`PythonScript`: `sourceCode`, `lastCompileResult`,
  `lastExecuteResult`, `numExecutions`, `verboseDebug`).
- **Smode does not keep the source file path of a Script**, only the pasted text
  (`sourceCode`). To reload a Script's code from a `.py`, you have to match them yourself, for
  example by the title of the file's header box or by `label` == file name (a Script that renames
  its label breaks this matching), then `tool.script.sourceCode.set(src)` (recompiles). Ready-made
  Script: [smode-clear-script-cache](https://github.com/gyomh/smode-clear-script-cache).
- Scripts are found in the **`.tools`** of the Scene, of the Compo (the `generator` of a
  `TextureLayer`) and of the groups, **not in `.layers`**. In a Script, `script` is the
  `PythonScriptTool` and `script.script` the internal object that carries `sourceCode`. To
  recognise yourself among the tools: `tool is script` (`getUniqueIdentifier()` is not
  convertible).
- Do not reload the bridge Script (`smode_bridge`, "At Every Update") from another Script: skip
  it explicitly.

- **File-writing trap on Windows**: `open(path, "w")` converts `\n` into `\r\n`; to write a `.py`
  without altering the line endings, open in binary or with `newline="\n"` (otherwise
  `sourceCode.get() == file` is false, see above).
- Complete example: the [smode-clear-script-cache](https://github.com/gyomh/smode-clear-script-cache)
  repository (options `NAME_FILTER`, `CLEAR_PYCACHE`, `RELOAD`, `RELOAD_SCRIPTS`).

### Subprocesses and threads from a Script — confirmed R15 (01/10/2026)

- **Never make the main thread wait** for a subprocess that queries the Smode interface (UI
  Automation): while waiting, Smode no longer answers UIA (`0 elements`, or `FindAll`
  "Unrecognized error"). Direct `subprocess.run` and a separate thread + `join()` both fail; a
  non-blocking `Popen` works. Seen in a script launched by Execute and through the bridge;
  another script using the same reading with `join` nevertheless worked for the author: the
  cause of the difference is not elucidated, so the non-blocking pattern below is the safest.
- **Pattern that works**: the Script launches a `daemon` thread and returns immediately; the
  thread does its work (subprocess, network), then has the Oil code executed on the main thread
  by posting `{"code": ...}` to a local HTTP bridge running in an "At Every Update" Script (see
  "The MCP bridge"). The thread itself never touches Oil.
- **Feedback**: a Script's parameters are set from the outside through `tool.dynamicVariables`
  (see "Declared parameters", corrected R15); `tool.label = "..."` remains the simplest way to
  make a state visible in the tree (find the `PythonScriptTool` by walking
  `layer.generator.tools`, by label prefix; `getUniqueIdentifier()` is unusable). A Script that
  resets its own `script.label` on every execution keeps the prefix stable.
- `tool.script.numExecutions.get()` = 0: the clicked Execute did not reach this Script (wrong row,
  old homonymous script, or script absent from the project reloaded without saving).
- Creating a Script in a project: `t = Oil.createObject("PythonScriptTool")`,
  `t.script.sourceCode.set(src)`, `t.launchMode.set(0)`, `t.label = "Name"`,
  `layer.generator.tools.append(t)` — confirmed.

### Reading the UI selection (UI Automation, outside Oil)

Oil exposes no selection (nothing in `engine`, `project`, scenes, timelines). See the
[smode-selection-reader](https://github.com/gyomh/smode-selection-reader) project: reading the
title of the Parameters panel. Limits: a single non-locked Parameters panel; the UIA tree is flat
(≈780 children under the window, ≈1500 unnamed `Custom` elements) so **the name of a selected
timeline is always "Main Timeline"**, impossible to know which scene/compo it comes from — select
the scene/compo layer instead. `FindAll` costs ≈5 ms per element even filtered by type: cache the
position of the title, `AutomationElement.FromPoint` (returns an empty `Custom` on the title) then
the neighbours with `TreeWalker.RawViewWalker` (`GetNextSibling`/`GetPreviousSibling`) to find the
`Text` (≈1 s instead of 4 s). `Add-Type -AssemblyName WindowsBase` is required for
`System.Windows.Point`.

Other findings (R15, 30/09/2026):
- **The locked (pinned) panel does not show the selected element**: reading a locked tab gives a
  misleading success. All non-locked panels show the same selection; only one tab is read at a time
  (the content of inactive tabs is absent from the UIA tree).
- Detecting the lock through the pixels of the icon: abandoned. It worked on the main screen but,
  on a secondary screen (1920x1080, 100 %, non-fullscreen window, negative coordinates), the
  `BoundingRectangle`s of the children are shifted by about 950 px in X (Y and left edge correct);
  even with `PerMonitorV2` the shift remains (probable JUCE multi-screen / DPI defect). Do not
  trust UIA coordinates to capture the screen.
- The title of the Parameters panel is a `Text` with a width/height ratio ≈ 6.82 (300x44 or
  150x22), with no trailing `:` and no `ComboBox` on the same line: this filter rules out numeric
  values, the Viewport title and the "Remaining:" panel.
- **Execute button of a Script's ROW in the Elements tree: does not change the selection**; only
  the Execute button of the Script's Parameters panel forces the selection onto the Script (the
  selection then becomes the Script itself).
- Launched from Smode (GUI process without a console), a `subprocess` must receive
  `stdin=subprocess.DEVNULL` (with `stdout=PIPE`, `stderr=PIPE`, `creationflags=0x08000000` to
  hide the window), otherwise `OSError(9, 'The handle is invalid')` after a Smode restart (not
  reproducible through the bridge, whose handles are valid). UTF-8 output on the PowerShell side
  (`[Console]::OutputEncoding`) and `utf-8-sig` decoding on the Python side for accented names.

### Deforming a geometry with a rig (Transform3d + masks) — confirmed R15 (07/10/2026)

- `GeometryLayer.generator.modifiers` (`OwnedVector`) receives `…GeometryModifier`s: found by
  trying `Oil.createObject`: `Transform3dGeometryModifier`, `ScaleGeometryModifier`,
  `DisplaceGeometryModifier` (no native Bend / Twist / Skin). Masks (`modifier.masks`):
  `LinearGeometryMask`, `SphereGeometryMask`, `BoxGeometryMask`, `CylinderGeometryMask`,
  `NoiseGeometryMask`, `RandomGeometryMask`, `FunctionGeometryMask`.
- `Transform3dGeometryModifier`: `anchor` (x/y/z in metres, local frame of the geometry),
  `rotation` (`EulerAngles`, order 0 = Rz·Ry·Rx, radians), `translation`, `scale`, `intensity`,
  `masks`. Without a mask: weight 1 everywhere.
- `LinearGeometryMask.segment.begin / end` (`Segment3d`): weight 0 at the start, 1 at the end and
  beyond (clamped ramp) → transition zone of a bend. Several chained modifiers (pivot = current
  joint, rotation relative to the previous bone, mask on the deformed bone) give linear skinning
  in an FK chain. Complete example: [smode-ik-rig](https://github.com/gyomh/smode-ik-rig)
  (IK Deform).
- **Subdivide the axis** or there is nothing to bend: `CapsuleGeometryGenerator.heightPrecision`
  (1 by default); `Precision2d` / `Precision3d` (`x`, `y`, `z`, `uniform` checkbox to untick first,
  otherwise everything changes together); scalar `precision` for Rectangle / Circle / Star.
- Existing geometry generators (`createObject`): Capsule, Box, Plane, Sphere, Cylinder, Torus,
  Circle, Helix, Star, Text, Particles, Rectangle. Capsule: the layer origin is the lower end.
  Vertex positions cannot be read from Python (`generator.positions` is opaque): verify by
  capturing the Smode window.

### Self-installing Scripts (IK rig) — confirmed R15 (07/10/2026)

- **Moving yourself**: `copy = script.clone()` (copies source + variables),
  `group.tools.append(copy)`, then remove the original from `parent.tools` by finding it with
  **`is`** (`parent.tools[i] is script`). `getUniqueIdentifier()` is not convertible in Python
  (`Unable to convert ... juce::Uuid`).
- **Writing into a script from other code**: `tool.script.sourceCode.set(src)` recompiles and
  executes once; `tool.execute.trig()` = one execution (useful to test frame by frame;
  `script.numExecutions` stays fixed if the script does not run by itself).
- **A linked ParameterBank `Parameter` (`ParameterLinkTarget`) pushes its own value back onto the
  target on every update**: writing only the script variable is cancelled (e.g. a `Create Rig`
  button reset to False). Also write into the Parameters whose
  `p.targets[k].target.get() is var`. Conversely, a bank field is not filled when you fill the
  variable on the script side: also write `p.value.set(...)`.
- **`WeakPointer(Layer).set(None)` is refused** (TypeError): to empty slots, empty the
  `OwnedVector` (`removeAt`) and add new `Oil.createObject('WeakPointer(Layer)')`s to it.
- **Vector script variables**: `Oil.createObject("OwnedVector(Boolean)")`
  (+ `append(Oil.createObject('Boolean'))`) works; an element can be the target of a
  `ParameterLinkTarget` (`lt.target.set(vec[i])`).
- Parameter value writes made through the API only propagate to the script at the next Smode
  update (not within the same call): to test, write the script variable directly.

## Imported 3D files, image textures and material compos (R15, 08/10/2026)

Verified while building a Blender -> Krita -> Smode texturing workflow (FBX pieces, one image texture per piece).

- **Importing an FBX by script** (the UI importer does the same): a `Group3dLayer` whose `.tools` holds a
  `MaterialBank`; one `GeometryLayer` per piece with `generator = Oil.createObject("Scene3dFileGeometryGenerator")`
  (`gen.file.path.set(r"C:\...\model.fbx")`, `gen.subGeometryToUse.set("NodeName")` - the node name in the file) and
  `renderer = ReferenceGeometryLayerUser` pointing at a material of the bank (see *Shared materials*). Build everything
  detached, append the group to the Compo last.
- **`useLocalPlacement`** (default **False** on a script-created generator; the UI importer sets **True**):
  - `True`: the geometry is in the node's local space (pivot = node origin, e.g. a joint). The layer's
    `placement.position` must carry the node position - set it yourself. This is what you want for rigging.
  - `False`: the geometry arrives already offset by the file's node transform. Adding the position on the layer
    **double counts** it (pieces separated by gaps).
  - A layer's `worldMatrix` only reflects the layer's own placement and is **stale for one evaluation** after you
    change it: read it in a later call.
- **Re-exported file**: setting the same `file.path` again does **not** reload it; call `gen.file.reload.trig()`.
- **Blender FBX export** (Y up for Smode): *Apply Transform* (`bake_space_transform=True`) with
  `apply_scale_options='FBX_SCALE_ALL'` gives vertices in metres, node scale 1 and **no -90 deg X rotation**. With
  `FBX_SCALE_NONE` / `FBX_SCALE_CUSTOM` the baked file stores centimetres + a node scale of 0.01, which Smode does not
  apply in local-placement mode (pieces 100x too big, stacked). Without baking, every node carries a 90 deg X rotation.
- **Image texture**: `Oil.createObject("ImageFileTextureGenerator")`, `gen.file.path.set(str)`. `sourceResolution` is
  0x0 and `liveStatus` is `uninitialized` until the next evaluation (read it in a later call).
- **Material map as a Compo** (to keep FX / scale reachable): `mat.components[0].map = compo`, with `compo =
  Oil.createObject("Compo")` - set `rasterizer.resolution.preset.set(40)` before width/height - and its layer's
  `generator` set to the generator (`ImageFileTextureGenerator`, `CheckerBoardTextureGenerator`, `UniformTextureGenerator`).
  `obj.clone()` deep-copies a material or a Compo: the copies are independent (checked by changing a checker size on one).
- **Reference cache**: after replacing a material's maps by script, layers that reference it keep the old content until
  `layer.renderer.referencer.reloadInstance.trig()`.
- `CheckerBoardTextureGenerator.size` is read in percent: `size.width.set(4.0)` shows `Canvas2dSize(400, 400)`.
- **Driving a Script's parameters from outside**: `tool.script.<name>` does **not** exist (only inside the Script);
  use `tool.dynamicVariables[i]`, looking the index up by `getFriendlyName()` (e.g. "Reset Rig").

## Known UI bugs

- **Links shown as "Disconnected"** after creation through the API although they really work
  (checked visually, the data flows). Not solved by the creation order. Fix observed: closing and
  reopening the project forces a full reload that fixes the display — a display cache that is not
  recomputed dynamically in a live session.
- **Scale that resets after insertion in the scene**: `ShapeTextureMask.shape.placement.
  scale.size` (circular "Stretch to..." masks) gets recomputed automatically once the document is
  fully installed in the live scene (seen twice, always towards the equivalent of
  500px/resolution). Systematic fix: re-apply these values in a "POST-INSERTION FIXES" block
  executed AFTER `parentElement.layers.append(...)`.
- **No way to override the displayed label** of a Script parameter — the label is auto-derived
  from the Python variable name (camelCase → Title Case). No `.label`/`setFriendlyName()` in the
  Python SDK for that; the only lever is renaming the variable.
- **`CustomEnumeration` stays empty in the panel** until the script has been RUN (Ctrl+Enter) at
  least once after the first Compile — the population happens in the body of the script
  (statements), not at the declaration.
- **`TimelineCue` (mainAnimation) built off-tree then inserted all at once: layers missing from
  the Timeline panel**, although playback really works (correct data, only the UI does not sync).
  Same family as the `ContentMap.target` bug (see above): Smode does not always notify the UI for
  an object built while its container is still outside the open document's tree. Confirmed fix:
  insert the `Compo` into the scene (`parentElement.layers.append(compoLayer)`) **before**
  creating the `TimelineCue`/calling `.createBlock()`, not after — reproduces the behaviour of
  step-by-step driving in a live session, where the Compo is already in the tree when the
  timeline is built.

## Observed instabilities

Two complete Smode crashes met while building this reference:
1. `Oil.docMe()` called right after handling an object freshly extracted from a vector
   post-append → correlated with a crash, not confirmed as the sole cause.
2. Re-fetching an object right after `append()` then accessing a sub-property (`.placement`) →
   `Access violation - no RTTI data!`, then a complete crash on the next request.

Neither happened when following the [golden rule](#golden-rule-configure-before-adding-never-after)
(configure everything before, never touch afterwards). At this stage, it is the best protection
known.

Two other complete crashes (R15, 06/10/2026), both due to **probing internal enumerations**:
3. `Oil.createObject('ActivationState')` followed by a `dir()` on an `ActivationState` variable.
4. A `.set(0..4)` loop on `ReferenceGeometryLayerUser().referencer.address.location` (freshly
   created).
Rule: never test values of an unknown enumeration. Read the value of an existing object
(`.get()`), then put **that** value back or a known value (e.g. `location.set(1)`).

After a crash, Smode may **reopen an old save**: the automatic saves are in
`Documents\Smode Files\<project>.project\.versions` (every 5 min); a text search in the file
(`IconFleche`, the name of an object) tells which one holds the wanted work.

## The MCP bridge (reminder)

Smode offers no official API for external control. The only path is a home-made bridge
([smode-mcp](https://github.com/gyomh/smode-mcp)): a Smode Script in Launch Mode **"At Every
Update"** (not Manual) starts a local HTTP server, which drops the requests into a
`queue.Queue()` + `threading.Event()` — the Oil code must run on Smode's main thread (running it
directly in the HTTP thread causes a total deadlock, confirmed through `netstat -ano`,
connections stuck in `CLOSE_WAIT`). `_EXEC_NAMESPACE = globals()` shared between all the calls →
persistent REPL-like behaviour, variables stay available from one call to the next.

**Security of an HTTP server launched from a Script** (found while writing
[smode-server-http](https://github.com/gyomh/smode-server-http)): listening on `127.0.0.1` is not
enough. A browser adds the `Origin` header to any cross-site request, **even towards 127.0.0.1**:
a visited site can send a `POST` `application/x-www-form-urlencoded` (the format of Chataigne's
HTTP module) that executes code in Smode (CSRF). For any endpoint that executes code: refuse the
requests carrying an `Origin` or a `Host` outside the list (DNS rebinding), unless a valid token is
given; only enable CORS on the endpoints without execution. Use a `ThreadingHTTPServer` so that a
slow request does not block the others. **Do not read Oil parameters (`script.host`,
`script.port`) from a secondary thread**: read them in the main thread and pass them as arguments
to the thread.

---

## Related projects

Smode Scripts and tools built with this reference (all under
[github.com/gyomh](https://github.com/gyomh)):
[smode-mcp](https://github.com/gyomh/smode-mcp) (MCP bridge), [smode-server-http](https://github.com/gyomh/smode-server-http),
[smode-selection-reader](https://github.com/gyomh/smode-selection-reader), [smode-ik-rig](https://github.com/gyomh/smode-ik-rig)
(IK Rig + IK Deform), [smode-clear-script-cache](https://github.com/gyomh/smode-clear-script-cache),
[smode-vizualiser](https://github.com/gyomh/smode-vizualiser), [smode-oscilloscope](https://github.com/gyomh/smode-oscilloscope),
[smode-trace-writer](https://github.com/gyomh/smode-trace-writer), [smode-light-setup](https://github.com/gyomh/smode-light-setup),
[smode-orbit-camera](https://github.com/gyomh/smode-orbit-camera), [smode-new-scene](https://github.com/gyomh/smode-new-scene),
[smode-streamdiff-ctrl](https://github.com/gyomh/smode-streamdiff-ctrl).

## Contributing

This reference is built from real use, not from reading official docs (which do not exist at this
level of detail). If you find a different behaviour, an extra trap, or a better method: open an
issue or a PR with the Smode Compose version you tested. Please mention if a point of this
reference has become obsolete after a Smode Tech update.
