---
name: reference-forge
description: Builds and edits 3D models in Blender (MCP / bpy) from reference images or reference models, following the user's request. Compares form, design, detail, colour and material against the right references, fixes gaps and re-verifies with measurable checks (silhouette IoU, blueprint overlays, relief maps, 360° part sets) and labelled progress collages. Use for faithful remakes, original reinterpretations and work that merges several references — hard-surface models such as weapons, vehicles, props, mechanical parts and modular attachments, whether remaking an existing model or building from scratch.
---

# reference-forge

## Language

Write every user-facing message, report and collage label in the operating system's display language. Detect it
once at the start (Windows: `(Get-UICulture).Name` in PowerShell; macOS: `defaults read -g AppleLanguages`;
Linux: `echo $LANG`). If detection fails, use the language the user writes in. An explicit language request from the
user overrides both. This file, code, object and file names stay in English unless the project uses other names.

## Purpose

Build the model the user asked for. Do not look at the references only at the start; compare against them throughout
production.

Never judge success by silhouette alone. Form, design, detail, colour, material and the required views are verified
together.

The user's explicit request overrides this skill's defaults. The skill is project-agnostic: take anything project
specific (paths, axes, colours, budget, naming) from project files, memory or the scene.

## 1. Turn the request into a working contract

First read the user's message, the provided files and the relevant scene. Do not ask for what is already known.

Ask all uncertainties that affect the work and cannot be resolved from the sources in one go, recommended option
first. Continue with any work that does not depend on the missing information.

Write a short working note covering:

- The model to build, its purpose (real-time game / render) and the delivery format.
- The working mode: faithful remake, original reinterpretation or reference merge.
- Which reference is used for which properties.
- Features to keep, allowed changes and out-of-scope work.
- Required views, quality thresholds and technical budget.
- Modularity: swappable parts (attachments), socket points, alternative sets.
- Environment: which Blender instance / MCP port (never touch another session's scene), save and commit policy.

Decide axis, units, scale, polygon and texture budget when the work needs them.

### Working modes

**Faithful remake:** keep the reference's distinctive form, proportions, part layout, details and appearance. Do not
redesign unless asked.

**Original reinterpretation:** lock the features the user wants kept. Make creative changes only in the allowed areas.

**Reference merge:** pick a source for each area, e.g. form from A, surface design from B, colour from C, and compare
each area against its source. A surface language taken from one source (slots, ribs, screw layout, chamfer and corner
radii) is adapted to the other source's form; placing the structure is not enough, the surface pattern is the work itself.

Whether a reference mesh may be inspected, edited or delivered depends on the user's request and the usage rights
available. When a remake is requested, delivering the reference mesh does not satisfy the request.

## 2. Reference priority and uncertainty

Tag each reference with one or more roles:

- Form and proportion.
- Part layout and connections.
- Design language and detail.
- Colour and material.
- Dimensions and scale.

Set the primary source for each area. Keep the priority the user set.

Do not silently average conflicting references. If the priority is unclear and it affects the result, ask.

Record unseen surfaces and inferred details as "estimated". Never report them as verified reference matches.

Do not treat a single perspective photo as an orthographic drawing. Account for perspective, lens and lighting uncertainty.

### Gathering references

Order: files the user gave → models already in the project/scene → external sources. Research externally only when
needed and within the permissions you have. Record the source and terms of use of every downloaded asset.

- **Files:** extract each archive into its own empty temporary folder. Report empty (few-byte) archives. Hook up the
  textures with the mesh (BaseColor, AO, Normal (flip green for DirectX), Roughness, Metallic). Verify unit and axis
  conversion with a render (e.g. cm → 0.01 scale, OBJ import axis conversion).
- **Multi-angle references (one angle is not enough):** manufacturer product galleries usually provide left, right,
  front, back, top and oblique views as separate images; open them side by side. Rotate a model in a 3D viewer
  (e.g. Sketchfab) by dragging and capture every angle.
- **3D from the internet:** Blender MCP `search_assets` (Sketchfab: realistic, licences vary; Poly Haven: CC0). Look
  at `previews` first. Tell the user what and from where before downloading, and get approval. Pass `target_size`
  to `import_asset`.
- **Real-world check:** do not trust reference models alone; find the real product's dimensions on manufacturer or
  retailer pages. Compute ratios and pick the reference that matches reality. Drop shape decisions that do not exist
  on the real object.
- **Compare part by part:** instead of a photo of the whole model, render the same part of each reference at the same
  apparent size from the same angles, side by side.

## 3. Define success criteria before starting

The default target is a score of 90/100.

This score is not an absolute or scientific "90% visual similarity" claim. It is a working score against the defined criteria.

For each area define:

- The reference to use.
- The measurement or review method.
- The pass threshold.
- Importance and weight.
- Critical failure conditions.

Suggested starting weights:

| Area | Weight |
|---|---|
| Form and proportion | 30% |
| Design and part layout | 25% |
| Detail accuracy | 20% |
| Colour distribution | 15% |
| Material appearance | 10% |

Adapt the weights to the request: a colour-focused request weights colour higher, a form-focused one weights form higher.

Never drop a requested area from evaluation. Mark areas that do not apply, with the reason, and redistribute their weight.

Default acceptance:

- Weighted total at least 90/100.
- Every mandatory area at least 90/100.
- Every required view passes its own mandatory checks.
- No critical defect.
- Technical delivery conditions met.

Apply different thresholds if the user sets them. Never lower thresholds later because the work got hard.

## 4. Separate measurement from visual review

Compute numeric measurements. Label visual assessments as reasoned review.

Never give a precise score for something that was not measured.

### Form and proportion

Use what fits:

- Silhouette IoU (side / top / front). Pick the grid cell per part (whole model 2 mm, small part 0.5 mm).
- Width, height and depth ratios.
- Position error of landmark points.
- Section and outer contour differences (slice-by-slice width/height).
- Part count and layout.

An IoU of 0.90 alone does not mean the whole model is 90% similar.

Measurement techniques and traps:

- **Silhouette → polygon:** polygon from column extremes of the silhouette raster. Breaks on slanted or undercut
  shapes; then draw the polygon from the blueprint by hand.
- **Crop-boundary trap:** if you crop a region at an axis value, the boundary looks like a fake edge; do not measure it.
- **Relief map:** a face's depth map (outermost coordinates) shows where protrusions are.
- **Separate by loose parts** (on a copy): gives boxes and centres of the reference's sub-parts.
- **Thin-part sampling:** thin triangles rasterise as dotted patterns; do not mistake the noise for a real difference.

### Design and detail

Inventory the important visible elements of the reference: screws (hex / torx / phillips / slot / nut), pins,
latches, hinges, springs, holes, slots, ribs, knurling/texture, chamfers, channels, engravings.

Check presence, count, position, orientation, size and shape of each. Weight distinctive details higher.

Looking detailed is not enough. Details in the wrong place or unrelated to the reference are not success.

### Colour and material

Compare colours on matching surface regions. Do not merge the background and different material regions into one average.

Examine colour distribution, lightness, saturation and hue differences. For numeric colour comparison match the
colour space and comparison conditions (texture pixels are usually sRGB; convert to linear for material inputs).

When extracting material values from reference textures, split them into regions (e.g. dark metal / coloured polymer)
and measure median and percentile range of colour, roughness and metallic per region.

Assess material classes (metal, rubber, paint, glass) by roughness, reflection, transparency and surface scale.

Do not take the light colour in a photo as the material colour. Record the uncertainty.

## 5. Prepare the scene and comparison conditions

Make sure you are in the right Blender scene (with several Blender instances, check which MCP server / port).
Do not change unrelated scenes or objects.

Keep references, production, alternatives and temporary tools in separate collections:
`REF_*` (references), `<Model>_vN/<region sub-collections>`, `ATT_*` (swappable parts), `OLD_*` (old versions,
excluded, never deleted), `TMP_*` (cameras, focus empties). Cutters (`CUT_*`) are hidden in render and viewport and
parented to their owner. Operate on copies of references.

Create a restore point before big changes. If you may not overwrite the main file, use a working copy. Pack external
textures (`pack()`) before saving; save and commit only when the user asks.

Make camera, framing, resolution, scale and alignment comparable.

Use neutral materials and suitable orthographic views for form review. Use fixed lighting, exposure and colour
management for appearance review.

When comparing to a perspective photo, match the camera as well as possible. Never hide camera error by distorting geometry.

Choose the required views per model. Besides the main views include angles that show depth, joints and distinctive details.

If comparison conditions change, regenerate earlier and later results under the same conditions.

### Alignment

- Set the axis convention and convert references to it (after import: `data.transform(matrix_basis)`).
- Two models in one frame: pick two anchor points (e.g. front edge of the main body + symmetry axis). Take scale from
  a known length ratio. Apply `M = T(B)·S(s)·T(−A)` to a copy. Check: a third point must land by itself; if it does
  not, an anchor is wrong.
- Align sub-part references to the surface/socket they attach to.
- Do not trust numbers in briefs; measure values such as axis height in the scene.

### Blueprints and overlays

- Without photos, the reference's own textured orthographic renders are the blueprints: right, left, top, bottom, front, back.
- Also place blueprints in the scene as `Empty (IMAGE)` (opacity ~0.45, in front, hidden in render).
- Render your model from the same camera and overlay it. Viewport capture tools may not show image empties; render overlays are reliable.
- Pixel → world: `u = centre + (px − W/2)·(ortho/W)`; the vertical axis is inverted. Check axis signs per view direction.
- Choose the ortho width per region so the region fills the frame.

### Comparison toolkit (mandatory)

These methods turn eyeballing into measurement. The table says which are mandatory at which stage. Images shown to
the user carry only short labels saying what the image and model are; no long explanations.

1. **Silhouette difference map (IoU):** reference and model are rasterised on the same orthographic axis at 2 mm
   (0.5 mm for small parts). Grey = overlap, red = in reference but not in model (missing volume), green = extra in
   model. Side, top and front are mandatory; bottom and back too for parts. Always reported with the numeric IoU.
   Dotted grey patterns are sampling noise from thin triangles, not differences. (`silcheck`)
2. **Part ID render:** each object gets its own flat colour (object colour, flat shading), rendered from at least 4
   angles. On the reference it shows part boundaries, sub-part count and where each part starts and ends; with the same
   colour mapping it verifies your part layout. Restore viewport settings afterwards.
3. **Textured blueprint and overlay:** the reference with its own textures (DirectX normals: green flipped) rendered
   orthographically from at least 4 directions; your model rendered with the same camera and its edges (magenta) drawn
   on top. Shows detail positions at pixel level. (`region_bp`, `region_cmp`, `overlay`)
4. **Relief (depth) map:** a depth image from a face's outermost coordinates, with the same colour range for reference
   and model. Shows position and depth of slots, engravings, pin heads, raised lettering and protrusions. (`relief`, `relief_png`)
5. **Reading the normal map (in UV space):** open the reference Normal map as a flat image and overlay the UV layout
   (UV layout export). Purple-blue (0.5, 0.5, 1) is flat; thin lines with red/green edges are grooves and bumps carried
   by the texture, not the geometry. Map each island to its face; add these details to the inventory and decide for
   each "geometry or texture". Read BaseColor, Roughness and AO the same way (labels, wear, dirt regions).
6. **Channel-by-channel texture comparison:** reference maps and your baked maps (BaseColor, Roughness, Metallic, AO,
   Normal) side by side at the same scale; then both models textured under the same light and camera. Shows hue, wear
   amount and placement, roughness distribution and how normal detail was matched.
7. **Surface relief render (normal / matcap):** your model without materials, normal direction as colour (or a
   matcap). Shows whether normal maps and micro surface actually read, and which faces stayed smooth.

| Stage | Mandatory methods |
|---|---|
| Design: reference analysis and inventory before modelling | 2, 3, 4, 5 (on the reference), 1 (baseline) |
| Verification: end of every region and before delivery | 1, 2, 3, 4 and the 360° close-up set (§6) |
| Texturing and painting: materials, UV, bake | 5, 6, 7 and textured side-by-side renders under the same light |

A stage is not passed until its mandatory methods have been produced. If a method cannot apply (e.g. the reference has
no textures), write that in the report with the reason.

### Progress collage (sent to the chat)

As work progresses, send the user labelled collages showing reference and output side by side. The user must be able
to tell what is what without reading an explanation.

- **When:** at the end of every region, at every stage change (blockout, detail, material/UV, delivery), after a big
  fix and whenever the user asks. It comes before the text report.
- **Layout:** columns `Reference (original)` | `Ours` | if needed `Difference / overlay` (silhouette difference, edge
  overlay, mask). Rows are views (right, left, top, bottom, front, back, 3/4 obliques, detail close-ups). Images in one
  row use the same camera, scale and light.
- **Labels (inside the image, in the user's language, short):** only what the image and the model are. Title = part
  and version (e.g. "Magazine v3"); column header = model name (e.g. "Reference: Cinnamon M4A1", "Ours: Rifle v3",
  "Difference"); row label = view (e.g. "Right", "Bottom", "3/4 front"). No explanations, measurements, reading
  instructions or footnotes (leave `note`, `subtitle`, `footer` empty in the spec). Views missing in the reference are
  drawn as an empty cell with a short "n/a" label in the user's language (`missing_label`).
- **Tool:** `scripts/rf_collage.py` (outside Blender, Pillow): `python rf_collage.py spec.json out.png`; the spec format
  is at the top of the script. Render the images to separate files in Blender, then build the collage.
- **Sending:** send the collage to the chat as a file that opens as an image, with no caption or one short line. If no
  file-sending tool exists, show the image in the chat and give the full file path. Split large sets into several
  collages (≤ 6 rows each).

## 6. Production order

Build the big form first. Then part layout, mid-scale design, fine detail and appearance.

For the big form, build the main masses from reference slices and take the section character from the reference
(rounded corner, flat chamfer, octagon, superellipse).

Split the model into functional or visual regions (e.g. main body → fastening elements → end parts → attachments).

For each region:

- Record the reference features and points to keep.
- Produce the region blueprints (at least 4 directions) and renders of the current state from the same cameras.
- List missing and wrong elements with positions; state explicitly what will not be done.
- Fix the most important differences. Delete misplaced items and rebuild them at the right coordinates. Do not break
  good parts: when replacing a mesh, swap the data so modifiers are kept.
- Produce the regional comparison.
- Check whether the change affected the whole model.

Never hide big form errors behind small details. Never add elements that are not in the reference just to make the model look complex.

### Per-part 360° review (solo)

When the reference is an assembly, evaluate every part both inside the whole and on its own. Before and after
modelling a part (e.g. a magazine):

1. **Isolate the part in the reference.** Put the object/group in a collection (on a copy, splitting by loose parts if
   needed) and hide everything else (solo). Note the neighbouring surfaces it attaches to.
2. **Produce a 360° set.** Same framing and light, at least: front, back, left, right, top, bottom and 8 obliques
   (4 from above, 4 from below), plus a close-up of every distinctive detail. If the part has cavities or openings,
   look from inside or through a section plane.
3. **Inventory every face element by element.** For each view list what you see (ribs, slots, embossing, engraving,
   screws, edge folds, windows, protrusions, steps) with position, count, depth/height and shape. Do not skip hard-to-see
   faces (bottom, back, inside, mating faces, parts covered when assembled).
4. **Compare across topics:** form and section, depth/relief (normal map and relief map), texture and surface language,
   UV layout and texel density, colour and material regions, wear/paint marks, connection details. Inspect the
   reference's texture maps (BaseColor, Normal, Roughness, AO) on the same part one by one; decide whether normal-map
   detail is matched in geometry or in texture.
5. **Shoot your part with the same set** and put each angle next to the reference. For every inventory item record:
   present and correct / present but wrong / missing / intentionally not done (reason).
6. **Detail the unseen places too.** Do not simplify faces that exist in the reference but are not visible from the
   main angle; a detailed easy face with flat remaining faces is not acceptable. Mark only regions that are truly not
   visible in the reference as "estimated" and fill them with plausible, consistent detail.
7. **Then return to the whole.** Re-evaluate the part inside the model, with its neighbours, from the same angles:
   proportion, joints, design-language consistency.

A part is not "done" until the inventory is met in every angle of its 360° set.

Choose the method per geometry. Do not tie the work to a single technique: boolean, loft, profile extrusion, lathe,
curved-axis loft, curves, sculpting or textures.

Verify that the tools, Blender version and helper scripts you plan to use actually exist. Never use missing tools as if they existed.

## 7. Automatic compare-and-fix loop

Waiting for user approval at the end of every region is not the default.

Within the agreed goal and scope, fix defects yourself; do not ask "shall I fix it", report what you fixed. Ask when
you would have to make a new design choice for the user (part type, proportion, colour, deliberate deviation from the
reference, scope change) or when sources conflict unresolvably; show the options as side-by-side renders when possible.

Run the loop like this:

1. Produce the current version's required renders and measurements (the stage's mandatory tools, §5 toolkit).
2. Compare overlays, side-by-side views and the needed detail crops against the reference.
3. Record each failure with region, area, view and severity.
4. Find the cause of the most important failure.
5. Make a limited change aimed at that cause.
6. Measure and review again under the same conditions.
7. Check for regressions in areas that passed before.
8. Keep the new version if it is better; revert if it is worse.
9. Continue until every acceptance condition is met.

Do not judge progress by the total score alone. A gain in one area cannot cover a failure in another mandatory area.

Do not rebuild the whole model without checking already solved local issues. If the error comes from the base
structure, remodel within the necessary scope.

Re-evaluate the whole model after every major stage. Regional success does not replace overall success.

## 8. When progress stalls

If the same failure does not improve meaningfully for three rounds, stop repeating the same operation.

Re-examine:

- The interpretation of the reference and the source priority.
- Camera, alignment, scale and comparison conditions.
- The geometry or material approach.
- Reference sufficiency and tool limits.

Change the approach according to the cause and retry.

Respect any time, resource or round limit the user set at the start.

If the quality target cannot be reached with the available information or tools:

- Keep the best verified version.
- State clearly which criteria are not met.
- Prove the cause of the blocker.
- Ask for the smallest piece of information or decision needed to continue.

Never change the scoring method because of a low result. Never report reaching a time or round limit as success.

## 9. Overall design and joints

Keep the reference's design language. Compare size, shape and spacing relations of repeated elements. Elements of the
same kind belong to the same family everywhere: slot shape (pill / oval / rectangle), corner radius scale, chamfer
width, screw head type, rib spacing, texture type.

Do not force every part to be identical. Keep intentional differences found in the reference.

Build a visual hierarchy between big form, mid detail and small detail. Keep detail scale proportional to part scale;
small scattered patterns look weak.

Every detail should look like it has a job (a screw holds something, a hinge could turn). Colour and material changes
belong at part boundaries and logical places.

Define how parts connect (screw to surface, cover to body, lever to shaft). Remove unwanted gaps, floating parts,
intersections and coplanar overlaps. Build the visible intermediate parts in connection areas too (nut, plate, collar,
tower, gasket); one part's end must neither sink into another nor float away from it.

Keep designed openings, panel gaps, mechanical clearances and required fits.

Apply distance checks only to relevant part pairs (BVH nearest distance; `gapcheck`). Set thresholds by model scale and joint type.

Nearest distance alone does not prove a joint is correct. Use sections and close-ups from at least two angles where needed.

Flat parts (pads, frames) placed on curved surfaces float at the edges: inflate a copy of the body slightly along its
normals (Displace ~0.8 mm) and give the part an INTERSECT boolean with it.

## 10. Regression control and records

For every meaningful round record:

- Version and changed region.
- The difference being addressed.
- The change made.
- Result before and after.
- Remaining issues and where records are stored.

If the project keeps a state file (e.g. CURRENT_STATE.md), keep the short progress note there and follow the project's
note rules. Store big measurement tables and images in separate files.

Keep the best acceptable version. Do not assume the latest version is the best.

Restore temporary visibility, camera or render changes at the end of an operation. Use try/finally in scripts where suitable.

Never delete old objects just because of a name clash. Check version and collection ownership; a helper that creates
objects must not delete a same-named object outside the current version's collections, it renames it instead
(`CURRENT_ROOTS` in `rf_helpers.py`).

## 11. Delivery check

Before delivery do a final verification in all required views: a solo 360° set for the whole model and every main part (§6).

Evaluate together:

- Form, proportion, design and detail.
- Colour distribution and material appearance.
- Joints and unwanted intersections.
- Technical conditions fitting the intended use.
- If export was requested, the look and integrity of the exported file.

Check UVs, normals, texture links, scale, sockets, polygon budget and file format against the intended use.

Do not produce unrequested extra deliverables.

The final report shows:

- Comparison images from angles matching the reference, as labelled progress collages (§5).
- Per-area results and the evaluation methods.
- Unmet criteria and known defects.
- Estimated (unseen) regions.
- Delivered files.

Never say "done" or "90% target reached" unless every mandatory condition passed.

## 12. UV and materials (LookDev)

Move to materials and UVs once the form is accepted. Materials are measured against the references too (§3 colour and
material areas, §4 colour and material). Take values from reference textures and real products first; the example
palette below is only for when there is no reference or the user asks for it.

### Layered materials (Substance-style)

Never leave a material as a single colour with constant roughness. Each material carries the suitable layers of:

1. **Base:** colour, metallic, roughness range.
2. **Roughness breakup:** low-frequency noise varies roughness within a range (fingerprints, oil smears).
3. **Micro surface:** high-frequency noise bump (anodised grain, paint grain) or, on polymer, a Voronoi + noise mix for stippling.
4. **Edge wear (curvature):** dot product of the Bevel node normal and the geometry normal → sharpen → break up with
   noise. Behave per material: painted/anodised metal reveals bare metal on edges; polymer never shows metal, it gets
   slightly lighter and rougher; rail teeth and hole edges wear most.
5. **Cavity dirt (AO):** Ambient Occlusion (outside, `inside=False`) + noise → matte dirt/dust/soot in cavities and between rail teeth.
6. **Optional:** heat discoloration toward a muzzle (gradient along an object-space axis), labels/engravings, oil sheen.

Rules:

- Blender 4.1+ has no `Musgrave`; use `Noise` and `Voronoi`. Check Principled input names (`Base Color`, `Metallic`,
  `Roughness`, `Normal`) before accessing them; find nodes by type, not by name.
- Procedural scales depend on real size: object scale must be applied (`apply_scale`) and `Object` coordinates used.
  Choose scale values for the model's units (in metres, scale 300–450 gives micro texture on a 5 cm part).
- The Bevel shader node only works in Cycles; review materials in Cycles (the edge mask is empty in EEVEE). Scripts
  that switch the engine restore the old value.
- Show every mask on its own (`debug='edge'` / `'dirt'`) and check it in the 360° set: wear only on edges that would
  really wear, dirt only in cavities. Worn metal looks black in a dark environment; check the lighting before judging.
- Review lighting: 3-point studio + neutral HDRI, fixed exposure. Compare materials under the same light.
- Assign materials by part role: list all parts, write each part's material group, then assign.

Example palette (M4/AR, Substance-style; adapt to the reference):

| Material | Parts | Base | Wear | Dirt | Micro |
|---|---|---|---|---|---|
| Black anodised metal | receiver, barrel, bolt, sights | `#18191B`, metallic 0.92, roughness 0.25–0.55 | bare steel `#A8AEB5`, metallic 1, roughness 0.2 | `#12100E`, metallic 0, roughness 0.85 | noise 350, bump 0.04 |
| Bronze anodised handguard | quad rail | `#5C4838`, metallic 0.88, roughness 0.38 | light bronze `#B5A695` (rail teeth, hole edges) | dark soot (inside holes) | noise 350, bump 0.04 |
| FDE tactical polymer | stock, grip, magazine | `#8C7355`, metallic 0, roughness 0.65 | lighter colour `#A38B6D`, roughness 0.78 | fine dust (between ribs) | Voronoi 450 + noise 250, bump 0.15 |
| FDE optics/accessories | optic, laser, light | `#736654`; cage metallic 0.75, plastic body 0 | per material | cavities | fine |

`scripts/rf_lookdev.py`: `layered_pbr(name, base, metal, rough, wear, dirt, micro, stipple, heat, debug)`,
`apply_scale(objs)`, `bake_pbr(objs, out_dir, size)`, `hex2lin`.

### UV

Procedural node trees do not travel to game engines (Godot, Unity, Unreal cannot read Blender nodes); materials are
baked to textures on UVs. Plan UVs before or together with materials.

- Unwrap the final mesh with booleans and modifiers applied; re-check UVs if geometry changes later.
- Put seams on hard edges and hidden places (bottom, inside, mating faces); unwrap flat faces as one island and
  cylinders with one seam. Straighten islands horizontally/vertically.
- Keep texel density consistent and record the target (e.g. a fixed value per unit for the whole asset at 2048 px).
  Close-up parts may get more space deliberately; record the ratio.
- Symmetric/repeated parts (screws, pins, rail teeth) may share UV space, without breaking normal-map orientation.
- Island padding per texture resolution (≥ 8 px at 2K); set the bake `margin` to match.
- Decide atlas/UDIM and material count together with the technical budget (§1).
- Check: 360° render with a checker texture; no stretching, skew or visible seams.

### Bake and delivery

- Channels: BaseColor, Roughness, Metallic (plus AO / ORM pack if needed), Normal. `bake_pbr` bakes with Cycles, takes
  Metallic through a temporary Emission route, and restores the engine and links.
- Match the normal-map convention to the target engine (Blender, Godot, Unity: OpenGL Y+; Unreal: DirectX Y−).
- Hook the baked textures onto the model and compare with the procedural version under the same light; fix
  resolution, padding or UVs if they differ.
- Materials are not done until the texturing stage's mandatory comparisons (§5 toolkit 5, 6, 7) are made: every
  reference map against your map channel by channel, then both models textured side by side under the same light.

## 13. Modular parts

- Every swappable part lives in its own collection, parented to a root Empty. The root records which socket it fits.
- The main model carries socket Empties. When the main model changes (length, position), move sockets and roots together.
- Alternatives sit on the same socket, one visible. Instead of deleting an old option, keep it as a hidden alternative.

## 14. Techniques

- Booleans: the MANIFOLD solver is more robust than EXACT; if EXACT returns an empty result, switch solver. Bevel and
  WeightedNormal come after booleans.
- Cutters must not pierce unwanted faces: a cylinder drilling a slanted face through its centre also drills the
  opposite face; start the cutter at the surface. Build open revolved parts (e.g. a hollow muzzle device) with a closed
  profile revolve (`lathe_loop`) so booleans get manifold input.
- Threads, grooves and rings go into the lathe profile instead of booleans.
- Real fasteners: screw head + recess (hex / torx / phillips / slot), nut + protruding bolt end, knurled screws.
- Rotate on the mesh with `T·R·T⁻¹`; object rotation may pivot around the world origin.
- New Empty / parent: do not set the parent inverse before the world matrix is updated (`view_layer.update()`). Moving
  an object between collections can reset its visibility; hide cutters again.
- Surface patterns in materials: roughness (Voronoi bump), diamond knurling (minimum of two crossed Wave textures), rubber (metallic 0).
- Viewport ↔ render visibility: manage alternative sets with collection `hide_render` + layer `hide_viewport`.

## 15. Avoid

- Proportions from the wrong source (e.g. an old model the user is not targeting), giving a result that does not look
  like the given reference; if the proportion source is unclear, ask per §2.
- Calling it done after one angle; flat, box-like surfaces.
- Detailing the easy face and leaving bottom, back, inside and mating faces flat (taking the easy way).
- Modelling a part from whole-model images only, without a solo 360° study of the reference part.
- Details in the wrong place or on the wrong side (eyeballed placement).
- Drifting away from the features to keep while detailing.
- Gaps between parts, floating pads/frames, ends sunk into each other.
- Keeping your own invented version when the user gave a reference.
- Deleting old objects through name clashes; big operations in an unsaved scene.
- Small, scattered, out-of-proportion patterns.
- Asking "want me to fix it?" instead of fixing a found defect.
- Single-colour constant-roughness materials; wear and dirt spread evenly everywhere; bare-metal wear on polymer.
- Delivering a game asset with procedural materials and no UVs.

## Helper scripts

`scripts/` — Blender scripts are loaded as text blocks and run with `exec(bpy.data.texts['…'].as_string())`
(load `rf_helpers.py` first; `rf_trace.py` depends on it). Set `OUT` (or the `RF_OUT` environment variable) to the
session's temp folder. `rf_collage.py` runs outside Blender.

| Script | Contents |
|---|---|
| `rf_helpers.py` | `profile`, `topview`, `box`, `lathe` / `lathe_loop`, `loft`, `loft_path`, `sweep`, `sell` / `rrect` sections, `bevel`, `boolcut`, `chamfer`, `make_rail`, `screw` / `nut` / `thumbnut`, `swapdata`, `setmat`, `bounds`; `AXIS_CENTER`, `CURRENT_ROOTS` |
| `rf_trace.py` | `refverts`, `trace` (reference slices), `loft_trace` (loft through slices) |
| `rf_silhouette.py` | `silcheck` (IoU + difference image), `profile_of`, `outline`, `relief` / `relief_png`, `collection_meshes` |
| `rf_blueprint.py` | `refmat` (material from a PBR texture set), `mkcam`, `render_with`, `overlay`, `region_bp`, `region_cmp` |
| `rf_gapcheck.py` | `gapcheck(objs, threshold)`: nearest distance between parts that should touch |
| `rf_lookdev.py` | `layered_pbr` (base + breakup + micro/stipple + edge wear + cavity dirt + heat, `debug` masks), `apply_scale`, `bake_pbr`, `hex2lin` |
| `rf_collage.py` | Progress collage: reference / ours / difference columns, view rows, short labels (Pillow, outside Blender) |

Defaults: +Y forward, +Z up, metres. Name prefixes and collection names are examples; adapt them to the project.
