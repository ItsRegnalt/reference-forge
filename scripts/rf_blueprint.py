"""reference-forge: textured orthographic blueprints of a reference and render overlays of your model.

Workflow: region_bp() renders the reference from 4+ orthographic directions; region_cmp() renders your model from
the same cameras and draws its edges (magenta) over the blueprint. Images go to OUT (or RF_OUT env var).
Every render function restores camera, engine, resolution and visibility afterwards.
"""
import bpy, os, math, numpy as np
from mathutils import Vector

OUT = os.environ.get('RF_OUT') or bpy.app.tempdir
TMP_COLLECTION = 'TMP_View'
# camera rotations (degrees) per direction tag; +Y forward, +Z up
CAMROT = {'R': (90, 0, 90), 'L': (90, 0, -90), 'T': (0, 0, 90), 'B': (180, 0, 90), 'F': (90, 0, 180), 'K': (90, 0, 0)}
CAMOFF = {'R': (1, 0, 0), 'L': (-1, 0, 0), 'T': (0, 0, 1), 'B': (0, 0, -1), 'F': (0, 1, 0), 'K': (0, -1, 0)}


def _tmp_collection():
    c = bpy.data.collections.get(TMP_COLLECTION)
    if not c:
        c = bpy.data.collections.new(TMP_COLLECTION); bpy.context.scene.collection.children.link(c)
    return c


def _key_light():
    l = bpy.data.objects.get('RF_KeyLight')
    if not l:
        l = bpy.data.objects.new('RF_KeyLight', bpy.data.lights.new('RF_KeyLight', 'SUN'))
        l.data.energy = 4.0; _tmp_collection().objects.link(l)
    return l


def refmat(name, folder, prefix, base='_BaseColor.png', ao='_AO.png', metal='_Metallic.png',
           rough='_Roughness.png', normal='_Normal_DirectX.png', directx=True):
    """Material from a reference's PBR texture set (missing maps are skipped). DirectX normals get green flipped."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bs.outputs[0], out.inputs[0])

    def tex(suf, noncolor):
        p = os.path.join(folder, prefix + suf)
        if not suf or not os.path.exists(p): return None
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(p, check_existing=True)
        if noncolor: n.image.colorspace_settings.name = 'Non-Color'
        return n
    bc, a = tex(base, False), tex(ao, True)
    if bc and a:
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1
        nt.links.new(bc.outputs[0], mix.inputs[6]); nt.links.new(a.outputs[0], mix.inputs[7]); nt.links.new(mix.outputs[2], bs.inputs['Base Color'])
    elif bc:
        nt.links.new(bc.outputs[0], bs.inputs['Base Color'])
    for suf, inp in ((metal, 'Metallic'), (rough, 'Roughness')):
        t = tex(suf, True)
        if t: nt.links.new(t.outputs[0], bs.inputs[inp])
    nm = tex(normal, True)
    if nm:
        nmap = nt.nodes.new('ShaderNodeNormalMap')
        if directx:
            sep = nt.nodes.new('ShaderNodeSeparateColor'); inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'
            inv.inputs[0].default_value = 1; com = nt.nodes.new('ShaderNodeCombineColor')
            nt.links.new(nm.outputs[0], sep.inputs[0]); nt.links.new(sep.outputs[0], com.inputs[0])
            nt.links.new(sep.outputs[1], inv.inputs[1]); nt.links.new(inv.outputs[0], com.inputs[1]); nt.links.new(sep.outputs[2], com.inputs[2])
            nt.links.new(com.outputs[0], nmap.inputs['Color'])
        else:
            nt.links.new(nm.outputs[0], nmap.inputs['Color'])
        nt.links.new(nmap.outputs[0], bs.inputs['Normal'])
    return m


def mkcam(region, tag, center, width):
    """Orthographic camera CAM_<region>_<tag> looking at `center`; tag in R L T B F K (right, left, top, bottom, front, back)."""
    n = f'CAM_{region}_{tag}'; c = bpy.data.objects.get(n)
    if not c:
        c = bpy.data.objects.new(n, bpy.data.cameras.new(n)); _tmp_collection().objects.link(c)
    off = CAMOFF[tag]
    c.data.type = 'ORTHO'; c.data.ortho_scale = width; c.data.clip_start = 0.01; c.data.clip_end = 5
    c.location = (center[0] + off[0], center[1] + off[1], center[2] + off[2])
    c.rotation_euler = tuple(math.radians(a) for a in CAMROT[tag]); return c


def render_with(objs, cam, path, res=(2400, 1600)):
    """Render only `objs` through `cam` with a key light from the camera side; transparent background."""
    sc = bpy.context.scene; r = sc.render
    saved = (sc.camera, r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.film_transparent, r.filepath)
    hid = {o.name: o.hide_render for o in bpy.data.objects}; colh = {c.name: c.hide_render for c in bpy.data.collections}
    l = _key_light(); old = l.rotation_euler.copy()
    try:
        keep = {o.name for o in objs}
        for o in bpy.data.objects:
            if o.type in ('MESH', 'CURVE'): o.hide_render = o.name not in keep
        for c in bpy.data.collections: c.hide_render = False
        for e in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
            try: r.engine = e; break
            except TypeError: pass
        r.resolution_x, r.resolution_y = res; r.resolution_percentage = 100; r.film_transparent = True
        d = cam.matrix_world.to_3x3() @ Vector((0, 0, 1))
        l.hide_render = False; l.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        l.rotation_euler.x += math.radians(25); l.rotation_euler.z += math.radians(20)
        sc.camera = cam; r.filepath = path; bpy.ops.render.render(write_still=True)
    finally:
        l.rotation_euler = old; l.hide_render = True
        for n, v in hid.items():
            if n in bpy.data.objects: bpy.data.objects[n].hide_render = v
        for n, v in colh.items():
            if n in bpy.data.collections: bpy.data.collections[n].hide_render = v
        sc.camera, r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.film_transparent, r.filepath = saved
    return path


def _load(path):
    im = bpy.data.images.load(path, check_existing=False)
    a = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4); bpy.data.images.remove(im); return a


def overlay(bp_path, mine_path, out_path, crop=None):
    """Blueprint darkened, with the model render's edges drawn in magenta on top."""
    A, M = _load(bp_path), _load(mine_path)
    over = lambda x: x[..., :3] * x[..., 3:4]
    C = over(A) * 0.85; mine = over(M)
    g = mine.mean(2) * 0.5 + M[..., 3] * 0.5
    e = np.abs(np.diff(g, axis=0, prepend=g[:1])) + np.abs(np.diff(g, axis=1, prepend=g[:, :1]))
    C[e > 0.05] = np.array([1.0, 0.1, 0.9])
    if crop: y0, y1, x0, x1 = crop; C = C[y0:y1, x0:x1]
    h, w = C.shape[:2]; im = bpy.data.images.new('rf_overlay', w, h)
    im.pixels[:] = np.concatenate([C, np.ones((h, w, 1), np.float32)], 2).ravel()
    im.filepath_raw = out_path; im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
    return out_path


def region_bp(region, refnames, center, width, tags=('R', 'L', 'T', 'B')):
    """Blueprints of the reference objects for one region: {tag: png}."""
    return {t: render_with([bpy.data.objects[n] for n in refnames], mkcam(region, t, center, width),
                           os.path.join(OUT, f'bp_{region}_{t}.png')) for t in tags}


def region_cmp(region, model_objs, version, tags=('R', 'L', 'T', 'B')):
    """Render your model with region_bp()'s cameras and overlay it: [overlay png per tag]."""
    out = []
    for t in tags:
        mp = render_with(model_objs, bpy.data.objects[f'CAM_{region}_{t}'], os.path.join(OUT, f'mine_{region}_{version}_{t}.png'))
        out.append(overlay(os.path.join(OUT, f'bp_{region}_{t}.png'), mp, os.path.join(OUT, f'ovl_{region}_{version}_{t}.png')))
    return out
