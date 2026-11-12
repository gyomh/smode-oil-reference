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
- [2D layer placement, masks and exposure](#2d-layer-placement-masks-and-exposure-r15-18-20102026)
- [2D shapes and groups: ShapeLayer, GroupLayer, 2D rigs](#2d-shapes-and-groups-shapelayer-grouplayer-2d-rigs-r15-30102026)
- [Particles (R15, 31/10/2026)](#particles-r15-31102026)
- [3D masks and fragment effects](#3d-masks-and-fragment-effects-r15-03112026)
- [Function cues](#function-cues-automatic-animation-without-the-main-timeline-r15-03112026)
- [Multiplying particle systems](#multiplying-particle-systems-shared-element-instantiate-point-renderers-r15-03112026)
- [Particles: text of sand, bank links](#particles-text-of-sand-bank-links-reading-errors-r15-05112026)
- [Multi-video ISF shaders, bank states, data textures](#multi-video-isf-shaders-bank-states-data-textures-r15-05112026)
- [A "plugin" Script: shared globals, document, shared videos](#a-plugin-script-shared-globals-document-shared-videos-r15-12112026)
- [Audio reactive](#audio-reactive)
- [Scripts created programmatically (PythonScriptTool)](#scripts-created-programmatically-pythonscripttool)
- [Imported 3D files, image textures and material compos](#imported-3d-files-image-textures-and-material-compos-r15-08102026)
- [File references, Media Directories and relink](#file-references-media-directories-and-relink-r15-08102026)
- [Web interface served by a Script](#web-interface-served-by-a-script-r15-08102026)
- [Widget Tool (R15, 09/10/2026)](#widget-tool-r15-09102026)
- [Video export from a script](#video-export-from-a-script-r15-11102026)
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
   No per-key removal either: a `Map` only offers `clear()`, `items()`, `size()`, `isEmpty()`.
6. `Oil.getObject(space, uniqueIdentifier)` exists ("Get the Oil object of the given uniqueIdentifier
   within the given space") but returned `None` for every format tried with the address of a live
   element (`"space"` / `"@space"` + `<uuid>` / `@<uuid>` / `{<uuid>}`, R15). The `@space/<uuid>`
   addresses shown by `WeakPointer.toString()` change at every session (not the uuids of the saved
   file). Not a usable lookup so far.

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
| `ProResProfile` (video export) | 0=proxy, 1=lt, 2=standard (default), 3=hq, 4=profile4444, 5=profile4444xq |
| `ProResColorSpace` | 0=limitedRange601 (default), 1=fullRange601, 2=limitedRange709, 3=fullRange709, 4=limitedRange2020, 5=fullRange2020 |
| `H264Profile` | 0=baseline, 1=main, 2=high (default) |
| `NvencPreset` | 0..6 = p1..p7 (default p7) |
| `AmfQualityPreset` / `H264Quality` | 0=speed, 1=balanced, 2=quality (default) |
| `FFMPEGHapProfile` | 0=hap (default), 1=hapAlpha, 2=hapQ |
| `HapProfile` (GPU / Squish encoder) | 0=hap (default), 1=hapAlpha |
| `HapEncoderQuality` | 0=localGPU, 1=squishLow, 2=squishMedium (default), 3=squishHigh |
| `MJPEGProfile` | 0=profile422 (default), 1=profile444 |
| `FFMPEGPCMComponentType` | 0=pcm_alaw, 1=pcm_f32be, 2=pcm_f32le (default), 3=pcm_f64be, 4=pcm_f64le, 5=pcm_mulaw, 6=pcm_s8, 7=pcm_s8_planar, 8=pcm_s16be, 9=pcm_s16be_planar, 10=pcm_s16le, 11=pcm_s16le_planar, 12=pcm_s24be, 13=pcm_s24daud, 14=pcm_s24le, 15=pcm_s24le_planar, 16=pcm_s32be, 17=pcm_s32le, 18=pcm_s32le_planar, 19=pcm_u8, 20=pcm_u16be, 21=pcm_u16le, 22=pcm_u24be, 23=pcm_u24le, 24=pcm_u32be, 25=pcm_u32le, 26=pcm_s64be, 27=pcm_s64le |

**Listing the values of a native enum** (R15, 18/10/2026): an `Enumeration` has no method that lists its values
(`getNumVariables()` = 0) and `set()` only takes an integer. On a throwaway object (e.g. an exporter created with
`Oil.createObject`, never added anywhere), `set(i)` for i = 0, 1, 2... then `toString()` gives each value. **Past the
last value `set()` does not fail**: `toString()` then returns the number itself (`"6"`) — stop at the first value
that is just its own index. Put the starting index back with `set()` afterwards.

`Oil.CustomEnumeration(("a","b"), 0)`, officially documented, **does not work**
(`AttributeError`). Fix: declare `x: Oil.createObject("CustomEnumeration")` empty, populate it in
the script body with `CustomEnumerator`s (`.label`=text, `.value`=int) through
`.enumerators.append(...)`, guarded by `if len(script.x.enumerators) == 0`. **R15 (07/10/2026):
the attribute is called `enumerators` (`OwnedVector(CustomEnumerator)`); the old names
`elements` / `CustomEnumerationElement` no longer exist** (`AttributeError` / `unknown Oil type
name`). `.set()/.get()` use the label (string), unlike native enums which use an integer.
Simpler alternative if a plain boolean is enough: `Oil.Boolean` avoids this whole bug.

**List filled at compile time (R15, 08/10/2026)**: the declaration accepts any expression; a lambda that
creates, fills and preselects the enumeration avoids the empty list until the first Execute (tested: fresh
compile and recompile over an old empty declaration):
```python
mode: (lambda e: ([e.enumerators.append((lambda n: (setattr(n, "label", lab), setattr(n, "value", i), n)[2])(
    Oil.createObject("CustomEnumerator"))) for i, lab in enumerate(("Relocate", "Consolidate"))],
    e.set("Relocate"), e)[2])(Oil.createObject("CustomEnumeration"))
```
(write it on a single line in the Script).

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

**Zones, layer targets and Processors** (R15, 14/10/2026, read on a show project):
- The zones of a ContentMap are `cm.rootArea.areas` (`ContentArea`, named by `.label`, e.g. `SCREEN 01`).
- A layer's `renderer.target.get()` can be one of these zones or the whole map (`cm.rootArea`): find the owner with
  `target.isChildOf(zone)` / `target.isChildOf(cm)` (true for the element itself too).
- `pipeline.processors` holds `ProcessorCompo` items (a compo: `layers`, `rasterizer`, `mainAnimation`...). A
  Processor groups or isolates parts of the pipeline, in any combination: one zone, several zones, one or several
  whole Content Maps, zones taken from different Content Maps... Each source is a `TextureLayer` whose generator
  is a `PipelineTextureGenerator` with `.source` (`PipelineSourceWeakPointer`) on a zone or a map
  (`toString()` = e.g. `SCREEN 01+02 -> SCREEN 01`), placed in the Processor's own frame.


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
- **Pivots and sizes (R15, 30/10/2026)**: `CapsuleGeometryGenerator.height` is the **total** length tip to tip and
  the pivot is the bottom tip (so cap centres at two joints a, b: `height = |ab| + 2r`, position = a - r);
  `CylinderGeometryGenerator` (`radius` = `Size2d`, elliptical) pivot = centre of the bottom cap; `PlaneGeometryGenerator`
  is born lying in XZ (a ground plane as is); a capsule turned along X: `orientation.z = -90°`. `placement.size`
  (`Size3d`, `linked` False) scales a layer per axis (ellipsoid from a sphere).
- **Rig with `Group3dLayer`** (FK): a `Group3dLayer` has `layers` and a `placement`; with `anchor = position = joint`
  its `orientation` turns its children around the joint (checked). Nested groups = hip > knee > ankle > toes.
  `RepeatGeometryModifier` (`count`, `placement` = offset applied per copy) in `generator.modifiers` repeats a
  geometry (fence posts, trees every period) in one layer. **The offset is in the geometry's own space, before the
  layer's `placement.size`**: on a layer scaled x 1.7 an offset D gives copies 1.7·D apart (it broke a seamless loop:
  hedges jumped at the loop point); use `D / size.x`.
- **Rolling ground that loops**: a displacement noise is not periodic, so it jumps at the loop point. Flattened grass
  ellipsoids (sphere radius 1 + `placement.size` = (rx, ry, rz), partly buried), one set per tile of the travel D,
  repeated every D and wider than D, overlap into continuous ridges that are exactly periodic; objects are set on them
  with the analytic height (max over the ellipsoids and their repeats).
- **Writing values**: a `Percentage` / light `intensity` takes a **fraction** (`intensity = 30.0` gave 3000 %, an all-white
  render); several fields of objects already in the tree (camera placement, light bounding box) ignore a direct `=`
  assignment silently: use `.set()`. Float fields refuse Python `int` (`TypeError ... expected Real or float`).

### PBR materials and procedural textures (R15, 30/10/2026)

- `PBRSurfaceGeometryRenderer` (assigned directly to `layer.renderer`, one renderer object per layer: never share it):
  channels `albedo`, `metallic`, `roughness`, `normal`, `emissive`, `occlusion` (+ `metallicFactor`,
  `roughnessFactor`, `normalLevel`, `side`, `depthBuffer`), each an `OwnedPointer(Colorizer3d)`, by default a
  `Uniform3dColorizer` (`.color`). **Default roughness = black (0 = mirror)**: always set it. Also exist
  `SubstancePBRSurfaceGeometryRenderer` / `SbsarFileTextureGenerator` (Substance), `TextureLayer3dColorizer`,
  `Gradient3dColorizer` (`gradient`, `shape`).
- Texture on a channel: `col = TextureLayer3dColorizer()`, `col.layer = <any TextureGenerator>`,
  `col.transform` (`Parametric2dPlacement`, `scale.scaleFactor` = fraction -> repeats `1/fraction` times),
  `mappingMode` (0 uv, 1 xy, 2 xz, 3 yz, 4 custom), `wrapModes.top/bottom/left/right`
  (`FrameWrapMode`: 0 transparent, 1 black, 2 white, 3 repeat, **4 mirroredRepeat** = any texture tiles without
  seam, 5 edge, 6 blurredEdge); then `renderer.getVariableByName("albedo").set(col)`.
- Procedural generators: `NoiseTextureGenerator` (`gradient` = `BitoneColorFunction` `beginColor` / `endColor` /
  `midPoint`, `scale` = feature size in px, `octaves`, `seed`, `resolution` Custom), `WoodTextureGenerator` (its
  default gradient **ends transparent**: set both colours), `MarbleTextureGenerator`, `BrickTextureGenerator`,
  `LinearGradientTextureGenerator` (`segment.begin/end`), `WhiteNoiseTextureGenerator`. No `DomainWarpingNoise` class.
- **UV axes of a ground plane**: on a `PlaneGeometryGenerator` (lying in XZ) the colorizer's
  `scaleFactor.width` repeats along **Z (the plane's `size.height`)** and `scaleFactor.height` along X: swap them,
  otherwise the texture is streaked along the strip.
- **Normal maps from noise**: `NoiseTextureGenerator` (black -> white) with a `DepthToNormalTextureModifier`
  (`softFactor`) in its `modifiers`, in a `TextureLayer3dColorizer` set on the material's `normal` +
  `normalLevel`: real relief on grass, dirt, bark, foliage, fabric (keep ~0.25-0.3 on clothes, more looks knitted).
- Organic shapes: `GeosphereGeometryGenerator` (`subdivision`) + `PositionNoiseGeometryModifier` (`strength`
  `Size3d`, `noise` = `ProcessedNoiseFunction`: `scale`, `octaves`, `seed.value`) = lumpy foliage clumps with real
  light/shadow detail. `TreeGeometryGenerator` is not instantiable.

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
- **Directional light (R15, 30/10/2026)**: aiming it like a spot (position + `target.targetObject` + `axis` zNeg) is
  the reliable way to get the wanted direction (Euler angles alone were ambiguous). Shadows are on by default
  (`shadowParameters`: `intensity`, `bias` default 0.1 m = shadows detached, `softRadius`, `softNumSamples`,
  `resolution` 2048). `sceneBoundingBox.automatic` = the whole scene: on a 300 m world the character's shadow
  disappears. Manual box: `automatic` False, `display` False, and **`center` / `size` are in the light's frame**
  (x / y across the beam, z along it: the target is at `center.z = -distance`); a box set in world coordinates
  puts the whole scene in shadow (dark render).
- An `AmbientLight` adds the same colour to every surface: above ~0.15 it washes the image out (grey haze, no
  contrast). Better: a strong warm sun with shadows + 2 weak cool directional "sky" lights without shadows
  (`shadowParameters.intensity = 0`) + a weak ground bounce from below + ambient ~0.1.

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

- **Sharing 3D geometry (R15, 31/10/2026)**: the way Smode's own example does it is a **`SharedElement(GeometryV9Generator)`
  tool** (`Oil.createObject("SharedElement(GeometryV9Generator)")`, appended to the compo's `tools`, `label` = name,
  `getVariableByName("content").set(generator)`) and layers whose `generator` is a **`ReferenceGeometryV9Generator`**
  with `referencer.address.location` = 0 and `referencer.address.elementPointer.set(se.getVariableByName("content"))`
  (the *Pointer variable* `content`, not the generator itself: with the generator the reference stays unresolved,
  `address.target.get()` is None), `referencer.shared` True. Each layer keeps its own `placement` and `renderer`; the
  reference has its own `modifiers`. What does NOT help: a `ReferenceLayer` (re-draws the target, the profile of 20
  of them reads 2.3x a clone's) and a `ReferenceGeometryV9Generator` aimed at another layer's generator with
  `location` 1 + `directPointer` (+7.1 ms for 20 instead of +6.3 for 20 clones). Via the shared element, 20 foliage
  layers cost +0.9 ms on the status-bar frame time (16.7 -> 17.5 ms) instead of +6.3 ms (status-bar reading, frame capped
  at 60 fps: indicative). `frameProfileTime` (every element, ms) is readable by script but only refreshes while the
  Profile column is displayed in the interface; layer times are not additive (a group reads 22 ms for children summing
  26 ms). Other reference classes found by probing `Oil.createObject`: `ReferenceGeometryV9Modifier`,
  `ReferenceTextureGenerator`, `ReferenceTextureModifier`.

- **Wiring shared geometry / materials by script (R15, 31/10/2026)**: the `SharedElement` and the `MaterialBank` have to be
  in the tree before the references can be resolved, so create the layers (with an unresolved `ReferenceGeometryV9Generator`
  / `ReferenceGeometryLayerUser`, `label` used as a key) in one call and link them in a later call: generator ->
  `ref.referencer.address.elementPointer.set(tool.getVariableByName("content"))`, `location` 0, `referencer.shared` True;
  material -> `address.directPointer.set(bank.materials[j])`, `location` 1. `Group3dLayer.tools` accepts both tools.
  A repeat modifier put on the reference is evaluated per layer (its offset is applied before the layer size); in a
  scene of 54 foliage layers, shared geometry + shared materials + coarser LOD (subdivision 4/3/2 -> 3/2/1) only moved the
  trees from ~17 to ~15-17 ms (profile noise is +-2 ms): the per-layer cost is mostly fragment work of the textured PBR
  materials (the same far trees with a plain-colour material read 4.7 ms instead of 8.0), not triangles or generation.
- **A wrapping world slide**: a world that is periodic in D0 only needs copies over one tile if its slide wraps: key
  `x = -D0` with a `StepKeyframeInterpolator` output, then `x = -v*eps` one frame later (instant, invisible jump).

- **Timeline sequences with break markers (R15, 31/10/2026, read from a project built by hand)**: `mainAnimation.timeMarkers`
  holds markers with `breaking` (play stops there until resumed) and `action` (`GotoTimelineAction` -> jumps to another
  marker: a loop that survives). A cue block with `footage.position.automateTransport` False does not drive the cue: the cue
  plays by itself (and loops between its own `parameters.in/out`; with `launchMode` restartWithActivation it restarts when its
  block activates) while a block with automateTransport True drives it. A `ParameterTrack` on the cue's `parameters.speed`
  (SpeedFactor) changes the playback speed of a looping cue. To find which object a parameter track drives, call
  `target.sourceElements()` on the track's target: it returns the track, named "Track <Element> <Parameter>".

- **Starting a transition at the end of a loop cycle (R15, 31/10/2026)**: a Script ("At Every Update", two `Oil.Boolean` buttons
  that it resets itself, since a `Trigger` cannot be read) watches the `transport.position` of the looping cue; a wrap is a
  drop of more than half its in/out range. At that frame it does `mt.transport.position.set(marker + elapsed)` then
  `mt.transport.play.trig()` (both in the same call work) with `elapsed = cue position - in`. Keep the Script's code in a
  string executed once (Smode recompiles the text every frame) and its state in a registry, not in `globals()`.
  `parameters.getVariableByName("in").value` gives the cue's loop range; a breaking marker stops the main timeline while
  the looping cue keeps playing by itself.

- **Driving a Script's `Oil.Boolean` button from a bank (R15, 31/10/2026)**: a `Parameter(Trigger)` links to it with a
  `SetConstantLinkModifier` (`p.modifiers[0].value.set(True)`: its default `False` makes the click do nothing); the Script
  resets its own button, so every click is a new False -> True change. A `Parameter(Boolean)` (on/off) linked to such a
  button needs two clicks: the Script resets the button but the parameter keeps its state, so the next click pushes
  a value the button already has. A bank Trigger fires from Python with `p.value.trig()`.

- **Key times below 0 are clamped to 0** (`cue.createKeyframe(param, -0.1, False)` stores a key at 0.0, a second one at 0.0 when 0
  is keyed too), keys past the end of the cue are kept. A Smooth (Catmull-Rom) loop therefore needs lead-in keys inside
  the cue: key the cycle from `OFF` (> one key spacing) and loop between `parameters.in = OFF` and `out = OFF + cycle`.
  A script-made block with default settings looped over the WHOLE cue length (1.25 s for a 1 s cycle + 0.25 s of
  neighbour keys), ignoring the cue's own in/out; in a hand-built sequence the cue (`launchMode` restartWithActivation,
  block `automateTransport` False) looped on its in/out (measured 1.0 s). Set the block's `footage.position.in/out`
  explicitly when you create the block by script.
- **A normal map on a very long ground strip made the lighting drift with the world offset (R15, 31/10/2026)**: a 600 m
  `PlaneGeometryGenerator` with a mirrored-repeat normal map got darker/brighter along its length (ground luma 45 -> 67 over
  25 m of slide, then a jump when the loop restarted) although the albedo texture was periodic. Found by switching layers
  off one by one and measuring the mean luma of image zones either side of the loop point; `normalLevel` 0 removed it.

## Compo camera (R15)

- **Camera of a compo (R15, 30/10/2026)**: editing `compo.defaultCamera` changed nothing on screen. What works: an
  `AffineCamera` with `placement = TargetOrientationDistance3dPlacement` (`target`, `orientation`, `distance`) and
  `frustum = FieldOfViewPerspectiveFrustum`, appended to `compo.cameras`, then `cam.makeCurrent.trig()` **in a later
  bridge call** (in the creation call `currentCamera` stays `None`). In the frustum the **horizontal** angle is the
  master (setting `vertical` was recomputed from it): vertical = 2·atan(tan(h/2) / aspect).
- Post-processing on `compo.modifiers`: `DepthOfFieldTextureModifier` ("legacy"; `focusParameters.automatic` False,
  `distance`, `focalRegion`, `near/farTransition`; `farBlur.radius` in px: ~20 for a photographic background blur, a
  small light halo appears around sharp edges), `AmbientOcclusionTextureModifier` (`radius`, `intensity`,
  `complexity`: low complexity = grainy), `ExposureTextureModifier`. No bloom, motion blur or fog class.
- A 2D layer (gradient sky) placed before the 3D layers is drawn behind them.
- **Photographic pipeline**: compo modifiers process the whole compo, so a grain layer on top would be blurred by the
  depth of field. Put the 3D scene in a sub-compo (`TextureLayer` "shot" whose generator is a `Compo` with its own
  `cameras`, lights, layers and lens modifiers AO / DOF / exposure; its camera made current with
  `sub.cameras[0].makeCurrent.trig()`), then above it in the main compo a vignette (`RadialGradientTextureGenerator`,
  transparent -> black alpha ~0.35) and grain (`WhiteNoiseTextureGenerator`, `blendingMode` overlay, opacity ~0.07),
  and the grade on the main compo (`TemperatureTextureModifier` red 0.54 / blue 0.46, `ChromaticAberrationTextureModifier`
  `distortion` ~0.04). The main timeline still drives keys and blocks inside the sub-compo.
- `BlendingMode` values: 0 passThrough, 1 replace, 2 normal, 3 dissolve, 4 darken, 5 multiply, 6 colorBurn,
  7 linearBurn, 8 darkerColor, 9 lighten, 10 screen, 11 colorDodge, 12 linearDodge, 13 lighterColor, 14 overlay,
  15 softLight, 16 hardLight, 17 vividLight, 18 linearLight, 19 pinLight, 20 hardMix, 21 difference, 22 exclusion,
  23 subtract, 24 divide, 25 hue, 26 saturation, 27 color, 28 luminosity, 29 alpha.
- `BrightnessContrastGammaTextureModifier` with `contrast` 0.12 on this HDR 3D render gave a black image with a few
  saturated spots: left out.
- **3D cost (RTX 4090 Laptop, 1080p)**: a directional light's shadows ≈ 6 ms (the shadow pass of all the geometry;
  `softNumSamples` 8 -> 4 and resolution 2048 -> 1024 changed nothing), the world's noisy geospheres ≈ 5.5 ms, DOF
  ≈ 1.4 ms, AO ≈ 0.6 ms; 256 vs 1024 px procedural textures: no measurable difference. Repeat motifs only as far
  as the camera sees (copies = view width at that depth + the travel, not a fixed count).
- A heavy build call (dozens of materials) can exceed the bridge's reply timeout ("Error executing tool"): the code
  still finishes in Smode; check the result in a next call before running it again.
- A `WeakPointer` cannot be emptied from Python (`set(None)` and `reset()` without its callback are refused).

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
- **Anchor, font, opacity (R15, 31/10/2026)**: `renderer.placement.position` is the **anchor** point, the **centre** of
  the text box by default (a left-aligned text at `position.x = 0.1` runs off the screen). To place the top-left corner:
  `placement.anchor.x = 0.0`, `placement.anchor.y = 0.0`. Font: `generator.font` is a `FontSelector` (`type` =
  `selectName`) whose `font` (`FreeTypeFontName`) is set with `generator.font.font.set("Consolas")` (default `Arial`,
  proportional: a columned log does not line up). `renderer.opacity.set(0.0..1.0)` exists on text and on the
  `SingleTextureRenderer` of a `TextureLayer`.
- **Introspection crash (R15, 31/10/2026)**: chained `dir()` / `getOilClassName()` on `generator.font`,
  `renderer.placement` and `renderer.atlas` of a throwaway `TextLayer`, in one call, **crashed Smode**. The same
  attributes read **one per call** are fine.
- **No bloom/glow class** (`BloomTextureModifier`, `GlowTextureModifier`... do not exist) and `BlurV8TextureModifier`
  has no `blendingMode`: for a glow, show the content twice (sub-compo), one copy blurred in `linearDodge`.

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
include them. `Process.MainWindowHandle` of Smode can be a 1x1 window: enumerate the process's visible top-level
windows (`EnumWindows` + `GetWindowThreadProcessId`) and take the largest one. To check an animation, grab a few crops
of the viewport ~0.1 s apart while the timeline plays and lay them out in one contact sheet.
**Without taking the focus (R15, 12/11/2026)**: `PrintWindow(hwnd, hdc, 2)` (`PW_RENDERFULLCONTENT`) from PowerShell captures the Smode window even behind
other windows, rendering included (verified on a 1920 x 1080 output window), about 250 ms per full-frame capture.

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
- **Main timeline of the project = `masterScene.mainAnimation`** (can be `None` until one is created;
  `masterScene.mainAnimation = Oil.createObject("TimelineCue")`). Dragging a Scene's timeline into it in the
  UI creates an `elementTracks` entry keyed by the **Scene** (R15, 11/10/2026): `ElementTrack.target` =
  `ElementAutomationTarget` (`element`, `activation`, `intensity` = the Scene's `opacity`, `transport` = the
  Scene timeline's transport), one `ElementTrackBlock` with `autoLength = true` (length = the Scene timeline
  length). Same result by script: `tc.createBlock(scene)[1]`, then `block.position.set(0)` (the block is
  created at the cursor) and `block.autoLength.set(True)`.
- `tc.transport.length.set(seconds)` is enough to resize a timeline: `parameters.targetLength` and
  `timeCode.endTime` follow by themselves. The **End** of a project video export (File > Export Video) is
  initialised with the main timeline length.
- Removing one track: impossible per key (see `Map` above); `tc.elementTracks.clear()` then recreate the
  wanted tracks, or switch a track off with `track.activation.set(False)`. After `clear()`, the Python
  wrappers of the old tracks/blocks point to destroyed objects: never touch them again (crash n°6).
- **Tracks made by `createBlock` are fragile (R15, 20/10/2026)**: they work, show in the Timeline panel and play,
  but as soon as a track is added **from the interface** (dropping an element on that timeline), every track
  created by script is wiped (`elementTracks` keeps only the new one; parameter tracks are not touched). Tracks
  that come from a clone (a cloned Scene) survive. Fix, tested: once the blocks are made, replace the timeline by
  its own clone — `scene.getVariableByName("mainAnimation").set(scene.mainAnimation.clone())`. Element tracks,
  blocks, fades, parameter tracks and keys are all kept (same counts, every weak pointer still resolves) and the
  tracks then survive a drop.
  **The clone has to be applied to every script-made timeline, not only the main one (R15, 31/10/2026)**: cues kept in an
  `AnimationBank` and keyed by `createKeyframe` / `createBlock` lost their tracks too when the user dropped an element on
  them (a loop cue lost its 4 parameter tracks, another its nested block). Pattern that survives: build + key a cue, then
  in a later call `cl = cue.clone(); bank.animations.remove(cue); bank.animations.append(cl)`, leaf cues first (a
  parent's block points at the cue it was made with: clear it and re-create it with the clone), main timeline blocks last,
  then clone the main timeline. Reading an animated value right after `transport.position.set()` in the same call gives
  the previous frame: read it in the next call.
- **Keys by script**: `tc.createKeyframe(parameter, seconds, False)` → `(ParameterTrack, Keyframe)` keys the
  parameter's **current** value (set it first) and creates the track if needed. A new key has
  `StepKeyframeInterpolator` on both sides: set `kf.inputInterpolator` / `kf.outputInterpolator` through
  `kf.getVariableByName(...).set(Oil.createObject("LinearKeyframeInterpolator"))` (also `Ease...`, `Smooth...`,
  `Step...`; `kf.linkInterpolators` = same on both sides). A segment uses the **output** interpolator of its left
  key and the **input** interpolator of its right key (Ease on the output = slow departure, Ease on the input =
  slow arrival). `EaseKeyframeInterpolator` has one variable, `function` (a `ClassObject`, default
  `SineFunctionShape`; `QuadFunctionShape` exists) that has **no setter from Python**. Keying again at the same
  time ADDS a second key; remove keys with `track.function.keyframes.removeAt(i)` / `.clear()`. `kf.position` is
  kept exactly (not rounded to a frame).
- The timeline drives its parameters **only while it plays or when the playhead is moved in the UI**:
  `transport.position.set(t)` from Python on a paused cue does not re-evaluate the keys (parameters keep the last
  value written by the script), so reading a parameter after it is not a check of the animation.
- **Block fades**: `block.footage.intensity.fadeIn` / `.fadeOut` are `Option(OpacityEaseParameters)`:
  `.enabled.set(True)`, `.value.length.set(seconds)`, `.value.getVariableByName("shape").set(
  Oil.createObject("LinearRampFunctionShape" | "SineFunctionShape"))`.
- Timecodes of a video block (`footage.position.in` / `out`, `targetLength`) are written in the **media's** frame
  rate: `0:00:02:28` on a 30 fps clip = 2 s + 28/30, not 28/60 on a 60 fps project.
- **Video block made by `createBlock`** (R15, 30/10/2026): `block.footage.position.automateTransport` is `False`, so the
  video stays on its first frame while the playhead moves ("Automate Transport" in the block's Footage - Position);
  set it to `True` and the video follows the playhead from the start of the block. The block length read back is the
  media's length, not the one written with `length.set()` (seen after cloning the timeline).
- **Activation of an Element or a track**: `obj.activation.set(False)` / `.set(True)`. The value is read as a
  **boolean**: `set(2)` (the "inactive" value) or `set(3)` switches it ON. Read back, `ActivationState` is 0 = active,
  1 = activationRequested (will be active with its parent, e.g. layers of an inactive scene), 2 = inactive. A layer
  switched off this way stays off when its parent compo is activated by a block; a parameter track whose keys were
  cleared can be switched off the same way.
- `scene.clone()` (any Element subtree) gives new UUIDs and remaps the timeline's weak pointers to the copies: in
  the detached clone `WeakPointer.get()` returns `None`, once inserted they resolve to the clone's own elements
  (blocks, fades and keys come along).
- A Scene made with `Oil.createObject("Scene")` has **no** `mainAnimation` (`None`): set a
  `TimelineCue` before inserting it.
- **Looping a timeline**: `tc.parameters.looping.set(True)` (`CuePlayParameters`: also `playMode`, `speed`, `in`/`out`).
- **Cyclic animation (walk cycle, R15, 30/10/2026)**: a `KeyframeFunction` has no repeat/cycle option (only `keyframes` and
  its buffer). Key ONE cycle in its own `TimelineCue` (`transport.length` = cycle length, `parameters.looping` = True) put in
  an `AnimationBank` (`bank.animations.append(cue)`, the bank in the `tools` of a layer/group/compo), then
  `tc.createBlock(cue)` on the main timeline (`createBlock` also takes a cue, not only layers): block `length` = the whole
  timeline, `block.footage.position.automateTransport.set(True)` and `.looping.set(True)`. The cue replays on the main
  timeline's clock (deterministic, loops with it). `cue.createKeyframe(...)` works on such a cue like on the main timeline.
  Applying the clone fix above afterwards keeps the block working.
- Before giving a key different input/output interpolators, `kf.linkInterpolators.set(False)`.
- **Interpolators, exact curves (measured frame by frame, R15, 30/10/2026)**: only `Linear`, `Ease`, `Smooth` and `Step`
  `KeyframeInterpolator` exist (no Bezier/tangent handles). With u = 0..1 across a segment:
  Ease out + Ease in = `(1 - cos(pi*u)) / 2`; Ease out + Linear in = `1 - cos(pi*u/2)`; Linear out + Ease in = `sin(pi*u/2)`.
  **Smooth = uniform Catmull-Rom per segment**: Hermite with tangents (per unit of u) `(p[i+1] - p[i-1]) / 2`, the same
  value used in both segments around a key, so the **speed is continuous only when keys are evenly spaced** (uneven
  spacing = speed jump at the key). First/last key: one-sided tangent `p1 - p0` / `pn - pn-1`, which ignores what comes
  next: a looping cycle keyed from 0 to its length gets a speed jump at every loop.
  Seamless smooth loop: key the cycle on an even grid with **one extra key on each side** (cycle from OFF to OFF + length,
  cue length = length + 2 * OFF), and loop only the cycle with the block's `footage.position` `in` / `out`
  (`Option(Seconds)`: `getVariableByName("in").enabled.set(True)`, `.value.set(OFF)`, same for `out`) + `looping`. Checked:
  the cue loops inside [in, out]. `KeyframeFunction.bufferData` stays empty (not a sampled curve).
- After `compo.getVariableByName("mainAnimation").set(clone)`, `transport.play.trig()` **in the same bridge call** does not
  start the new timeline: play it in a later call.

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

## 2D layer placement, masks and exposure (R15, 18-20/10/2026)

Measured while rebuilding pre-rendered clips from their source images (`TextureLayer` in a `Compo`):
- **Stacking**: `compo.layers[0]` is the **bottom** layer (drawn first), the last one is on top.
- **Reordering image layers without `removeAt`** (30/10/2026): swap their files,
  `layer.generator.file.path.set("<Media Directory name>/<folder>/<file>.png")` (same form as `file.path.get()`); no
  object is destroyed. Timeline tracks belong to the layer object, not to the file: apply the keys and blocks again
  after a swap. Adding a layer to a compo: `new = layer.clone()`, configure it, `compo.layers.insert(i, new)` (no
  problem seen, in a scene that was not active).
- `Parametric2dPlacement.position` (`Canvas2dPosition`): fractions of the compo, **y down** (0 = top), the
  anchor (default centre) is placed there. `rotation` (`Angle`) is set in **radians**
  (`rotation.set(10)` = 572.958°), **positive = clockwise** on screen.
- `ScaleFactorPlacement2dScale`: **100 % = the texture's own pixels** (a 2224 px wide image in a 3840 px compo
  covers 0.579 of it). `scaleFactor` is `linked` by default: `linked.set(False)` before setting `width` and
  `height` apart. Another scale mode: `placement.getVariableByName("scale").set(Oil.createObject(
  "SizePlacement2dScale"))`, `size` (`Canvas2dSize`) in fractions of the compo.
- A Parametric placement scales THEN rotates: an image rotated then squashed (a tilted disc) cannot be made with
  it. `Perspective2dPlacement` places the texture by its **4 corners**: `position` is a `Quadrilateral` with `a`,
  `b`, `c`, `d` (top-left, top-right, bottom-right, bottom-left, `Canvas2dPosition` fractions) — any affine or
  perspective placement. Swap it in with `renderer.getVariableByName("placement").set(Oil.createObject(
  "Perspective2dPlacement"))`. (Or nest: rotate inside a square sub-compo, squash the sub-compo layer.)
- `placement.previousMatrix` (`Matrix4d`, row vectors, compo fractions) = the matrix of the last frame
  rendered: the real size and position on screen, once the layer has been drawn.
- `Compo.background` (`HsvColor`, `00000000` by default): `background.alpha.set(1.0)` for an opaque black
  background (like a video).
- `GroupTextureRenderer.renderers`: one texture drawn several times, each `SingleTextureRenderer` with its own
  placement, blend and opacity (each can have its own timeline block).
- **Mask in the image's own space**: `MaskTextureModifier` in `generator.modifiers` (image generator or Compo),
  `masks` = `OwnedVector(TextureMask)`: `ShapeTextureMask` (`shape` = `RectangleShapeGenerator` or
  `CircleShapeGenerator`, each with its own `placement` in fractions of the image, `feather`, `inverse`,
  `blendingMode`) or `GradientTextureMask`. Build it complete before appending it; its placement can be keyed
  (a window that follows a moving image).
- `ExposureTextureModifier` (`exposure` in stops, `offset`, `gamma`, `intensity`) in `generator.modifiers`: keying
  `exposure` -8 ↔ 0 along a block fade gives a nicer fade than opacity alone.
- 16-bit PNG files load fine in `ImageFileTextureGenerator`.

## 2D shapes and groups: ShapeLayer, GroupLayer, 2D rigs (R15, 30/10/2026)

Found while building a side-view walking character out of rectangles and circles:
- **`ShapeLayer`** = `generator` (`OwnedPointer(ShapeGenerator)`, null until assigned) + `renderer` (`DefaultShapeRenderer`:
  `fill` / `stroke` with `.enabled` + `.color` `HsvColor`, `stroke.thickness`, `opacity`, `blendingMode`, `placement`).
  Generators: `RectangleShapeGenerator`, `CircleShapeGenerator` (`RoundedRectangle...`, `Ellipse...`, `Polygon...` do not
  exist). Size and position of the shape = **`generator.placement`** (`Parametric2dPlacement` with a `SizePlacement2dScale`):
  `scale.size.width/height` are fractions of the compo's width/height (`linked.set(False)` first), so a circle with
  `width != height` in pixels is an ellipse. `edgeLength` goes from 0 to 2000 on insertion.
  **The size is reset to 500 px a frame or two after insertion**, even when set before the append, and re-applying it in the
  same bridge call is not enough: re-apply it in a **later** call (see "Known UI bugs").
- **`GroupLayer`** (no `Group2dLayer`) = the 2D group: `layers`, `tools`, `placement` (`Parametric2dPlacement`, scale
  `ScaleFactorPlacement2dScale`). Its children keep coordinates in fractions of the compo. Rotation turns around the
  **anchor**: with `anchor = position = (jx, jy)` the group renders unchanged and `rotation` turns it around the point
  (jx, jy), with no distortion from the compo's aspect ratio. Nested groups give forward kinematics (hip > knee > ankle):
  build every part in its rest pose and put each joint's pivot on its group.
- A translated group still draws children placed **outside** the 0-1 frame (no clipping): a group holding several copies
  of a decor tile, moved by exactly a whole number of tiles, scrolls in a seamless loop.
- `compo.layers[0]` is the bottom layer, and the same inside a `GroupLayer`.
- A solid layer = `TextureLayer` + `UniformTextureGenerator` (fills the compo). Sized rectangle: on `renderer.placement`,
  `getVariableByName("scale").set(Oil.createObject("SizePlacement2dScale"))`, then `scale.size` in compo fractions
  (`linked` False first) and `position`; not reset after insertion, unlike shapes. Rotated, its edges look like a shape's.
- `GroupShapeGenerator` (`shapes` vector, each sub-shape with its own `placement`) also gets its sub-shapes reset to
  500 px after insertion. `edgeLength` is recomputed by the engine (a written value is overwritten a few frames later).

### Render cost (R15, 30/10/2026, RTX 4090 Laptop, compo 1920x1080 at 60 fps)

Measured by toggling layers while the timeline plays (`engine.status.frame.rate.toString()` = `"35.09 ms / 28.5"`,
`frame.deltaTime` = frames skipped per render): **each shape costs ~0.14 ms whatever its size**, also when it is a
sub-shape of a `GroupShapeGenerator` (merging does not help) or drawn in a small sub-compo; a solid layer costs
~0.03-0.07 ms; a `GroupLayer` almost nothing. With 160 shapes the frame went to 35 ms (30 fps, choppy playback).
- When nothing is animated (timeline paused) nothing is re-rendered: 60 fps whatever the content. While playing, a static
  sub-compo is still rendered every frame; a `FreezeTextureModifier` on it does not stop that. `Compo.baker`
  (`CompoBaker`, `SceneBaker`) is not a texture cache.
- Fix that worked (160 shapes -> 30 shapes + 30 solids, 35 ms -> 16.7 ms): rectangles as solid layers, and every
  repeated motif drawn ONCE in a tile `Compo` (custom resolution = tile size) shown N times by a
  `GroupTextureRenderer` on its `TextureLayer` (`renderers.append(SingleTextureRenderer)`, each with its own
  `placement`; default scale = 100 % of the texture's pixels). Shapes crossing a tile edge are repeated on the other
  side (shift of one tile) so the copies join.

## CRT screen look: bloom, barrel warp, scanlines, vignette (R15, 31/10/2026)

Built for a fake-OS animation (see `os_anim_crt.py` pattern), all on `compo.modifiers` / top layers:
- **Bloom is a style of the blur**, not a class: `BlurV8TextureModifier` with `style.blendingModeWithInput.set(12)`
  (linearDodge), `style.luminosityThreshold` (0.30), `style.outputLuminosity` (1.4 = 140 %), `radius` 16. The blur has
  no `blendingMode` of its own; `style` (`BlurStyleParameters`) also holds `aggregator`, `invertBlendingOrder`,
  `maskInterpretation`.
- **Barrel / pincushion distortion = `WarpTextureModifier`** (mesh warp, `points` = `OwnedVector(Warp2dPoint)`, each with
  `position` and `delta`, both `Canvas2dPosition` in compo fractions; `precision.x/.y` = subdivisions, `editSource`,
  `perspectiveMapping`, `filtering`). A new Warp starts with the 4 corner points. **Do `points.clear()` first and append
  the grid ROW BY ROW** (leaving the 4 default corners at the head of the vector tears the mesh). 9x9 points with
  `delta = (0.5*u*K*r2, 0.5*v*K*r2)`, `u,v` in [-1, 1], `r2 = u*u + v*v`: **K < 0 = barrel** (edges pulled in, black
  corners), K > 0 = pincushion; K = -0.05 reads as a CRT. Set `editSource.set(False)`; after `modifiers.append(w)` a
  toggle `w.activation.set(False)` then `set(True)` was needed before it rendered. Put it LAST so it bends the bloom and
  the overlays too.
- **Scanlines**: `CheckerBoardTextureGenerator` with `size.linked = False`, `size.width = 4000` (one column), `size.height = 3`,
  `evenColor` alpha 0, `oddColor` black alpha 0.35, on a top `TextureLayer`.
- **Vignette**: `GradientTextureGenerator` (`type` `Circular2dGradient`, `gradient` `BitoneColorFunction`): `beginColor`
  alpha 0 -> `endColor` black alpha 0.95; the circle is `position` (`Ellipse`: `center`, `size` in **pixels**, `rotation`),
  2600 x 1600 on a 1920 x 1080 compo (`size.linked = False` first). `renderer.blendingMode` of a `TextureLayer` is not a
  plain enum (`toString()` = `BlendingMode()`): keep the Normal mode and use alpha.
- **`clear()` on a built scene crashes Smode** (31/10/2026, twice): `comp.layers.clear()` + `comp.modifiers.clear()` on a
  Compo holding 100+ layers and a Warp. Rebuild from an empty Compo instead. **Emptying a standalone Compo document (no Scenes to drop) works with `removeAt`, one element at a time** (R15, 31/10/2026, 13 nested layers + Warp + Bloom + a script, no crash): `tools.removeAt(i)` for the script, `modifiers.removeAt(0)` twice, then `layers.removeAt(names.index(name))` from the top down; the timeline tracks of the removed layers disappear by themselves (0 left). **A script that caches layers in `globals()` must key its cache on the script object itself** (`c_ is script`), not on the Compo: after emptying and rebuilding in the same document the Compo is the same Python object, so the cache kept 148 stale (destroyed) layers.

## Timeline-first animation: sub-Compos as animatable "windows" (R15, 31/10/2026)

Built for a 30 s fake-OS animation where every move must be a key the user can edit (no script-driven motion):
- **`GroupLayer` has no opacity** (only `placement`, `layers`, `tools`, `worldMatrix`). To fade/move/scale a set of layers
  with keys, put them in a sub-`Compo` (custom 1920x1080 `rasterizer.resolution`, `preset.set(40)`) shown by a
  `TextureLayer` (`generator = subCompo`): `renderer.opacity`, `renderer.placement.position/anchor`,
  `scale.scaleFactor.width/height` are all keyable. Sub-Compos nested in a Compo **document** render without any target.
  Windows = a wrapper per window; scale about the window centre by setting `anchor` = `position` = centre (fractions of the
  texture = of the compo) and `scale.scaleFactor.linked = False`, then key width then height ("line opens, then window").
- **Keys by `tc.createKeyframe(param, seconds, False)`** work on parameters of layers nested in sub-Compos
  (`tc` = the document's `mainAnimation`), on `TextureLayer.renderer.opacity`, `placement.position.x/.y`,
  `scale.scaleFactor.width/.height`, `scale.size.width` of a solid layer, and on the **declared parameters of a
  PythonScriptTool** (`tool.dynamicVariables[i]`, declaration order, `Oil.Percentage`). 586 keys / 35 tracks created in one call.
  `Step` (default) interpolators make jitter/blink; `Linear`/`Ease` via `kf.linkInterpolators.set(False)` +
  `getVariableByName("inputInterpolator"/"outputInterpolator").set(Oil.createObject("EaseKeyframeInterpolator"))`.
  A step track holds its FIRST key's value before it: add a key at t = 0 with the rest value.
- **Text cannot be keyed** (strings). Pattern: the script declares `Progress` parameters (0..1), keyed on the timeline
  (two keys per typed line: start and end time, value = typed characters / total); the script only does
  `text[:int(progress * len(text))]`. Typing speed/pauses are then edited as keys. Keep ambient motion (bars, gauges, clock)
  in the script only if it is not something the user must retime.
- Keys are evaluated **only while the timeline plays** (or when the playhead is moved in the UI): to check a frame from the
  bridge, `transport.position.set(t - 0.25)`, `play.trig()`, wait ~250 ms, grab the screen, `pause.trig()` (real position
  read back; +-0.4 s). Apply the clone fix (`mainAnimation.set(mainAnimation.clone())`) in a later call.
- **Compo blocks on the timeline = the organisation rule** (31/10/2026): give each top-level object its own block (`tc.createBlock(layer)` -> `(track, block)`; `block.autoLength.set(False)`, `block.position.set(s)`, `block.length.set(s)`) covering only the time it is needed: the layer is displayed only inside its block, and the timeline reads like a file tree (13 tracks for the fake-OS compo). Skip layers that already have a track (`for k, tr in tc.elementTracks.items(): k.get()`), as the user may have placed blocks by hand; then apply the clone fix in a later call (all 13 tracks and 35 parameter tracks survived). **Any animated element gets its block, nested ones included**: `tc.createBlock(layer)` accepts a layer deep in sub-Compos (e.g. `Boot Logo/Progress Bar/Bar Fill`, `Desktop/Icon Network/Highlight`, `Window Terminal/Content`); 20 element tracks in the fake-OS compo, the block spanning the element's keys. Several nested layers can share a label (3 `Highlight`): identify tracks by the layer object, not the label.
- Parameters of a script can be read by `getattr(script, name)` (returns a `Percentage`, `.get()`).

## Project organisation: "folders" in the tree and the timeline (R15, 31/10/2026)

Convention used for the fake-OS compo (and the rule to follow for any Smode project built by script). A sub-`Compo` shown by a
`TextureLayer` is the "folder" of the Elements tree; a leaf layer is a "file". `layer.label` and the sub-Compo's `label` carry the same
readable title-case name (`Icon Network`, never `IC1_G3`).
- **One object = one folder**: an icon, a gauge, a progress bar, a window frame each get their own sub-Compo, containing only their own
  leaves with generic readable names (`Border`, `Background`, `Highlight`, `Glyph 1..n`, `Label`, `Track`, `Fill`...).
- **Tree of the fake-OS compo** (13 top-level entries):
  ```
  Boot Log                         Window Terminal / Window Network / Window System
  Boot Logo                          |- Frame    (Border, Background, Title Bar)
    `- Progress Bar (Border,          `- Content  (Title Text + Terminal Text | Traffic Label, Traffic Bars [Bar 1..24,
       Background, Fill)                          Baseline], Hosts Text | Gauge CPU/Memory/Link [Track, Fill, Gauge Name],
  Desktop                                        Info Text)
    |- Grid (Vertical/Horizontal Line n)
    |- Scan Line
    |- Top Bar (Background, Line, Left Text, Clock)
    `- Icon Terminal / Network / System / Archive (Border, Background, Highlight, Glyph n, Label)
  Cursor (Crosshair Horizontal/Vertical, Cursor Point) | Alert Denied / Granted (Band + text) | Glitch Bars
  Fade To Black | CRT Scanlines | CRT Vignette
  ```
  Order = Elements-panel order = draw order (first = bottom). Modifiers (`Bloom`, `CRT Curvature`) and the script sit beside the layers.
- **Timeline mirrors the tree**: one block per top-level folder, plus one block for every nested element that carries keys
  (`Bar Fill`, the 3 `Highlight`, the 3 `Content`): 20 element tracks, each block spanning the period where the element is needed (see the
  block rule above). `tc.elementTracks` is a flat `Map` keyed by layer: the nesting is NOT stored there, only in the Compo tree, so
  identify a track by its layer object (`k.get()`) or by the full path `Window Terminal/Content`, never by the label alone.
- **Script lookups by path, not by code**: register every layer under its full path and its last two names (`"Icon Network/Glyph 1"`,
  `"Content/Terminal Text"`) while walking `compo.layers` -> `layer.generator.layers` for sub-Compos; build-side helper
  `at("Desktop/Icon Network/Highlight")` descends the same way.
- **Verified in the UI (31/10/2026): the Timeline panel shows the tree, collapsible.** Nested blocks are listed under their parent
  (`Desktop` > 3 `Highlight`; `Window Network` > `Content`), a block expands to the element's sub-elements, and each keyed parameter
  (`Opacity`, `Position -> X/Y`, `Scale -> Scale Factor`...) is a row **under the element it animates**, with its keys as diamonds in
  the lane. Hovering a row gives the full path (`Simulation OS Timeline -> Desktop -> Icon System -> Highlight`), which is how to tell
  apart layers that share a label. So the tree convention above carries over to the timeline for free: a well-named folder
  structure is a well-organised timeline. (The `elementTracks` `Map` itself stays flat; the nesting is rebuilt by the panel from the Compo tree.)

## Old TV in Smode: FBX import, emissive screen, simulated screen light (R15, 31/10/2026)

Built from a Blender FBX (`Apply Transform`, `FBX_SCALE_ALL`: metres, Y up) for a Compo document ("Old TV retro").
- **`subGeometryToUse` addresses a node by its PATH**: `"Old TV Root/TV Body"`, not `"TV Body"` (a bare node name leaves the
  generator in `error: could not retrieve the file information (have you deleted your file?)` although the file is found and
  `Scene3dFile.meshes` / `.vertices` read right). An empty value is shown as `<ALL>` (the whole file). The valid choices are not
  listed by the API (`StringWithChoices` has only `get` / `set`); `Scene3dFile.importAsGroup3dLayer` needs two arguments
  (`group3dImporterClass`, `targetParent`) we could not guess. The `Scene3dFile` of a node with a parent Empty needs the parent in the path.
- **Media Directory path** works for FBX and images: `"Smode Files/Old TV retro/old_tv_v02_textured.fbx"` (copy the files into a
  sub-folder of the Media Directory, folder list in `%APPDATA%\Smode Compose\configurations\Data_15_9.configuration`); `reload.trig()`
  after a fresh copy. Portable, unlike an absolute `G:\...` path.
- **No PBR when only the albedo matters**: a plain `SurfaceGeometryRenderer` with the Diffuse component only (`components.removeAt(1)`
  drops the Specular one). **Emissive-only surface** = that material with `autoIlluminate.set(1.0)` (it is a PERCENTAGE: 1.0 = fully
  self-lit, the surface ignores the lights). `PBRSurfaceGeometryRenderer` has `albedo` / `roughness` / `metallic` / `emissive` / `normal`
  / `occlusion` as `OwnedPointer(Colorizer3d)` (`Uniform3dColorizer`, `Gradient3dColorizer`, `Texture3dColorizer`) but
  `Texture3dColorizer.texture` takes a volumetric `Texture3d` (default `CheckerBoard3dTexture`): **no UV image colorizer was found**,
  so image PBR maps cannot be wired by script this way.
- **Sharing an animated compo**: a `ReferenceTextureGenerator` pointed straight at a compo (`location` 1 + `directPointer`) renders a
  FROZEN frame (the one of its creation) and ignores the timeline. Use `SharedElement(Compo)` (tool of the compo, `content` set to the
  compo or a clone) and references with `address.location` 0, `address.elementPointer.set(se.getVariableByName("content"))`,
  `referencer.shared` True: the status says "Parameters are shared across all shared references" (expected). The compo is
  then evaluated once, driven by the main-timeline block of the layer that references it, and the layer, a material map and a light map
  all show the same animation. After changing a material, `layer.renderer.referencer.reloadInstance.trig()` on the geometry layer.
- **Hiding a driver layer**: a layer whose block must drive a shared compo cannot be hidden by `activation.set(False)` or
  `renderer.opacity.set(0)` (the block re-activates it / resets it); park it off-screen with `renderer.placement.position.x.set(6.0)`.
- **Emissive textures do not light the scene in Smode**: simulate the glow with a `PointLight` placed just in front of the glass and
  `directionalMap = EquirectangularDirectionalMapGenerator` (`generator` = a compo of 2048 x 1024 = 360 x 180 deg, `orientation`
  `EulerAngles`) in which the texture sits in a cone (170 deg wide, 4:3, plus a dim ochre base colour of the map background so the
  parts at grazing angles still glow). `orientation.y = pi` points the map forward (+Z, the TV faces +Z in Smode after the Blender
  conversion). `attenuation.interval` defaults to (5 m, 10 m): no falloff nearby. A glow barely lights a surface coplanar with the
  glass (grazing angle): the knobs, grille and antenna catch it, the cabinet front hardly does; intensity 8 on a mostly dark UI texture.
- Other class names found: `PointLight.directionalMap` types `UniformDirectionalMapGenerator`, `EquirectangularDirectionalMapGenerator`
  (`generator`, `orientation`, `mirror`, `cylindricalDistort`, `topSmoothing`, `bottomSmoothing`), `ReferenceDirectionalMapGenerator`.
- A Compo document that becomes a "project" by saving under a new name keeps being a **Compo** for the bridge (`script.project` does not
  exist): `engine.content.customContent.get()` is the open document (`is script.parentElement` is True).

## Particles (R15, 31/10/2026)

- **`.compo` files use "Node" where the Python API says "Geometry"**: `ParticlesNodeGenerator` = `ParticlesGeometryGenerator`,
  `SpritePointsNodeRenderer` = `SpritePointsGeometryRenderer`, `PointAttributesNodeModifier` = `PointAttributesGeometryModifier`,
  `AgeVertexMask` = `AgeGeometryMask`. `createObject` fails on the file names. Other classes keep their name: `GravityField`,
  `TurbulenceField`, `AttractorField`, `VortexField`, `EventParticleRule`, `PlanePositionSampler`, `LinePositionSampler`,
  `PointPositionSampler`, `RandomDirectionSampler`. The official examples are plain text in
  `<Smode>\packs\Features\Particles\*.compo` (field, rule, sprite, collision, colorize examples): the fastest way to learn a setup.
- Structure: `GeometryLayer` with `generator = ParticlesGeometryGenerator` and `renderer = SpritePointsGeometryRenderer` (direct
  assignment). Generator: `emissionParameters` (`rate`, `lifeTime`, `speed`, `initialCount`, `preSimulationQuality`, `maximumCount`,
  `particlesCount` = live count, read only), `fixedUpdateRate` (`.enabled`, `.value`; the examples enable it at 60), `positions`
  (a sampler), `fields` and `rules` (OwnedVectors), `modifiers`. Renderer: `maps[0]` is already an `ImageFileTextureGenerator`
  (`.file.path.set("Standard Pack/Texture/Particle/Dot White b.png")`), `size.objectSpaceSize.width/height`.
- Fade by age: `PointAttributesGeometryModifier` with `selector = AgeGeometryMask` and `opacity` = a `KeyframeFunction`
  (`.keyframes`, each with `.position` 0..1 = age and `.key` = value; clone a key and `append` to add one).
- **The generator has its own transport, a `StandalonePlayer` (`generator.transport.player`), not tied to the main timeline.** No
  block on the main timeline is needed (do not add one for a particle system). Parameters: `launchMode` restartWithActivation,
  `automateTransport` true, `looping`, `speed`, `targetLength`.
- **TRAP: the player that comes with a script-created generator never starts.** `transport.state` stays `finalized`, position 0,
  `particlesCount` 0, even after toggling `activation`, `transport.reset.trig()` or `transport.play.trig()`, while the same setup
  built in the UI runs. Fix, tested: `t = generator.transport; t.player = Oil.createObject("StandalonePlayer"); t.play.trig()`
  (state `ready` right after the assignment, `playing` on the next call: 195 particles at 1.95 s). Doing "remove standalone" and
  adding the player back in the UI also works. Check with `transport.state` / `transport.position` in a LATER call.
- Fields: `GravityField.force`, `TurbulenceField` (`intensity`, `forceStrength`, `positionStrength`, `velocityStrength`, `noise`,
  `curlNoise`, own `transport`), `AttractorField` (`position`, `power`, `disperser`), `LorenzAttractorField` (`center`, `scale`,
  `rho`, `sigma`, `beta`, `positionStrength`), `VortexField` (`strength`, `attraction`, `attenuation`, `placement`), `FrictionField`
  (`coefficient`). All have `intensity` and `masks`.
- **Update of the player trap**: `transport.play.trig()` in the SAME call as the player assignment leaves the state at `ready`; trigger
  it in a LATER call. Moving the layer into another compo (UI) puts the player back to `ready` / count 0: same fix. Values read inside one
  call are frozen: sample over several calls.
- **Rules and groups** (confirmed by the user, 03/11/2026): an `EventParticleRule` = `condition` + `groupFilter` (`.enabled`, `.value`; the
  `[n]` shown in the UI) + `actions`. Conditions: `AgeParticleCondition` (`threshold` 0..1), `CollisionParticleCondition`
  (`collidables`), `NullParticleCondition` (always true: use it to apply an action per group). Actions: `BounceParticleAction`
  (`restitution`, `friction`, `traversalChance`), `EmitParticleAction` (`numParticles`, `lifetime`, `speed`, `directions`,
  `inheritParticleSpeed`, sub-`actions`), `ColorizeParticleAction` (`color`, an `HsvColor`), `ChangeGroupParticleAction` (UI name
  "Increase Group by"; `value`, `incremental`). **The group only changes through `ChangeGroupParticleAction`** (not implicitly), and an
  `EmitParticleAction` needs it in its own `.actions`, otherwise the emitted particles stay in the parent's group and trigger the same
  rule again (loop). One group per generation (tree, cascade); colour per group = `ColorizeParticleAction` under a `NullParticleCondition`.
- **Two families**: a particles generator layer (simple emitters: plane / line / point samplers) or an
  `EmitParticlesGeometryModifier` on any 3D object (same `emissionParameters`, `fields`, `rules`, `fixedUpdateRate`, own `transport`).
  Its `operatorMode` (`GeometryOperatorMode`, an "Advanced" parameter in the UI): 0 replace, 1 append, 2 prepend; **replace swaps the
  incoming geometry for the emitted particles** (the generator's own trace vanishes), append keeps both.
- Limits: `rate` x `lifeTime` has to stay under `maximumCount` (1e6): a `rate` of 1e10 gave `particlesCount` 0. Renderers: `SpritePointsGeometryRenderer`,
  `SimplePointsGeometryRenderer` (`size` in px, the lightest), `ThickLinesGeometryRenderer`. `MotionLinesGeometryModifier`
  (`steps`, `limitLength`, `maximumLength`) draws the PAST PATH of each moving particle; `ConnectPointsGeometryModifier` is a proximity
  graph (every neighbour inside the distance window), not a polyline: very heavy (4 fps at rate 6000, 1 mm). For a continuous trace use enough
  particles and a sprite larger than the spacing.
- Keys added with `clone()` + `append()` on a `KeyframeFunction` ended up out of position order (0, 1, 0.5) and only the middle colour
  showed; sorting them by position fixed it (not confirmed on screen). Colour per group is more reliable.

## 3D masks and fragment effects (R15, 03/11/2026)

- `renderer.effects` can hold `GeometryMaskDiscardFragmentModifier` ("3D Discard": `invert`, `threshold`, `masks`; binary, `invert` makes a
  hole in the mask volume) and `GeometryMaskAlphaFragmentModifier` ("3D Alpha": `masks` only, multiplies the alpha by the mask value: soft).
- Masks: `BoxGeometryMask` (`size`, `placement`, `exponent`, `roudness`, `roudnessRadius`), `SphereGeometryMask`, `CylinderGeometryMask`
  (`capsulify`), `LinearGeometryMask`, `NoiseGeometryMask` (own `transport`), `FresnelGeometryMask` (`exponent` 5, `ratio` 1; uses the
  normals, poor on a very deformed mesh), `RandomGeometryMask`, `FunctionGeometryMask`, `TextureLayerGeometryMask`, `ColorGeometryMask`,
  `AgeGeometryMask`. No explicit feather: `exponent` softens the edge (0 = hard edge, confirmed by the user).
- `Displace` moves vertices along their normals (a cube's faces separate); `Transform3d` + a mask (noise) modulates the strength of the
  transform per point. Several copies of one compo: a `GroupTextureRenderer` holding N `SingleTextureRenderer` redisplays ONE compo render.

## Function cues: automatic animation without the main timeline (R15, 03/11/2026)

- UI: right-click the PARAMETER to animate: Smode creates the right `FunctionCue` (type `Meters`...) already linked, min/max in the parameter's
  unit, `launchMode` restartWithActivation (starts alone). The element menu (Animation > Footage Cue / Timeline / control cues) does not offer them.
- Script: `Oil.createObject("FunctionCue(Meters)")` (bare `FunctionCue` is abstract), `cue.function = Oil.createObject(
  "ParametricScalarFunction(Seconds, Meters)")` (`None` by default), `function.shape = LinearRampFunctionShape | NoiseFunctionShape`
  (`frequency` 10, `contrast`, `type` 0 simplex / 1 perlin), `function.parameters` (`minimum`, `maximum`, `period`, `phase`, `offset`,
  `wrapMode`, `repetitions`), `cue.parameters` (`looping`, `targetLength`, `speed`, `launchMode`), `animationBank.animations.append(cue)`,
  `cue.targets.append(ParameterLinkTarget)` with `.target.set(param)`, then `cue.transport.play.trig()` in a later call.
- **Linear ramp needs `phase` = 0.5**: it then starts at `minimum` and goes min -> max in one `period`; with phase 0 it started mid-range at half
  slope (measured on the real output; reading the parameters back proved nothing). `wrapMode` 1 repeat = abrupt return (scope flyback).
- A linked `Parameter` does NOT forward to its own targets when a cue writes into its `.value` (the link only reacts to UI changes): link the cue
  straight to the final target. `timeline.parameterTracks` is a Map (`.items()`, no index): neutralise a track with `function.keyframes.clear()`
  + `activation.set(False)`.
- Range mapping: `RemapLinkModifier` (`inputRange`, `outputRange` = `Interval(Real)`) in `ParameterLinkTarget.modifiers` (tested: output 0.5..0.5 freezes
  the target); `FunctionLinkModifier(Percentage, Meters)` can be created with its types in brackets. A cue in the target's own unit is simpler.
- A 4 m high frame: `AffineCamera` at distance 3.4641, vertical fov 60 deg (1920x1080): 25 % from the top = +1 m.


## Multiplying particle systems: shared element, Instantiate, point renderers (R15, 03/11/2026)

- **Shared element**: the particles generator can live in a `SharedElement(GeometryV9Generator)` (in `compo.tools`, `.content` = the
  generator) and the layer uses a `ReferenceGeometryV9Generator` (`.referencer`: `address`, `shared` True, `localElementSpace`,
  `reloadInstance`; its own `modifiers`). The simulation is computed once; cloning a reference works (status success; `directPointer`
  stays `None`, the location is `internalIndirect`).
- **`InstantiateGeometryModifier`** (Operators): `generators` (OwnedVector, references allowed), `referential`, `selector` (a
  `RandomGeometryMask` picking which generator goes to which vertex), `masks`, `intensity`. **One copy per vertex of the incoming geometry**:
  `SegmentGeometryGenerator.precision` n gives n+1 vertices (precision 3 = 4 particle systems, confirmed), a `PlaneGeometryGenerator`
  `precision` (`Precision2d`, `uniform` False before `x`/`y`) gives (x+1)(y+1). `referential` (`ReferentialChoice`: 0 vertex, 1 world,
  2 camera, 3 sphericalCamera) is the ORIENTATION frame of each copy, not its position: with `vertex`, moving the last point of a segment
  rotates the frame. A new Instantiate already holds a default `BoxGeometryGenerator` in `generators`: `removeAt(0)`.
- **"No Lines Adjacency information in geometry"** (red cross on the layer): a `ThickLinesGeometryRenderer` on point geometry (particles). Use a
  `SimplePointsGeometryRenderer` (`size` in px, the lightest) or add a `MotionLinesGeometryModifier` after the Instantiate (status turned to
  success; not judged on screen). The error hid the fact that the per-vertex instancing worked.
- `DemultiplyGeometryModifier` (`instances`, `strength` in m, `differentiation`, `interval`, `noise`, own `transport`) duplicates the geometry N times,
  offset by noise: 100 copies of 10 000 points in point rendering stayed light.
- **Emission direction**: `TargetDirectionSampler` (`target`, `spread`) shoots every particle toward a point (default 0,0,0): a stream of particles
  from the layer's position toward the target. The emitter position = the layer placement (+ the sampler placement). A `TurbulenceField` has NO
  position: it fills the space (curl noise, `noise.scale` = feature size). `positionStrength` moves the particles directly (visible);
  `forceStrength` 356 with speed 10 showed nothing because the particles leave a 4 m frame in a fraction of a second. Whether
  `AttractorField.position` is local or world is not tested.
- Validated look (user: "very beautiful"): plane 4.46 x 2.4 m, precision 50 x 50 (2601 vertices), 3 references to 3 colour variants picked by
  the random selector, shared system rate 1000 / lifeTime 2 / speed 0.2 / turbulence (force 100, position 1, velocity 1) / colour and opacity by age
  / 4 rules, about 5 million points in `SimplePointsGeometryRenderer`, feedback + blur on the compo (not measured in fps).

- **Filling a shape (text) with instances: mask BEFORE the Instantiate** (validated by the user, who rebuilt it by hand). On the plane, put a
  `RandomPointsGeometryModifier` (`count`, `seed`, `masks`, `operatorMode`; the official example is "Random Points Modifier (on a Plane)") with a
  `TextureLayerGeometryMask` in ITS `masks` (`generator` = a copy of a sub-Compo holding a text layer; it accepts a `Compo`), then the
  `InstantiateGeometryModifier` after it (`modifiers.insert(0, randomPoints)`). The points land only inside the letters and each gets one
  system. Putting the same mask on the Instantiate's own `masks`, or a 2D `MaskTextureModifier` (`TextureLayerTextureMask`, `ChannelColorSelector`
  channel 1 luminance + `multiplyByAlpha`) on the compo, works but only crops the picture: long strands drown the letters. No "delete points by
  mask" modifier exists in the examples; Random Points + mask plays that role.
- Keep the strands shorter than a letter stroke (`lifeTime` ~0.5, lower turbulence `positionStrength`); a plane stood up facing the camera
  is rotated 90 deg around x. **Animating the `seed`** with a `FunctionCue(PositiveInteger)` (ramp 0..205 over 3 s, speed 0.08, looping, target =
  `randomPoints.seed.value`) re-sows the points inside the letters: the strands "grow back" (not seen by Claude, reported by the user).
- Geometry modifiers found in the official examples: Repeat, Transform3d, Displace, Colorize, ColorizeFunction, Instantiate, Scale, ScaleFunction,
  UVTransform, UVCameraMapping, Rotate, ExtrudeShape, Mirror, Opacity, SolidifyPath, EmitParticles, PositionNoise, PointAttributes, RandomPoints,
  Quantize, ColorizeTextureLayer, TransformTriangles, ConnectPoints, Group, Compute, MotionLines, Demultiply, Spherify.

## Particles: text of sand, bank links, reading errors (R15, 05/11/2026)

- **Reading a full error message**: `obj.liveStatus.toString()` is truncated (`error: Ran...`); `obj.liveStatus.success.toString()` returns the whole
  text. This is how the next point was found.
- **`TextGeometryGenerator` is an outline (spline), not a surface**: an `EmitParticlesGeometryModifier` on it fails with "Random emission is not
  implemented in geometries of type Text Spline Geometry". To emit from a word: `PlaneGeometryGenerator` -> `RandomPointsGeometryModifier` with a
  `TextureLayerGeometryMask` (`generator` = a `Compo` holding a `TextLayer`) -> `EmitParticlesGeometryModifier` (`operatorMode` replace) ->
  `PointAttributesGeometryModifier` (opacity by age). All statuses success, grains produced.
- A `Compo` made with `Oil.createObject("Compo")` has a **0 x 0 resolution**: set `processor.resolution.linked` False, then `width` / `height`
  (1920 x 1080) before using it as a mask source. `LocalTextGenerator`: `text` (default "SMODE"), `style.size` (px), `style.bold`,
  `style.foreground` (`HsvColor`, `red`/`green`/`blue`).
- **Sand blown away** (checked on screen): grains emitted in a burst (`rate` 50000 then 0 by a Step key at 0.6 s), `speed` 0, `lifeTime` 9 +- 1.5,
  `SimplePointsGeometryRenderer`. **A `GravityField` used as wind is a UNIFORM force: every grain leaves as one block.** The gradual break-up comes from
  a `TurbulenceField` with a small-scale noise (`noise.scale` 0.25 m, `octaves` 2, `forceStrength` 24, `positionStrength` 1.0) plus a weak wind and a
  `FrictionField`: the word crumbles from the top, then spreads into a cloud. Fields' `intensity` is keyable (Linear ramp 3 -> 5 s).
- Timeline of such a system: `createKeyframe` on `emissionParameters.rate` (Step holds the value), on each field's `intensity`; a layer block of 12 s in
  a loop restarts the emitter (`restartWithActivation`) at every turn. To replace tracks: `elementTracks.clear()` and `parameterTracks.clear()`
  FIRST, then remove the layer. Jumping inside the loop after the emission window shows an empty screen (the grains are only emitted in the first 0.6 s).
- **Bank links**: `Parameter(Trigger)` -> `manualEmit.emitNow` works (a Kick emitted 1601 particles); a reversed `RemapLinkModifier` range (begin > end)
  collapses to a single value, use begin < end with `inverse` True; the links of a new bank only apply after `parameter.applyNow.trig()`;
  a stepped palette = `FunctionLinkModifier(Percentage, Angle)` whose `KeyframeFunction(Percentage, Angle)` starts with 0 keys (create
  `Keyframe(Percentage, Angle)` objects by hand, Step by default) driving a `HueSaturationLuminanceTextureModifier.hue` placed FIRST in the compo effects.
- **Seeing the render**: the viewport can be captured (see "Checking visually"): two PowerShell scripts (window rectangle + `CopyFromScreen`: one single capture, and a
  contact sheet of the viewport at a fixed interval, refusing to capture if Smode is not on top); the Smode window can sit at negative coordinates (-8,-8).
- A 4-system VJ set (MotionLines + feedback + blur at 1080p, four systems running at opacity 0) ran at about 10 fps on the author's machine (reported, not
  measured by script): check the ms / fps in the status bar before keeping such a set.

## Multi-video ISF shaders, bank states, data textures (R15, 05/11/2026)

Verified while building a real-time datamosh: one `IsfFileTextureModifier` receives two clips and their vector videos, at 60 FPS.

**Variables of an ISF modifier**
- `mod.dynamicVariables` gives the inputs; the useful name is `d.getFriendlyName()`, the shader's `LABEL` with capitalised words (`Pulses Per Measure`).
  `{d.getFriendlyName(): d for d in mod.dynamicVariables}` gives access by name.
- **An image input is an `OwnedPointer(TextureGenerator)`**: `dv["Clip B"].set(video)` accepts a `VideoFileTextureGenerator` created by script.
- **Plugging a video adds a `Transport` dynamic variable** (`StandalonePlayableCueTransport`) to the list. To save and restore settings, filter on `getOilClassName()`,
  otherwise `float(d.toString())` raises `ValueError`.
- Classes observed: `float` from 0 to 1 = `Percentage`, `float` with minimum 0 = `PositiveReal`, other `float` = `Real`, `bool` = `Boolean`, `long` with `LABELS` =
  `CustomEnumeration`, `event` = `IsfEvent` (`.trig()`).
- `Percentage`: `set(0.35)` but `toString()` returns `35.000` (divide by 100 when reading). `CustomEnumeration`: `set("Motion First")` by menu text, `toString()` returns that text,
  `.enumerators` lists the `CustomEnumerator` objects (`label`, `value`).
- Reinstalling the modifier (`removeAt` + new object) destroys its links: rebuild them a few frames later, once the variables exist.
- `TIMEDELTA`, `FRAMEINDEX`, `IMG_SIZE`, multiple passes and `PERSISTENT` work. The engine runs faster than the clip (60 Hz against 25 fps): to process each clip frame once,
  detect the change in a pass rather than rely on `FRAMEINDEX`.

**A data texture must have a gamma of 1**
- A video holding data (vectors, coded masks) is decoded as a picture: neutral 128 becomes about 0.22 and the shader sees a parasitic shift (37 px per frame on a +-64 px range),
  with no error. Set `video.gammaValue.enabled.set(True)` then `video.gammaValue.value.set(1.0)`.
- To store this data losslessly, `qtrle` (`.mov`, lossless, one pixel per 16 px block) worked.

**SMODE video warnings**: it warns on an MP4 source, on HAP with fewer chunks than threads / 4 (`-chunks 8` in ffmpeg for 32 threads), and on a codec outside its list (HAP, HAP Alpha,
Hap Q, HapR, ProRes, NotchLC). `qtrle` triggers this last warning, with no problem observed.

**Synchronised videos**: `reset.trig()` on every `video.transport` then `play.trig()` on every one, in the same execution: 4 streams with 0 frame of gap on each pair. A video created by script
needs `video.transport.player = Oil.createObject("StandalonePlayer")` then `player.parameters.looping.set(True)`.

**`ParameterBank` states** (`ParametersState`, tested on `Boolean`, `Percentage`, `Real`, `PositiveReal`, `CustomEnumeration`)
- `state.apply.trig()`, `bank.applyNext.trig()` and `bank.currentStateIndex.set(i)` apply a state and drive the linked targets. The official sample is
  `packs/Features/Misc/Parameters States.compo`.
- `bank.saveAsNew.trig()` captures every value of the bank, but leave frames before reading the new state in `bank.states`: 2 frames were enough.
- **Build the states before adding the links**: the capture then leaves the targets alone. Adding a link afterwards sends nothing until the `Parameter` value changes.
- **A link only sends changes**: writing directly to the target is not overwritten (seen over 1 s, and different from the script variable case, see the Scripts section), but re-applying a state whose value already
  equals the `Parameter` restores nothing. Also write to `p.value`, or fire `p.applyNow.trig()` (tested: the value goes back to the target).
- **Trap: never link a `Parameter` to a shader menu (`CustomEnumeration`) (corrected 12/11/2026).** A `Parameter(CustomEnumeration)` with no choices empties its
  target's menu. Filling `p.value.enumerators` (`c = Oil.createObject("CustomEnumerator")`, `c.label.set(...)`, `c.value.set(...)`, no `clone`) does not hold:
  **SMODE does not save these choices in the compo, only the text value.** On reopening, the bank has an empty menu and its link empties the shader's.
  A linked `Parameter(Integer)` or `(Real)` also empties the menu on its first value change. Once the menu is empty, the input still shows its text
  (`toString()` returns "Tempo") but the shader receives 0, with no error at all. Only recreating the modifier brings the menu back. Validated workaround: an
  unlinked `Parameter(Integer)` whose position a Script copies into the menu by its text (`d.set("Tempo")`), reading the bank only once a second.
- A bank survives the recreation of the target modifier, states included: clear `p.targets` and rebuild the links.
- Firing a state from a timeline was not tested.

**Tempo, audio, measurements**
- `TempoTool` (in `compo.tools`): `tempo`, `tap`, `resync`, `positionInMeasure`. A `Link` (`ParameterLinkSource.target` = `positionInMeasure`) to a `Percentage` input gives the shader
  its position in the measure.
- Other `TempoTool` properties: `beatsPerMeasure` (length of the measure, hence of `positionInMeasure`), `speedMultiplier`, `beatDuration` (ms), `positionInBeat`,
  `beatCount`, `tapCount`, `timeValue`. `positionInMeasure.toString()` returns a percentage (`34.667`).
- `AudioSpectrumLinkSource`: `extractor.audioChannel`, `extractor.frequencyInterval`, `extractor.amplitudeInterval`, `method`, to send a band (kick) to a parameter. Wiring verified, not the result on real sound.
- `engine.status.gpuConsumption`, `.cpuConsumption`, `.frame.rate.toString()` (`16.67 ms / 60`) read the load by script. The GPU reading is noisy, with isolated spikes.

**Web interface of a Script** (adds to the dedicated section)
- Changing `sourceCode` or the version restarts the server: an open page misses a request. Do not leave a network error on screen forever: clear it after a few seconds, and reload the page
  when the version returned by the API changes.
- `ThreadingHTTPServer` with its default queue: 0 failures at 6 and 20 parallel requests, 49 refused out of 600 at 60 in parallel.
- A `data:image/svg+xml` favicon in the `<head>` works with no extra route; check it at 16 px.
- **Sliders**: a drag sends about 60 values a second, and a round trip to the Script takes about 90 ms. Sending them all left SMODE 0.33 s behind the hand.
  One request in flight per parameter, with the latest value waiting behind it, brings this down to 0.08-0.20 s. Sending every 50 ms without waiting for the
  answer was worse (up to 0.44 s). Update the field's display locally, not at the next poll.
- Defaults of an ISF shader for an interface: read the JSON header (`/* ... */`). The name SMODE shows is the `LABEL` with each word capitalised
  ("Pulses per Measure" becomes "Pulses Per Measure", "(s)" stays as it is).

**Standard Pack**: `packs/Standard Pack/ISF/Stylize/Glitch/` holds `FastMosh` and `Feedback Mosh`; `ISF/Color/Masking/Optical Flow Generator` and `ISF/Distort/Distortion/Optical Flow Distort` also exist.

## A "plugin" Script: shared globals, document, shared videos (R15, 12/11/2026)

Verified while turning a Script into a plugin dragged alone into any compo (real-time datamosh).

**Scripts and documents**
- **All Scripts share the same Python globals, even across documents** (verified: a variable set by one Script is read by another). Two copies
  of the same Script, or two versions, overwrite each other's functions and state. Remedy: run the code in a dictionary of its own per version
  (`exec(compile(code, ...), space)`, passing `Oil` and `engine` in) and keep one state per tool.
- Oil wrappers are stable: `script` is the same Python object from frame to frame, so `id(tool)` and `is` identify a Script.
  `tool.getUniqueIdentifier()` on a `PythonScriptTool` raises `TypeError` (`juce::Uuid` cannot be converted).
- **SMODE only runs the Scripts of the document in front**: a bridge left in a compo in the background stops answering (504).
- A Script dragged into the tools starts with `launchMode` `manual`. After `sourceCode.set`, its `dynamicVariables` are filled only once the call
  has returned (a `KeyError` on their names in the same call).
- **Path of the document**: walk up from the Script (`tool.parentElement`, then `.parent` for a Compo or a pointer) to the object of class
  `Document(TextureGenerator)`. `doc.nativeFile.toString()` gives the absolute path (`...\test datamosh2\test datamosh2.compo`), an empty string
  while it has never been saved; `doc.hasUnsavedChanges`; its parent is the `Unsaved Documents` or `Files` vector.
- **A deleted object, or one from a closed document**: touching it sometimes raises `RuntimeError('Access violation - no RTTI data!')`, but reading
  on every frame a `Parameter` just removed from its bank crashed SMODE (no Python exception). Never keep an Oil object cached without checking
  it still exists (here: read the bank again as soon as its parameter count changes).
- Autosaves `<doc>.versions\<doc>.compo.AutoSave<date>` are complete compos: copied as a `.compo` next to the original, they open again. A bank's
  states can be read in them (`values`: key = uuid of the `Parameter`, typed value `'Real @... 2.`).

**Shared videos by script**
- Shared element: `se = Oil.createObject("SharedElement(TextureGenerator)")`, `se.content = video`, then `subcompo.tools.append(se)`. Its displayed
  name is the file's. Reference: `Oil.createObject("ReferenceTextureGenerator")`, `referencer.address.location.set(0)` (`internalIndirect`),
  `referencer.address.elementPointer.set(se.getVariableByName("content"))`, `referencer.shared.set(True)`.
- The video behind a reference: `ref.referencer.address.target.get()`. Point a reference at another element: `elementPointer.set(...)` again.
  `ref.clone()` gives a copy whose target is empty until it is pointed again.
- **A shared video that nothing references does not play** (its position stays at 0, no load measured): a library of shared clips only costs the
  clips in use. Two references to the same element share one decode and one transport.
- An image input of an ISF modifier accepts a reference; code that read `input.file` or `input.transport` must go through `target`.

**Video player and generators**
- `video.transport.player.parameters`: `in` and `out` (optional: `.enabled`, `.value`), `looping`, `speed`, `playMode`, `targetLength`;
  `in` is a Python keyword: `getattr(params, "in")`. **Changing `file.path` keeps the previous clip's `out` point**: a shorter clip holds its last
  image instead of looping. Set `out.enabled` to False on load. Times read `h:mm:ss:frames`.
- `UniformTextureGenerator`: plain colour generator, almost free, for a layer whose picture comes from a modifier. Size:
  `resolution.preset.set(40)` (Custom) then `resolution.width.set(w)` / `height.set(h)`. In the shader, read the output size from a persistent
  buffer (`IMG_SIZE(myBuffer)`), the layer's own image no longer being the source.
- Warning on a qtrle video: "The codecs that are supported officially by smode are: HAP, HAP Alpha, Hap Q, HapR, ProRes, NotchLC and NotchLC
  Alpha." (`liveStatus.success`), with no effect on playback.

**Parameter banks (additions)**
- Adding a `Parameter` to an existing bank leaves its states alone: a state saved before does not touch that parameter.
- An **unlinked** `Parameter(CustomEnumeration)` works as a selector (a list of clips for instance): a Script fills its choices on load (they are
  not saved) and reacts when its value changes; a state saved with it recalls the choice.

**Testing without disturbing the user**
- Background capture of the SMODE window with `PrintWindow(hwnd, hdc, 2)` (see "Checking visually"): bursts of captures with the tempo position
  proved that a freeze engaged (strictly identical images with the speed at 0).
- Web interface: headless Edge with `--remote-debugging-port` and `websocket-client` (`Runtime.evaluate`, `Input.dispatchMouseEvent`,
  `Page.captureScreenshot`, and `Runtime.exceptionThrown` to catch the page's JavaScript errors).

## Audio reactive

`AudioSpectrumLinkSource` — native class to continuously inject the intensity of a frequency band
into any parameter through a Link.
- `.extractor` (`AudioSpectrumExtractor`): `.audioChannel` (`WeakPointer(AudioDeviceChannel)`,
  `.set(channelObj)`), `.frequencyInterval`/`.amplitudeInterval` (`Interval` with
  `.begin`/`.end`/`.center`/`.size`).
- **Units changed in R15 (30/10/2026)**: `frequencyInterval` is `Interval(Frequency)` in **Hz** and
  `amplitudeInterval` is `Interval(Decibel)` in **dB** (both were `Percentage` in R13). Old percentage
  values are silently clamped (22.05 Hz minimum, 0 dB) -> zero-width intervals, the output stays at 0
  and the UI shows the Links as "Disconnected" although they are healthy. Fresh extractor defaults:
  330-550 Hz, -40-0 dB. Frequency: min 22.05 Hz, no hard max. Amplitude: clamped to [-50, 0] dB.
  `end >= begin` is enforced: set `begin` to its floor, then `end`, then `begin`.
- R15 `AudioSpectrumLinkSource` attributes: `method` (`AudioSpectrumExtractorMethod`: 0 mean, 1 max,
  2 smoothMax — `mean` flattens wide bands), `exponent`, `channel`, `outputChannel`, `outputValue`
  (readable output, handy to debug). Exposed parameters in natural units:
  `Parameter(Frequency)`, `Parameter(Decibel)` (no `Oil.Frequency`/`Oil.Decibel` declaration types:
  use `Oil.PositiveReal`/`Oil.Real` in a Script header).
- Channel spectrum: `inputChannels[i].spectrum` (`AffineTransformedSampledRealFunction`,
  `inputScaling` = Hz per bin, e.g. 43.15 = 44100/1024; `outputScaling` 50 / `outputOffset` -50 = 0..1
  -> -50..0 dB). Level: `channel.vuMeter.intensity.get()` (`PPMVuMeter`). The device must have
  `computeWaveformAndSpectrum` = True.
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
Python 3.12.3 in R15 15.9; `sys.path` = `''`, `python\Lib`, `python\Lib\site-packages`, `python\DLLs`, the Smode
folder: no user site-packages, so packages installed for another Python are not visible. The working directory was
`C:\WINDOWS\system32` (30/10/2026): use absolute paths.

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
- **ALL-CAPS names are kept as is** (`RELOCATE` → "RELOCATE", `SECTION_RELOCATE` unchanged, `x_RELOCATE` →
  "X_RELOCATE"). Trick to structure the panel: dummy parameters `RELOCATE: Oil.String("--------")` act as section
  titles (reset the value on each run in case the user edits it: `setattr(script, "RELOCATE", "-" * 40)`).
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
- **Shared globals also include the MCP bridge (09/10/2026)**: a Manual Script triggered from the
  bridge (`tool.execute.trig()`) ran synchronously inside the bridge call, and its module-level loop
  variable `t` overwrote the bridge's own `t` (-> `'WidgetTool' object has no attribute 'launchMode'`).
  Put the whole body of a script in one function (`def _myscript_main(): ...`, then call it): nothing
  leaks except that function name.
- **A `CustomEnumeration` parameter loses its `enumerators` when the script recompiles**
  (`sourceCode.set(...)`), unlike the other parameter values: repopulate it on the next run, and do not
  treat an empty list as "first install" only.
- **An `HsvColor` set on a freshly created `Parameter` before its append into the bank does not stick**
  (back to `00000000`), whereas a `Percentage` does: copy colours (`red/green/blue/alpha`) after the append.
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
- **"At Every Update" runs the whole source again on every frame, in the same globals** (R15, 18/10/2026): every
  `class` is created again each frame. An exception class raised by a thread and caught a few frames later is no
  longer the same object, so `except MyError:` misses it. Keep such classes (anything compared by identity) in a
  persistent dict: `MyError = _STATE.setdefault("MyError", MyError)`.
- **Smode builds the Script again from its text on every run** (R15 15.9, 30/10/2026). Each run goes through
  `SmodeSDK.PythonScriptInstance` (`site-packages/Smode/SmodeSDK.py`): `ast.parse` of the whole source, the parameter
  declarations executed (the parameters are created again), `ast.unparse` of the other statements, `compile`, then
  `exec`. In "At Every Update" that happens on every frame, whatever the code does. The cost follows the number of
  syntax nodes and of parameters (~0.05 ms each); comments cost nothing, one big string literal very little.
  Measured: empty Script 0.1 ms; a 250-line HTTP bridge with 10 parameters 9.4 ms per frame (about 2 fps on a
  project running at 12 fps); a 4000-line Script took a project from 11.8 to 6.6 fps (7.2 fps with its body not
  executed).
  - Keep the code in a string run once, and only call one function on each frame (0.6 ms for the same bridge
    with 2 parameters):
    ```python
    port: Oil.PositiveInteger(8891)

    _MY_CODE = r'''
    def my_frame():
        ...
    '''
    if globals().get("_MY_CODE_RUN") != _MY_CODE:     # first run, or new code pasted
        exec(compile(_MY_CODE, "my_script", "exec"), globals())
        _MY_CODE_RUN = _MY_CODE
    my_frame()
    ```
  - Or keep the code in a file, read once: `try: my_frame()` / `except NameError: exec(open(path).read(),
    globals())`. To reload it when the file changes, the code checks `os.path.getmtime` every few seconds and removes
    `my_frame` from `globals()`: the next frame reads the file again.
  - Everything outside the string is unparsed and compiled again on every frame: keep that part and the number of
    parameters as small as possible.
  - Functions created by `exec(compile(src, "my_script", "exec"))` have `__code__.co_filename == "my_script"`: a
    purge of stale functions can leave alone the functions of the other Scripts in the shared globals.
- **Threads and the Python lock (GIL)** (R15, 18/10/2026, measured from a Script thread while Smode runs): Smode
  holds the lock most of the time. Every `ctypes` call through `WinDLL` releases it and then waits ~30-250 ms to get
  it back: `time.sleep(0.02)` lasts 49 ms (median), a 40x40 screen capture (10 GDI calls) 149 ms, `EnumWindows` +
  `GetWindowText` over 430 windows 619 ms, one log line (open / write / close) ~100 ms. A busy wait is not better.
  - Quick calls that never wait for Smode's main thread can keep the lock: load the DLL with `ctypes.PyDLL`
    (64-bit Windows has one calling convention). Capture 149 -> 41 ms, window search 619 ms -> 1 ms.
  - Not through `PyDLL`: anything that sends a message to Smode's own windows (`GetWindowText` sends `WM_GETTEXT`
    to the main thread: use `InternalGetWindowText`, same result without a message), blocking calls (`MessageBox`),
    input (`SendInput`, `SetCursorPos`), activation, clipboard.
  - Write files from one dedicated thread fed by a `queue.SimpleQueue` (the working thread no longer waits).
  - No low-level hook (`WH_KEYBOARD_LL` / `WH_MOUSE_LL`) in Python inside Smode: every input event of the system
    waits for the Python callback (keys sent with `SendInput` took ~50 ms each). Put the hook in a separate process
    (e.g. PowerShell with `Add-Type` C#) and send its events back through stdout.
  - A thread started from the MCP bridge only runs while the main thread executes Python, and the bridge globals
    are reassigned between calls: import inside the thread function.
- A Windows command line is limited to 32767 characters: a long PowerShell script passed with `-EncodedCommand`
  fails with *The filename or extension is too long*. Write it to a `.ps1` file, start it with `-File`, and read
  commands with `[Console]::In.ReadLine()`.

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

## File references, Media Directories and relink (R15, 08/10/2026)

Verified by relinking a project with 136 media files (ProRes videos + PNGs) after reorganising the folders on disk.

- **No relink feature** in the UI or the docs. The DLLs contain a "Relocate media directory" command (right-click on a
  Media Directory, untested) which only helps if the inner folder structure is unchanged.
- **Stored path**: each file is a `FileReference(VideoFileContent)` (video) or `FileReference(Color2dMipmaps)` (image),
  usually `layer.generator.file`. Its variables: `path` (String), `reload` (Trigger), `file` (`WeakPointer(File)`).
  `path` is `MediaDirectoryName/subfolder/file`: the first segment is the Media Directory **name**, not a disk path.
- **Missing file**: `ref.file.get().getOilClassName()` is `MissingFile` (shown as `<Missing File>`). Found:
  `VideoFile` / `ImageFile`, with `.nativeFile` (absolute disk path via `str(fo.nativeFile.get())`).
- **Relink**: `ref.path.set("NewMediaDirectory/subfolder/file")` is enough: the file resolves immediately (no
  `reload` needed). Check the file exists on disk first (`os.path.exists`), then read the class of `ref.file.get()` again.
- **Finding every reference**: generic tree walk from `script.project` with `getNumVariables()` / `getVariable(i)` /
  `getVariableName(i)`, plus `len(o)` / `o[i]` for vectors and `.get()` on `OwnedPointer`s (Compo generators sit behind
  them). Deduplicate by `getUniqueIdentifier()` **only when it is non-zero** (otherwise the walk stops after a few
  objects) and skip primitive types (`String`, `Boolean`, `Real`...). ~62,000 objects walked in a few seconds on a
  show project.
- Setting an attribute on `script` from the bridge is refused (`AttributeError` on `_cppSmodeSDK.Element`): to keep
  objects between calls, use `builtins`.
- **Media Directories list**: `%APPDATA%\Smode Compose\configurations\Data_<version>.configuration`
  (e.g. `Data_15_8`), blocks `{name = "...", directory = "C:\\...", readOnly = true}` (`\\` escapes). Smode
  writes it **a few seconds late** after adding one in the UI: a script reading it right away may miss the new
  folder. No direct `Oil` access found (only `Oil.getObject(space, uuid)`).
- **Absolute path accepted**: `ref.path.set(r"G:\folder\file.wav")` resolves a file outside any Media Directory;
  Smode rewrites it with `/` and **keeps it after closing / reopening** (not portable).
- **Other `FileReference` types**: `FileReference(AudioFileContent)` (→ `AudioFile`),
  `FileReference(Group3dLayer)` (imported FBX, one per layer of the group → `Scene3dFile`),
  `FileReference(GeometryLayerUser)` (empty path, ignore).
- **Freshly copied file on disk**: right after `shutil.copy2` + `ref.path.set(...)`, the reference often stays
  `MissingFile` (deferred indexing). Call `ref.reload.trig()` and check again in a **later** call / run; 2-3 passes
  may be needed.
- **Scene of a reference**: top-level Scenes are the `Scene`-class layers in `masterScene.layers` (the
  `masterScene` has no label); track them during the tree walk.
- `getUniqueIdentifier()` on a `PythonScriptTool` raises `TypeError ... juce::Uuid`: wrap it in a try (the generic
  walk already does); to find a tool, compare `script.sourceCode` instead.

## Web interface served by a Script (R15, 08/10/2026)

Pattern validated with [smode-filemanager](https://github.com/gyomh/smode-filemanager) (`Smode_Filemanager_GUI.py`):
a real graphical interface for a Script, with nothing to install.

- **Script in Launch Mode "At Every Update"**: it starts a `ThreadingHTTPServer` on `127.0.0.1` once (state kept in a
  global, e.g. `_FMG`) then, on every frame, processes a `queue.Queue` of Oil tasks.
- **Oil only on the main thread**: the HTTP thread posts a task (`{"task", "arg", "done": Event}`) and waits for the
  `Event`; the next frame runs it. Heavy work **without Oil** (`os.walk`, chunked file copy with progress) stays in a
  thread: Smode does not freeze.
- **Globals are shared between Scripts**: prefix everything (`fmg_...`, `_FMG`) so you do not overwrite another
  Script's functions.
- **Code updates**: the module is re-run on every frame with the new `sourceCode`, so the functions the server calls
  are always the latest; restart the server only when a version constant or the port changes. With the code kept in
  a string run once (see "Smode builds the Script again from its text on every run"), run the string again when it
  changes.
- **One server per port on Windows**: `HTTPServer` sets `allow_reuse_address = True`, and on Windows `SO_REUSEADDR`
  lets a second server bind a port already in use without any error (e.g. a second Smode with the same
  project open): the connections then go to either one. Set `allow_reuse_address = False` in the server class to get the
  `OSError` instead.
- **Large tools: the interface outside Smode**. The threads of a Script run under Smode's Python lock and the source
  is rebuilt on every frame: for a large tool, put the interface and the long work in a separate program (its own
  Python), and keep in Smode a short "At Every Update" agent that runs a fixed list of named Oil tasks asked over
  `127.0.0.1` (never code received over HTTP). The Script can start the program with `os.startfile` (from a thread).
  A `.pyw` is run by the `py` launcher, which takes the newest Python installed (possibly 32-bit): a first line
  `#!python3.11` chooses the version.
- **App window**: `msedge.exe --app=http://127.0.0.1:<port> --window-size=1400,900` opens a window without an
  address bar (Edge ships with Windows 10/11).
- **Security**: listen on `127.0.0.1` only, reject a `Host` header other than `127.0.0.1` / `localhost` (DNS
  rebinding) and a foreign `Origin`; do not expose arbitrary code execution.
- **Native folder picker** from the page: run PowerShell with `-STA` and `System.Windows.Forms.FolderBrowserDialog`
  (`TopMost` owner form) via `subprocess` from the HTTP thread; reveal in Explorer: `explorer /select,<file>`.
  `file:///` links are blocked by browsers (download or open in the browser).
- **Drop-down lists**: the highlight of an open native `<select>` is forced by Windows (grey) and ignores the page
  colours; for a consistent interface, draw your own list (button + panel) and keep the hidden `<select>` as the
  model (value + `change` event).
- **The server survives closing the project**: threads, sockets and Python globals stay in memory for the whole
  Smode session; when the project is reopened, the Script finds its server already running (so an "on first server
  start" never fires again). To react to a Script restart (project reopened, Script added, set back to At Every
  Update), store the time on each run: a gap of more than a few seconds = restart. At that point, forget cached Oil
  references (they belong to the old project).
- **Execution counter**: `tool.script.numExecutions.get()` counts the runs of this Script instance (one per frame in
  At Every Update, ~47/s measured).
- **POST-only API**: a foreign web page can trigger a GET without an `Origin` header (`<img src="http://127.0.0.1:...">`);
  a POST from it always carries its `Origin`, which is refused.
- **ASCII .py file**: how Smode decodes a .py dropped into the project is not verified; to be safe, write accented
  characters as `\uXXXX` escapes (Python strings, and the JS of the HTML).
- **Check the interface without touching the user's window**: `msedge --headless=new
  --user-data-dir=<temporary folder> --lang=en --window-size=1400,900 --virtual-time-budget=8000
  --screenshot=capture.png http://127.0.0.1:<port>/` (`--lang` sets `navigator.language`).

## Widget Tool (R15, 09/10/2026)

Custom control surface (Tool element, SMODE 10+), built in the **Widget Editor** (EDIT mode,
drag & drop). Public docs are 5 lines long; everything below was found live.

**Structure (only 2 concrete widget classes exist, confirmed in `api-Smode.dll`):**
```
WidgetTool (in scene/compo .tools; also has runOnServer)
└─ groupDefinition : GroupWidgetDefinition   target (= the WidgetTool itself), bounds, caption
   └─ definitions : OwnedVector(WidgetDefinition)   # WidgetDefinition = abstract
        ParameterWidgetDefinition   target  : ObjectWeakPointer (element OR variable)
                                    bounds  : PixelRectangle (position.x/y, size.width/height), absolute pixels
                                    caption : String  -> stored but NOT displayed (see below)
```
- **Point at the VALUE, not the element.** `d.target.set(param.value)` / `state.apply` /
  `bank.applyNext` / `layer.opacity`. Dropping an element (a `ParametersState`, a `ParameterBank`)
  gives an empty box with an icon. Dropping a `Parameter` element works (shows its label as title)
  but does not show the "driven" state.
- `str(d.target)` prints `''` while the definition is not in the document — not an error:
  `d.target.get()` returns the variable; after the append it prints `@space/<uuid>/value`.
- **Title displayed = name of the target**: element label (`Opacity (reel)`) or variable name
  (`Value`, `Apply`, `Apply Next`). `caption` is ignored for parameter widgets, and there is **no
  rename** in the UI (right click in EDIT mode = Delete only; "Change Caption" exists in
  `Designer.dll` but is not reachable). Workaround: a widget pointing at the `Parameter` element,
  24 px high, placed over the value widget's title bar, as a label.
- **Widget look = type + box shape**, no style choice: Percentage in a tall box = vertical fader,
  in a square box = knob; HsvColor = colour wheel; Trigger = button. A Percentage driven by a Link
  gets a **green frame** and is read-only. `UnboundedPercentage` (e.g. `scaleFactor.width`) has no
  max → numeric field, never a fader (go through a bounded bank `Parameter(Percentage)`).
- **Z order = order of `definitions`: the last one is drawn on top.** Reorder by rebuilding: create
  copies (target, bounds, caption) with `defs.append` / `defs.insert(i, obj)`, then
  `defs.removeAt(old)`. Ready-made script: `Widget_ZOrder_GYOMH.py` (front/back/up/down + auto sort
  by area).
- **A nested `GroupWidgetDefinition` is not rendered** (empty frame, no caption, children hidden).
- Limits: no scrolling/zoom in the canvas (anything out of the window is unreachable), absolute
  layout, no remote/web access (the HTTP API of `NetworkPlugin.dll`, `/api/live/...`, does not
  serve widgets). Strength: the panel is saved in the project/compo and survives renames.
- Official example: `packs/Features/Misc/WidgetTool.compo` = a WidgetTool showing the macros of a
  `ParameterBank` (FADER 01...), each driving several targets through `ParameterLinkTarget` +
  `FunctionLinkModifier`/`KeyframeFunction` curves. The widget is only a view of the bank.

- **Building panels by script** (ready-made: `Widget_Builder_GYOMH.py`, one panel per `ParameterBank`):
  - A script can target **variables the UI cannot drag**: `bank.applyPrevious` / `applyNext` /
    `applyRandom` / `saveAsNew`, `currentStateIndex`, or a `Parameter(UnboundedPercentage)` value
    (the UI refuses to drop it). Any `Parameter(<Type>)` can be created (`Parameter(UnboundedPercentage)`,
    `Parameter(PositivePixels)`...): give a monitor the type of the property it watches.
  - Widget sizes found: button reduced to 104x56 (title bar + button, 112 for "Apply Previous");
    a value field fits in 104x56 (Percentage included: no knob at that height); fader 104x272; colour
    wheel 272 wide. The editor works on an 8 px grid: 8 px = minimum spacing.
  - **Rebuild by replacing the WidgetTool, not by `definitions.clear()` + refill**: when the panel is open
    in the Widget Editor, the editor writes its cached copy (old positions) back over a cleared and
    refilled list. A brand-new WidgetTool (old one removed) displays correctly, editor open or not.
  - Removing `WidgetTool`, `ParameterBank` and `LinkBank` from `container.tools` with `removeAt(k)`
    (index found with `container.tools[k] is obj`) works without crash (Links first, then banks, then
    panel). Hidden tag to find a panel again after a rename: `groupDefinition.caption` (stored, never shown).
  - A bank `Parameter` **with targets** gets an automatic name from its target and **cannot be renamed
    in the UI** (`p.label.set()` works by script); a Parameter **without targets** (e.g. a monitor) can be
    renamed in the tree. Matching a monitor to its property across rebuilds: `str(link.source.target)`
    (`@space/<uuid>/scaleFactor/width`) is stable.

**Transitions between bank states**: no duration on the State — add a **Dynamic** modifier to the
bank parameter's `ParameterLinkTarget.modifiers` (or `Parameter.modifiers`): `SmoothLinkModifier`
(`positiveSpeed`/`negativeSpeed`), `InertiaLinkModifier` (`maxSpeed`, `acceleration`),
`BounceLinkModifier` (`speed`, `adaptationSpeed`), also `Extrapolate`, `Derivative`,
`InterpretSpeed`; common: `bypassModifierAboveDelta`. `DynamicLinkModifier` itself is abstract.
The bank fader jumps; only the target glides.

**"Monitor" fader of the real (smoothed) value**: a `Parameter(Percentage)` in a separate bank
(states do not capture it) + a `Link` in a `LinkBank`: `source = ParameterLinkSource`
(`target.set(realVar)`), `targets.append(ParameterLinkTarget)` with `target.set(monitor.value)`.
Works by script. A Link only transmits **changes** of its source (`numChanges`): the monitor keeps
its old value until the source moves once. Trap: a layer has its own `opacity` AND its generator
has another `opacity` (same name in the tree).
- `ParametersState`: `apply` (Trigger), `values` = `Map(WeakPointer(Parameter), Object)`.
  `ParameterBank`: `states`, `currentStateIndex`, `currentState`, `applyPrevious`, `applyNext`,
  `applyRandom`, `saveAsNew`, `recording`, `loop`.
- Owner of a variable: `var.isChildOf(element)` works (an element is a child of itself) — used to
  name widgets "Parameter > Value".

## Video export from a script (R15, 11/10/2026)

The API exists (`SmodeSDK.SceneVideoExportTask()` is an official helper in `site-packages/Smode/SmodeSDK.py`),
but **launching the export from Python depends on the licence**.

- Classes (`Plugins/VideoExport.dll`): `SceneVideoExportTask` / `CompoVideoExportTask` +
  `SceneVideoExportUserSettings` / `CompoVideoExportUserSettings`: `begin` / `end` (`Seconds`), `timeBase`
  (`VideoTimeBase`), `speed`, `fileName`, `outputDirectory` (`NativeDirectory`), `startImmediately`,
  `soundAlert`, `fileExporter`, `targets` (`VideoExportTargetSelection`: `selectedScopes` / `selectedLeaves`,
  `ObjectSelection` with `insert()`); the Compo version also has `resolution`. `task.parameters`
  (`VideoExportParameters`): `documentToClone` (the project), `rootExportedElement` (the element whose main
  timeline is exported, e.g. a Scene), `settings` (`OwnedPointer`, direct assignment).
- Exporters (`Plugins/AVStreaming.dll`), set on `settings.fileExporter` / `.videoExporter` / `.audioExporter`
  (`None` = no audio): containers `FFMPEGQuicktimeAVFileExporter` (default), `FFMPEGMPEG4AVFileExporter`,
  `FFMPEGMatroskaAVFileExporter`, `FFMPEGAVIAVFileExporter`, `FFMPEGWAVAVFileExporter`,
  `ImageSequenceAVFileExporter`; video `FFMPEGProResVideoExporter` (`profile`, `colorSpace`),
  `FFMPEGHapVideoExporter` (default), `FFMPEGH264NvencVideoExporter` / `FFMPEGH264AmfVideoExporter` /
  `FFMPEGH264AutoVideoExporter` / `FFMPEGOpenH264VideoExporter` (`bitrate`, `profile`...),
  `FFMPEGQuicktimeMJPEGVideoExporter`, `FFMPEGQuicktimeAnimationVideoExporter` (`exportAlpha`),
  `ImageSequenceVideoExporter` (+ `Png` / `Jpeg` / `Targa` `FreeImageFileExporter`); audio `FFMPEGAACAudioExporter`,
  `FFMPEGAC3AudioExporter`, `FFMPEGFLACAudioExporter`, `FFMPEGPCMAudioExporter` (`numChannels`, `timeBase`).
- Task queue: `engine.tasks.group` (`RootGroupTask`: `tasks`, `paused`, `sequential = False` by default). Even
  so, queued video exports are rendered **one after the other**, not in parallel (observed, R15, 14/10/2026).
- **Licence gate**: everything above can be built, but `engine.tasks.group.tasks.append(task)` raises
  `ValueError('your license does not allow to export using python')` (check inside `Plugins/Python.dll`)
  with a Smode Compose edition + "4K Video Export (Pro Codec | No Watermark)" licence. Which licence allows
  it was not verified. The current licence can be read: `engine.licensing.features` (`videoFileExport`,
  `videoFileExportPro`, `videoFileExportUnwatermaked`, `videoFileExportMultiTarget` = several targets in
  one export, `maxVideoFileExportWidth/Height/Pixels`...) and `engine.licensing.licenses`
  (`editionProduct`, `videoExportProduct`).
- The settings of the **File > Export Video** dialog are a GUI-side object (saved in
  `AppData\Roaming\Smode Compose\configurations\Kiwi_<version>.configuration`, key
  `sceneVideoExportUserSettings`: last file name, output directory, end...), not reachable from Oil.
- **Export tasks created by the UI** (R15, 14/10/2026), readable from a script in `engine.tasks.group.tasks`:
  - each Ok of the dialog adds a `SceneVideoExportTask` named `Video Export of <project file> > <fileName>`
    (a Cancel adds nothing: comparing the task names before / after tells the two apart);
  - `state` (`TaskState`): `uninitialized` (waiting, e.g. Start Immediately unticked: `paused = true`), `running`,
    `terminated`; `status.state` = `success` (else `status.message`); `progressionString` e.g.
    `679/1001 Frames 13.58s /20.02s (Remaining time: 16 secs)` then `Done: 1001 Frames exported`;
    `startTimeSinceEpochMs` (0 until it starts); **no end time** (note it yourself when `terminated` shows up);
  - finished tasks **stay in the list** until removed in the Tasks menu;
  - `progression` is a `Percentage`: **`.get()` returns a fraction 0..1** while `toString()` shows 0..100
    (`0.678` / `67.832`);
  - `parameters.documentToClone` is the live `ProjectDocument` (`script.project.isChildOf(doc)` is true) and a
    paused task stays `uninitialized`, yet **the render is the state of the project at the Ok click**: a project
    changed afterwards (other Scene activated, main timeline rebuilt) does not change an export started later
    from the Tasks menu (checked on the rendered file). Preparing the next export right after an Ok is safe.
- On disk the spaces of the file name become `_` (`TEST_Scene 1_v1` -> `TEST_Scene_1_v1.mov`).
- `PythonScript.executeDuringExports` (on `tool.script`, `False` by default): the Scripts of the exported copy of
  the project do not run during the render.
- **Export targets** = Content Maps and Processors only: a zone of a ContentMap cannot be exported on its own. To
  export a zone, or an assembly of zones / Content Maps, build a Processor for it (see *Zones, layer targets and
  Processors* above), e.g. one Processor per screen.
- **After the Ok, an export loading its media blocks Smode's main thread** (17 s seen on a show project with long
  video clips): the "At Every Update" Scripts do not run during that time. A Script that detects a reopened project
  through a gap between two frames must not take this pause for one (compare the project name instead).
- **Exporters described by Oil** (R15, 18/10/2026): `Oil.createObject(className)` builds one (nothing exported);
  `getFriendlyName()` gives the name shown in the Export Video window, and its variables
  (`getNumVariables` / `getVariable(i)` / `getVariableName(i)` / `getFriendlyName()`) give its options in order:
  - containers (`...AVFileExporter`): Apple QuickTime, Audio Video Interleaved, MPEG-2, MPEG-4, Matroska,
    Windows Media (`audioExporter`, `videoExporter`), Image Sequence (`audioExporter`, `videoExporter`,
    `audioFileExporter`), audio only: Waveform Audio, Audio IFF, Free Lossless Audio Codec;
  - video: Apple ProRes (`cpuUsage`, `profile`, `colorSpace`), Hap (`cpuUsage`, `profile`, `numChunks`), Hap (GPU or
    Squish encoder) (`profile`, `numChunks`, `encoderQuality`), Nvenc H.264 (`bitrate` "40000k", `preset`,
    `profile`), AMF H.264 (`qualityPreset`), H.264 (best available) (`encodingQuality`), Open H.264, QuickTime
    MJPEG, QuickTime Animation (`exportAlpha`), Windows Media Video, Image Sequence (`imageFileExporter`); all have
    `timeBase` and `resolution` (set by the export);
  - audio: AAC and AC-3 (`numChannels`, `cpuUsage`, `bitrate`), FLAC, PCM (`componentType`); `timeBase` 48000/1.
  - The window does not show every variable (ProRes: Cpu Usage and Profile only; `colorSpace` hidden).
  - An exporter **owned** by a task (`task.parameters.settings.fileExporter`, its `videoExporter`...) returns the
    friendly name of its *variable* ("File Exporter", "Video Exporter"): to get the format name, use
    `Oil.createObject(obj.getOilClassName()).getFriendlyName()`.
- **An export cancelled in Smode** (Tasks menu): its `state` becomes `canceled`, then the task disappears from
  `engine.tasks.group.tasks`. A task has no cancel method (`RootGroupTask` has `cancelable` / `pausable`, both
  `false`, and `sequential` = `false`).
- **Defaults of a freshly created exporter** (R15, 18/10/2026): codec of each container — Apple QuickTime and AVI:
  Hap; MPEG-4: H.264 (best available); MPEG-2 and Matroska: Open H.264; Windows Media: Windows Media Video; Image
  Sequence: `ImageSequenceVideoExporter` with `TargaFreeImageFileExporter`; Waveform Audio and Audio IFF: PCM audio;
  Free Lossless Audio Codec: FLAC audio; `audioExporter` = `null` (no audio) in the video containers. Options:
  `cpuUsage` 75 %, H.264 / WMV / MJPEG `bitrate` "40000k", AAC / AC-3 `bitrate` "300k", audio `numChannels` 2 and
  `timeBase` 48000/1, Hap `numChunks` 16, QuickTime Animation `exportAlpha` true; enum defaults in the table of
  *Enums: never guess the index*.
- **Variables of a `SceneVideoExportTask`**: `name`, `paused`, `progression`, `progressionString`, `status`
  (`SuccessStatus`), `state` (`TaskState`), `relatedFile`, `startTimeSinceEpochMs`, `image` (`OwnedColor2dBuffer`),
  `parameters` (`VideoExportParameters`: `documentToClone`, `rootExportedElement`, `settings`), `renderingContext`
  (`OfflineRenderingContext`), `previousOnAir`. **The settings of an export started from the window are readable on
  its task** after the Ok: `task.parameters.settings` (`SceneVideoExportUserSettings`) -> `fileExporter` -> its
  `audioExporter` / `videoExporter` and their option values (e.g. ProRes `profile`, `colorSpace`, `cpuUsage`).

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
  **Same bug on `ShapeLayer` generators** (`RectangleShapeGenerator` / `CircleShapeGenerator`, R15, 30/10/2026): every
  new shape is back to 500 px a frame or two after insertion, so a fix in the same bridge call is overwritten — re-apply
  the sizes (keep them in a dict keyed by label) in a **later** bridge call.
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

A fifth crash (R15, 08/10/2026), triggered through the MCP bridge:
5. A `PythonScriptTool` in Launch Mode "At Every Update" added to `masterScene.tools`, then removed with
   `tools.removeAt(i)` in the next call → `ACCESS_VIOLATION` in `juce.dll`. The bridge itself runs in
   `masterScene.tools`, during the Scripts' execution loop.
Rule: set the Script to Manual (`launchMode.set(0)`) in one call, and remove it only in a later call (removing
Manual Scripts never caused trouble).

A sixth crash (R15, 11/10/2026), through the MCP bridge:
6. A loop over the bridge's `globals()` calling `getOilClassName()` on every value → `ACCESS_VIOLATION` in
   `api-Oil.dll`. Among the variables left by earlier calls were wrappers of `ElementTrack` /
   `ElementTrackBlock` destroyed in the meantime by `timeline.elementTracks.clear()`: a Python wrapper does
   not keep its Oil object alive, it dangles.
Rule: never touch a wrapper whose object may have been destroyed (cleared vector/map, removed element); in
the bridge, work inside functions (local variables) and `del` the module-level ones, never scan `globals()`.

A seventh crash (R15, 30/10/2026), through the MCP bridge, no log nor dump:
7. Rebuilding a whole 3D compo in one call (`layers.clear()` of ~40 layers incl. lights whose `target.targetObject`
   pointed at a group of the same tree, `modifiers.clear()`, `cameras.clear()` of the **current** camera, then
   re-creation) worked three times, then killed Smode the fourth time. SmodeLauncher restarted Smode, which
   reopened **another project** (the last one of the previous session), not the document being edited.
Rule (to confirm): for a 3D rebuild, reset the lights' targets and make another camera current in a first call,
clear in a second call, rebuild in a third; or update the existing objects instead of rebuilding.
Note: changes made by script do not mark the document as modified (no `*`, `hasUnsavedChanges` False), so a Ctrl+S
saves them without warning.

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

**Bridge in a Compo document** (R15, 30/10/2026): when the open document is a `.compo` (not a project), `script.project`
raises `AttributeError`; `script.parentElement` is the Compo and `script.document` a `Document(TextureGenerator)`. A Compo
document is evaluated on its own (no Content Map target needed for its timeline and shapes to play). To run a long build
script kept on disk without filling the shared namespace: `ns = {"Oil": Oil, "script": script};
exec(open(path, encoding="utf-8").read(), ns)`.

**Reading values every frame from the bridge** (R15, 30/10/2026): replacing `_processQueue` in the namespace had no
effect (never called), but the request queue object persists and its `empty()` is called every frame: swap
`_SMODE_MCP_REQUEST_QUEUE` for a proxy whose `empty()` first runs a sampler (try/except) then delegates
(`__getattr__` -> the real queue). Samples (e.g. timeline position + parameters) are taken on the main thread at the
render rate, in sync with the timeline (no frame offset). Put the real queue back afterwards and drop the wrappers of
sampled objects before deleting them. Same trick for an automatic benchmark (toggle a layer, wait ~25 frames, average
`frame.rate` over ~40 frames).

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

### Monitor 70 / LED / screen compo lessons (R15, 31/10/2026)

- **Black solid behind the screen compo**: a Compo shown on a 3D screen has a transparent background; the FBX body shows through. Put an opaque black Solid layer at the bottom of the compo.
- **Cameras live in `comp.cameras`** (not layers/tools): `comp.cameras.append(cam)`, then in a later call `cam.makeCurrent.trig()`.
- **A material reached through a MaterialBank + `ReferenceGeometryLayerUser` may not be applied** to a given layer (the colour never changed). For something that must visibly react, put a direct `SurfaceGeometryRenderer` on the GeometryLayer.
- **Animating `autoIlluminate`/diffuse level of a lit material is not visible** when the colour stays lit by ambient/other lights: key the **colour** of the texture instead. `UniformTextureGenerator.color` (HsvColor) is keyable: `tr, kf = tc.createKeyframe(u.color, t, False)`. `createKeyframe` returns `(track, key)`.
- **Deleting a parameter's owner (e.g. a material) deletes its parameter tracks automatically.** There is no API to delete a single track, and `parameterTracks.clear()` crashes Smode.
- `transport.play` / `transport.pause` are Triggers: `.trig()`. After a crash the saved document may be an old version: save often.
- `AmbientLight` (intensity, `diffuse.color`), `PlaneGeometryGenerator` (size.width/height; rotate x by -pi/2 for a floor).

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
