# Smode Oil API — Référence non-officielle

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
- [Verrou et activation (ActivationState)](#verrou-et-activation-activationstate)
- [Matériaux partagés, références, profondeur](#matériaux-partagés-références-profondeur-r15)
- [Caméra de la Compo](#caméra-de-la-compo-r15)
- [Texte (TextLayer)](#texte-textlayer)
- [Parameter banks liées à un Script](#parameter-banks-liées-à-un-script-r15)
- [Vérifier visuellement (hors API)](#vérifier-visuellement-hors-api)
- [Système de Parameters / Links / Cues](#système-de-parameters--links--cues)
- [Timeline (TimelineCue)](#timeline-timelinecue)
- [Audio réactif](#audio-réactif)
- [Scripts créés par programmation (PythonScriptTool)](#scripts-créés-par-programmation-pythonscripttool)
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
le corps du script avec `CustomEnumerationElement` (`.label`=texte, `.value`=int) via
`.elements.append(...)`, protégé par `if len(script.x.elements) == 0`. `.set()/.get()` utilisent
le label (string), contrairement aux enums natifs qui utilisent un entier. Alternative plus simple
si un simple booléen suffit : `Oil.Boolean` évite tout ce bug.

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
- Exemple complet (rig IK/FK de N bones, poignées, banks) : projet `Smode_IK`, script `ik_arm_solver.py`.
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
- Création d'un matériau par script (aucun appel UI) : voir `make_icon_material` dans `ik_arm_solver.py`
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
  variable. Le Parameter prend la couleur de son bank (`colorLabel`). Le lien est à sens unique
  (bank → script) : un paramètre que le script remet lui-même à zéro (bouton) reste coché dans le bank.
- Le `colorLabel` de tout élément : `c = o.colorLabel; c.red.set(r/255)` (valeurs 0-1, `SrgbColor`).

## Vérifier visuellement (hors API)

Le rendu ne se lit pas par script. Technique qui marche : PowerShell, `GetWindowRect` du processus
Smode + `Graphics.CopyFromScreen` sur ce rectangle seul (jamais l'écran entier), puis lecture du PNG.
Recadrer sur le viewport pour lire une icône ; la barre d'état en bas de la fenêtre donne les erreurs
de rendu (« No direct pointer », « Unspecified reference », « No Triangles... »).

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

## Audio réactif

`AudioSpectrumLinkSource` — classe native pour injecter en continu l'intensité d'une bande de
fréquence dans n'importe quel paramètre via un Link.
- `.extractor` (`AudioSpectrumExtractor`) : `.audioChannel` (`WeakPointer(AudioDeviceChannel)`,
  `.set(channelObj)`), `.frequencyInterval`/`.amplitudeInterval` (`Interval(Percentage)` avec
  `.begin`/`.end`/`.center`/`.size`).
- Devices audio : `engine.devices.devices`, chaque `JuceAudioDevice` a `.inputChannels`
  (ex. "Left"/"Right" en DirectSound, 8 canaux nommés en ASIO Voicemeeter).

## Scripts créés par programmation (PythonScriptTool)

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
- Un `Real` refuse un `int` Python (`TypeError ... expected Real or float`) : toujours `float(...)`.
- Un script peut aussi s'auto-câbler / se recolorer lui-même (`script.colorLabel`, `script.x.set(...)`).

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
`smode-selection-reader` : lecture du titre du panneau Paramètres. Limites : un seul panneau
Paramètres non verrouillé ; l'arbre UIA est plat (≈780 enfants sous la fenêtre, ≈1500 éléments
`Custom` sans nom) donc **le nom d'une timeline sélectionnée est toujours « Main Timeline »**,
impossible de savoir de quelle scène/compo elle vient — sélectionner le layer de la scène/compo.
`FindAll` coûte ≈5 ms par élément même filtré par type : mettre en cache la position du titre,
`AutomationElement.FromPoint` (renvoie un `Custom` vide sur le titre) puis les voisins
`TreeWalker.RawViewWalker` (`GetNextSibling`/`GetPreviousSibling`) pour trouver le `Text` (≈1 s au lieu
de 4 s). `Add-Type -AssemblyName WindowsBase` requis pour `System.Windows.Point`.

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

---

## Contributing

Cette référence est construite par l'usage réel, pas par lecture de doc officielle (qui
n'existe pas pour ce niveau de détail). Si vous découvrez un comportement différent, un piège
supplémentaire, ou une meilleure méthode : ouvrez une issue ou une PR avec la version de Smode
Compose testée. Merci d'indiquer si un point de cette référence est devenu obsolète suite à une
mise à jour Smode Tech.
