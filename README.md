# reference-forge

**A Claude Code skill for reference-driven 3D modelling in Blender.**

Give Claude reference images or reference models and ask for a model. reference-forge turns that into a disciplined
art-pipeline: it sets measurable targets, builds the model region by region in Blender through MCP, compares every part
against the references from every angle, fixes what is off, and shows you labelled side-by-side collages while it works.

It was born while remaking hard-surface game weapons, so it shines on weapons, vehicles, props, mechanical parts and
modular attachments, but nothing in it is weapon-specific.

---

## What it does

- **Working contract first.** Reads your request, files and scene; asks only what it cannot find out; writes down the
  model, purpose, working mode (faithful remake, original reinterpretation or reference merge), which reference drives
  what, and the budget.
- **Measurable success.** A 90/100 working score across weighted areas (form, design, detail, colour, material) with
  per-area thresholds. No "looks done to me" endings.
- **Comparison toolkit.** Silhouette IoU difference maps, part-ID renders, textured blueprint overlays, relief (depth)
  maps, normal-map reading in UV space, channel-by-channel texture comparison and surface-relief renders, each mandatory
  at a defined stage (design, verification, texturing).
- **Solo 360° part reviews.** Every part is isolated and shot from 14+ angles, inventoried face by face (bottom, back,
  inside and mating faces included) and matched element by element, so hidden faces do not get the lazy treatment.
- **Automatic compare-and-fix loop.** Fixes defects without asking, checks for regressions, keeps the best version,
  changes approach when progress stalls, and only asks you real design decisions.
- **LookDev and bake.** Layered procedural PBR materials (base, roughness breakup, micro bump / stippling, edge wear,
  cavity dirt, heat), UV rules and a bake helper that produces BaseColor / Roughness / Metallic / Normal for game engines.
- **Progress collages in the chat.** Reference | ours | difference columns, one row per view, short labels in your
  language.
- **Modular attachments.** Swappable parts on root Empties that snap to socket Empties on the main model.
- **Speaks your language.** Replies and collage labels follow your operating system's display language.

## Requirements

- [Claude Code](https://claude.com/claude-code) (CLI, desktop app or IDE extension).
- Blender 4.1 or newer (tested on 5.2).
- A Blender MCP server that lets Claude run Python in Blender and capture views, for example
  [blender-mcp](https://github.com/ahujasid/blender-mcp) (`uvx blender-mcp` + its Blender add-on).
- Python 3 with [Pillow](https://pypi.org/project/pillow/) for the collage script (`pip install pillow`).
- Cycles for material review and baking (the Bevel shader node used for edge wear is Cycles-only).

## Installation

Clone the repository into your Claude Code skills folder; the repository root is the skill folder.

```bash
git clone https://github.com/ItsRegnalt/reference-forge.git ~/.claude/skills/reference-forge
```

On Windows (PowerShell):

```powershell
git clone https://github.com/ItsRegnalt/reference-forge.git "$env:USERPROFILE\.claude\skills\reference-forge"
```

To share it with a single project instead, clone it into `<project>/.claude/skills/reference-forge`.

Restart Claude Code (or start a new session) and the skill is picked up automatically. Update later with `git pull`.

## Usage

Just describe what you want and hand over references. The skill triggers on reference-driven modelling requests, or
call it by name.

```text
Remake the rifle in refs/m4a1.zip in Blender. Keep its proportions, build your own geometry,
and give me a modular stock, optic and foregrip.
```

```text
/reference-forge Model this magazine from these three product photos; check every face from 360°.
```

```text
Texture the receiver like the reference textures: black anodised metal with edge wear and cavity dirt,
then bake it for Godot.
```

What you will see:

1. A short working note and, if needed, one batch of questions.
2. Blockout → detail → materials / UV → delivery, region by region.
3. A labelled collage after every region and stage, then a short report with the measurements.

### Running two Blender instances in parallel

Want one agent on a rifle and another on a pistol? Start a second Blender, set its MCP add-on to another port
(e.g. 9877) and register a second MCP server that points there:

```bash
claude mcp add blender2 -e BLENDER_PORT=9877 -- uvx blender-mcp
```

Tell each session which server to use; never let two agents drive the same scene.

## Helper scripts

The scripts live in `scripts/`. Inside Blender they are loaded as text blocks and executed
(`exec(bpy.data.texts['rf_helpers.py'].as_string())`); Claude does this for you.

| Script | What it is for |
|---|---|
| `rf_helpers.py` | Geometry builders: profile extrusion, lathe / closed lathe, lofts, curved-path lofts, sweeps, superellipse and rounded-rect sections, bevel, boolean cuts, chamfers, Picatinny-style rails, real screws / nuts / knurled knobs |
| `rf_trace.py` | Slice reference meshes and loft new bodies through the slices |
| `rf_silhouette.py` | Silhouette IoU with red/green difference images, outlines, relief (depth) maps |
| `rf_blueprint.py` | Textured orthographic blueprints of a reference and magenta edge overlays of your model |
| `rf_gapcheck.py` | Finds gaps between parts that should touch |
| `rf_lookdev.py` | Layered procedural PBR materials, scale applying, PBR baking |
| `rf_collage.py` | Labelled progress collages (runs outside Blender) |

Conventions: +Y forward, +Z up, metres. Set `OUT` or the `RF_OUT` environment variable for image output.

## Repository layout

```text
reference-forge/
├── SKILL.md        # the skill Claude reads
├── README.md
├── LICENSE         # MIT
└── scripts/        # Blender / Python helpers
```

## Notes and limits

- Reference models you own or are allowed to use are fine as references. When you ask for a remake, the skill builds
  its own geometry rather than delivering the reference mesh.
- Downloading assets or opening external sites is always done with your approval.
- Scores are working scores against the defined criteria, not a scientific similarity measurement.
- Procedural materials must be baked before they work in a game engine.

## License

[MIT](LICENSE) © 2026 ItsRegnalt

---

## Türkçe özet

**reference-forge**, Blender'da referans görsel veya modellerden 3D model üretmek için bir Claude Code skill'idir.
İsteği bir çalışma sözleşmesine çevirir, 90/100 puanlı ölçülebilir hedef koyar, modeli MCP üzerinden bölge bölge kurar,
her parçayı referansla 360° karşılaştırır (silüet farkı, blueprint bindirme, kabartma haritası, normal haritası okuma),
bulduğu kusuru sormadan düzeltir ve ilerledikçe sohbete etiketli referans / çıktı kolajları gönderir. Katmanlı
prosedürel malzeme, UV ve oyun motorları için bake adımlarını da kapsar. Cevaplarını işletim sisteminizin dilinde verir.

Kurulum: depoyu `~/.claude/skills/reference-forge` klasörüne klonlayın ve Claude Code'u yeniden başlatın.
