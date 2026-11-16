# SMODE R15 classes and their settings (read by script)

Generated from the catalogue of the Node Editor (16/11/2026): each class was created with `Oil.createObject(cls)` on a
throwaway object and its variables walked (`getNumVariables` / `getVariableName` / `getVariable`), two levels deep
inside composite values. Columns: the path to write (`obj.<path>.set(...)`), the Oil class of the variable, the default
value of a fresh object, the choices of an enumeration (index order: `set(i)` or `set("name")`). Colours are shown as
hex; angles are listed in degrees (Oil stores radians: `set(math.radians(x))`). `Percentage` takes 0..1 in `set()` and
prints x100 in `toString()`. Variables that hold objects, pointers, vectors, strings and transports are left out: see the README
for those (masks, maps, players, references). Presets: the libraries of `packs/Standard Pack/Presets` that have a file for the
class (`Default`, `Advanced Presets`); setting `preset.presetName` does not apply one (see the README).

Classes: 94. Settings: 1079.

## Contents

- [Texture modifiers](#texture-modifiers-layer-generator-modifiers-compo-modifiers-renderer-effects): `AlphaChokerTextureModifier`, `AmbientOcclusionTextureModifier`, `AntiAliasingTextureModifier`, `BlurTextureModifier`, `BlurV8TextureModifier`, `BrightnessContrastGammaTextureModifier`, `ColorBalanceTextureModifier`, `ColorFunctionTextureModifier`, `ColorizeTextureModifier`, `DepthOfFieldTextureModifier`, `DepthOfFieldV8TextureModifier`, `DepthToNormalTextureModifier`, `DiscardAlphaTextureModifier`, `DisplaceTextureModifier`, `DrosteTextureModifier`, `EmbossTextureModifier`, `FlipTextureModifier`, `FrameDelayTextureModifier`, `FreezeTextureModifier`, `GrayscaleTextureModifier`, `HueSaturationLuminanceTextureModifier`, `MaskTextureModifier`, `MatteTextureModifier`, `OverlayTextureModifier`, `PolarCoordinatesTextureModifier`, `RGBSeparateTextureModifier`, `RadialDistortionTextureModifier`, `RedGreenBlueTextureModifier`, `ScrollTextureModifier`, `SobelTextureModifier`, `SparklesTextureModifier`, `SwirlTextureModifier`, `TemperatureTextureModifier`, `TilesTextureModifier`, `Transform2dTextureModifier`, `TritoneTextureModifier`, `UpscaleTextureModifier`, `VibranceTextureModifier`, `WarpTextureModifier`
- [Texture masks](#texture-masks-masktexturemodifier-masks-modifier-masks): `ColorTextureMask`, `DepthTextureMask`, `FunctionTextureMask`, `GradientTextureMask`, `LinearTextureMask`, `NoiseTextureMask`, `PeopleTextureMask`, `PlacementTextureMask`, `RadialTextureMask`, `ShapeTextureMask`, `TextureLayerTextureMask`
- [Texture generators](#texture-generators-texturelayer-generator-a-material-map-a-mask-image): `BrickTextureGenerator`, `CheckerBoardTextureGenerator`, `DotsTextureGenerator`, `GlitchTextureGenerator`, `LensFlareTextureGenerator`, `LinearGradientTextureGenerator`, `MandelbrotFractalsTextureGenerator`, `MarbleTextureGenerator`, `MonjoriTextureGenerator`, `MultiPointGradientTextureGenerator`, `NoiseTextureGenerator`, `RadialFunctionTextureGenerator`, `RadialGradientTextureGenerator`, `SoftEdgeTextureGenerator`, `TestPatternTextureGenerator`, `UniformTextureGenerator`, `WhiteNoiseTextureGenerator`, `WoodTextureGenerator`
- [3D colour sources of a PBR channel](#3d-colour-sources-of-a-pbr-channel-no-uv): `CheckerBoard3dTexture`, `Gradient3dColorizer`, `UVW3dTexture`
- [Geometry generators](#geometry-generators-geometrylayer-generator): `BoxGeometryGenerator`, `CapsuleGeometryGenerator`, `CircleGeometryGenerator`, `CylinderGeometryGenerator`, `FunctionSplineGeometryGenerator`, `GeosphereGeometryGenerator`, `GridPointsGeometryGenerator`, `GroupGeometryGenerator`, `HelixGeometryGenerator`, `KnotGeometryGenerator`, `ParticlesGeometryGenerator`, `PlaneGeometryGenerator`, `RandomPointsGeometryGenerator`, `RectangleGeometryGenerator`, `SegmentGeometryGenerator`, `SphereGeometryGenerator`, `StageDisplayGeometryGenerator`, `StarGeometryGenerator`, `TextGeometryGenerator`, `TorusGeometryGenerator`, `TrackingSystemGeometryGenerator`
- [Shapes and layers](#shapes-and-layers): `GroupShapeGenerator`, `NullLayer`

## Texture modifiers (`layer.generator.modifiers`, `compo.modifiers`, `renderer.effects`)

### `AlphaChokerTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `choke` | `Real` | -1 |  |
| `iterations` | `PositiveInteger` | 8 |  |
| `size.width` | `HorizontalCanvasValue` | 0 |  |
| `size.height` | `VerticalCanvasValue` | 0 |  |
| `size.linked` | `Boolean` | true |  |

### `AmbientOcclusionTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `sourceLevel` | `Percentage` | 1 |  |
| `quality.automatic` | `Boolean` | true |  |
| `quality.gammaValue` | `GammaValue` | 1 |  |
| `quality.pixelType` | `PixelType` | 0 (clamped8Bits) | clamped8Bits, clamped10Bits, clamped16Bits, hdr16Bits, hdr32Bits |
| `quality.mipmapping` | `Boolean` | false |  |
| `quality.downSampling.width` | `DownSamplingFactor` | 0 (one) | one, oneOverTwo, oneOverFour, oneOverEight, oneOverSixteen, oneOverThiryTwo, oneOverSixtyFour |
| `quality.downSampling.height` | `DownSamplingFactor` | 0 (one) | one, oneOverTwo, oneOverFour, oneOverEight, oneOverSixteen, oneOverThiryTwo, oneOverSixtyFour |
| `quality.downSampling.link` | `Boolean` | true |  |
| `quality.samplingParameters.minificationFilter` | `Boolean` | true |  |
| `quality.samplingParameters.magnificationFilter` | `Boolean` | true |  |
| `quality.samplingParameters.bindFilters` | `Boolean` | true |  |
| `quality.samplingParameters.horizontalWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.verticalWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.depthWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.bindWrapModes` | `Boolean` | true |  |
| `quality.samplingParameters.anisotropy` | `PositiveInteger` | 16 |  |
| `quality.samplingParameters.compareWithDepth` | `Boolean` | false |  |
| `shadowRange.center` | `PositiveMeters` | 1.1 |  |
| `shadowRange.size` | `Meters` | 2 |  |
| `shadowRange.begin` | `PositiveMeters` | 0.1 |  |
| `shadowRange.end` | `PositiveMeters` | 2.1 |  |
| `shadowRange.invertible` | `Boolean` | true |  |
| `projectInHemisphere` | `Boolean` | true |  |
| `radius` | `PositiveReal` | 0.5 |  |
| `luminance` | `PositiveReal` | 0 |  |
| `complexity` | `PositiveInteger` | 8 |  |
| `blurRadius` | `PositiveReal` | 0.005 |  |
| `blurPrecision` | `PositiveReal` | 0.3 |  |
| `blurComplexity` | `PositiveInteger` | 6 |  |
| `color` | `HsvColor` | #000000 |  |
| `blendingMode` | `BlendingMode` | 2 (normal) | passThrough, replace, normal, dissolve, darken, multiply, colorBurn, linearBurn, darkerColor, lighten, screen, colorDodge, linearDodge, lighterColor, overlay, softLight, hardLight, vividLight, linearLight, pinLight, hardMix, difference, exclusion, subtract, divide, hue, saturation, color, luminosity, alpha |

### `AntiAliasingTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `size.width` | `HorizontalCanvasValue` | 0 |  |
| `size.height` | `VerticalCanvasValue` | 0 |  |
| `size.linked` | `Boolean` | true |  |

### `BlurTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `samples.number` | `PositiveInteger` | 15 |  |
| `samples.distance.width` | `HorizontalCanvasValue` | 0 |  |
| `samples.distance.height` | `VerticalCanvasValue` | 0 |  |
| `samples.distance.linked` | `Boolean` | true |  |
| `samples.downSampling.width` | `DownSamplingFactor` | 2 (oneOverFour) | one, oneOverTwo, oneOverFour, oneOverEight, oneOverSixteen, oneOverThiryTwo, oneOverSixtyFour |
| `samples.downSampling.height` | `DownSamplingFactor` | 2 (oneOverFour) | one, oneOverTwo, oneOverFour, oneOverEight, oneOverSixteen, oneOverThiryTwo, oneOverSixtyFour |
| `samples.downSampling.link` | `Boolean` | true |  |
| `additionalBrightness` | `SignedPercentage` | 0 |  |
| `sourceLevel` | `Percentage` | 0 |  |
| `pixelType` | `PixelType` | 0 (clamped8Bits) | clamped8Bits, clamped10Bits, clamped16Bits, hdr16Bits, hdr32Bits |

### `BlurV8TextureModifier`

Presets: **Default** (Gaussian, Gaussian (fast), Box, Directional, Radial (zoom), Noisy, Bloom (small), Bloom (large), Glow (small), Glow (large), Lens blur (hexagonal bokeh), Lens blur (circular bokeh), Special - Starglow, Special - Super Starglow, Special - Glitch diffuse, Special - Glitch dark diffuse, Special - Dilate, Special - Erode, Radial (spin), Radial (Zoom), Denoise, Denoise - Hard Edges, Denoise - Star) ; **Advanced Presets** (Weeds, Dirty lens, Van Gogh, Smudge, Stained Glass, Smear (large), Psychedelics, Shivering, Noisy (animated), Glitch - Old VHS, Glitch - Shift colors, Glitch - Over saturate, RGB Separate blur, Color based directional blur)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `radius` | `PositivePixels` | 10 |  |
| `shape` | `BlurShape` | 0 (gaussian) | gaussian, box, circle, ring, hexagonal, zoom, spin, directional, star4Branches, star8Branches, randomBox, randomCircle, randomTriangle, diffuse, custom |
| `quality.budget.lookups` | `StrictlyPositiveInteger` | 20 |  |
| `quality.budget.perfectBudget` | `StrictlyPositiveInteger` | 1 |  |
| `quality.downSampling.enabled` | `Boolean` | false |  |
| `quality.pixelType.enabled` | `Boolean` | false |  |
| `quality.pixelType.value` | `PixelType` | 0 (clamped8Bits) | clamped8Bits, clamped10Bits, clamped16Bits, hdr16Bits, hdr32Bits |
| `quality.mipmapping` | `Boolean` | true |  |
| `quality.samplingParameters.minificationFilter` | `Boolean` | true |  |
| `quality.samplingParameters.magnificationFilter` | `Boolean` | true |  |
| `quality.samplingParameters.bindFilters` | `Boolean` | true |  |
| `quality.samplingParameters.horizontalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.verticalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.depthWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.bindWrapModes` | `Boolean` | true |  |
| `quality.samplingParameters.anisotropy` | `PositiveInteger` | 16 |  |
| `quality.samplingParameters.compareWithDepth` | `Boolean` | false |  |
| `style.luminosityThreshold` | `Percentage` | 0 |  |
| `style.blendingModeWithInput` | `BlendingMode` | 1 (replace) | passThrough, replace, normal, dissolve, darken, multiply, colorBurn, linearBurn, darkerColor, lighten, screen, colorDodge, linearDodge, lighterColor, overlay, softLight, hardLight, vividLight, linearLight, pinLight, hardMix, difference, exclusion, subtract, divide, hue, saturation, color, luminosity, alpha |
| `style.invertBlendingOrder` | `Boolean` | false |  |
| `style.outputLuminosity` | `UnboundedPercentage` | 1 |  |
| `style.maskInterpretation` | `BlurTextureMaskInterpretation` | 0 (fade) | fade, radius, radiusAndFade |
| `horizontalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `verticalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |

### `BrightnessContrastGammaTextureModifier`

Presets: **Default** (Light Contrast, Medium Contrast, Hard Contrast)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `brightness` | `SignedPercentage` | 0 |  |
| `contrast` | `SignedPercentage` | 0 |  |
| `gamma` | `SignedPercentage` | 0 |  |

### `ColorBalanceTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `shadows.cyanRed` | `SignedPercentage` | 0 |  |
| `shadows.magentaGreen` | `SignedPercentage` | 0 |  |
| `shadows.yellowBlue` | `SignedPercentage` | 0 |  |
| `shadows.multiplier` | `PositiveReal` | 1 |  |
| `midtones.cyanRed` | `SignedPercentage` | 0 |  |
| `midtones.magentaGreen` | `SignedPercentage` | 0 |  |
| `midtones.yellowBlue` | `SignedPercentage` | 0 |  |
| `midtones.multiplier` | `PositiveReal` | 1 |  |
| `highlights.cyanRed` | `SignedPercentage` | 0 |  |
| `highlights.magentaGreen` | `SignedPercentage` | 0 |  |
| `highlights.yellowBlue` | `SignedPercentage` | 0 |  |
| `highlights.multiplier` | `PositiveReal` | 1 |  |
| `preserveLuminosity` | `Boolean` | true |  |
| `overallMultiplier` | `PositiveReal` | 1 |  |

### `ColorFunctionTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `channels.red` | `Boolean` | true |  |
| `channels.green` | `Boolean` | true |  |
| `channels.blue` | `Boolean` | true |  |
| `channels.alpha` | `Boolean` | false |  |
| `function.inputBlack` | `Percentage` | 0 |  |
| `function.inputGamma` | `PositiveReal` | 1 |  |
| `function.inputWhite` | `Percentage` | 1 |  |
| `function.outputBlack` | `Percentage` | 0 |  |
| `function.outputWhite` | `Percentage` | 1 |  |

### `ColorizeTextureModifier`

Presets: **Default** (Binarize)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `colorSelector.channel` | `TextureChannel` | 1 (luminance) | gray, luminance, red, green, blue, alpha, custom |
| `colorSelector.coefficients.red` | `Percentage` | 0.2126 |  |
| `colorSelector.coefficients.green` | `Percentage` | 0.7152 |  |
| `colorSelector.coefficients.blue` | `Percentage` | 0.0724 |  |
| `colorSelector.coefficients.alpha` | `Percentage` | 0 |  |
| `colorSelector.multiplyByAlpha` | `Boolean` | true |  |
| `colorSelector.function.inputBlack` | `Percentage` | 0 |  |
| `colorSelector.function.inputGamma` | `PositiveReal` | 1 |  |
| `colorSelector.function.inputWhite` | `Percentage` | 1 |  |
| `colorSelector.function.outputBlack` | `Percentage` | 0 |  |
| `colorSelector.function.outputWhite` | `Percentage` | 1 |  |
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.intermediateColor` | `HsvColor` | #808080 |  |
| `gradient.endColor` | `HsvColor` | #ffffff |  |
| `gradient.intermediatePosition` | `Percentage` | 0.5 |  |
| `gradient.midPoint1` | `Percentage` | 0.5 |  |
| `gradient.midPoint2` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps1` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.steps2` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |

### `DepthOfFieldTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `visualizeLayers` | `Boolean` | false |  |
| `blurLayerVisualization` | `Boolean` | false |  |
| `focusParameters.automatic` | `Boolean` | true |  |
| `focusParameters.overridePlacementDistance` | `Boolean` | false |  |
| `focusParameters.distance` | `PositiveMeters` | 3 |  |
| `focusParameters.focalRegion` | `PositiveMeters` | 5 |  |
| `focusParameters.nearTransition` | `PositiveMeters` | 3 |  |
| `focusParameters.farTransition` | `PositiveMeters` | 6 |  |
| `nearBlur.intensity` | `Percentage` | 1 |  |
| `nearBlur.radius` | `PositivePixels` | 15 |  |
| `nearBlur.shape` | `BlurShape` | 0 (gaussian) | gaussian, box, circle, ring, hexagonal, zoom, spin, directional, star4Branches, star8Branches, randomBox, randomCircle, randomTriangle, diffuse, custom |
| `nearBlur.quality.mipmapping` | `Boolean` | true |  |
| `nearBlur.style.luminosityThreshold` | `Percentage` | 0 |  |
| `nearBlur.style.blendingModeWithInput` | `BlendingMode` | 2 (normal) | passThrough, replace, normal, dissolve, darken, multiply, colorBurn, linearBurn, darkerColor, lighten, screen, colorDodge, linearDodge, lighterColor, overlay, softLight, hardLight, vividLight, linearLight, pinLight, hardMix, difference, exclusion, subtract, divide, hue, saturation, color, luminosity, alpha |
| `nearBlur.style.invertBlendingOrder` | `Boolean` | false |  |
| `nearBlur.style.outputLuminosity` | `UnboundedPercentage` | 1 |  |
| `nearBlur.style.maskInterpretation` | `BlurTextureMaskInterpretation` | 0 (fade) | fade, radius, radiusAndFade |
| `nearBlur.horizontalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `nearBlur.verticalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `farBlur.intensity` | `Percentage` | 1 |  |
| `farBlur.radius` | `PositivePixels` | 8 |  |
| `farBlur.shape` | `BlurShape` | 0 (gaussian) | gaussian, box, circle, ring, hexagonal, zoom, spin, directional, star4Branches, star8Branches, randomBox, randomCircle, randomTriangle, diffuse, custom |
| `farBlur.quality.mipmapping` | `Boolean` | true |  |
| `farBlur.style.luminosityThreshold` | `Percentage` | 0 |  |
| `farBlur.style.blendingModeWithInput` | `BlendingMode` | 2 (normal) | passThrough, replace, normal, dissolve, darken, multiply, colorBurn, linearBurn, darkerColor, lighten, screen, colorDodge, linearDodge, lighterColor, overlay, softLight, hardLight, vividLight, linearLight, pinLight, hardMix, difference, exclusion, subtract, divide, hue, saturation, color, luminosity, alpha |
| `farBlur.style.invertBlendingOrder` | `Boolean` | false |  |
| `farBlur.style.outputLuminosity` | `UnboundedPercentage` | 1 |  |
| `farBlur.style.maskInterpretation` | `BlurTextureMaskInterpretation` | 0 (fade) | fade, radius, radiusAndFade |
| `farBlur.horizontalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `farBlur.verticalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |

### `DepthOfFieldV8TextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `radius` | `PositivePixels` | 40 |  |
| `shape` | `BlurShape` | 2 (circle) | gaussian, box, circle, ring, hexagonal, zoom, spin, directional, star4Branches, star8Branches, randomBox, randomCircle, randomTriangle, diffuse, custom |
| `quality.budget.lookups` | `StrictlyPositiveInteger` | 100 |  |
| `quality.budget.perfectBudget` | `StrictlyPositiveInteger` | 1 |  |
| `quality.downSampling.enabled` | `Boolean` | true |  |
| `quality.pixelType.enabled` | `Boolean` | false |  |
| `quality.pixelType.value` | `PixelType` | 0 (clamped8Bits) | clamped8Bits, clamped10Bits, clamped16Bits, hdr16Bits, hdr32Bits |
| `quality.mipmapping` | `Boolean` | true |  |
| `quality.samplingParameters.minificationFilter` | `Boolean` | true |  |
| `quality.samplingParameters.magnificationFilter` | `Boolean` | true |  |
| `quality.samplingParameters.bindFilters` | `Boolean` | true |  |
| `quality.samplingParameters.horizontalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.verticalWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.depthWrapMode` | `TextureWrapMode` | 1 (mirroredRepeat) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.bindWrapModes` | `Boolean` | true |  |
| `quality.samplingParameters.anisotropy` | `PositiveInteger` | 16 |  |
| `quality.samplingParameters.compareWithDepth` | `Boolean` | false |  |
| `style.luminosityThreshold` | `Percentage` | 0 |  |
| `style.blendingModeWithInput` | `BlendingMode` | 1 (replace) | passThrough, replace, normal, dissolve, darken, multiply, colorBurn, linearBurn, darkerColor, lighten, screen, colorDodge, linearDodge, lighterColor, overlay, softLight, hardLight, vividLight, linearLight, pinLight, hardMix, difference, exclusion, subtract, divide, hue, saturation, color, luminosity, alpha |
| `style.invertBlendingOrder` | `Boolean` | false |  |
| `style.outputLuminosity` | `UnboundedPercentage` | 1 |  |
| `style.maskInterpretation` | `BlurTextureMaskInterpretation` | 0 (fade) | fade, radius, radiusAndFade |
| `horizontalWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `verticalWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `visualizeLayers` | `Boolean` | false |  |

### `DepthToNormalTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `softFactor` | `Percentage` | 0.1 |  |

### `DiscardAlphaTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `premultiplyByAlpha` | `Boolean` | false |  |

### `DisplaceTextureModifier`

Presets: **Default** (Displace - 100px, Displace - 500px, Displace - 1000px) ; **Advanced Presets** (Water Ripples, Shattered Glass, Curtains)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `inputResolution.width` | `PositiveInteger` | 0 |  |
| `inputResolution.height` | `PositiveInteger` | 0 |  |
| `mapScale.width` | `Real` | 1 |  |
| `mapScale.height` | `Real` | 1 |  |
| `mapScale.linked` | `Boolean` | true |  |
| `distance` | `Pixels` | 10 |  |
| `rotation` | `Angle` | 0 |  |

### `DrosteTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `ellipse.center.x` | `HorizontalCanvasValue` | 0.5 |  |
| `ellipse.center.y` | `VerticalCanvasValue` | 0.5 |  |
| `ellipse.size.width` | `PositivePixels` | 1000 |  |
| `ellipse.size.height` | `PositivePixels` | 1000 |  |
| `ellipse.size.linked` | `Boolean` | true |  |
| `ellipse.rotation` | `Angle` | 0 |  |
| `rectangular` | `Boolean` | false |  |
| `branches` | `Integer` | 1 |  |
| `scale` | `PositiveReal` | 0.25 |  |

### `EmbossTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `size.width` | `HorizontalCanvasValue` | 0 |  |
| `size.height` | `VerticalCanvasValue` | 0 |  |
| `size.linked` | `Boolean` | true |  |
| `type` | `EmbossModeList` | 0 (emboss) | emboss, edgeDetection |

### `FlipTextureModifier`

Presets: **Default** (Horizontal Flip, Vertical Flip, Flip Both)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `horizontalFlip` | `Boolean` | false |  |
| `verticalFlip` | `Boolean` | false |  |

### `FrameDelayTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `rasterizeQuality.automatic` | `Boolean` | true |  |
| `rasterizeQuality.gammaValue` | `GammaValue` | 1 |  |
| `rasterizeQuality.pixelType` | `PixelType` | 0 (clamped8Bits) | clamped8Bits, clamped10Bits, clamped16Bits, hdr16Bits, hdr32Bits |
| `rasterizeQuality.mipmapping` | `Boolean` | false |  |
| `rasterizeQuality.downSampling.width` | `DownSamplingFactor` | 0 (one) | one, oneOverTwo, oneOverFour, oneOverEight, oneOverSixteen, oneOverThiryTwo, oneOverSixtyFour |
| `rasterizeQuality.downSampling.height` | `DownSamplingFactor` | 0 (one) | one, oneOverTwo, oneOverFour, oneOverEight, oneOverSixteen, oneOverThiryTwo, oneOverSixtyFour |
| `rasterizeQuality.downSampling.link` | `Boolean` | true |  |
| `rasterizeQuality.samplingParameters.minificationFilter` | `Boolean` | true |  |
| `rasterizeQuality.samplingParameters.magnificationFilter` | `Boolean` | true |  |
| `rasterizeQuality.samplingParameters.bindFilters` | `Boolean` | true |  |
| `rasterizeQuality.samplingParameters.horizontalWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `rasterizeQuality.samplingParameters.verticalWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `rasterizeQuality.samplingParameters.depthWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `rasterizeQuality.samplingParameters.bindWrapModes` | `Boolean` | true |  |
| `rasterizeQuality.samplingParameters.anisotropy` | `PositiveInteger` | 16 |  |
| `rasterizeQuality.samplingParameters.compareWithDepth` | `Boolean` | false |  |
| `frames` | `PositiveInteger` | 1 |  |
| `blendingMode` | `BlendingMode` | 1 (replace) | passThrough, replace, normal, dissolve, darken, multiply, colorBurn, linearBurn, darkerColor, lighten, screen, colorDodge, linearDodge, lighterColor, overlay, softLight, hardLight, vividLight, linearLight, pinLight, hardMix, difference, exclusion, subtract, divide, hue, saturation, color, luminosity, alpha |

### `FreezeTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `quality.automatic` | `Boolean` | true |  |
| `quality.gammaValue` | `GammaValue` | 1 |  |
| `quality.pixelType` | `PixelType` | 0 (clamped8Bits) | clamped8Bits, clamped10Bits, clamped16Bits, hdr16Bits, hdr32Bits |
| `quality.mipmapping` | `Boolean` | false |  |
| `quality.downSampling.width` | `DownSamplingFactor` | 0 (one) | one, oneOverTwo, oneOverFour, oneOverEight, oneOverSixteen, oneOverThiryTwo, oneOverSixtyFour |
| `quality.downSampling.height` | `DownSamplingFactor` | 0 (one) | one, oneOverTwo, oneOverFour, oneOverEight, oneOverSixteen, oneOverThiryTwo, oneOverSixtyFour |
| `quality.downSampling.link` | `Boolean` | true |  |
| `quality.samplingParameters.minificationFilter` | `Boolean` | true |  |
| `quality.samplingParameters.magnificationFilter` | `Boolean` | true |  |
| `quality.samplingParameters.bindFilters` | `Boolean` | true |  |
| `quality.samplingParameters.horizontalWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.verticalWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.depthWrapMode` | `TextureWrapMode` | 3 (clampToEdge) | repeat, mirroredRepeat, clampToBorder, clampToEdge |
| `quality.samplingParameters.bindWrapModes` | `Boolean` | true |  |
| `quality.samplingParameters.anisotropy` | `PositiveInteger` | 16 |  |
| `quality.samplingParameters.compareWithDepth` | `Boolean` | false |  |

### `GrayscaleTextureModifier`

Presets: **Default** (balanced RGB, full Red, full Green, full Blue, Magenta, Yellow, Cyan, Full)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `redPower` | `Percentage` | 0.2989 |  |
| `greenPower` | `Percentage` | 0.587 |  |
| `bluePower` | `Percentage` | 0.114 |  |

### `HueSaturationLuminanceTextureModifier`

Presets: **Advanced Presets** (+20° Hue, -20° Hue, 180° Hue, Saturation +, Saturation ++, Saturation -, Saturation --, Grey)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `hue` | `Angle` | 0 |  |
| `saturation` | `SignedPercentage` | 0 |  |
| `luminance` | `SignedPercentage` | 0 |  |

### `MaskTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |

### `MatteTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `show.enabled` | `Boolean` | false |  |
| `show.value` | `MatteTextureDisplay` | 0 (inputImage) | inputImage, filteredImage, rawAlphaMatte, alphaMatte, shadow, despillAmount |
| `erode.enabled` | `Boolean` | true |  |
| `erode.radius` | `PositivePixels` | 1.5 |  |
| `erode.shape` | `MatteBlurShape` | 0 (gaussian) | gaussian, box, circle |
| `smoothEdges.enabled` | `Boolean` | false |  |
| `smoothEdges.radius` | `PositivePixels` | 1.5 |  |
| `smoothEdges.shape` | `MatteBlurShape` | 0 (gaussian) | gaussian, box, circle |
| `despill.enabled` | `Boolean` | true |  |
| `despill.amount` | `Percentage` | 0.5 |  |
| `despill.normalisation` | `MatteDespillNormalisation` | 0 (luminosity) | luminosity, backComponent, grayScale, none |
| `advancedMode` | `Boolean` | false |  |

### `OverlayTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `inputLevel` | `Percentage` | 1 |  |
| `modifiedLevel` | `Percentage` | 1 |  |
| `invertBlendingOrder` | `Boolean` | false |  |
| `blendingMode` | `BlendingMode` | 2 (normal) | passThrough, replace, normal, dissolve, darken, multiply, colorBurn, linearBurn, darkerColor, lighten, screen, colorDodge, linearDodge, lighterColor, overlay, softLight, hardLight, vividLight, linearLight, pinLight, hardMix, difference, exclusion, subtract, divide, hue, saturation, color, luminosity, alpha |

### `PolarCoordinatesTextureModifier`

Presets: **Default** (Polar Coordinates - 0 Repetitions, Polar Coordinates - 3 Repetitions, Polar Coordinates - 5 Repetitions, Polar Coordinates - 10 Repetitions) ; **Advanced Presets** (Mirror Polar Coordinates)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `circularRepetitions` | `PositiveReal` | 1 |  |
| `angle` | `Angle` | 0 |  |
| `angleDelta` | `Angle` | 0 |  |
| `radiusRepetitions` | `PositiveReal` | 1 |  |
| `radiusOffset` | `Percentage` | 0 |  |

### `RGBSeparateTextureModifier`

Presets: **Advanced Presets** (Small RGB)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `size.width` | `HorizontalCanvasValue` | 0 |  |
| `size.height` | `VerticalCanvasValue` | 0 |  |
| `size.linked` | `Boolean` | true |  |
| `sourceLevel` | `Percentage` | 0 |  |
| `hue` | `Percentage` | 0 |  |
| `scale` | `Real` | -0.005 |  |
| `radius.x` | `PositivePixels` | 5 |  |
| `radius.y` | `PositivePixels` | 5 |  |
| `radius.z` | `PositivePixels` | 5 |  |
| `radius.linked` | `Boolean` | true |  |
| `redAngle` | `Angle` | 0 |  |
| `greenAngle` | `Angle` | 120 |  |
| `blueAngle` | `Angle` | 240 |  |
| `normalized` | `Boolean` | false |  |
| `alphaProcessing` | `RGBSeparateAlphaProcessing` | 0 (separateAlpha) | separateAlpha, conserveAlpha |

### `RadialDistortionTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `undistort` | `Boolean` | false |  |
| `k1` | `Real` | 0 |  |
| `k2` | `Real` | 0 |  |

### `RedGreenBlueTextureModifier`

Presets: **Default** (Red, Green, Blue, Magenta, Cyan, Yellow, Black)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `color` | `HsvColor` | #ffffff |  |

### `ScrollTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `displayAspectRatio` | `Real` | 0 |  |
| `anchor.x` | `HorizontalCanvasValue` | 0.5 |  |
| `anchor.y` | `VerticalCanvasValue` | 0.5 |  |
| `rotation` | `Angle` | 0 |  |
| `scrollX` | `Percentage` | 0 |  |
| `scrollY` | `Percentage` | 0 |  |

### `SobelTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `size.width` | `HorizontalCanvasValue` | 0 |  |
| `size.height` | `VerticalCanvasValue` | 0 |  |
| `size.linked` | `Boolean` | true |  |
| `threshold` | `Percentage` | 0.4 |  |
| `edgesColor` | `HsvColor` | #000000 |  |
| `colorizeEdgesWithSource` | `Boolean` | false |  |
| `drawEdgesUnderSource` | `Boolean` | false |  |
| `sourceLevel` | `Percentage` | 0 |  |
| `blendingMode` | `BlendingMode` | 2 (normal) | passThrough, replace, normal, dissolve, darken, multiply, colorBurn, linearBurn, darkerColor, lighten, screen, colorDodge, linearDodge, lighterColor, overlay, softLight, hardLight, vividLight, linearLight, pinLight, hardMix, difference, exclusion, subtract, divide, hue, saturation, color, luminosity, alpha |

### `SparklesTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `precision.x` | `StrictlyPositiveInteger` | 100 |  |
| `precision.y` | `StrictlyPositiveInteger` | 100 |  |
| `precision.uniform` | `Boolean` | true |  |
| `attractionIterations` | `PositiveInteger` | 10 |  |
| `attractionStep` | `Percentage` | 0.1 |  |
| `intensityThreshold` | `Percentage` | 0.5 |  |
| `size.width` | `HorizontalCanvasValue` | 0 |  |
| `size.height` | `VerticalCanvasValue` | 0 |  |
| `size.linked` | `Boolean` | true |  |
| `lightness` | `Percentage` | 1 |  |
| `sourceLevel` | `Percentage` | 1 |  |

### `SwirlTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `ellipse.center.x` | `HorizontalCanvasValue` | 0.5 |  |
| `ellipse.center.y` | `VerticalCanvasValue` | 0.5 |  |
| `ellipse.size.width` | `PositivePixels` | 1500 |  |
| `ellipse.size.height` | `PositivePixels` | 1500 |  |
| `ellipse.size.linked` | `Boolean` | true |  |
| `ellipse.rotation` | `Angle` | 0 |  |
| `function.parameters.minimum` | `SignedPercentage` | -1 |  |
| `function.parameters.maximum` | `SignedPercentage` | 1 |  |
| `function.parameters.inverse` | `Boolean` | false |  |
| `function.parameters.period` | `PositiveReal` | 1 |  |
| `function.parameters.offset` | `UnboundedPercentage` | 0 |  |
| `function.parameters.phase` | `Percentage` | 0.5 |  |
| `function.parameters.repetitions` | `StrictlyPositiveInteger` | 1 |  |
| `strength` | `Angle` | 5 |  |

### `TemperatureTextureModifier`

Presets: **Default** (Cold Filter 1, Cold Filter 2, Warm Filter 1, Warm Filter 2, Warm Filter 3)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `red` | `Percentage` | 0.5 |  |
| `green` | `Percentage` | 0.5 |  |
| `blue` | `Percentage` | 0.5 |  |
| `preserveLuminosity` | `Boolean` | true |  |

### `TilesTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `patternWrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `patternWrapModes.top` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `patternWrapModes.bottom` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `patternWrapModes.left` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `patternWrapModes.right` | `FrameWrapMode` | 0 (transparent) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `uniformTiles` | `Boolean` | true |  |
| `scaleMin.width` | `Real` | 1 |  |
| `scaleMin.height` | `Real` | 1 |  |
| `scaleMin.linked` | `Boolean` | true |  |
| `scaleMax.width` | `Real` | 1 |  |
| `scaleMax.height` | `Real` | 1 |  |
| `scaleMax.linked` | `Boolean` | true |  |
| `neighborhoodOverlap` | `Boolean` | false |  |
| `angleMin` | `Angle` | 0 |  |
| `angleMax` | `Angle` | 0 |  |
| `opacityMin` | `Percentage` | 1 |  |
| `opacityMax` | `Percentage` | 1 |  |
| `colorizeMin` | `Percentage` | 1 |  |
| `colorizeMax` | `Percentage` | 1 |  |

### `Transform2dTextureModifier`

Presets: **Default** (2D Transform - Horizontal Flip, 2D Transform - Vertical Flip, 2D Transform - Top Left Anchor, 2D Transform - Bottom Right Anchor, 2D Transform - Bottom Left Anchor, 2D Transform - Top Right Anchor) ; **Advanced Presets** (Horizontal repeat, Mirror Repeat, Transparent, Mirror Right, Mirror Left)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `wrapModes.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `wrapModes.top` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.bottom` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.left` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |
| `wrapModes.right` | `FrameWrapMode` | 3 (repeat) | transparent, black, white, repeat, mirroredRepeat, edge, blurredEdge |

### `TritoneTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `channel` | `TextureChannel` | 1 (luminance) | gray, luminance, red, green, blue, alpha, custom |
| `level.inputBlack` | `Percentage` | 0 |  |
| `level.inputGamma` | `PositiveReal` | 1 |  |
| `level.inputWhite` | `Percentage` | 1 |  |
| `level.outputBlack` | `Percentage` | 0 |  |
| `level.outputWhite` | `Percentage` | 1 |  |
| `threshold` | `Percentage` | 0.5 |  |
| `lowColor` | `HsvColor` | #000000 |  |
| `mediumColor` | `HsvColor` | #808080 |  |
| `highColor` | `HsvColor` | #ffffff |  |

### `UpscaleTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `algorithm` | `UpscaleAlgorithm` | 0 (SimpleUpscale) | SimpleUpscale, SuperRes |
| `upscaleFactor` | `UpscaleFactor` | 2 (x2) | x4_3, x1_5, x2, x3, x4 |
| `withoutMaxine` | `Boolean` | false |  |
| `enhence` | `Percentage` | 0.4 |  |
| `strong` | `Boolean` | false |  |

### `VibranceTextureModifier`

Presets: **Advanced Presets** (Vibrance -, Vibrance +)

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `vibrance` | `SignedPercentage` | 0.5 |  |

### `WarpTextureModifier`

| path | Oil class | default | choices |
|---|---|---|---|
| `intensity` | `Percentage` | 1 |  |
| `precision.x` | `StrictlyPositiveInteger` | 1 |  |
| `precision.y` | `StrictlyPositiveInteger` | 1 |  |
| `precision.uniform` | `Boolean` | true |  |
| `editSource` | `Boolean` | true |  |
| `keepInputAsBackground` | `Boolean` | false |  |
| `perspectiveMapping` | `Boolean` | false |  |
| `filtering` | `Boolean` | true |  |

## Texture masks (`MaskTextureModifier.masks`, `modifier.masks`)

### `ColorTextureMask`

Presets: **Default** (Chroma Key, Chroma Key - Sky, Chroma Key - Green Screen, Chroma Key - Blue Screen, Chroma Key - Black, Chroma Key - White)

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `colorSelector.channel` | `TextureChannel` | 1 (luminance) | gray, luminance, red, green, blue, alpha, custom |
| `colorSelector.coefficients.red` | `Percentage` | 0.2126 |  |
| `colorSelector.coefficients.green` | `Percentage` | 0.7152 |  |
| `colorSelector.coefficients.blue` | `Percentage` | 0.0724 |  |
| `colorSelector.coefficients.alpha` | `Percentage` | 0 |  |
| `colorSelector.multiplyByAlpha` | `Boolean` | true |  |
| `colorSelector.function.inputBlack` | `Percentage` | 0 |  |
| `colorSelector.function.inputGamma` | `PositiveReal` | 1 |  |
| `colorSelector.function.inputWhite` | `Percentage` | 1 |  |
| `colorSelector.function.outputBlack` | `Percentage` | 0 |  |
| `colorSelector.function.outputWhite` | `Percentage` | 1 |  |

### `DepthTextureMask`

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `distanceInterval.center` | `PositiveMeters` | 5 |  |
| `distanceInterval.size` | `Meters` | 10 |  |
| `distanceInterval.begin` | `PositiveMeters` | 0 |  |
| `distanceInterval.end` | `PositiveMeters` | 10 |  |
| `distanceInterval.invertible` | `Boolean` | true |  |
| `includeBackground` | `Boolean` | true |  |
| `function.parameters.minimum` | `Percentage` | 0 |  |
| `function.parameters.maximum` | `Percentage` | 1 |  |
| `function.parameters.inverse` | `Boolean` | false |  |
| `function.parameters.period` | `Percentage` | 1 |  |
| `function.parameters.offset` | `UnboundedPercentage` | 0 |  |
| `function.parameters.phase` | `Percentage` | 0.5 |  |
| `function.parameters.repetitions` | `StrictlyPositiveInteger` | 1 |  |

### `FunctionTextureMask`

Presets: **Default** (Linear fx Mask, Placement fx Mask, Circular Fx Gradient Mask)

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `mask.blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `mask.opacity` | `Percentage` | 1 |  |
| `mask.inverse` | `Boolean` | false |  |
| `mask.segment.begin.x` | `HorizontalCanvasValue` | 0.5 |  |
| `mask.segment.begin.y` | `VerticalCanvasValue` | 0 |  |
| `mask.segment.end.x` | `HorizontalCanvasValue` | 0.5 |  |
| `mask.segment.end.y` | `VerticalCanvasValue` | 1 |  |
| `function.parameters.minimum` | `Percentage` | 0 |  |
| `function.parameters.maximum` | `Percentage` | 1 |  |
| `function.parameters.inverse` | `Boolean` | false |  |
| `function.parameters.period` | `Percentage` | 1 |  |
| `function.parameters.offset` | `UnboundedPercentage` | 0 |  |
| `function.parameters.phase` | `Percentage` | 0.5 |  |
| `function.parameters.repetitions` | `StrictlyPositiveInteger` | 1 |  |

### `GradientTextureMask`

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `smoothness` | `PositiveReal` | 2 |  |
| `position.center.x` | `HorizontalCanvasValue` | 0.5 |  |
| `position.center.y` | `VerticalCanvasValue` | 0.5 |  |
| `position.size.width` | `PositivePixels` | 1000 |  |
| `position.size.height` | `PositivePixels` | 1000 |  |
| `position.size.linked` | `Boolean` | false |  |
| `position.rotation` | `Angle` | 0 |  |
| `function.inputBlack` | `Percentage` | 0 |  |
| `function.inputGamma` | `PositiveReal` | 1 |  |
| `function.inputWhite` | `Percentage` | 1 |  |
| `function.outputBlack` | `Percentage` | 0 |  |
| `function.outputWhite` | `Percentage` | 1 |  |

### `LinearTextureMask`

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `segment.begin.x` | `HorizontalCanvasValue` | 0.5 |  |
| `segment.begin.y` | `VerticalCanvasValue` | 0 |  |
| `segment.end.x` | `HorizontalCanvasValue` | 0.5 |  |
| `segment.end.y` | `VerticalCanvasValue` | 1 |  |

### `NoiseTextureMask`

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `seed.value` | `PositiveInteger` | 0 |  |
| `seed.incrementAtActivation` | `Boolean` | false |  |
| `scale.width` | `PositivePixels` | 100 |  |
| `scale.height` | `PositivePixels` | 100 |  |
| `scale.linked` | `Boolean` | true |  |
| `offset.x` | `HorizontalCanvasValue` | 0.5 |  |
| `offset.y` | `VerticalCanvasValue` | 0.5 |  |
| `fractalize` | `Percentage` | 1 |  |
| `octaves` | `StrictlyPositiveInteger` | 1 |  |
| `frequencyMultiplier` | `Percentage` | 0.5 |  |
| `absolute` | `Boolean` | false |  |

### `PeopleTextureMask`

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `blockSize` | `StrictlyPositiveInteger` | 16 |  |

### `PlacementTextureMask`

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `feather.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `feather.top` | `ClampedVerticalCanvasValue` | 0 |  |
| `feather.bottom` | `ClampedVerticalCanvasValue` | 0 |  |
| `feather.left` | `ClampedHorizontalCanvasValue` | 0 |  |
| `feather.right` | `ClampedHorizontalCanvasValue` | 0 |  |
| `feather.exponent` | `PositiveReal` | 2 |  |
| `feather.centralBrightness` | `Percentage` | 0.5 |  |
| `gamma` | `GammaValue` | 1 |  |
| `dithering` | `Percentage` | 0 |  |

### `RadialTextureMask`

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `ellipse.center.x` | `HorizontalCanvasValue` | 0.5 |  |
| `ellipse.center.y` | `VerticalCanvasValue` | 0.5 |  |
| `ellipse.size.width` | `PositivePixels` | 1000 |  |
| `ellipse.size.height` | `PositivePixels` | 1000 |  |
| `ellipse.size.linked` | `Boolean` | true |  |
| `ellipse.rotation` | `Angle` | 0 |  |
| `feather.link` | `FrameSidesLink` | 4 (all) | none, leftRight, topBottom, leftRightAndTopBottom, all |
| `feather.top` | `ClampedVerticalCanvasValue` | 0 |  |
| `feather.bottom` | `ClampedVerticalCanvasValue` | 0 |  |
| `feather.left` | `ClampedHorizontalCanvasValue` | 0 |  |
| `feather.right` | `ClampedHorizontalCanvasValue` | 0 |  |
| `feather.exponent` | `PositiveReal` | 2 |  |
| `feather.centralBrightness` | `Percentage` | 0.5 |  |
| `fillOutside` | `Boolean` | false |  |

### `ShapeTextureMask`

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `feather.enabled` | `Boolean` | true |  |
| `feather.width` | `PositivePixels` | 0 |  |
| `feather.centering` | `SignedPercentage` | -1 |  |
| `feather.exponent` | `PositiveReal` | 2 |  |
| `feather.centralBrightness` | `Percentage` | 0.5 |  |
| `semiTransparentWhileUnclosed` | `Boolean` | true |  |
| `enableAntiAliasing` | `Boolean` | true |  |

### `TextureLayerTextureMask`

Presets: **Default** (Compo Mask, Noise Mask, Parent Input Mask, CheckerBoard, CheckerBoard Horizontal Lines, CheckerBoard Vertical Lines)

| path | Oil class | default | choices |
|---|---|---|---|
| `blendingMode` | `TextureMaskBlendingMode` | 0 (add) | add, remove, multiply, replace |
| `opacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `colorSelector.channel` | `TextureChannel` | 1 (luminance) | gray, luminance, red, green, blue, alpha, custom |
| `colorSelector.coefficients.red` | `Percentage` | 0.2126 |  |
| `colorSelector.coefficients.green` | `Percentage` | 0.7152 |  |
| `colorSelector.coefficients.blue` | `Percentage` | 0.0724 |  |
| `colorSelector.coefficients.alpha` | `Percentage` | 0 |  |
| `colorSelector.multiplyByAlpha` | `Boolean` | true |  |
| `colorSelector.function.inputBlack` | `Percentage` | 0 |  |
| `colorSelector.function.inputGamma` | `PositiveReal` | 1 |  |
| `colorSelector.function.inputWhite` | `Percentage` | 1 |  |
| `colorSelector.function.outputBlack` | `Percentage` | 0 |  |
| `colorSelector.function.outputWhite` | `Percentage` | 1 |  |

## Texture generators (`TextureLayer.generator`, a material map, a mask image)

### `BrickTextureGenerator`

Presets: **Default** (Canvas, CrossWalk Vertical)

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #b71400 |  |
| `gradient.endColor` | `HsvColor` | #d9dbd6 |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `brickSize.width` | `HorizontalCanvasValue` | 0.3 |  |
| `brickSize.height` | `VerticalCanvasValue` | 0.15 |  |
| `brickSize.linked` | `Boolean` | false |  |
| `brickRatioWidth` | `Percentage` | 0.9 |  |
| `brickRatioHeight` | `Percentage` | 0.85 |  |
| `offsetPositionX` | `Percentage` | 0.1 |  |
| `offsetPositionY` | `Percentage` | 0.1 |  |

### `CheckerBoardTextureGenerator`

Presets: **Default** (Alpha Simulation, Black and White 10px, Black and White 2x2, Black and White 5x5, Horizontal Bands 10%, Horizontal Bands 1px, Vertical Bands 10%, Vertical Bands 1px)

| path | Oil class | default | choices |
|---|---|---|---|
| `oddColor` | `HsvColor` | #000000 |  |
| `evenColor` | `HsvColor` | #ffffff |  |
| `size.width` | `HorizontalCanvasValue` | 0.1 |  |
| `size.height` | `VerticalCanvasValue` | 0.1 |  |
| `size.linked` | `Boolean` | true |  |
| `offset.x` | `HorizontalCanvasValue` | 0 |  |
| `offset.y` | `VerticalCanvasValue` | 0 |  |
| `balance.width` | `SignedPercentage` | 0 |  |
| `balance.height` | `SignedPercentage` | 0 |  |
| `balance.linked` | `Boolean` | false |  |

### `DotsTextureGenerator`

Presets: **Default** (CheckerBoard, CheckerBoard n Dots)

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.endColor` | `HsvColor` | #ffffff |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `angle` | `Angle` | 0 |  |
| `sharpness` | `SignedPercentage` | 0.6 |  |
| `offset.x` | `HorizontalCanvasValue` | 0.5 |  |
| `offset.y` | `VerticalCanvasValue` | 0.5 |  |
| `dotSize.width` | `HorizontalCanvasValue` | 0.1 |  |
| `dotSize.height` | `VerticalCanvasValue` | 0.1 |  |
| `dotSize.linked` | `Boolean` | true |  |

### `GlitchTextureGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `frequency` | `FramePerSecond` | 50 |  |
| `periodInFrames.enabled` | `Boolean` | true |  |
| `periodInFrames.value` | `StrictlyPositiveInteger` | 1 |  |
| `color` | `HsvColor` | #ffffff |  |
| `glitch` | `Boolean` | true |  |

### `LensFlareTextureGenerator`

Presets: **Default** (Dirt Flare Horizontal, Dirt Flare Thin Light, Dirt Flare Thin Light II, Horizontal Blue, Horizontal light, Horizontal light 2, Horizontal light 3, Horizontal light II, Red Bright , Sun Glare, Sun Glare 2, Sun flare, Sun flare God Rays, Default Flare, Default Flare Light, Default Flare Octogonal)

| path | Oil class | default | choices |
|---|---|---|---|
| `segment.begin.x` | `HorizontalCanvasValue` | 0 |  |
| `segment.begin.y` | `VerticalCanvasValue` | 0 |  |
| `segment.end.x` | `HorizontalCanvasValue` | 1 |  |
| `segment.end.y` | `VerticalCanvasValue` | 1 |  |

### `LinearGradientTextureGenerator`

Presets: **Default** (Black -> Transparent, White -> Transparent, Black -> Transparent (Horizontal), White -> Transparent (Horizontal))

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.endColor` | `HsvColor` | #ffffff |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `segment.begin.x` | `HorizontalCanvasValue` | 0.5 |  |
| `segment.begin.y` | `VerticalCanvasValue` | 0 |  |
| `segment.end.x` | `HorizontalCanvasValue` | 0.5 |  |
| `segment.end.y` | `VerticalCanvasValue` | 1 |  |

### `MandelbrotFractalsTextureGenerator`

Presets: **Default** (MandelSmoke, MandelSnow, MandelSnow 2, Mandel Hugo I, Mandel Hugo II, Julia I, Julia II, Julia III, Close I, Pyramid) ; **Advanced Presets** (MandelSmoke, MandelSnow, MandelSnow 2, Mandel Hugo I, Mandel Hugo II, Julia I, Julia II, Julia III, Close I, Pyramid)

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.endColor` | `HsvColor` | #ffffff |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `iterations` | `StrictlyPositiveInteger` | 45 |  |
| `anchor.x` | `HorizontalCanvasValue` | 0.5 |  |
| `anchor.y` | `VerticalCanvasValue` | 0.5 |  |
| `position.x` | `HorizontalCanvasValue` | 0.95 |  |
| `position.y` | `VerticalCanvasValue` | 0.5 |  |
| `distortOffset.x` | `HorizontalCanvasValue` | 0 |  |
| `distortOffset.y` | `VerticalCanvasValue` | 0 |  |
| `size.width` | `Real` | 0.3 |  |
| `size.height` | `Real` | 0.45 |  |
| `size.linked` | `Boolean` | false |  |
| `distortScale.width` | `Real` | 1 |  |
| `distortScale.height` | `Real` | 1 |  |
| `distortScale.linked` | `Boolean` | false |  |

### `MarbleTextureGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #e6e3d6 |  |
| `gradient.endColor` | `HsvColor` | #0000ff |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `noiseScale.x` | `Real` | 0.5 |  |
| `noiseScale.y` | `Real` | 0.1 |  |
| `noiseScale.z` | `Real` | 0.1 |  |
| `noiseScale.linked` | `Boolean` | false |  |
| `amplify` | `PositiveReal` | 0.5 |  |

### `MonjoriTextureGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `horizontalDistort` | `Real` | 1 |  |
| `verticalDistort` | `Real` | 1 |  |
| `vortexize` | `Real` | 1 |  |
| `colorize` | `Real` | 0.52 |  |

### `MultiPointGradientTextureGenerator`

Presets: **Default** (3 Points Gradient, 4 Points Gradient, 5 Points Gradient)

| path | Oil class | default | choices |
|---|---|---|---|
| `sharpness` | `PositiveReal` | 5 |  |
| `interpolator` | `MultiPointGradientInterpolator` | 0 (blend) | blend, discriminate |
| `border.enabled` | `Boolean` | false |  |
| `border.value.color` | `HsvColor` | #000000 |  |
| `border.value.strength` | `PositiveReal` | 1 |  |

### `NoiseTextureGenerator`

Presets: **Default** (Chiseled, Cobblestone, Fractured Cell, Perlin, Simplex)

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.endColor` | `HsvColor` | #ffffff |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `seed.value` | `PositiveInteger` | 0 |  |
| `seed.incrementAtActivation` | `Boolean` | false |  |
| `scale.width` | `PositivePixels` | 100 |  |
| `scale.height` | `PositivePixels` | 100 |  |
| `scale.linked` | `Boolean` | true |  |
| `offset.x` | `HorizontalCanvasValue` | 0.5 |  |
| `offset.y` | `VerticalCanvasValue` | 0.5 |  |
| `fractalize` | `Percentage` | 1 |  |
| `octaves` | `StrictlyPositiveInteger` | 1 |  |
| `frequencyMultiplier` | `Percentage` | 0.5 |  |
| `absolute` | `Boolean` | false |  |

### `RadialFunctionTextureGenerator`

Presets: **Default** (Noise Radial Function, Audio Waveform Radial Function, Audio Spectrum Radial Function, Keyframe Radial Function)

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.endColor` | `HsvColor` | #ffffff |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `function.parameters.minimum` | `PositiveReal` | 0 |  |
| `function.parameters.maximum` | `PositiveReal` | 1 |  |
| `function.parameters.inverse` | `Boolean` | false |  |
| `function.parameters.period` | `SingleTurnAngle` | 6.2832 |  |
| `function.parameters.offset` | `UnboundedPercentage` | 0 |  |
| `function.parameters.phase` | `Percentage` | 0.5 |  |
| `function.parameters.repetitions` | `StrictlyPositiveInteger` | 1 |  |
| `ellipse.center.x` | `HorizontalCanvasValue` | 0.5 |  |
| `ellipse.center.y` | `VerticalCanvasValue` | 0.5 |  |
| `ellipse.size.width` | `PositivePixels` | 1000 |  |
| `ellipse.size.height` | `PositivePixels` | 1000 |  |
| `ellipse.size.linked` | `Boolean` | true |  |
| `ellipse.rotation` | `Angle` | 0 |  |
| `center.x` | `HorizontalCanvasValue` | 0.5 |  |
| `center.y` | `VerticalCanvasValue` | 0.5 |  |

### `RadialGradientTextureGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.endColor` | `HsvColor` | #ffffff |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `ellipse.center.x` | `HorizontalCanvasValue` | 0.5 |  |
| `ellipse.center.y` | `VerticalCanvasValue` | 0.5 |  |
| `ellipse.size.width` | `PositivePixels` | 1000 |  |
| `ellipse.size.height` | `PositivePixels` | 1000 |  |
| `ellipse.size.linked` | `Boolean` | true |  |
| `ellipse.rotation` | `Angle` | 0 |  |

### `SoftEdgeTextureGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.endColor` | `HsvColor` | #000000 |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `orientation` | `Placement2dOrientation` | 0 (normal) | normal, rotated90Cw, rotated180, rotated90Ccw |
| `interval.center` | `Percentage` | 0.5 |  |
| `interval.size` | `SignedPercentage` | 1 |  |
| `interval.begin` | `Percentage` | 0 |  |
| `interval.end` | `Percentage` | 1 |  |
| `interval.invertible` | `Boolean` | true |  |
| `power` | `PositiveReal` | 2 |  |
| `centralBrightness` | `Percentage` | 0.5 |  |
| `gamma` | `PositiveReal` | 2.2 |  |

### `TestPatternTextureGenerator`

Presets: **Default** (Corners, Text Info, Circles, Fine grid, 100 Px Grid, 512 Px Grid, 8 Px Grid, Edges and Moving Bars, 8 Px Grid And Corners, Colored Grid, Colored Grid and labels)

| path | Oil class | default | choices |
|---|---|---|---|
| `opacity` | `Percentage` | 1 |  |
| `tilesResolution.enabled` | `Boolean` | false |  |
| `tilesResolution.value.width` | `PositivePixels` | 120 |  |
| `tilesResolution.value.height` | `PositivePixels` | 120 |  |
| `tilesResolution.value.linked` | `Boolean` | false |  |
| `tilesCount.x` | `StrictlyPositiveInteger` | 16 |  |
| `tilesCount.y` | `StrictlyPositiveInteger` | 9 |  |
| `tilesCount.uniform` | `Boolean` | false |  |
| `gridJustification` | `Justification` | 4 (topLeft) | middleCenter, middleLeft, middleRight, topCenter, topLeft, topRight, bottomCenter, bottomLeft, bottomRight |
| `background` | `HsvColor` | #000000 |  |
| `coloredCheckerBoard.enabled` | `Boolean` | false |  |
| `coloredCheckerBoard.orientation` | `Orientation` | 1 (horizontal) | vertical, horizontal |
| `coloredCheckerBoard.individualModules.x` | `StrictlyPositiveInteger` | 4 |  |
| `coloredCheckerBoard.individualModules.y` | `StrictlyPositiveInteger` | 4 |  |
| `coloredCheckerBoard.individualModules.uniform` | `Boolean` | true |  |
| `grid.enabled` | `Boolean` | true |  |
| `grid.color` | `HsvColor` | #ffffff |  |
| `grid.thickness` | `PositiveReal` | 1 |  |
| `tileLabels.enabled` | `Boolean` | false |  |
| `tileLabels.color` | `HsvColor` | #ffffff |  |
| `tileLabels.size` | `Percentage` | 0.7 |  |
| `tileLabels.outline` | `Boolean` | true |  |
| `cornerCircles.enabled` | `Boolean` | true |  |
| `cornerCircles.color` | `HsvColor` | #ffffff |  |
| `cornerCircles.thickness` | `PositiveReal` | 2 |  |
| `cornerCirclesCount` | `StrictlyPositiveInteger` | 1 |  |
| `centeredCircles.enabled` | `Boolean` | true |  |
| `centeredCircles.color` | `HsvColor` | #ffffff |  |
| `centeredCircles.thickness` | `PositiveReal` | 2 |  |
| `centeredCirclesCount` | `StrictlyPositiveInteger` | 5 |  |
| `diagonals.enabled` | `Boolean` | true |  |
| `diagonals.color` | `HsvColor` | #ffffff |  |
| `diagonals.thickness` | `PositiveReal` | 1 |  |
| `edges.enabled` | `Boolean` | true |  |
| `edges.color` | `HsvColor` | #0000ff |  |
| `edges.thickness` | `PositiveReal` | 1 |  |
| `corners.enabled` | `Boolean` | true |  |
| `corners.color` | `HsvColor` | #ff0000 |  |
| `corners.thickness` | `PositiveReal` | 1 |  |
| `logo.enabled` | `Boolean` | true |  |
| `logo.alpha` | `Percentage` | 0.6 |  |
| `logo.size` | `Percentage` | 0.35 |  |
| `labelText.enabled` | `Boolean` | true |  |
| `labelText.color` | `HsvColor` | #ffffff |  |
| `labelText.size` | `Percentage` | 0.15 |  |
| `resolutionText.enabled` | `Boolean` | false |  |
| `resolutionText.color` | `HsvColor` | #ffffff |  |
| `resolutionText.size` | `Percentage` | 0.1 |  |
| `textPosition` | `Justification` | 0 (middleCenter) | middleCenter, middleLeft, middleRight, topCenter, topLeft, topRight, bottomCenter, bottomLeft, bottomRight |
| `movingBarsPeriod` | `Seconds` | 3 |  |
| `horizontalBar.enabled` | `Boolean` | false |  |
| `horizontalBar.color` | `HsvColor` | #ff0000 |  |
| `horizontalBar.thickness` | `PositiveReal` | 4 |  |
| `verticalBar.enabled` | `Boolean` | false |  |
| `verticalBar.color` | `HsvColor` | #ff0000 |  |
| `verticalBar.thickness` | `PositiveReal` | 4 |  |

### `UniformTextureGenerator`

Presets: **Default** (White, Black, Red, Green, Blue, Cyan, Magenta, Yellow, Grey)

| path | Oil class | default | choices |
|---|---|---|---|
| `color` | `HsvColor` | #000000 |  |

### `WhiteNoiseTextureGenerator`

Presets: **Default** (Colored White Noise, RGB Noise)

| path | Oil class | default | choices |
|---|---|---|---|
| `centralColor` | `HsvColor` | #808080 |  |
| `hueRandom` | `Percentage` | 0 |  |
| `saturationRandom` | `Percentage` | 0 |  |
| `lightnessRandom` | `Percentage` | 1 |  |
| `alphaRandom` | `Percentage` | 0 |  |

### `WoodTextureGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `gradient.beginColor` | `HsvColor` | #994c1a |  |
| `gradient.endColor` | `HsvColor` | #663312 |  |
| `gradient.midPoint` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |
| `noiseScale.width` | `Real` | 0.5 |  |
| `noiseScale.height` | `Real` | 0.1 |  |
| `noiseScale.linked` | `Boolean` | false |  |
| `noisiness` | `PositiveReal` | 10 |  |
| `ringFrequency` | `PositiveReal` | 10 |  |

## 3D colour sources of a PBR channel (no UV)

### `CheckerBoard3dTexture`

| path | Oil class | default | choices |
|---|---|---|---|
| `oddColor` | `HsvColor` | #000000 |  |
| `evenColor` | `HsvColor` | #ffffff |  |
| `count.x` | `PositiveReal` | 2 |  |
| `count.y` | `PositiveReal` | 2 |  |
| `count.z` | `PositiveReal` | 2 |  |
| `count.linked` | `Boolean` | true |  |

### `Gradient3dColorizer`

| path | Oil class | default | choices |
|---|---|---|---|
| `shape` | `GeometryMaskPreset` | 0 (u) | u, v, x, y, z, custom |
| `gradient.beginColor` | `HsvColor` | #000000 |  |
| `gradient.intermediateColor` | `HsvColor` | #808080 |  |
| `gradient.endColor` | `HsvColor` | #ffffff |  |
| `gradient.intermediatePosition` | `Percentage` | 0.5 |  |
| `gradient.midPoint1` | `Percentage` | 0.5 |  |
| `gradient.midPoint2` | `Percentage` | 0.5 |  |
| `gradient.quantize` | `Boolean` | false |  |
| `gradient.steps1` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.steps2` | `StrictlyPositiveInteger` | 2 |  |
| `gradient.smoothing` | `Percentage` | 0 |  |
| `gradient.ditherize` | `Percentage` | 0 |  |

### `UVW3dTexture`

| path | Oil class | default | choices |
|---|---|---|---|
| `gamma` | `GammaValue` | 2.2 |  |

## Geometry generators (`GeometryLayer.generator`)

### `BoxGeometryGenerator`

Presets: **Default** (Box - Precision 1, Box - Precision 100, Box - Precision 500, Box - Precision 1000)

| path | Oil class | default | choices |
|---|---|---|---|
| `size.x` | `PositiveMeters` | 1 |  |
| `size.y` | `PositiveMeters` | 1 |  |
| `size.z` | `PositiveMeters` | 1 |  |
| `size.linked` | `Boolean` | true |  |
| `precision.x` | `StrictlyPositiveInteger` | 10 |  |
| `precision.y` | `StrictlyPositiveInteger` | 10 |  |
| `precision.z` | `StrictlyPositiveInteger` | 10 |  |
| `precision.uniform` | `Boolean` | true |  |
| `uvMode` | `BoxUVMode` | 0 (repeatOnEachFace) | repeatOnEachFace, horizontalSplit, verticalSplit, crossHorizontal |
| `faces.positiveX` | `Boolean` | true |  |
| `faces.negativeX` | `Boolean` | true |  |
| `faces.positiveY` | `Boolean` | true |  |
| `faces.negativeY` | `Boolean` | true |  |
| `faces.positiveZ` | `Boolean` | true |  |
| `faces.negativeZ` | `Boolean` | true |  |
| `widthSlice.center` | `Percentage` | 0.5 |  |
| `widthSlice.size` | `SignedPercentage` | 1 |  |
| `widthSlice.begin` | `Percentage` | 0 |  |
| `widthSlice.end` | `Percentage` | 1 |  |
| `widthSlice.invertible` | `Boolean` | true |  |
| `heightSlice.center` | `Percentage` | 0.5 |  |
| `heightSlice.size` | `SignedPercentage` | 1 |  |
| `heightSlice.begin` | `Percentage` | 0 |  |
| `heightSlice.end` | `Percentage` | 1 |  |
| `heightSlice.invertible` | `Boolean` | true |  |
| `wireframe` | `Wireframe` | 0 (all) | all, onlyOnU, onlyOnV |
| `axisWireframe` | `AxisWireframe` | 0 (completeAxis) | completeAxis, xYAxisWireframe, yZAxisWireframe, xZAxisWireframe |

### `CapsuleGeometryGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `heightPrecision` | `StrictlyPositiveInteger` | 1 |  |
| `capPrecision` | `StrictlyPositiveInteger` | 50 |  |
| `rotationPrecision` | `StrictlyPositiveInteger` | 50 |  |
| `radius` | `PositiveMeters` | 0.1 |  |
| `height` | `PositiveMeters` | 1 |  |
| `horizontalSlice.center` | `Percentage` | 0.5 |  |
| `horizontalSlice.size` | `SignedPercentage` | 1 |  |
| `horizontalSlice.begin` | `Percentage` | 0 |  |
| `horizontalSlice.end` | `Percentage` | 1 |  |
| `horizontalSlice.invertible` | `Boolean` | true |  |
| `verticalSlice.center` | `Percentage` | 0.5 |  |
| `verticalSlice.size` | `SignedPercentage` | 1 |  |
| `verticalSlice.begin` | `Percentage` | 0 |  |
| `verticalSlice.end` | `Percentage` | 1 |  |
| `verticalSlice.invertible` | `Boolean` | true |  |
| `wireframe` | `Wireframe` | 0 (all) | all, onlyOnU, onlyOnV |

### `CircleGeometryGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `radius` | `PositiveMeters` | 1 |  |
| `precision` | `StrictlyPositiveInteger` | 50 |  |

### `CylinderGeometryGenerator`

Presets: **Default** (Cylinder - Precision 100, Cylinder - Precision 500, Cylinder - Precision 1000)

| path | Oil class | default | choices |
|---|---|---|---|
| `precision.x` | `StrictlyPositiveInteger` | 50 |  |
| `precision.y` | `StrictlyPositiveInteger` | 10 |  |
| `precision.uniform` | `Boolean` | false |  |
| `radius.width` | `PositiveMeters` | 1 |  |
| `radius.height` | `PositiveMeters` | 1 |  |
| `radius.linked` | `Boolean` | true |  |
| `height` | `PositiveMeters` | 2 |  |
| `horizontalSlice.center` | `Percentage` | 0.5 |  |
| `horizontalSlice.size` | `SignedPercentage` | 1 |  |
| `horizontalSlice.begin` | `Percentage` | 0 |  |
| `horizontalSlice.end` | `Percentage` | 1 |  |
| `horizontalSlice.invertible` | `Boolean` | true |  |
| `verticalSlice.center` | `Percentage` | 0.5 |  |
| `verticalSlice.size` | `SignedPercentage` | 1 |  |
| `verticalSlice.begin` | `Percentage` | 0 |  |
| `verticalSlice.end` | `Percentage` | 1 |  |
| `verticalSlice.invertible` | `Boolean` | true |  |
| `topCap` | `Boolean` | true |  |
| `bottomCap` | `Boolean` | true |  |
| `wireframe` | `Wireframe` | 0 (all) | all, onlyOnU, onlyOnV |
| `wireframeCaps` | `Boolean` | false |  |

### `FunctionSplineGeometryGenerator`

Presets: **Default** (Function Spline - Circle)

| path | Oil class | default | choices |
|---|---|---|---|
| `function.bufferComponents` | `PositiveInteger` | 0 |  |
| `function.bufferBegin` | `Real` | 0 |  |
| `function.bufferEnd` | `Real` | 0 |  |
| `closed` | `Boolean` | false |  |
| `precision` | `StrictlyPositiveInteger` | 100 |  |

### `GeosphereGeometryGenerator`

Presets: **Default** (Geosphere - Subdivision 0, Geosphere - Subdivision 8)

| path | Oil class | default | choices |
|---|---|---|---|
| `radius` | `PositiveMeters` | 1 |  |
| `subdivision` | `PositiveInteger` | 3 |  |
| `sliceTriangles.center` | `Percentage` | 0.5 |  |
| `sliceTriangles.size` | `SignedPercentage` | 1 |  |
| `sliceTriangles.begin` | `Percentage` | 0 |  |
| `sliceTriangles.end` | `Percentage` | 1 |  |
| `sliceTriangles.invertible` | `Boolean` | true |  |

### `GridPointsGeometryGenerator`

Presets: **Default** (Grid Points - 1x1x1, Grid Points - 2x2x1, Grid Points - 4x4x1, Grid Points - 4x4x4, Grid Points - 10x10x10)

| path | Oil class | default | choices |
|---|---|---|---|
| `size.x` | `PositiveMeters` | 1 |  |
| `size.y` | `PositiveMeters` | 1 |  |
| `size.z` | `PositiveMeters` | 1 |  |
| `size.linked` | `Boolean` | true |  |
| `precision.x` | `StrictlyPositiveInteger` | 10 |  |
| `precision.y` | `StrictlyPositiveInteger` | 10 |  |
| `precision.z` | `StrictlyPositiveInteger` | 10 |  |
| `precision.uniform` | `Boolean` | true |  |

### `GroupGeometryGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `joiner.enabled` | `Boolean` | false |  |
| `joiner.shape` | `SdfJoiner` | 0 (fillet) | fillet, chamfer, smoothPolynomial, smoothExponential, columns, stairs |
| `joiner.exponent` | `PositiveReal` | 2 |  |
| `joiner.count` | `StrictlyPositiveInteger` | 2 |  |
| `joiner.radius` | `PositiveMeters` | 0.1 |  |
| `merger` | `SdfMerger` | 0 (passThrough) | passThrough, replace, add, subtract, intersect, exclude |
| `mergeOpacity` | `Percentage` | 1 |  |
| `inverse` | `Boolean` | false |  |
| `distanceOffset` | `Real` | 0 |  |
| `texCoordsBlend` | `PositiveReal` | 0.1 |  |
| `normalsBlend` | `PositiveReal` | 0.1 |  |

### `HelixGeometryGenerator`

Presets: **Default** (Helix - Spiral)

| path | Oil class | default | choices |
|---|---|---|---|
| `precision` | `StrictlyPositiveInteger` | 1000 |  |
| `radius.center` | `Meters` | 1 |  |
| `radius.size` | `Real` | 2 |  |
| `radius.begin` | `Meters` | 0 |  |
| `radius.end` | `Meters` | 2 |  |
| `radius.invertible` | `Boolean` | true |  |
| `angleBegin` | `Angle` | 0 |  |
| `angleEnd` | `Angle` | 1800 |  |

### `KnotGeometryGenerator`

Presets: **Default** (Knot 2, Knot 3 - Circle, Knot 4, Knot 5 - Spirograph, Knot 6, Knot 7, Knot 8, Knot 9)

| path | Oil class | default | choices |
|---|---|---|---|
| `precision` | `StrictlyPositiveInteger` | 200 |  |
| `slice.center` | `Percentage` | 0.5 |  |
| `slice.size` | `SignedPercentage` | 1 |  |
| `slice.begin` | `Percentage` | 0 |  |
| `slice.end` | `Percentage` | 1 |  |
| `slice.invertible` | `Boolean` | true |  |
| `offset` | `Percentage` | 0 |  |
| `knotType` | `KnotType` | 0 (knot1) | knot1, knot2, knot3, knot4, knot5, knot6, knot7, knot8, knot9 |

### `ParticlesGeometryGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `fixedUpdateRate.enabled` | `Boolean` | true |  |
| `fixedUpdateRate.value` | `Frequency` | 60 |  |
| `emissionParameters.seed.value` | `PositiveInteger` | 0 |  |
| `emissionParameters.seed.incrementAtActivation` | `Boolean` | false |  |
| `emissionParameters.particlesCount` | `PositiveInteger` | 0 |  |
| `emissionParameters.initialCount` | `Percentage` | 0 |  |
| `emissionParameters.preSimulationQuality` | `Percentage` | 0 |  |
| `emissionParameters.rate` | `PositiveReal` | 100 |  |
| `emissionParameters.speed` | `Real` | 0.1 |  |
| `emissionParameters.speedRandom` | `Real` | 0 |  |
| `emissionParameters.interpolateBetweenFrames` | `Boolean` | true |  |
| `emissionParameters.lifeTime` | `Seconds` | 10 |  |
| `emissionParameters.lifeTimeRandom` | `Seconds` | 0 |  |
| `emissionParameters.manualEmit.count` | `PositiveInteger` | 1000 |  |
| `emissionParameters.maximumCount` | `PositiveInteger` | 1000000 |  |

### `PlaneGeometryGenerator`

Presets: **Default** (Plane - Precision: 1, Plane - Precision: 100, Plane - Precision: 500, Plane - Precision: 1000)

| path | Oil class | default | choices |
|---|---|---|---|
| `anchor.x` | `HorizontalCanvasValue` | 0.5 |  |
| `anchor.y` | `VerticalCanvasValue` | 0.5 |  |
| `size.width` | `PositiveMeters` | 1 |  |
| `size.height` | `PositiveMeters` | 1 |  |
| `size.linked` | `Boolean` | true |  |
| `precision.x` | `StrictlyPositiveInteger` | 10 |  |
| `precision.y` | `StrictlyPositiveInteger` | 10 |  |
| `precision.uniform` | `Boolean` | true |  |
| `widthSlice.center` | `Percentage` | 0.5 |  |
| `widthSlice.size` | `SignedPercentage` | 1 |  |
| `widthSlice.begin` | `Percentage` | 0 |  |
| `widthSlice.end` | `Percentage` | 1 |  |
| `widthSlice.invertible` | `Boolean` | true |  |
| `heightSlice.center` | `Percentage` | 0.5 |  |
| `heightSlice.size` | `SignedPercentage` | 1 |  |
| `heightSlice.begin` | `Percentage` | 0 |  |
| `heightSlice.end` | `Percentage` | 1 |  |
| `heightSlice.invertible` | `Boolean` | true |  |
| `wireframe` | `Wireframe` | 0 (all) | all, onlyOnU, onlyOnV |

### `RandomPointsGeometryGenerator`

Presets: **Default** (Random Points - On Plane (horizontal), Random Points - On Plane (vertical), Random Points - On Line (horizontal), Random Points - On Line (vertical), Random Points - On Sphere (1m), Random Points - On Box (1m), Random Points - On Cylinder, Random Points - Single Point)

| path | Oil class | default | choices |
|---|---|---|---|
| `seed.value` | `PositiveInteger` | 0 |  |
| `seed.incrementAtActivation` | `Boolean` | false |  |
| `count` | `PositiveInteger` | 1000 |  |

### `RectangleGeometryGenerator`

Presets: **Default** (Rectangle - Precision 1, Rectangle - Precision 100, Rectangle - Precision 500, Rectangle - Precision 1000, Solidy Path - Rectangle)

| path | Oil class | default | choices |
|---|---|---|---|
| `size.width` | `PositiveMeters` | 1 |  |
| `size.height` | `PositiveMeters` | 1 |  |
| `size.linked` | `Boolean` | false |  |
| `anchor.x` | `Meters` | 0 |  |
| `anchor.y` | `Meters` | 0 |  |
| `anchor.z` | `Meters` | 0 |  |
| `precision` | `StrictlyPositiveInteger` | 5 |  |

### `SegmentGeometryGenerator`

Presets: **Default** (Segment - Precision 10, Segment - Precision 100, Segment - Precision 500, Segment - Precision 1000)

| path | Oil class | default | choices |
|---|---|---|---|
| `segment.begin.x` | `Meters` | 0 |  |
| `segment.begin.y` | `Meters` | 0 |  |
| `segment.begin.z` | `Meters` | 0 |  |
| `segment.end.x` | `Meters` | 1 |  |
| `segment.end.y` | `Meters` | 0 |  |
| `segment.end.z` | `Meters` | 0 |  |
| `precision` | `StrictlyPositiveInteger` | 1 |  |

### `SphereGeometryGenerator`

Presets: **Default** (Sphere - Precision 100, Sphere - Precision 500., Sphere - Precision 1000)

| path | Oil class | default | choices |
|---|---|---|---|
| `radius` | `PositiveMeters` | 1 |  |
| `precision.x` | `StrictlyPositiveInteger` | 80 |  |
| `precision.y` | `StrictlyPositiveInteger` | 50 |  |
| `precision.uniform` | `Boolean` | false |  |
| `longitudeSlice.center` | `Percentage` | 0.5 |  |
| `longitudeSlice.size` | `SignedPercentage` | 1 |  |
| `longitudeSlice.begin` | `Percentage` | 0 |  |
| `longitudeSlice.end` | `Percentage` | 1 |  |
| `longitudeSlice.invertible` | `Boolean` | true |  |
| `latitudeSlice.center` | `Percentage` | 0.5 |  |
| `latitudeSlice.size` | `SignedPercentage` | 1 |  |
| `latitudeSlice.begin` | `Percentage` | 0 |  |
| `latitudeSlice.end` | `Percentage` | 1 |  |
| `latitudeSlice.invertible` | `Boolean` | true |  |
| `wireframe` | `Wireframe` | 0 (all) | all, onlyOnU, onlyOnV |

### `StageDisplayGeometryGenerator`

No plain setting (objects, pointers or vectors only).

### `StarGeometryGenerator`

Presets: **Default** (Star - Circle, Star - losange, Star - Octogon, Star - Sun, Star - Triangle)

| path | Oil class | default | choices |
|---|---|---|---|
| `precision` | `StrictlyPositiveInteger` | 5 |  |
| `innerRadius` | `PositiveMeters` | 0.5 |  |
| `outerRadius` | `PositiveMeters` | 1 |  |
| `branchesCount` | `StrictlyPositiveInteger` | 6 |  |

### `TextGeometryGenerator`

Presets: **Default** (3D Text - Font test, 3D Text)

| path | Oil class | default | choices |
|---|---|---|---|
| `maxDeviation` | `PositiveMeters` | 0.6 |  |
| `maxDistance` | `PositiveMeters` | 1 |  |
| `anchor.x` | `HorizontalCanvasValue` | 0.5 |  |
| `anchor.y` | `VerticalCanvasValue` | 0.5 |  |
| `enableGroupId` | `Boolean` | false |  |
| `maxLineWidth` | `PositiveReal` | 15 |  |
| `font.size` | `PositiveInteger` | 12 |  |
| `font.extraKerning` | `Real` | 0 |  |
| `font.options.bold` | `Boolean` | false |  |
| `font.options.italic` | `Boolean` | false |  |
| `font.options.underlined` | `Boolean` | false |  |
| `justification` | `Justification` | 0 (middleCenter) | middleCenter, middleLeft, middleRight, topCenter, topLeft, topRight, bottomCenter, bottomLeft, bottomRight |

### `TorusGeometryGenerator`

Presets: **Default** (Torus - Precision 3, Torus - Precision 100, Torus - Precision 500, Torus - Precision 1000)

| path | Oil class | default | choices |
|---|---|---|---|
| `precision.x` | `StrictlyPositiveInteger` | 80 |  |
| `precision.y` | `StrictlyPositiveInteger` | 20 |  |
| `precision.uniform` | `Boolean` | false |  |
| `ringRadius` | `PositiveMeters` | 1 |  |
| `thickness` | `PositiveMeters` | 0.2 |  |
| `twist` | `Angle` | 0 |  |
| `twistOffset` | `Angle` | 0 |  |
| `ringRadiusSlice.center` | `Percentage` | 0.5 |  |
| `ringRadiusSlice.size` | `SignedPercentage` | 1 |  |
| `ringRadiusSlice.begin` | `Percentage` | 0 |  |
| `ringRadiusSlice.end` | `Percentage` | 1 |  |
| `ringRadiusSlice.invertible` | `Boolean` | true |  |
| `thicknessSlice.center` | `Percentage` | 0.5 |  |
| `thicknessSlice.size` | `SignedPercentage` | 1 |  |
| `thicknessSlice.begin` | `Percentage` | 0 |  |
| `thicknessSlice.end` | `Percentage` | 1 |  |
| `thicknessSlice.invertible` | `Boolean` | true |  |
| `wireframe` | `Wireframe` | 0 (all) | all, onlyOnU, onlyOnV |

### `TrackingSystemGeometryGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `orientationAxis` | `EulerAnglesOrder` | 0 (xyz) | xyz, xzy, yxz, yzx, zxy, zyx |
| `projectY.enabled` | `Boolean` | false |  |
| `projectY.value` | `Meters` | 0 |  |

## Shapes and layers

### `GroupShapeGenerator`

| path | Oil class | default | choices |
|---|---|---|---|
| `edgeLength` | `PositivePixels` | 0 |  |
| `merger` | `SdfMerger` | 0 (passThrough) | passThrough, replace, add, subtract, intersect, exclude |
| `mergeOpacity` | `Percentage` | 1 |  |
| `rasterizeMergedShape` | `Boolean` | true |  |
| `joiner.enabled` | `Boolean` | false |  |
| `joiner.shape` | `SdfJoiner` | 0 (fillet) | fillet, chamfer, smoothPolynomial, smoothExponential, columns, stairs |
| `joiner.exponent` | `PositiveReal` | 2 |  |
| `joiner.count` | `StrictlyPositiveInteger` | 2 |  |
| `joiner.radius` | `PositivePixels` | 5 |  |
| `rasterizeShapes` | `Boolean` | false |  |

### `NullLayer`

| path | Oil class | default | choices |
|---|---|---|---|
| `display` | `NullLayerDisplay` | 1 (sphere) | none, sphere, sphereAndText |
| `radius` | `PositiveMeters` | 0.1 |  |
