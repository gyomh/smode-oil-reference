# Smode Oil API — Référence non-officielle

*[English version](README.md)*

> Smode Tech ne publie pas de documentation de l'API Oil/SmodeSDK pour un pilotage externe.
> Tout ce qui suit vient de reverse engineering (introspection live via `dir()` / `Oil.docMe()`)
> et de retours d'usage réels, accumulés en construisant des features avec le
> [pont MCP smode-mcp](https://github.com/gyomh/smode-mcp). Vérifié sur Smode Compose R13 et versions ultérieures.
> Contributions bienvenues — voir CONTRIBUTING en bas de fichier.

## Sommaire
- [Introspection sûre](#introspection-sûre)
- [Règle d'or : configurer avant d'ajouter, jamais après](#règle-dor--configurer-avant-dajouter-jamais-après)
- [Une Compo sans target n'est jamais évaluée par le moteur](#une-compo-sans-target-nest-jamais-évaluée-par-le-moteur)
- [Le piège `.linked`](#le-piège-linked)
- [Résolutions](#résolutions)
- [Pointeurs polymorphes (OwnedPointer)](#pointeurs-polymorphes-ownedpointer)
- [Enums : jamais deviner l'index](#enums--jamais-deviner-lindex)
- [Cartographie de l'arbre projet](#cartographie-de-larbre-projet)
- [Géométrie 3D : GeometryLayer, placement, angles](#géométrie-3d--geometrylayer-placement-angles-confirmé-r15-06102026)
- [Lumières 3D](#lumières-3d-r15-07102026)
- [Verrou et activation (ActivationState)](#verrou-et-activation-activationstate)
- [Matériaux partagés, références, profondeur](#matériaux-partagés-références-profondeur-r15)
- [Caméra de la Compo](#caméra-de-la-compo-r15)
- [Texte (TextLayer)](#texte-textlayer)
- [Parameter banks liées à un Script](#parameter-banks-liées-à-un-script-r15)
- [Vérifier visuellement (hors API)](#vérifier-visuellement-hors-api)
- [Système de Parameters / Links / Cues](#système-de-parameters--links--cues)
- [Timeline (TimelineCue)](#timeline-timelinecue)
- [Modificateurs, générateurs et masques (aperçu)](#modificateurs-générateurs-et-masques-aperçu)
- [Audio réactif](#audio-réactif)
- [Scripts créés par programmation (PythonScriptTool)](#scripts-créés-par-programmation-pythonscripttool)
- [Fichiers 3D importés, textures image et compos de matériau](#fichiers-3d-importés-textures-image-et-compos-de-matériau-r15-08102026)
- [Références de fichiers, Media Directories et relink](#références-de-fichiers-media-directories-et-relink-r15-08102026)
- [Interface web servie par un Script](#interface-web-servie-par-un-script-r15-08102026)
- [Bugs UI connus](#bugs-ui-connus)
- [Instabilités observées](#instabilités-observées)
- [Le pont MCP (rappel)](#le-pont-mcp-rappel)

---

## Introspection sûre

Aucun stub Python (`.pyi`) n'existe : `site-packages/Smode/Oil.py` est un wrapper de ~80 lignes
autour d'extensions compilées dans `Smode.exe`, sans les vraies définitions de classes.

Méthodes fiables, à utiliser dans cet ordre :
1. `obj.getOilClassName()` — nom de classe réel.
2. `dir(obj)` — liste des attributs/méthodes, léger, sans risque connu.
3. `Oil.createObject("NomDeClasse")` dans un `try/except` — testez si une classe existe sans
   avoir à la deviner dans la doc.
4. `Oil.docMe(obj)` — introspection complète documentée officiellement (types, hiérarchie).
   **Fonctionne bien sur un objet isolé** (juste créé, ou lu proprement depuis l'arbre). Éviter
   de l'appeler sur un objet qu'on vient de manipuler dans un append/removeAt risqué (voir
   section instabilités) — pas confirmé comme LA cause d'un crash, mais corrélé une fois.
5. `Map` Oil (ex. `TimelineCue.elementTracks`) : pas d'accès par index entier (`map[0]` lève
   `TypeError`, il attend un objet-clé) — itérer avec `.items()` (retourne des paires clé/valeur
   Python classiques).

## Règle d'or : configurer avant d'ajouter, jamais après

Le pattern qui fonctionne de façon fiable et reproductible :

```python
obj = Oil.createObject("MaClasse")
obj.propriete = valeur          # tout configurer ICI
obj.sousObjet.propriete2 = ...
parent.collection.append(obj)   # append en tout dernier
# ne plus JAMAIS toucher `obj` après l'append
```

Deux façons de casser ça, observées concrètement :
- **Re-fetch après append puis accès à une sous-propriété** (ex. `parent.areas[0].placement`)
  → `RuntimeError: Access violation - no RTTI data!`, et une tentative suivante peut carrément
  crasher Smode (connexion HTTP fermée de force). Le vecteur "Owned" semble transférer la
  propriété de l'objet à l'append — la référence Python d'origine devient invalide.
- **Configurer un objet AVANT append, puis le relire après** (ex. `VideoOutput.label`,
  `.outputDevice.deviceName/.factory`) : les valeurs configurées ne tiennent PAS toujours —
  vues revenues à des défauts (`"Video Output 1"` / `"Remote Video Output"`) après append dans
  `pipeline.outputs`. Confirmé sur les objets liés au moteur (`engine.*`) ; pas reproduit sur les
  objets de scène (Compo/GeometryLayer/AffineCamera — ceux-là gardent bien leur config après
  append). Donc cette règle est solide pour l'arbre de scène, à re-vérifier au cas par cas côté
  `engine.*`.

## Une Compo sans target n'est jamais évaluée par le moteur

Règle générale, indépendante du cas Timeline/Link où elle a été découverte (détails et exemple
complet dans la section [Timeline (TimelineCue)](#timeline-timelinecue)) : une `Compo` embarquée
via un `TextureLayer` (`compoLayer.generator = compo`) dont le `TextureLayer.renderer.target`
n'a **jamais été assigné à une destination de rendu** (typiquement une `ContentMap`, dans
`script.project.pipeline.contentMaps`) n'est **pas évaluée par le moteur** — ni son rendu visuel,
ni ses `Link`s, ni ses `Script`s "At Every Update" internes, **même si tout le reste est
structurellement correct**. Ce qui ressemblait à répétition à des bugs "objet construit par
script qui ne s'active pas" (Links inertes notamment) venait en réalité de là. Réflexe pour tout
script qui construit une Compo destinée à un comportement live (pas seulement statique) :

```python
contentMaps = script.project.pipeline.contentMaps
if len(contentMaps) > 0:
    compoLayer.renderer.target.set(contentMaps[0])
```

Assigner le target dès la construction (avant d'ajouter du contenu qui doit être live dedans,
même logique que la règle Timeline-avant/après-insertion) suffit ; aucune action manuelle
supplémentaire n'est nécessaire ensuite.

## Le piège `.linked`

Toute taille/résolution 2D a un flag `.linked` (Boolean), **True par défaut**, qui force
silencieusement `width == height` (ou X == Y) dès qu'on modifie une seule des deux valeurs —
**aucune erreur**, juste un résultat visuel faux. Toujours :

```python
obj.size.linked = False   # AVANT
obj.size.width = 1000.0
obj.size.height = 200.0
```

Concerné : `Canvas2dSize` (placement/scale), `Size3d(PositiveMeters)` (géométrie 3D — **a aussi
un `.linked`, True par défaut** : sur un `BoxGeometryGenerator`, `size.x = 1.0; size.y = 0.1;
size.z = 0.1` donne 0.1 / 0.1 / 0.1 sans erreur, corrigé en mettant `size.linked = False` AVANT ;
corriger après coup sur un objet déjà appended fonctionne), `InheritableImageResolution`,
`ImageResolution`, `CheckerBoardTextureGenerator.size/.balance`.

Générateur de couleur unie (layer "Uniform" dans l'UI) : `UniformTextureGenerator` — `.color`
est un `HsvColor` (`.red`/`.green`/`.blue`/`.hue`/`.saturation`/`.value`/`.alpha`, chacun un
`Percentage` avec `.get()`/`.set()`). À assigner à `TextureLayer.generator` (pas `"Uniform"` tout
court, ce nom n'existe pas comme classe Oil).

## Résolutions

Deux classes différentes selon le contexte :
- `InheritableImageResolution` (Compo.rasterizer, ContentArea.resolution, ContentMap.rasterizer/
  rootArea.resolution) : a un `.preset` (enum `ImageResolutionPreset`, classe wrapper avec
  `.get()`/`.set()`, PAS assignable par `=` direct — `obj.preset = 40` lève
  `TypeError: invalid 'preset' variable type: expected ImageResolutionPreset, not <class 'int'>`)
  qui démarre à **41 = "Inherited"** — dans cet état, `.width`/`.height` sont **totalement
  ignorés** (l'UI affiche "Inherited" même si width/height ont été explicitement réglés), la
  résolution vient du parent. Il faut `.preset.set(40)` ("Custom...") AVANT de fixer width/height.
  Si les valeurs custom correspondent pile à un preset nommé (ex. 1280x720 = "HD 720"), `.preset`
  se réaffiche automatiquement avec ce nom — cosmétique uniquement, les valeurs restent bonnes.
- `ImageResolution` (device NDI, etc.) : pas de notion "Inherited", `.width`/`.height` directs
  (avec `.linked` quand même).

Piège classique : régler la résolution d'un générateur interne (ex. `GradientTextureGenerator.
resolution`) en pensant que ça change la taille de la Compo affichée à l'écran — non, ça ne pilote
que l'échantillonnage interne de CE générateur. La vraie taille vient toujours de
`Compo.rasterizer.resolution`.

## Pointeurs polymorphes (OwnedPointer)

Certaines propriétés sont des `OwnedPointer(BaseClass)` — nulles/non instanciées tant qu'on n'y
assigne pas explicitement un objet concret :
- `GeometryLayer.generator` (`OwnedPointer(GeometryGenerator)`), `.renderer`
  (`OwnedPointer(GeometryRenderer)`)
- `AffineCamera.placement`, `ContentArea.placement` (`OwnedPointer(Placement2d/3d)`)

```python
cube.generator = Oil.createObject("BoxGeometryGenerator")   # assignation directe, pas .set()
cube.renderer = Oil.createObject("SurfaceGeometryRenderer")
```

`VideoOutput.outputDevice` n'est PAS un pointeur owned vers un device concret mais un
`VideoOutputDeviceSelector` (champs `deviceName`/`factory`/`hostName`/`preferredAddress`) — un
sélecteur par nom, pas une instance directe.

## Enums : jamais deviner l'index

Le même nom de propriété peut référencer des enums **différents** selon la classe porteuse.
Toujours vérifier `prop.getOilClassName()` avant de fixer un index. Valeurs confirmées :

| Enum | Valeurs connues |
|---|---|
| `BlendingMode` (effets/renderer) | 10=screen, 12=linearDodge, 0=passThrough... |
| `TextureMaskBlendingMode` (masques) | 0=add, 1=remove, 2=multiply, 3=replace |
| `PixelateMode` | 0=downscaleFactor, 1=numPixelsWidth, 2=numPixelsHeight (`.value` reste un simple `Real` quel que soit le mode — régler `.mode` AVANT `.value`) |
| `NoiseFunctionShapeType` | 0=simplexNoise (défaut), 1=perlinNoise |
| `CuePlayParameters.launchMode` | 0=manual, 1=restartWithActivation, 2=restartWithIntensity, 3=playWithIntensity |
| `PythonScriptLaunchMode` | 0=manual, 1=atPreload, 2=atActivation, 3=atParameterChange, 4=atEveryUpdate, 5=atDeactivation, 6=atUnload |
| `FunctionWrapMode` | 0=clamp, 1=repeat, 2=mirroredRepeat |

`Oil.CustomEnumeration(("a","b"), 0)` documenté officiellement **ne fonctionne pas**
(`AttributeError`). Fix : déclarer `x: Oil.createObject("CustomEnumeration")` vide, peupler dans
le corps du script avec des `CustomEnumerator` (`.label`=texte, `.value`=int) via
`.enumerators.append(...)`, protégé par `if len(script.x.enumerators) == 0`. **R15 (07/10/2026) :
l'attribut s'appelle `enumerators` (`OwnedVector(CustomEnumerator)`) ; les anciens noms
`elements` / `CustomEnumerationElement` n'existent plus** (`AttributeError` / `unknown Oil type
name`). `.set()/.get()` utilisent le label (string), contrairement aux enums natifs qui utilisent
un entier. Alternative plus simple si un simple booléen suffit : `Oil.Boolean` évite tout ce bug.

**Liste remplie dès la compilation (R15, 08/10/2026)** : la déclaration accepte une expression quelconque ;
une lambda qui crée, remplit et pré-sélectionne l'énumération évite la liste vide jusqu'au premier Execute
(testé : compilation neuve et recompilation par-dessus une ancienne déclaration vide) :
```python
mode: (lambda e: ([e.enumerators.append((lambda n: (setattr(n, "label", lab), setattr(n, "value", i), n)[2])(
    Oil.createObject("CustomEnumerator"))) for i, lab in enumerate(("Relocate", "Consolidate"))],
    e.set("Relocate"), e)[2])(Oil.createObject("CustomEnumeration"))
```
(à écrire sur une seule ligne dans le Script).

Enum `Placement3dTargetAxis` (`placement.target.axis`, lisible via `.toString()`) : 0 = xPos,
1 = xNeg, 2 = zPos (défaut), 3 = zNeg ; 4 et 5 ne sont pas valides (valeurs testées sur un objet
jetable non ajouté à la scène).

## Cartographie de l'arbre projet

```
script.project
├── masterScene.layers[]           # scène principale, calques (TextureLayer, GeometryLayer...)
├── pipeline
│   ├── contentMaps[]              # ContentMap (mapping écran/zones) — PAS un TextureGenerator,
│   │                               # ne rentre pas dans un TextureLayer.generator
│   ├── outputs[]                  # VideoOutput (OwnedVector(VideoOutput)), relie une source du
│   │                               # pipeline à un outputDevice via VideoOutputDeviceSelector
│   ├── channels[]                 # OwnedVector(ChannelV9), abstrait, sous-classes non identifiées
│   └── virtualScreens[]
└── topology

Compo                                # pas de .masterScene : les layers sont directs
├── layers[]                         # OwnedVector(Layer), comme masterScene.layers
├── rasterizer.resolution            # InheritableImageResolution (piège Custom/Inherited)
└── mainAnimation                    # MainAnimationOwnedPointer, ex. TimelineCue

engine                              # niveau système, PAS projet (partagé entre projets ouverts)
├── configuration.timing.requestedFrameRate  # VideoTimeBase (.p/.q) — frame rate global
├── devices.devices[]               # OwnedVector(Device) — matériel détecté (storage, capture,
│                                    # audio...) + `deviceConfigurationDirty` (Trigger) pour forcer
│                                    # un rescan. ATTENTION : un objet ajouté manuellement ici
│                                    # disparaît après un trig() de deviceConfigurationDirty
│                                    # (rebuild depuis la source de vérité réelle, pas depuis nos
│                                    # ajouts ad-hoc)
└── configuration
    ├── videoOutputs[]              # VideoOutputDeviceConfiguration — NON confirmé comme le
    │                                # binding réel du panneau Preferences > Engine > Video
    │                                # Outputs (testé vide alors qu'une ligne existait à l'écran :
    │                                # emplacement réel encore NON localisé, à creuser)
    ├── graphicsWindows[]           # config fenêtres/affichage, pas les video outputs
    └── configurations              # NamedObjectMap, presets de config (pas exploré en détail)
```

**Afficher une Compo dans une ContentMap** : PAS via `ContentMap.currentCamera` (fausse piste — ce
`WeakPointer(CameraV9)` existe bien mais n'est pas le mécanisme d'affichage standard ; laisser
`.reset()`/vide). Le vrai mécanisme, visible dans le panneau UI des layers comme une colonne
"target" (qui remplace le blend mode "Normal" pour les layers top-level) : le **renderer** du
TextureLayer qui enveloppe la Compo a une propriété `target` (`SceneTargetWeakPointer`) à pointer
vers la `ContentMap` (directement, pas besoin de `.rootArea` ici — contrairement à
`VideoOutput.source`) :
```python
compoLayer = Oil.createObject("TextureLayer")
compoLayer.generator = compo          # la Compo a afficher
parentScene.layers.append(compoLayer) # renderer par defaut = SingleTextureRenderer

compoLayer.renderer.target.set(cm)    # cm = la ContentMap (deja appended dans pipeline.contentMaps)
```
Un layer avec un `target` non résolu s'affiche en rouge avec `<Missing Target>` dans l'UI —
symptôme fiable pour repérer un layer censé alimenter une ContentMap mais mal câblé.

**LIMITE MAJEURE CONFIRMÉE (2026-07-10)** : `renderer.target.set(cm)` via le pont MET À JOUR la
valeur (relecture immédiate via `.get()` confirme le bon pointeur, pas d'erreur), **mais ne
déclenche PAS le rendu réel**. Testé sur 3 ContentMaps différentes (2 créées par script, 1 créée
entièrement à la main dans l'UI par Guillaume) : dans les 3 cas, `set()` via script laisse
l'aperçu de la ContentMap noir/vide, alors que **re-sélectionner manuellement la MÊME valeur dans
le dropdown UI fait apparaître le rendu immédiatement**. Contrairement au bug des Links
"Disconnected" (fixable en fermant/rouvrant le projet), **fermer/rouvrir le projet ne corrige PAS
celui-ci** — confirmé en conditions réelles. Conclusion : `.set()` sur un `SceneTargetWeakPointer`
change la donnée mais ne déclenche pas la notification interne qui active le pipeline de rendu ;
seule une interaction UI directe (re-sélection dans le dropdown) semble le faire. Workaround
actuel : le script peut préparer/câbler la valeur (utile pour du câblage en masse), mais un passage
manuel dans l'UI reste nécessaire pour activer réellement chaque target. Aucune méthode
alternative trouvée à ce jour (pas de `.trig()`/`.refresh()` déclencheur identifié sur
`ContentMap`, `TextureLayer`, ou `SingleTextureRenderer`).

**Relier une ContentMap à un VideoOutput** : `VideoOutput.source` est un `PipelineSourceWeakPointer`
qui refuse une `ContentMap` directement (erreur Smode, popup UI :
`"Wrong target type for pipeline source pointer: it should point to either a Content Area or a
Video Rasterizer"` — pas remontée comme exception côté pont, seulement visible dans l'UI). Il
faut pointer vers sa `ContentArea` (`cm.rootArea`, pas `cm`) :
```python
outputVideo.source.set(cm.rootArea)   # pas outputVideo.source.set(cm)
```

**ContentMap / zones** (`pipeline.contentMaps`) :
```python
cm = Oil.createObject("ContentMap")
cm.rasterizer.resolution.preset.set(40)   # 40=Custom, sinon reste sur Inherited (41) et ignore width/height
cm.rasterizer.resolution.linked = False
cm.rasterizer.resolution.width = 3000
cm.rasterizer.resolution.height = 200
cm.rootArea.resolution.preset.set(40)
cm.rootArea.resolution.linked = False
cm.rootArea.resolution.width = 3000
cm.rootArea.resolution.height = 200

zone = Oil.createObject("ContentArea")
# resolution NON touchee : reste sur le defaut Inherited (preset=41) -- voir note ci-dessous,
# c'est le SCALE qui definit la taille finale d'une sous-zone, pas la resolution
zone.placement.scale.size.linked = False
zone.placement.scale.size.width = 0.5    # fraction du parent (50% de la largeur de rootArea)
zone.placement.scale.size.height = 1.0   # 100% de la hauteur
zone.placement.position.x = 0.25         # centre de la zone, fraction 0-1 du parent
zone.placement.position.y = 0.5
cm.rootArea.areas.append(zone)    # configurer AVANT, append en dernier — jamais retoucher après

script.project.pipeline.contentMaps.append(cm)
```

**Resolution vs Scale sur une sous-`ContentArea`** : contrairement au `rootArea`/`rasterizer` de
la `ContentMap` elle-même (où `.resolution.preset` DOIT passer à 40=Custom pour un pixel size
explicite, voir plus haut), une **sous-zone** (`ContentArea` ajoutée à `.areas`) doit rester en
`.resolution.preset` par défaut (**41 = Inherited**) — ne pas y toucher. La taille finale en
pixels de la sous-zone est déterminée par **`.placement.scale.size`** (fraction du parent, ex.
`0.5` = 50% de la largeur du parent) : `resolution.width` affiché dans l'UI pour une zone Inherited
n'est qu'une valeur EXTRAITE/calculée (parent × scale), pas une valeur à régler soi-même. Confirmé
en inspectant une `ContentArea` créée manuellement dans l'UI par Guillaume : `resolution.preset=41`,
`scale.width=0.5`, `scale.height=1.0`.

**Unités de `Canvas2dPosition`/`Canvas2dSize`** : fractions normalisées 0.0–1.0 (PAS des pixels),
confirmé en lisant les défauts d'une `ContentArea` fraîche (`position=(0.5, 0.5)`,
`anchor=(0.5, 0.5)`, `scale.size=(1.0, 1.0)` = 100%). `position` représente où se place le point
d'ancrage (`anchor`) DANS le repère 0–1 du parent — avec l'ancrage par défaut au centre (0.5,0.5),
`position=(0.5, 0.5)` = zone centrée occupant tout le parent. Pour poser côte à côte N zones de
largeur égale, régler `scale.width = 1.0/N` (scale, pas resolution) et calculer le centre de
chaque zone en fraction du parent : `position.x = (i + 0.5) / N`. Erreur classique : passer des
valeurs "façon pixels" (ex. `960.0` au lieu de `0.75`) → accepté sans erreur mais interprété comme
une fraction énorme (`960.0` devient `96000%` dans l'UI), zone hors cadre.

Piège annexe : modifier `.placement.scale`/`.position`/`.resolution` sur une `ContentArea` déjà
**appended** (re-fetch après coup) retombe dans le pattern crash-prone documenté plus haut — en
cas d'erreur de valeur après append, préférer `areas.clear()` + recréer les zones proprement
plutôt que corriger les objets existants en place.

## Géométrie 3D : GeometryLayer, placement, angles (confirmé R15, 06/10/2026)

- **Les angles Python sont en RADIANS** (`placement.orientation.z = math.radians(90)`), pas en
  degrés. Piège silencieux : écrire `77.5` donne 77.5 rad modulo 2π (≈123°), sans erreur. Vérifié en
  relisant `layer.worldMatrix` (`m.x.x.get()`, `m.x.y.get()` = axe X monde, `m.w.x/.y/.z` = position).
- `GeometryLayer` : `generator` (`OwnedPointer(GeometryV9Generator)` : `BoxGeometryGenerator`
  `.size`, `SphereGeometryGenerator` `.radius`, `CylinderGeometryGenerator`), `renderer`
  (`SurfaceGeometryRenderer`), `placement` (`PositionOrientationSize3dPlacement`, déjà instancié) :
  `anchor` (x/y/z Meters), `position` (x/y/z Meters), `orientation` (`EulerAngles` : x/y/z Angle +
  `order` + `axisAngle`), `target` (`Placement3dTarget` : `axis`, `targetObject`, `upVector` =
  look-at natif), `size` (`Size3d(Real)`). Pas de hiérarchie parent/enfant entre `GeometryLayer`
  (pas de `.layers`) ; `GroupLayer` n'a qu'un `Placement2d`.
- **Aucune classe IK / Bone / Skeleton / Constraint dans Smode** (`createObject` échoue ; les
  mots-clés n'existent que dans les importeurs FBX / Assimp / NatNet). Un IK se calcule à la main.
- **Écrire un placement depuis un Script « At Every Update » fonctionne** (≈1900 exécutions sans
  erreur, lecture/écriture de `layer.placement.position.x = v` sur des layers déjà appended, aucun
  crash). Dans un `PythonScriptTool` placé dans `compo.tools`, `script.parentElement` est la
  **Compo** (`.layers`), pas la scène. Retrouver les layers par label :
  `{str(l.label.get()): l for l in (comp.layers[i] for i in range(len(comp.layers)))}`.
- Le projet ouvert est `script.project` (`.masterScene`, `.pipeline`) ; `engine.content.
  customContent` est toujours vide, ne pas y chercher le projet.
- Exemple complet (rig IK/FK de N bones, poignées, banks) : dépôt [smode-ik-rig](https://github.com/gyomh/smode-ik-rig).
- `PlaneGeometryGenerator` : `size.width/height` (`Size2d`, pas `.x/.y`), `anchor` (`Canvas2dPosition`, 0,5
  = centre) ; **le plan naît couché dans le plan XZ (normale = Y local)** : pour le dresser face à +Z,
  rotation `orientation.x = -π/2` (colonnes `[[1,0,0],[0,0,1],[0,-1,0]]`).
- `CircleGeometryGenerator` = **contour seulement** : rendu en surface → erreur UI « Surface No Triangles
  information in geometry » ; à rendre avec `ThickLinesGeometryRenderer` (`map` = `UniformTextureGenerator`
  dont `.color` règle la couleur du trait ; `thickness` en px). `SphereGeometryGenerator.precision` =
  `Precision2d` (`.uniform = False` avant de régler `.x/.y`). `CapsuleGeometryGenerator` : axe Y, pivot à la base.
- `NullLayer` : **invisible et non sélectionnable dans le viewport** (seulement dans l'arbre) ; pour une
  poignée cliquable, utiliser une vraie géométrie (plan).
- `Group3dLayer` : `worldMatrix` lisible (colonnes `m.x/.y/.z/.w`, vaut 0 avant la 1re évaluation) ;
  un calque hors du groupe ne suit pas sa transformation sauf si le script l'applique.
- Matrice monde : `layer.worldMatrix` → `m.x.x.get()`... ; rotation = colonnes normalisées.

## Lumières 3D (R15, 07/10/2026)

- Classes instanciables avec `Oil.createObject` et ajoutées **directement à `layers`** (pas de
  `LightLayer` / wrapper) : `SpotLight`, `PointLight`, `DirectionalLight`, `AmbientLight`.
  `AreaLight` est abstraite (`cannot instantiate abstract class`).
- Attributs communs : `intensity` (`Percentage`), `diffuse` (`LightComponentParameters` : `.color`
  `HsvColor`, `.level`, `.enable`), `specular` (`.color`, `.level`, `.shininess`, `.enable`),
  `placement` (`PositionOrientationSize3dPlacement`, comme un `GeometryLayer`), `visibilityScope`
  (`LightVisibilityScope`, défaut 0 = `compoAndSubCompos` : **une lumière dans un `Group3dLayer`
  éclaire toute la compo**, pas seulement le groupe), `volumetric`, `activation`.
- Spécifiques : `SpotLight` (`attenuation`, `radialAttenuation` = `FalloffFunction(PositiveAngle)` avec
  `.interval` / `.exponent`, `color`, `backgroundColor`), `PointLight` (`radius`, `attenuation`,
  `areaNoise`, `areaNumSamples`, `directionalMap`), `DirectionalLight` (`shadowParameters`).
  `AmbientLight` n'a que les attributs communs.
- **Viser un point** : `light.placement.target.targetObject.set(layer)` (`WeakPointer(Layer)`, un
  `NullLayer` convient) + `placement.target.axis` (enum, voir « Enums »). **Un Spot émet vers son
  -Z local** alors que le défaut `axis = zPos (2)` aligne le +Z vers la cible : sans `axis.set(3)`
  (zNeg) la lumière éclaire à l'opposé. Vérification par script : avec zNeg, la colonne `z` de
  `worldMatrix` a un produit scalaire positif avec la position de la lumière (elle pointe à
  l'opposé de la cible). Position sphérique autour de la cible : `x = d·cos(el)·sin(az)`,
  `y = d·sin(el)`, `z = d·cos(el)·cos(az)` (azimut 0 = côté +Z, +90° = +X).
- Intensité / couleur / activation se modifient après l'`append` sans problème (mise à jour en place
  d'un rig existant depuis un Script). Exemple complet : dépôt [smode-light-setup](https://github.com/gyomh/smode-light-setup).

## Verrou et activation (ActivationState)

- `layer.editable` (cadenas du calque : non sélectionnable dans le viewport), `layer.activation`
  (œil : inactif = hors rendu) et `solo` sont des **`ActivationState`**.
- **`.set()` prend un BOOLÉEN** (`True` = actif / modifiable, `False` = inactif / verrouillé). Y passer
  un entier est lu comme « vrai » et ne change rien (silencieux). `.get()` renvoie 0 (actif) ou 2
  (inactif) ; `.toString()` donne `'active'` / `'inactive'`.
- **Ne pas faire** : `Oil.createObject('ActivationState')` ni `dir()` sur une de ces variables → plantage
  complet de Smode (observé). Lire/écrire la valeur d'un objet existant est sûr.
- Un `MaterialBank`, un `ParameterBank`, un calque texte se verrouillent de la même façon
  (`obj.editable.set(False)`), avant ou après l'`append`.

## Matériaux partagés, références, profondeur (R15)

- `Group3dLayer.tools` accepte un `MaterialBank` (`Oil.createObject('MaterialBank')`) dont `.materials`
  est un `OwnedVector(GeometryLayerUser)` : on y met un `SurfaceGeometryRenderer` (le matériau, `label`
  = son nom). Réglages utiles : `side` (0 front, 1 back, 2 both), `autoIlluminate`, `depthBuffer.test` /
  `.write`, `components[0]` = `DiffuseSurfaceComponent` (`map` = n'importe quel `TextureGenerator`, dont
  une `Compo` 1024² à fond transparent contenant un `ShapeLayer` → icône vectorielle ; `masks` =
  `GeometryMask`). Un nouveau `SurfaceGeometryRenderer` a 2 composants (Diffuse + Specular).
- **Référencer un matériau depuis un calque** (`layer.renderer = ...`) :
  ```python
  r = Oil.createObject('ReferenceGeometryLayerUser')
  ad = r.referencer.address
  ad.directPointer.set(material)      # l'objet matériau lu dans bank.materials[j]
  ad.location.set(1)                  # 1 = pointeur direct ; la valeur par défaut 0 donne
                                      # « Unspecified reference » et le calque disparaît
  layer.renderer = r
  ```
  `ad.target.get()` n'est non-None que quand la référence est résolue. **Une référence garde un état en
  cache** : après modification du matériau (ex. `depthBuffer.test`), faire
  `layer.renderer.referencer.reloadInstance.trig()` sur chaque calque qui le référence, ou recréer la
  référence. Une référence posée depuis l'extérieur du groupe qui contient le bank peut signaler
  « No direct pointer ».
- Un plan **tourné face à la caméra coupe les autres plans** : le test de profondeur cache la moitié
  qui passe derrière (poignée « coupée en L »). Pour une poignée toujours visible : matériau avec
  `depthBuffer.test = False` + `reloadInstance` sur les références.
- `SphereGeometryMask` (dans `components[0].masks`) a rendu le plan invisible dans nos essais ; la façon
  fiable de dessiner un cercle/icône sur un plan est une texture avec alpha (Compo + ShapeLayer).
- Création d'un matériau par script (aucun appel UI) : voir `make_icon_material` dans les scripts de [smode-ik-rig](https://github.com/gyomh/smode-ik-rig)
  (`GroupShapeGenerator.shapes` ← `LineShapeGenerator` avec `segment.begin/end` en coordonnées 0-1 ;
  `DefaultShapeRenderer` : `fill.enabled`, `stroke.enabled/.color/.thickness` en pixels de la texture).

## Caméra de la Compo (R15)

- `compo.currentCamera.get()` (caméra courante, celle de la liste des éléments) peut être **différente** de
  `compo.defaultCamera` (caméra interne d'une Compo neuve). Lire d'abord `currentCamera`.
- Placement `TargetOrientationDistance3dPlacement` (caméra « orbitale ») : `target` (`Position3d`),
  `orientation` (`EulerAngles`, ordre 0), `distance` ; **pas de `position`** (AttributeError). Frustum
  `FieldOfViewPerspectiveFrustum` : `horizontal` / `vertical` en radians.
- Rotation monde de la caméra = `Rz·Ry·Rx(orientation)` (sans transposée), position = `target + R·(0,0,distance)`.
  Vérifié en projetant des points connus (perspective, FOV 60°) et en comparant aux pixels d'une capture :
  4,7 px RMS contre 36 px pour la convention suivante. Un plan billboard = `R_cam · Rx(-90°)`.

## Texte (TextLayer)

- `TextLayer` = `generator` `LocalTextGenerator` (`text` MultiLineString `.set('...')`, accents OK ;
  `style.size`, `style.foreground` `HsvColor` en 0-1, **`style.background` = `Option(HsvColor)` : `.enabled` +
  `.value` (alpha = opacité du fond)**) + `renderer` `DefaultTextRenderer` : `placement.position` (fractions
  0-1 de la compo), `size.width.type` (0 auto, **1 wordWrap**, 2 shrinkToFit) + `size.width.size` (px),
  `size.height.type` (0 auto), `style.alignment` (0 middleCenter, 1 middleLeft, 2 middleRight, 3 topCenter,
  4 topLeft). Résolution de la compo : `compo.rasterizer.resolution.width.get()`.
- Pour qu'un texte d'avertissement ne soit pas rendu : `layer.activation.set(False)` et texte vide quand
  il n'y a rien à dire.

## Parameter banks liées à un Script (R15)

- Un `Parameter(Boolean)` / `Parameter(Angle)` / ... (`Oil.createObject('Parameter(Angle)')`) porte
  `label`, `value`, `expose`, `modifiers` et **`targets` : `OwnedVector(LinkTarget)`** — pas besoin de
  `LinkBank` : `lt = Oil.createObject('ParameterLinkTarget'); lt.target.set(script.maVariable);
  p.targets.append(lt); bank.parameters.append(p)`. Valeur initiale du Parameter = valeur courante de la
  variable. Le Parameter prend la couleur de son bank (`colorLabel`). Voir aussi la section « Scripts qui
  s'auto-installent » : le Parameter lié repose sa propre valeur sur le script.
- Le `colorLabel` de tout élément : `c = o.colorLabel; c.red.set(r/255)` (valeurs 0-1, `SrgbColor`).

## Vérifier visuellement (hors API)

Le rendu ne se lit pas par script. Technique qui marche : PowerShell, `GetWindowRect` du processus
Smode + `Graphics.CopyFromScreen` sur ce rectangle seul (jamais l'écran entier), puis lecture du PNG.
Recadrer sur le viewport pour lire une icône ; la barre d'état en bas de la fenêtre donne les erreurs
de rendu (« No direct pointer », « Unspecified reference », « No Triangles... »).
Attention : si la fenêtre Smode est sur un autre écran avec d'autres fenêtres par-dessus, la capture les inclura.

## Scene imbriquée (nested Scene layer)

`Scene` est une classe Oil à part entière (confirmé `getOilClassName() == "Scene"`), pas juste le
nom informel de `masterScene`. Un layer de `masterScene.layers` (ou de `Scene.layers`, récursif)
peut être directement de classe `Scene` (pas seulement `TextureLayer`/`GeometryLayer`) — elle a
alors ses propres `layers[]`, `mainAnimation` (`OwnedPointer`, comme `Compo.mainAnimation`) et
`tools` (`OwnedVector(Tool)`, comme `compo.tools`). C'est exactement ce qu'affiche l'UI comme
"Scene" avec ses enfants "Main Timeline" / "Parameters" / "Animations" / "Links" / (calques).

Une `Scene` fraîchement créée (`Oil.createObject("Scene")`) a tout vide : `mainAnimation=None`,
`tools` et `layers` de taille 0 — rien n'est créé par défaut, tout est à construire à la main.

Les 3 banks visibles dans l'UI sous une Scene/Compo sont 3 classes Oil différentes, pas juste des
labels du même `ParameterBank` : `ParameterBank` ("Parameters"), `AnimationBank` ("Animations"),
`LinkBank` ("Links") — toutes ajoutées via `.tools.append(...)`. Leur `.label` reste une chaîne
vide même en usage normal (le nom affiché dans l'UI vient du type, pas de `.label`).

Pattern complet vérifié (règle d'or : tout configurer avant le dernier append) :
```python
scene = Oil.createObject("Scene")
scene.label = "Scene"

tc = Oil.createObject("TimelineCue")
scene.mainAnimation = tc                       # OwnedPointer, assignation directe comme Compo

scene.tools.append(Oil.createObject("ParameterBank"))
scene.tools.append(Oil.createObject("AnimationBank"))
scene.tools.append(Oil.createObject("LinkBank"))

compo = Oil.createObject("Compo")
compoLayer = Oil.createObject("TextureLayer")
compoLayer.generator = compo
compoLayer.label = "Compo"
scene.layers.append(compoLayer)

script.project.masterScene.layers.append(scene)   # dernier append
```
`label` (sur `Scene`/`TextureLayer`, wrappé en `_cppSmodeOil.String`) accepte l'assignation directe
`obj.label = "texte"` aussi bien que `.set()`/`.get()` — les deux fonctionnent, contrairement aux
enums qui exigent `.set()`.
(Script prêt à l'emploi : [smode-new-scene](https://github.com/gyomh/smode-new-scene).)

## Système de Parameters / Links / Cues

- `ParameterBank` (dans `compo.tools`) + `Parameter(Type)` (ex. `Parameter(Angle)`,
  `Parameter(SpeedFactor)`, `Parameter(Boolean)`) exposent des contrôles dans l'UI Smode.
- Lier un paramètre à une propriété cible : créer un `ParameterLinkTarget`, `.target.set(var)`,
  puis `sourceWithTargets.targets.append(lt)`.
- `FunctionCue(Type)` (ex. `Angle`) + `ParametricScalarFunction({input=Seconds, output=Angle})`
  + une `shape` (`LinearRampFunctionShape`, `NoiseFunctionShape`...) pour des animations en boucle.
  **Toujours régler explicitement** `minimum`/`maximum`/`period`/`wrapMode`/`phase`/`offset`/
  `repetitions` — les défauts silencieux (souvent `maximum=minimum=0`) donnent une sortie plate
  sans aucune erreur.
- Pour des cibles avec des plages de sortie différentes depuis une seule source : ne pas relier
  directement (même valeur brute partout) — donner à chaque `ParameterLinkTarget.modifiers` son
  propre `FunctionLinkModifier({input=Percentage, output=Percentage})` avec une `KeyframeFunction`
  (2 `Keyframe` mini, interpolateurs par défaut = `StepKeyframeInterpolator` → forcer
  `LinearKeyframeInterpolator` explicitement sur `.inputInterpolator`/`.outputInterpolator`).
- **Mirorer un champ live vers un autre (ex. `TimelineCue.transport.position` → `Text` d'un
  `LocalTextGenerator`, pour un affichage timecode)** : la bonne méthode est **"Expose As..."**
  (clic-droit UI sur le champ source) puis glisser le résultat sur le champ cible — Smode crée
  un `Link` dans un `LinkBank` (dans `compo.tools`) avec `.source` = `ParameterLinkSource`
  (`.target` = WeakPointer vers le champ SOURCE, ex. `transport.position` ; `.modifiers` contient
  un `ToStringLinkModifier` qui fait la conversion `Seconds` → texte formaté timecode
  `H:MM:SS:FF`) et `.targets` = un `ParameterLinkTarget` (`.target` = WeakPointer vers le champ
  DESTINATION, ex. `textGenerator.text` ; `.modifiers` vide).
  **Reconstruire cette structure via script semblait ne pas fonctionner** au premier essai, même
  en reproduisant fidèlement la structure complète (`Oil.createObject("Link")` +
  `ParameterLinkSource`/`ParameterLinkTarget` + `ToStringLinkModifier` sur `.modifiers` de la
  source + `.target.set(prop)` sur les deux bouts + `linkBank.links.append()`) : le `Link` se
  crée sans erreur, structure identique en introspection (classes, cibles résolues, modifier
  présent) à un Link natif, mais restait figé sur sa valeur placeholder.
  **Cause racine trouvée : ce n'est pas le Link, c'est l'absence de `target` sur la Compo.** Une
  `Compo` embarquée via un `TextureLayer` (`compoLayer.generator = compo`) sans que
  `compoLayer.renderer.target` pointe vers une `ContentMap` (ou autre destination de rendu)
  n'est **jamais évaluée par le moteur** — ni son rendu, ni ses `Link`s, ni rien d'autre à
  l'intérieur, qu'ils soient natifs ou créés par script. Dès qu'un target est assigné
  (`compoLayer.renderer.target.set(contentMap)`, avec `contentMap` pris dans
  `script.project.pipeline.contentMaps`), un `Link` scripté identique à celui décrit ci-dessus se
  met à jour en continu **sans aucune action manuelle**, dès sa création — confirmé en lecture
  active (`text` suivant `transport.position` image par image). Toggler `link.activation` (essayé
  avant de trouver la vraie cause) ne donnait au mieux qu'une évaluation ponctuelle figée — piste
  abandonnée, inutile une fois le vrai problème (target manquant) identifié.
  **Règle générale, pas spécifique aux Links** : toute Compo construite par script et destinée à
  un comportement "live" (Links, Scripts internes, animations) doit recevoir un target dès sa
  construction, sinon rien ne s'anime dedans, même si tout est structurellement correct. Note :
  ceci n'annule pas la limite documentée plus haut sur `renderer.target.set()` qui ne réactive
  pas forcément l'AFFICHAGE d'une ContentMap déjà utilisée ailleurs (bug distinct) — ici on parle
  de l'évaluation/exécution du contenu de la Compo elle-même, qui elle fonctionne dès l'assignation
  du target, sans étape manuelle supplémentaire.

## Timeline (TimelineCue)

- `Compo.mainAnimation` (`MainAnimationOwnedPointer`) accepte un `Oil.createObject("TimelineCue")`
  — assignation directe (`compo.mainAnimation = tc`), pas `.set()` (règle OwnedPointer habituelle).
- `TimelineCue.createBlock(element)` → `(ElementTrack, ElementTrackBlock)` : crée le track ET le
  bloc pour un layer donné en une seule fois, positionné au curseur. Repositionner ensuite à la
  main : `block.autoLength.set(False)` puis `block.position.set(secondes)` / `block.length.set(
  secondes)` (les deux en `Seconds`, pas en frames — convertir via le frame rate, voir plus bas).
- Structure sous-jacente (visible en clair dans un `.compo`/`.project` sauvegardé) :
  `TimelineCue.elementTracks` = `Map({key = WeakPointer(Element), value = ElementTrack})`,
  `ElementTrack.blocks` = `OwnedVector(ElementTrackBlock)`.
- Parcourir les clips : `for element, track in timeline.elementTracks.items()` ; `element.get()` donne
  le layer, `track.blocks[0]` le premier bloc (`.position` / `.length` en secondes). `elt.isChildOf(layer)`
  est **vrai aussi pour le layer lui-même** (`elt == layer` marche aussi). Pour une Scene, le propriétaire
  de la timeline est le layer (`scene.layers` + `scene.mainAnimation`) ; pour un layer Compo, c'est
  `layer.generator`. Toute timeline créée s'appelle « Main Timeline » (non renommable).
- **Bug d'affichage lié à l'ordre de construction** → voir "Bugs UI connus" : construire toute la
  timeline (`createBlock` + réglages) AVANT que la `Compo` soit insérée dans l'arbre du document
  fait planter la synchro du panneau Timeline (layers invisibles, lecture correcte quand même).
  Toujours insérer la `Compo` dans la scène d'abord, construire le `TimelineCue` ensuite.
- Frame rate global du projet, pour convertir images → secondes : `engine.configuration.timing.
  requestedFrameRate` (`VideoTimeBase` avec `.p`/`.q`, ex. 60/1 = 60fps). Pas de propriété
  framerate sur `Compo`/`Pipeline` — c'est un réglage moteur, partagé entre projets ouverts.
- **Animation de paramètres (R15)** : animer une position par clés crée dans la timeline principale
  (`project.masterScene.mainAnimation`, pas `compo.mainAnimation`) une entrée de
  `TimelineCue.parameterTracks` = `Map(ObjectWeakPointer → ParameterTrack(Seconds, Meters))` ; la piste a
  `targetParameter` et `function` = `KeyframeFunction` (`.keyframes`, `len()`, temps dans `.input`). Une piste
  par axe (`x`, `y`) de chaque `Placement`. Lecture par script : `ma.transport.position.set(t)`,
  `ma.transport.play.trig()` / `pause.trig()`, `ma.transport.playing.get()`.
- **Deux écrivains sur une même valeur** : la timeline **réécrit à chaque image** les paramètres qu'elle
  anime, y compris la valeur tenue après la dernière clé. Un Script « At Every Update » qui écrit aussi
  ces paramètres entre en conflit ; s'il compare « position lue » et « position que j'ai écrite » pour
  détecter une manipulation à la main, il prend la réécriture de la timeline pour un tirage (symptôme :
  animation qui saute 1 image sur 2 après la dernière clé). Remède : ne conclure à une action manuelle que
  si la valeur lue change **aussi par rapport à l'image précédente** (la timeline réécrit à l'identique, un
  tirage change à chaque image), ou ne pas écrire sur les paramètres animés.
- Diagnostic image par image : faire écrire une ligne par exécution du Script dans un fichier
  (`open(path, 'a')`), jouer la timeline par script, puis analyser le fichier (les appels du pont ne sont
  pas synchrones avec les images).

## Modificateurs, générateurs et masques (aperçu)

Constats d'usage (R13-R15), classes vues en construisant des scripts :
- **Effets de post-traitement d'une Compo** (`PixelateTextureModifier`, `FeedbackTextureModifier`...) :
  s'ajoutent à `compo.modifiers` (niveau Compo), pas à `renderer.effects`. Un calque frère placé hors de la Compo
  ne subit pas ces effets.
- **Masque d'un dégradé** : une Compo interne contenant une forme sert de `TextureLayerTextureMask.generator`
  sur un `MaskTextureModifier` appliqué à un `GradientTextureGenerator` ; dégradé multicolore via
  `QuadritoneColorFunction` (4 couleurs + 2 positions intermédiaires).
- **Forme point par point** : `PathShapeGenerator.path.points`, chaque `Path2dControlPoint` a
  `position.x/.y`. Trois points à la même X (bas fixe / oscillant / bas fixe) donnent des barres à transitions
  plates ; l'alternance fixe/oscillant donne des pics arrondis. Un point peut être la cible
  (`ParameterLinkTarget.target.set(cp.position.y)`) d'un Link audio.
- **Proportionnalité** : `ParameterLinkSource` + `MultiplyLinkModifier` (facteur par cible) relie un seul
  `Parameter` à N cibles à des échelles différentes (voir aussi `FunctionLinkModifier` plus haut).
- `TestPatternTextureGenerator` : chaque composant (`grid`, `horizontalBar`, `verticalBar`, `diagonals`,
  `corners`, `cornerCircles`, `centeredCircles`, `edges`, `logo`, `coloredCheckerBoard`, `resolutionText`,
  `tileLabels`, `labelText` ; `labelText` et `tileLabels` sont deux composants distincts) a son `.enabled`,
  tous actifs par défaut selon le preset : pour n'en montrer qu'un, désactiver explicitement tous les autres.
  Le générateur a aussi son propre `.background` (couleur avec alpha).
- `UpscaleTextureModifier` (natif) : `algorithm` 0 = SimpleUpscale, 1 = SuperRes (2 et plus invalides),
  `upscaleFactor`, `outputResolution`, `enhence` (netteté), `intensity`, `strong`, `withoutMaxine`. En
  SimpleUpscale ce n'est **pas** de l'IA (ni Maxine) : un simple agrandissement plus un peu de netteté, coût
  quasi nul en performance.
- `StreamDiffusionTextureModifier` (paquet SmodeTech StreamDiffusion-R15) : `mode` et `acceleration`
  (enum `StreamDiffusionAcceleration` : 0 = none, 1 = torchCompile, 2 = tensorRT) sont **verrouillés dans
  l'UI** dès que le process est connecté, mais restent modifiables par `.set()` via script et déclenchent un
  rechargement du pipeline (`isStreamRecreating = 1`). `modelName` accepte un identifiant Hugging Face absent
  des presets (ex. `IDKiro/sdxs-512-0.9`). Un process Python crashé ne se relance pas (`execute.trig()`,
  bascule d'`activation`, `resetEvent` : sans effet) : il faut supprimer et recréer le modificateur. Le
  retrouver par **nom** (recherche récursive) car son index bouge quand d'autres modificateurs sont ajoutés. Script prêt à l'emploi :
  [smode-streamdiff-ctrl](https://github.com/gyomh/smode-streamdiff-ctrl).

## Audio réactif

`AudioSpectrumLinkSource` — classe native pour injecter en continu l'intensité d'une bande de
fréquence dans n'importe quel paramètre via un Link.
- `.extractor` (`AudioSpectrumExtractor`) : `.audioChannel` (`WeakPointer(AudioDeviceChannel)`,
  `.set(channelObj)`), `.frequencyInterval`/`.amplitudeInterval` (`Interval(Percentage)` avec
  `.begin`/`.end`/`.center`/`.size`).
- Devices audio : `engine.devices.devices`, chaque `JuceAudioDevice` a `.inputChannels`
  (ex. "Left"/"Right" en DirectSound, 8 canaux nommés en ASIO Voicemeeter).
  Exemples : [smode-vizualiser](https://github.com/gyomh/smode-vizualiser),
  [smode-oscilloscope](https://github.com/gyomh/smode-oscilloscope).

## Scripts créés par programmation (PythonScriptTool)

**Moteur de script.** Python embarqué = CPython 3.12 complet (`python312.dll` + dossier `python\`, stdlib
entière : `http.server`, `socketserver`, `threading`, `json`), en R13 comme en R15, un seul interpréteur.
C'est la **seule famille de script** (aucun Lua ni JavaScript : l'analyse de `Plugins/*.dll` ne montre que
`Python.dll`, `PythonScriptTool`, `PythonEngineComponent`, `PythonFileScriptToolConverter` ; les autres
plugins « code » sont des intégrations tierces comme Notch, Substance, TouchDesigner). Conséquence : un
vérificateur de syntaxe externe en Python 3.11 rejette des f-strings imbriquées que Smode accepte (3.12).
`Oil` est déjà injecté dans le contexte d'un Script : `import Oil` est inutile. `site-packages/Smode/`
(`Oil.py`, `SmodeSDK.py`, `Sys.py`) enveloppe des extensions compilées dans `Smode.exe` : pas d'`import
Smode` depuis un interpréteur externe. La doc officielle (doc.smode.io, section Python scripting) précise que
l'API n'est pas publiée.

Confirmé fiable :
```python
tool = Oil.createObject("PythonScriptTool")
tool.script.sourceCode.set(codeString)
tool.launchMode.set(4)   # atEveryUpdate
```
Debug : `.script.numExecutions.get()` (compteur, tourne ou pas), `.script.lastExecuteResult.
status.state/.message` (erreur), `.script.lastExecuteResult.printed` (stdout du dernier run).
`tool.script.parentElement` pointe vers son conteneur DIRECT, pas la scène racine — piège si on
suppose la même structure que le script du pont MCP lui-même.

**Paramètres déclarés (`nom: Oil.Type(...)`) — CORRIGÉ R15 (06/10/2026)** : l'ancienne version de
cette référence affirmait qu'ils n'étaient pas introspectables de l'extérieur (`.dynamicVariables`
vide). C'est faux **une fois le script compilé** (`tool.execute.trig()` après `sourceCode.set`) :
`tool.dynamicVariables` liste les paramètres **dans l'ordre de déclaration** et chacun est lisible
ET modifiable : `dv[i].get()`, `dv[i].set(v)`, `dv[i].getFriendlyName()` (libellé affiché), slots
`WeakPointer` (`dv[i].set(layer)`), vecteurs (`dv[0][k].set(layer)`), boutons Boolean (`.set(True)`).
Un câblage de slots par script est donc possible. Les valeurs et les liens (Parameter bank →
paramètre) **survivent à une recompilation** tant que le nom de la variable ne change pas ; renommer
une variable détruit l'ancien paramètre (nouvel objet, valeur par défaut).
- Libellé affiché = nom de variable : camelCase coupé en mots, **espace inséré avant un chiffre**
  (`bone3Rotation` → « Bone 3Rotation », `boneRotation3` → « Bone Rotation 3 », `BONE3Rotation` →
  inchangé). Impossible d'obtenir « Bone3 Rotation » ni un numéro dynamique côté Script ; le libellé
  d'un `Parameter` de bank, lui, est libre (`p.label = ...`).
- Types vus : `Oil.Boolean`, `Oil.Meters`, `Oil.PositiveMeters`, `Oil.PositiveInteger`, `Oil.String`,
  `Oil.createObject("Angle")`, `Oil.createObject("WeakPointer(Layer)")`,
  `Oil.createObject("OwnedVector(WeakPointer(Layer))")` (liste de slots dont le script règle la
  taille lui-même avec `append` / `removeAt`, ex. selon un entier « nombre de bones »).
- **Noms en MAJUSCULES conservés tels quels** (`RELOCATE` → « RELOCATE », `SECTION_RELOCATE` → inchangé,
  `x_RELOCATE` → « X_RELOCATE »). Astuce pour structurer le panneau : des faux paramètres
  `RELOCATE: Oil.String("--------")` servent de titres de section (remettre la valeur à chaque exécution si
  l'utilisateur la modifie : `setattr(script, "RELOCATE", "-" * 40)`).
- **Les déclarations de paramètres doivent précéder tout autre statement, `import` compris**
  (`ScriptStatementOrderException: Parameter declarations should be placed before any other
  statement`) : mettre `import math` etc. après le bloc de déclarations.
- **Noms réservés** : toute variable de script qui porte le nom d'un attribut natif d'élément (ex.
  `preset`, `label`, `tools`, `activation`) entre en conflit : `script.preset` renvoie le
  `ElementPresetSelector` natif, pas votre variable (`'ElementPresetSelector' object has no attribute
  'enumerators'`). Préfixer (`lightPreset`).
- Types de déclaration vérifiés : `Oil.HsvColor()`, `Oil.Percentage(x)`, `Oil.PositiveMeters(x)`,
  `Oil.Boolean(x)`, `Oil.PositiveInteger(x)`, `Oil.createObject("Angle")` ; `Oil.Angle` et
  `Oil.Color` n'existent pas. Angles en radians (`.set(math.radians(d))`).
- **Installer et lancer un Script depuis le pont** : `sourceCode.set(src)` + `parent.tools.append(t)`
  compile bien (`dynamicVariables` remplies) mais n'exécute pas ; faire `t.execute.trig()` dans un
  appel, puis lire `script.lastExecuteResult` / `numExecutions` dans l'appel **suivant** (l'exécution
  a lieu après le retour du pont). Pour changer un paramètre : `t.dynamicVariables[i].set(v)` puis
  `execute.trig()`. Un `print` du Script apparaît dans la sortie de l'appel qui a déclenché l'exécution.
- Un `Real` refuse un `int` Python (`TypeError ... expected Real or float`) : toujours `float(...)`.
- Un script peut aussi s'auto-câbler / se recolorer lui-même (`script.colorLabel`, `script.x.set(...)`).
- **Les scripts partagent le même espace de noms global (R15, 06/10/2026).** Deux copies du même script
  dans un projet (ex. un rig de bras et un rig de jambe) lisent et écrivent les **mêmes** `globals()` :
  un drapeau « initialisation à l'import faite » posé par le premier empêche le second de créer ses
  objets (banks de paramètres jamais créées), un cache d'étiquette partagé bloque la mise à jour du
  `label` du second, et tout état mémorisé d'une image à l'autre (pose précédente, etc.) est mélangé
  entre les deux. **Ne jamais stocker d'état par script dans `globals()` directement** : ranger l'état
  dans un registre indexé par l'objet qui distingue le script, par exemple sa compo :
  ```python
  def S():
      reg = globals().setdefault('_REGISTRY', [])
      comp = script.parentElement
      for c, d in reg:
          if c is comp: return d          # le même élément Smode donne toujours le même objet Python
      d = {}; reg.append((comp, d)); return d
  ```
- **Un Script peut vivre dans un `Group3dLayer`** (`group.tools.append(tool)`) : `script.parentElement` est
  alors le groupe (`.layers`, `.tools`, `.placement`, `.worldMatrix`), pas la Compo. Chaîne de parents
  vérifiée : script → `Group3dLayer` → (groupes imbriqués…) → `Compo` → `TextureLayer` → `Scene` → `Project`
  (`element.parentElement`, `AttributeError` au sommet). `rasterizer`, `currentCamera` et `defaultCamera`
  n'existent que sur la **Compo** : la retrouver en remontant les parents jusqu'à `getOilClassName() ==
  'Compo'`. `Group3dLayer.tools` accepte `PythonScriptTool`, `ParameterBank` et `MaterialBank`. La
  `worldMatrix` d'un groupe **hérite des groupes parents** (rotation / position cumulées) : un rig dans un
  groupe lui-même dans un groupe tourné fonctionne si on travaille en coordonnées locales du groupe et si on
  lit la `worldMatrix` du groupe pour toute orientation monde (ex. poignée face à la caméra). Permet des rigs
  imbriqués (corps > bras, jambes) avec un script par groupe (voir état par script ci-dessus).
  Vérifié : `comp_a is comp_b` est vrai pour deux lectures du même élément, y compris après `gc.collect()`.
  (`getUniqueIdentifier()` lève une exception, `WeakPointer.toString()` renvoie une chaîne vide : pas
  utilisables comme identifiant.) Un script collé depuis un fichier Windows peut avoir des fins de ligne
  `\r\n` : sans effet sur l'exécution, mais `sourceCode.get() == fichier` est alors faux.

**Cascade d'activation** : un calque racine `activation="inactive"` gèle tout ce qui est dessous
(y compris des Scripts "At Every Update" imbriqués), sans erreur ni message. Réflexe de debug si
un script "ne tourne plus" : vérifier `layer.activation.get()` en remontant toute la hiérarchie,
pas seulement le script lui-même.

### Déclencher un Script depuis un autre Script (slots) — confirmé R15 (30/09/2026)

- Déclarer un slot où l'utilisateur glisse un Script : `slot1: Oil.createObject("WeakPointer(PythonScriptTool)")`.
  `script.slot1.get()` renvoie le `PythonScriptTool` (ou `None`).
- Exécuter ce Script : `tool.execute.trig()` (`execute` est un objet `Trigger`, pas une fonction :
  `tool.execute()` lève `'Trigger' object is not callable`). Synchrone, incrémente `numExecutions`.
- `Oil.createObject("Trigger")` est déclarable en paramètre de Script, mais aucune méthode de
  lecture (seulement `.trig()`) : pas de moyen trouvé de détecter un clic depuis le Script.
  Un `Oil.Boolean(False)` remis à `False` par le script fait office de bouton.
- `tool.getUniqueIdentifier()` **plante** : `TypeError: Unable to convert function return value
  ... juce::Uuid`. Ne pas l'utiliser. Une exception non rattrapée dans un Script "At Every
  Update" l'arrête complètement (le pont MCP répond alors en 504).
- Le namespace `globals()` d'un Script **survit au recollage du code** : une fonction retirée du
  source reste appelable jusqu'au redémarrage de Smode. Un serveur HTTP créé avec
  `if "x" not in globals()` garde aussi l'ancienne classe de handler. Solution du pont : case
  `restartServer` (purge des fonctions absentes du source via `ast` + `script.script.sourceCode.get()`,
  puis redémarrage du serveur dans un thread — `shutdown()` bloquerait le thread principal).

### Recharger un script / vider le cache Python — confirmé R15 (06/10/2026)

- Smode R15 n'a **qu'un seul interpréteur Python embarqué** (`sys.prefix` = dossier `python` de Smode
  Compose), ~170 modules chargés au démarrage (stdlib, `Smode`, `Smode.Oil`, `_cppSmode*`). Un module
  utilisateur importé par un Script reste dans `sys.modules` : le modifier sur disque ne suffit pas, il
  faut le purger (modules utilisateur seulement, en épargnant `__main__`, `Smode*`, `_cpp*`, stdlib et
  site-packages) puis `importlib.invalidate_caches()`, et supprimer au besoin les `__pycache__`.
  L'API Oil n'expose aucun cache de scripts (`PythonScript` : `sourceCode`, `lastCompileResult`,
  `lastExecuteResult`, `numExecutions`, `verboseDebug`).
- **Smode ne garde pas le chemin du fichier source d'un Script**, seulement le texte collé
  (`sourceCode`). Pour recharger le code d'un Script depuis un `.py`, il faut apparier soi-même, par
  exemple par le titre de la boîte d'en-tête du fichier ou par `label` == nom du fichier (un Script qui
  renomme son label casse cet appariement), puis `tool.script.sourceCode.set(src)` (recompile).
- Les Scripts se trouvent dans les **`.tools`** de la Scène, de la Compo (le `generator` d'un
  `TextureLayer`) et des groupes, **pas dans `.layers`**. Dans un Script, `script` est le
  `PythonScriptTool` et `script.script` l'objet interne qui porte `sourceCode`. Pour se reconnaître
  soi-même parmi les tools : `tool is script` (`getUniqueIdentifier()` n'est pas convertible).
- Ne pas recharger le Script du pont (`smode_bridge`, « At Every Update ») depuis un autre Script : il
  faut le sauter explicitement.
- **Piège d'écriture de fichier sous Windows** : `open(chemin, "w")` convertit `\n` en `\r\n` ; pour écrire
  un `.py` sans altérer les fins de ligne, ouvrir en binaire ou avec `newline="\n"` (sinon
  `sourceCode.get() == fichier` est faux, voir plus haut).
- Exemple complet : dépôt [smode-clear-script-cache](https://github.com/gyomh/smode-clear-script-cache) (options `NAME_FILTER`,
  `CLEAR_PYCACHE`, `RELOAD`, `RELOAD_SCRIPTS`).

### Sous-processus et fils depuis un Script — confirmé R15 (01/10/2026)

- **Ne jamais faire attendre le fil principal** un sous-processus qui interroge l'interface Smode
  (UI Automation) : pendant l'attente, Smode ne répond plus à UIA (`0 elements`, ou `FindAll`
  « Unrecognized error »). `subprocess.run` direct et fil séparé + `join()` échouent tous deux ;
  `Popen` non bloquant fonctionne. Constaté dans un script lancé par Execute et via le pont ; un autre
  script utilisant la même lecture avec `join` fonctionnait pourtant chez l'auteur : cause de la différence
  non élucidée, le motif non bloquant ci-dessous est donc le plus sûr.
- **Motif qui marche** : le Script lance un fil `daemon` et retourne aussitôt ; le fil fait son travail
  (sous-processus, réseau), puis fait exécuter le code Oil sur le fil principal en postant
  `{"code": ...}` sur un pont HTTP local tournant dans un Script « At Every Update » (voir "Le pont
  MCP"). Le fil lui-même ne touche jamais à Oil.
- **Retour d'info** : les paramètres d'un Script se règlent de l'extérieur via `tool.dynamicVariables`
  (voir « Paramètres déclarés », corrigé R15) ; `tool.label = "..."` reste le moyen le plus simple de
  rendre un état visible dans l'arbre (retrouver le `PythonScriptTool` en parcourant
  `layer.generator.tools`, par préfixe de label ; `getUniqueIdentifier()` est inutilisable). Un Script
  qui remet son propre `script.label` à chaque exécution garde le préfixe stable.
- `tool.script.numExecutions.get()` = 0 : l'Execute cliqué n'a pas atteint ce Script (mauvaise ligne,
  ancien script homonyme, ou script absent du projet rechargé sans sauvegarde).
- Créer un Script dans un projet : `t = Oil.createObject("PythonScriptTool")`, `t.script.sourceCode.set(src)`,
  `t.launchMode.set(0)`, `t.label = "Nom"`, `layer.generator.tools.append(t)` — confirmé.

### Lire la sélection de l'UI (UI Automation, hors Oil)

Oil n'expose aucune sélection (rien dans `engine`, `project`, scènes, timelines). Voir le projet
[smode-selection-reader](https://github.com/gyomh/smode-selection-reader) : lecture du titre du panneau Paramètres. Limites : un seul panneau
Paramètres non verrouillé ; l'arbre UIA est plat (≈780 enfants sous la fenêtre, ≈1500 éléments
`Custom` sans nom) donc **le nom d'une timeline sélectionnée est toujours « Main Timeline »**,
impossible de savoir de quelle scène/compo elle vient — sélectionner le layer de la scène/compo.
`FindAll` coûte ≈5 ms par élément même filtré par type : mettre en cache la position du titre,
`AutomationElement.FromPoint` (renvoie un `Custom` vide sur le titre) puis les voisins
`TreeWalker.RawViewWalker` (`GetNextSibling`/`GetPreviousSibling`) pour trouver le `Text` (≈1 s au lieu
de 4 s). `Add-Type -AssemblyName WindowsBase` requis pour `System.Windows.Point`.

Autres constats (R15, 30/09/2026) :
- **Le panneau verrouillé (épingle) n'affiche pas l'élément sélectionné** : lire un onglet verrouillé donne
  un succès trompeur. Tous les panneaux non verrouillés affichent la même sélection ; un seul onglet est lu à
  la fois (le contenu des onglets inactifs est absent de l'arbre UIA).
- Détection du verrou par les pixels de l'icône : abandonnée. Elle marchait sur l'écran principal mais, sur un
  écran secondaire (1920x1080, 100 %, fenêtre non plein écran, coordonnées négatives), les `BoundingRectangle`
  des enfants sont décalés d'environ 950 px en X (Y et bord gauche corrects) ; même avec
  `PerMonitorV2` le décalage reste (probable défaut JUCE multi-écrans / DPI). Ne pas se fier aux
  coordonnées UIA pour capturer l'écran.
- Le titre du panneau Paramètres est un `Text` de proportion largeur/hauteur ≈ 6,82 (300x44 ou 150x22), sans
  `:` final et sans `ComboBox` sur la même ligne : ce filtre écarte les valeurs numériques, le titre du
  Viewport et le panneau « Remaining: ».
- **Bouton Execute de la LIGNE d'un Script dans l'arbre Éléments : ne change pas la sélection** ; seul le
  bouton Execute du panneau Paramètres du Script oblige à sélectionner le Script (la sélection devient alors le
  Script lui-même).
- Lancé depuis Smode (processus GUI sans console), un `subprocess` doit recevoir `stdin=subprocess.DEVNULL`
  (avec `stdout=PIPE`, `stderr=PIPE`, `creationflags=0x08000000` pour masquer la fenêtre), sinon
  `OSError(9, 'The handle is invalid')` après un redémarrage de Smode (non reproductible via le pont, dont les
  handles sont valides). Sortie en UTF-8 côté PowerShell (`[Console]::OutputEncoding`) et décodage
  `utf-8-sig` côté Python pour les noms accentués.

### Déformer une géométrie par rig (Transform3d + masques) — confirmé R15 (07/10/2026)

- `GeometryLayer.generator.modifiers` (`OwnedVector`) reçoit des `…GeometryModifier` : trouvés par essai de
  `Oil.createObject` : `Transform3dGeometryModifier`, `ScaleGeometryModifier`, `DisplaceGeometryModifier` (pas de Bend /
  Twist / Skin natifs). Masques (`modifier.masks`) : `LinearGeometryMask`, `SphereGeometryMask`, `BoxGeometryMask`,
  `CylinderGeometryMask`, `NoiseGeometryMask`, `RandomGeometryMask`, `FunctionGeometryMask`.
- `Transform3dGeometryModifier` : `anchor` (x/y/z en mètres, repère local de la géométrie), `rotation` (`EulerAngles`,
  ordre 0 = Rz·Ry·Rx, radians), `translation`, `scale`, `intensity`, `masks`. Sans masque : poids 1 partout.
- `LinearGeometryMask.segment.begin / end` (`Segment3d`) : poids 0 au début, 1 à la fin et au-delà (rampe bornée) → zone de
  transition d'un pli. Plusieurs modifiers enchaînés (pivot = articulation courante, rotation relative au bone précédent,
  masque sur le bone déformé) donnent un skinning linéaire en chaîne FK. Exemple complet : [smode-ik-rig](https://github.com/gyomh/smode-ik-rig)
  (IK Deform).
- **Subdiviser l'axe** sinon rien à plier : `CapsuleGeometryGenerator.heightPrecision` (1 par défaut) ; `Precision2d` /
  `Precision3d` (`x`, `y`, `z`, case `uniform` à décocher d'abord, sinon tout change ensemble) ; `precision` scalaire pour
  Rectangle / Circle / Star.
- Générateurs de géométrie existants (`createObject`) : Capsule, Box, Plane, Sphere, Cylinder, Torus, Circle, Helix, Star,
  Text, Particles, Rectangle. Capsule : l'origine du calque est l'extrémité basse. Les positions de sommets ne sont pas
  lisibles en Python (`generator.positions` opaque) : vérifier par capture de la fenêtre Smode.

### Scripts qui s'auto-installent (rig IK) — confirmé R15 (07/10/2026)

- **Se déplacer soi-même** : `copie = script.clone()` (copie source + variables), `groupe.tools.append(copie)`,
  puis retirer l'original de `parent.tools` en le retrouvant avec **`is`** (`parent.tools[i] is script`).
  `getUniqueIdentifier()` n'est pas convertible en Python (`Unable to convert ... juce::Uuid`).
- **Écrire dans un script depuis un autre code** : `tool.script.sourceCode.set(src)` recompile et exécute une fois ;
  `tool.execute.trig()` = une exécution (utile pour tester image par image ; `script.numExecutions` reste fixe si le
  script ne tourne pas tout seul).
- **Un `Parameter` de ParameterBank lié (`ParameterLinkTarget`) repose sa propre valeur sur la cible à chaque mise à
  jour** : écrire seulement la variable du script est annulé (ex. un bouton `Create Rig` remis à False). Écrire aussi
  dans les Parameters dont `p.targets[k].target.get() is var`. Inversement, un champ de bank n'est pas rempli quand on
  remplit la variable côté script : écrire `p.value.set(...)` aussi.
- **`WeakPointer(Layer).set(None)` est refusé** (TypeError) : pour vider des emplacements, vider l'`OwnedVector`
  (`removeAt`) et y ajouter de nouveaux `Oil.createObject('WeakPointer(Layer)')`.
- **Variables de script vectorielles** : `Oil.createObject("OwnedVector(Boolean)")` (+ `append(Oil.createObject('Boolean'))`)
  fonctionne ; un élément peut être la cible d'un `ParameterLinkTarget` (`lt.target.set(vec[i])`).
- Les écritures de valeur de Parameter faites par l'API ne se propagent au script qu'à la mise à jour suivante de
  Smode (pas dans le même appel) : pour tester, écrire directement la variable du script.

## Fichiers 3D importés, textures image et compos de matériau (R15, 08/10/2026)

Vérifié en construisant un workflow Blender -> Krita -> Smode (pièces FBX, une texture image par pièce).

- **Importer un FBX par script** (l'import de l'interface fait pareil) : un `Group3dLayer` dont `.tools` contient un
  `MaterialBank` ; un `GeometryLayer` par pièce avec `generator = Oil.createObject("Scene3dFileGeometryGenerator")`
  (`gen.file.path.set(r"C:\...\modele.fbx")`, `gen.subGeometryToUse.set("NomDuNoeud")` - le nom du nœud dans le fichier) et
  `renderer = ReferenceGeometryLayerUser` qui pointe un matériau de la banque (voir *Matériaux partagés*). Tout construire
  hors de la Compo, ajouter le groupe en dernier.
- **`useLocalPlacement`** (**faux** par défaut sur un générateur créé par script ; l'import de l'interface le met à **vrai**) :
  - `vrai` : la géométrie est dans le repère local du nœud (pivot = origine du nœud, par ex. une articulation). La
    `placement.position` du calque doit porter la position du nœud - à poser soi-même. C'est ce qu'il faut pour un rig.
  - `faux` : la géométrie arrive déjà décalée par la transformation du nœud du fichier. Ajouter la position sur le calque
    la **compte deux fois** (pièces écartées).
  - La `worldMatrix` d'un calque ne reflète que son propre placement et est **périmée pendant une évaluation** après un
    changement : la relire dans un appel suivant.
- **Fichier ré-exporté** : remettre le même `file.path` ne le recharge **pas** ; appeler `gen.file.reload.trig()`.
- **Export FBX Blender** (Y haut pour Smode) : *Apply Transform* (`bake_space_transform=True`) avec
  `apply_scale_options='FBX_SCALE_ALL'` donne des sommets en mètres, une échelle de nœud de 1 et **aucune rotation de
  -90° en X**. Avec `FBX_SCALE_NONE` / `FBX_SCALE_CUSTOM`, le fichier contient des centimètres + une échelle de nœud de 0,01,
  que Smode n'applique pas en placement local (pièces 100 fois trop grosses, empilées). Sans « bake », chaque nœud porte une
  rotation de 90° en X.
- **Texture image** : `Oil.createObject("ImageFileTextureGenerator")`, `gen.file.path.set(str)`. `sourceResolution` vaut
  0x0 et `liveStatus` est `uninitialized` jusqu'à l'évaluation suivante (relire dans un appel suivant).
- **Map de matériau en Compo** (pour garder FX / échelle accessibles) : `mat.components[0].map = compo`, avec `compo =
  Oil.createObject("Compo")` - `rasterizer.resolution.preset.set(40)` avant width/height - et le `generator` de son calque
  réglé (`ImageFileTextureGenerator`, `CheckerBoardTextureGenerator`, `UniformTextureGenerator`). `obj.clone()` copie en
  profondeur un matériau ou une Compo : les copies sont indépendantes (vérifié en changeant la taille d'un damier sur une).
- **Cache des références** : après remplacement des maps d'un matériau par script, les calques qui le référencent gardent
  l'ancien contenu tant que `layer.renderer.referencer.reloadInstance.trig()` n'est pas appelé.
- `CheckerBoardTextureGenerator.size` se lit en pourcentage : `size.width.set(4.0)` affiche `Canvas2dSize(400, 400)`.
- **Piloter les paramètres d'un Script de l'extérieur** : `tool.script.<nom>` n'existe **pas** (seulement dans le Script) ;
  utiliser `tool.dynamicVariables[i]`, en cherchant l'indice par `getFriendlyName()` (ex. « Reset Rig »).

## Références de fichiers, Media Directories et relink (R15, 08/10/2026)

Vérifié en relinkant un projet de 136 médias (vidéos ProRes + PNG) après rangement des dossiers sur le disque.

- **Pas de fonction relink** dans l'interface ni dans la doc. Les DLL contiennent une commande « Relocate media
  directory » (clic droit sur un Media Directory, non testée) qui ne sert que si l'arborescence interne est inchangée.
- **Chemin stocké** : chaque fichier est un `FileReference(VideoFileContent)` (vidéo) ou `FileReference(Color2dMipmaps)`
  (image), en général `layer.generator.file`. Ses variables : `path` (String), `reload` (Trigger), `file`
  (`WeakPointer(File)`). `path` vaut `NomDuMediaDirectory/sous-dossier/fichier` : le premier segment est le **nom** du
  Media Directory, pas un chemin disque.
- **Fichier introuvable** : `ref.file.get().getOilClassName()` vaut `MissingFile` (affiché `<Missing File>`). Trouvé :
  `VideoFile` / `ImageFile`, avec `.nativeFile` (chemin disque absolu via `str(fo.nativeFile.get())`).
- **Relink** : `ref.path.set("NouveauMediaDirectory/sous-dossier/fichier")` suffit : le fichier est résolu tout de
  suite (pas besoin de `reload`). Vérifier l'existence sur disque avant (`os.path.exists`), puis relire la classe de
  `ref.file.get()`.
- **Trouver toutes les références** : parcours générique de l'arbre depuis `script.project` avec `getNumVariables()` /
  `getVariable(i)` / `getVariableName(i)`, plus `len(o)` / `o[i]` pour les vecteurs et `.get()` sur les
  `OwnedPointer` (les generators de Compo sont derrière). Dédupliquer par `getUniqueIdentifier()` **seulement s'il est
  non nul** (sinon le parcours s'arrête après quelques objets) et ignorer les types primitifs (`String`, `Boolean`,
  `Real`...). ~62 000 objets parcourus en quelques secondes sur un projet de spectacle.
- Une variable posée sur `script` depuis le pont n'est pas acceptée (`AttributeError` sur `_cppSmodeSDK.Element`) :
  pour garder des objets d'un appel à l'autre, utiliser `builtins`.
- **Liste des Media Directories** : `%APPDATA%\Smode Compose\configurations\Data_<version>.configuration`
  (ex. `Data_15_8`), blocs `{name = "...", directory = "C:\\...", readOnly = true}` (échappements `\\`). Smode
  l'écrit **avec quelques secondes de retard** après un ajout dans l'UI : un script qui la lit juste après peut
  ne pas voir le nouveau dossier. Pas d'accès direct trouvé via `Oil` (seulement `Oil.getObject(space, uuid)`).
- **Chemin absolu accepté** : `ref.path.set(r"G:\dossier\fichier.wav")` résout le fichier hors de tout Media
  Directory ; Smode le réécrit avec des `/` et le **conserve après fermeture / réouverture** (non portable).
- **Autres types de `FileReference`** : `FileReference(AudioFileContent)` (→ `AudioFile`),
  `FileReference(Group3dLayer)` (FBX importé, une par calque du groupe → `Scene3dFile`),
  `FileReference(GeometryLayerUser)` (path vide, à ignorer).
- **Fichier fraîchement copié sur le disque** : juste après `shutil.copy2` + `ref.path.set(...)`, la
  référence reste souvent `MissingFile` (indexation différée). Appeler `ref.reload.trig()` et revérifier dans
  un appel / une exécution **suivante** ; 2-3 passages peuvent être nécessaires.
- **Scene d'une référence** : les Scenes de premier niveau sont les calques de classe `Scene` dans
  `masterScene.layers` (la `masterScene` n'a pas de label) ; à repérer pendant le parcours de l'arbre.
- `getUniqueIdentifier()` d'un `PythonScriptTool` lève `TypeError ... juce::Uuid` : entourer d'un try (le
  parcours générique le fait déjà) ; pour retrouver un tool, comparer plutôt `script.sourceCode`.

## Interface web servie par un Script (R15, 08/10/2026)

Modèle validé avec [smode-filemanager](https://github.com/gyomh/smode-filemanager) (`Smode_Filemanager_GUI.py`) :
une vraie interface graphique pour un Script, sans rien installer.

- **Script en Launch Mode « At Every Update »** : il démarre une fois un `ThreadingHTTPServer` sur `127.0.0.1`
  (état gardé dans un global, ex. `_FMG`) puis, à chaque frame, traite une `queue.Queue` de tâches Oil.
- **Oil seulement sur le thread principal** : le thread HTTP pose une tâche (`{"task", "arg", "done": Event}`) et
  attend l'`Event` ; la frame suivante l'exécute. Le travail lourd **sans Oil** (`os.walk`, copie de fichiers par
  blocs avec progression) reste dans un thread : Smode ne gèle pas.
- **Les globals sont partagés entre Scripts** : préfixer tout (`fmg_...`, `_FMG`) pour ne pas écraser les fonctions
  d'un autre Script du projet.
- **Mise à jour du code** : le module est réexécuté à chaque frame avec le nouveau `sourceCode`, donc les fonctions
  appelées par le serveur sont toujours les dernières ; redémarrer le serveur seulement si une constante de version
  ou le port change.
- **Fenêtre d'application** : `msedge.exe --app=http://127.0.0.1:<port> --window-size=1400,900` ouvre une fenêtre
  sans barre d'adresse (Edge est présent sur Windows 10/11).
- **Sécurité** : écouter `127.0.0.1` seulement, refuser un en-tête `Host` autre que `127.0.0.1` / `localhost` (DNS
  rebinding) et un `Origin` étranger ; ne pas exposer d'exécution de code arbitraire.
- **Choix de dossier natif** depuis la page : lancer PowerShell en `-STA` avec `System.Windows.Forms.FolderBrowserDialog`
  (fenêtre propriétaire `TopMost`) par `subprocess` depuis le thread HTTP ; afficher dans l'Explorateur :
  `explorer /select,<fichier>`. Les liens `file:///` sont bloqués par les navigateurs (téléchargement ou ouverture
  dans le navigateur).
- **Listes déroulantes** : la surbrillance d'un `<select>` natif ouvert est imposée par Windows (gris) et ne
  suit pas les couleurs de la page ; pour une interface cohérente, dessiner sa propre liste (bouton + panneau) en
  gardant le `<select>` caché comme modèle (valeur + événement `change`).

## Bugs UI connus

- **Liens affichés "Disconnected"** après création via l'API alors qu'ils fonctionnent réellement
  (vérifié visuellement, la donnée circule). Pas résolu par l'ordre de création. Fix constaté :
  fermer et rouvrir le projet force un rechargement complet qui corrige l'affichage — cache
  d'affichage qui ne se recalcule pas dynamiquement en session live.
- **Scale qui se réinitialise après insertion en scène** : `ShapeTextureMask.shape.placement.
  scale.size` (masques circulaires "Stretch to...") se fait recalculer automatiquement une fois
  le document entièrement installé dans la scène live (observé 2 fois, toujours vers l'équivalent
  de 500px/résolution). Fix systématique : réappliquer ces valeurs dans un bloc "POST-INSERTION
  FIXES" exécuté APRÈS `parentElement.layers.append(...)`.
- **Pas de méthode pour surcharger le libellé affiché** d'un paramètre de Script — le libellé est
  auto-dérivé du nom de variable Python (camelCase → Title Case). Aucune `.label`/
  `setFriendlyName()` dans le SDK Python pour ça ; seul levier = renommer la variable.
- **`CustomEnumeration` reste vide dans le panneau** tant que le script n'a pas été RUN
  (Ctrl+Entrée) au moins une fois après le premier Compile — le peuplement se fait dans le corps
  du script (statements), pas à la déclaration.
- **`TimelineCue` (mainAnimation) construite hors-arbre puis insérée d'un coup : layers absents
  du panneau Timeline**, alors que la lecture fonctionne réellement (donnée correcte, juste l'UI
  qui ne se synchronise pas). Même famille que le bug `ContentMap.target` (ligne ~188) : Smode ne
  notifie pas toujours l'UI pour un objet construit pendant que son conteneur est encore hors de
  l'arbre du document ouvert. Fix confirmé : insérer la `Compo` dans la scène (`parentElement.
  layers.append(compoLayer)`) **avant** de créer le `TimelineCue`/appeler `.createBlock()`, pas
  après — reproduit le comportement d'un pilotage pas-à-pas en session live, où la Compo est déjà
  dans l'arbre au moment où la timeline se construit.

## Instabilités observées

Deux crashs complets de Smode rencontrés en construisant cette référence :
1. `Oil.docMe()` appelé juste après avoir manipulé un objet fraîchement extrait d'un vecteur
   post-append → corrélé à un crash, pas confirmé comme cause unique.
2. Re-fetch d'un objet juste après `append()` puis accès à une sous-propriété (`.placement`) →
   `Access violation - no RTTI data!`, puis crash complet à la requête suivante.

Aucun des deux n'est arrivé en respectant la [règle d'or](#règle-dor--configurer-avant-dajouter-jamais-après)
(tout configurer avant, jamais retoucher après). À ce stade, c'est la meilleure protection connue.

Deux autres crashs complets (R15, 06/10/2026), tous deux dus à du **sondage d'énumérations internes** :
3. `Oil.createObject('ActivationState')` suivi d'un `dir()` sur une variable `ActivationState`.
4. Une boucle `.set(0..4)` sur `ReferenceGeometryLayerUser().referencer.address.location` (créée à neuf).
Règle : ne jamais tester des valeurs d'une énumération inconnue. Lire la valeur d'un objet existant
(`.get()`), puis re-poser **cette** valeur ou une valeur connue (ex. `location.set(1)`).

Après un plantage, Smode peut **rouvrir une vieille sauvegarde** : les sauvegardes automatiques sont dans
`Documents\Smode Files\<projet>.project\.versions` (toutes les 5 min) ; une recherche de texte dans
le fichier (`IconFleche`, nom d'un objet) dit laquelle contient le travail voulu.

## Le pont MCP (rappel)

Smode ne propose pas d'API officielle pour un pilotage externe. Le seul chemin est un pont
maison ([smode-mcp](https://github.com/gyomh/smode-mcp)) : un Script Smode en Launch Mode
**"At Every Update"** (pas Manual) démarre un serveur HTTP local, qui dépose les requêtes dans
une `queue.Queue()` + `threading.Event()` — le code Oil doit s'exécuter sur le thread principal
de Smode (l'exécuter directement dans le thread HTTP cause un deadlock total, confirmé via
`netstat -ano`, connexions bloquées en `CLOSE_WAIT`). `_EXEC_NAMESPACE = globals()` partagé
entre tous les appels → comportement type REPL persistant, les variables restent disponibles
d'un appel à l'autre.

**Sécurité d'un serveur HTTP lancé depuis un Script** (constaté en écrivant [smode-server-http](https://github.com/gyomh/smode-server-http)) : écouter
sur `127.0.0.1` ne suffit pas. Un navigateur ajoute l'en-tête `Origin` à toute requête inter-sites, **même vers
127.0.0.1** : un site visité peut envoyer un `POST` `application/x-www-form-urlencoded` (le format du module
HTTP de Chataigne) qui exécute du code dans Smode (CSRF). Pour tout endpoint qui exécute du code : refuser
les requêtes portant un `Origin` ou un `Host` hors liste (DNS rebinding), sauf jeton valide ; n'activer le CORS
que sur les endpoints sans exécution. Utiliser un `ThreadingHTTPServer` pour qu'une requête lente ne bloque pas
les autres. **Ne pas lire de paramètres Oil (`script.host`, `script.port`) depuis un fil secondaire** : les lire
dans le fil principal et les passer en argument au fil.

---

## Projets liés

Scripts et outils Smode construits avec cette référence (tous sous [github.com/gyomh](https://github.com/gyomh)) :
[smode-mcp](https://github.com/gyomh/smode-mcp) (pont MCP), [smode-server-http](https://github.com/gyomh/smode-server-http),
[smode-selection-reader](https://github.com/gyomh/smode-selection-reader), [smode-ik-rig](https://github.com/gyomh/smode-ik-rig)
(IK Rig + IK Deform), [smode-clear-script-cache](https://github.com/gyomh/smode-clear-script-cache),
[smode-vizualiser](https://github.com/gyomh/smode-vizualiser), [smode-oscilloscope](https://github.com/gyomh/smode-oscilloscope),
[smode-trace-writer](https://github.com/gyomh/smode-trace-writer), [smode-light-setup](https://github.com/gyomh/smode-light-setup),
[smode-orbit-camera](https://github.com/gyomh/smode-orbit-camera), [smode-new-scene](https://github.com/gyomh/smode-new-scene),
[smode-streamdiff-ctrl](https://github.com/gyomh/smode-streamdiff-ctrl).

## Contributing

Cette référence est construite par l'usage réel, pas par lecture de doc officielle (qui
n'existe pas pour ce niveau de détail). Si vous découvrez un comportement différent, un piège
supplémentaire, ou une meilleure méthode : ouvrez une issue ou une PR avec la version de Smode
Compose testée. Merci d'indiquer si un point de cette référence est devenu obsolète suite à une
mise à jour Smode Tech.
