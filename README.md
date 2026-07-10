# Smode Oil API — Référence non-officielle

> Smode Tech ne publie pas de documentation de l'API Oil/SmodeSDK pour un pilotage externe.
> Tout ce qui suit vient de reverse engineering (introspection live via `dir()` / `Oil.docMe()`)
> et de retours d'usage réels, accumulés en construisant des features avec le
> [pont MCP smode-mcp](https://github.com/gyomh/smode-mcp). Vérifié sur Smode Compose R13.
> Contributions bienvenues — voir CONTRIBUTING en bas de fichier.

## Sommaire
- [Introspection sûre](#introspection-sûre)
- [Règle d'or : configurer avant d'ajouter, jamais après](#règle-dor--configurer-avant-dajouter-jamais-après)
- [Le piège `.linked`](#le-piège-linked)
- [Résolutions](#résolutions)
- [Pointeurs polymorphes (OwnedPointer)](#pointeurs-polymorphes-ownedpointer)
- [Enums : jamais deviner l'index](#enums--jamais-deviner-lindex)
- [Cartographie de l'arbre projet](#cartographie-de-larbre-projet)
- [Système de Parameters / Links / Cues](#système-de-parameters--links--cues)
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
3. `Oil.createObject("NomDeClasse")` dans un `try/except` — teste si une classe existe sans
   avoir à la deviner dans la doc.
4. `Oil.docMe(obj)` — introspection complète documentée officiellement (types, hiérarchie).
   **Fonctionne bien sur un objet isolé** (juste créé, ou lu proprement depuis l'arbre). Éviter
   de l'appeler sur un objet qu'on vient de manipuler dans un append/removeAt risqué (voir
   section instabilités) — pas confirmé comme LA cause d'un crash, mais corrélé une fois.

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

## Le piège `.linked`

Toute taille/résolution 2D a un flag `.linked` (Boolean), **True par défaut**, qui force
silencieusement `width == height` (ou X == Y) dès qu'on modifie une seule des deux valeurs —
**aucune erreur**, juste un résultat visuel faux. Toujours :

```python
obj.size.linked = False   # AVANT
obj.size.width = 1000.0
obj.size.height = 200.0
```

Concerné : `Canvas2dSize` (placement/scale), `Size3d(PositiveMeters)` (géométrie 3D — ici pas de
`.linked`, x/y/z indépendants), `InheritableImageResolution`, `ImageResolution`,
`CheckerBoardTextureGenerator.size/.balance`.

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

engine                              # niveau système, PAS projet (partagé entre projets ouverts)
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

**Limite majeure** : les paramètres déclarés en tête d'un Script (`nom: Oil.Type(...)`) ne sont
PAS introspectables depuis l'extérieur du script (ni `.dynamicVariables` — toujours vide — ni
`getVariableByName`). Impossible de câbler par script un WeakPointer exposé en paramètre d'un
AUTRE Script ; seul l'utilisateur peut le faire à la main (drag & drop dans l'UI). Un script peut
en revanche s'auto-câbler lui-même au premier run (`if script.x.get() is None: script.x.set(...)`)
puisque ça se passe depuis l'intérieur.

**Cascade d'activation** : un calque racine `activation="inactive"` gèle tout ce qui est dessous
(y compris des Scripts "At Every Update" imbriqués), sans erreur ni message. Réflexe de debug si
un script "ne tourne plus" : vérifier `layer.activation.get()` en remontant toute la hiérarchie,
pas seulement le script lui-même.

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

## Instabilités observées

Deux crashs complets de Smode rencontrés en construisant cette référence :
1. `Oil.docMe()` appelé juste après avoir manipulé un objet fraîchement extrait d'un vecteur
   post-append → corrélé à un crash, pas confirmé comme cause unique.
2. Re-fetch d'un objet juste après `append()` puis accès à une sous-propriété (`.placement`) →
   `Access violation - no RTTI data!`, puis crash complet à la requête suivante.

Aucun des deux n'est arrivé en respectant la [règle d'or](#règle-dor--configurer-avant-dajouter-jamais-après)
(tout configurer avant, jamais retoucher après). À ce stade, c'est la meilleure protection connue.

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
n'existe pas pour ce niveau de détail). Si tu découvres un comportement différent, un piège
supplémentaire, ou une meilleure méthode : ouvre une issue ou une PR avec la version de Smode
Compose testée. Merci d'indiquer si un point de cette référence est devenu obsolète suite à une
mise à jour Smode Tech.
