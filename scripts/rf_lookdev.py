
"""reference-forge: layered procedural PBR (Substance-style) and baking.

Layers: Base + Roughness Breakup + Micro Bump / Stipple + Edge Wear + Cavity Dirt (+ optional Heat).
Blender 4.1+ / 5.x. Visual debugging: layered_pbr(..., debug='edge' | 'dirt') shows a mask on its own.
The Bevel shader node only works in Cycles (the edge mask is empty in EEVEE): review materials in Cycles.
Game engines cannot read Blender node trees: bake to textures on UVs with bake_pbr().
"""
import bpy, math

def hex2lin(h):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)

def _inp(node, *names):
    for n in names:
        if n in node.inputs: return node.inputs[n]
    raise KeyError(f'{node.bl_idname}: {names} not found; available: {[i.name for i in node.inputs]}')

def _out(node, *names):
    for n in names:
        if n in node.outputs: return node.outputs[n]
    raise KeyError(f'{node.bl_idname}: {names} not found; available: {[o.name for o in node.outputs]}')

def _mix_rgb(nt, a, b, fac, blend='MIX'):
    m = nt.nodes.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = blend
    nt.links.new(fac, m.inputs[0])
    for sock, val in ((m.inputs[6], a), (m.inputs[7], b)):
        if isinstance(val, tuple): sock.default_value = val
        else: nt.links.new(val, sock)
    return m.outputs[2]

def _mix_f(nt, a, b, fac):
    m = nt.nodes.new('ShaderNodeMix'); m.data_type = 'FLOAT'
    nt.links.new(fac, m.inputs[0])
    for sock, val in ((m.inputs[2], a), (m.inputs[3], b)):
        if isinstance(val, (int, float)): sock.default_value = val
        else: nt.links.new(val, sock)
    return m.outputs[0]

def _ramp(nt, src, p0, p1, c0=(0, 0, 0, 1), c1=(1, 1, 1, 1)):
    r = nt.nodes.new('ShaderNodeValToRGB')
    r.color_ramp.elements[0].position = p0; r.color_ramp.elements[0].color = c0
    r.color_ramp.elements[1].position = p1; r.color_ramp.elements[1].color = c1
    nt.links.new(src, r.inputs['Fac']); return r.outputs['Color']

def _noise(nt, vec, scale, detail=6.0, rough=0.6):
    n = nt.nodes.new('ShaderNodeTexNoise')
    _inp(n, 'Scale').default_value = scale; _inp(n, 'Detail').default_value = detail
    _inp(n, 'Roughness').default_value = rough
    nt.links.new(vec, _inp(n, 'Vector')); return _out(n, 'Fac')

def layered_pbr(name, base, metal, rough=(0.35, 0.50),
                wear=None, dirt=None, micro=None, stipple=None, heat=None,
                breakup_scale=12.0, coord_scale=1.0, debug=None):
    """
    base   : '#RRGGBB' (sRGB) or linear (r, g, b, a)
    metal  : 0..1 ; rough = (min, max) breakup range
    wear   : dict(color, metal, rough, radius=0.003, lo=0.55, hi=0.75, noise=45)   edge wear
    dirt   : dict(color, metal=0, rough=0.85, distance=0.02, lo=0.35, hi=0.75)    cavity dirt (AO)
    micro  : dict(scale=350, strength=0.04, distance=0.001)                         micro grain bump
    stipple: dict(voronoi=450, noise=250, strength=0.15, distance=0.002)           polymer stippling bump
    heat   : dict(axis='Y', start=0.5, end=0.6, color='#2a2420', rough=0.7)        heat discoloration along an
                                                                                    object-space axis
    """
    col = lambda c: hex2lin(c) if isinstance(c, str) else c
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); P = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(P.outputs[0], out.inputs['Surface'])
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    _inp(mp, 'Scale').default_value = (coord_scale,) * 3
    nt.links.new(_out(tc, 'Object'), _inp(mp, 'Vector')); V = mp.outputs[0]

    # base + roughness breakup
    bcol = col(base)
    br = _noise(nt, V, breakup_scale, 8.0, 0.65)
    rmap = nt.nodes.new('ShaderNodeMapRange'); nt.links.new(br, _inp(rmap, 'Value'))
    _inp(rmap, 'To Min').default_value = rough[0]; _inp(rmap, 'To Max').default_value = rough[1]
    C = bcol; M = float(metal); Rg = _out(rmap, 'Result')

    edge = None
    if wear:
        bev = nt.nodes.new('ShaderNodeBevel'); bev.samples = wear.get('samples', 4)
        _inp(bev, 'Radius').default_value = wear.get('radius', 0.003)
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
        nt.links.new(_out(bev, 'Normal'), dot.inputs[0]); nt.links.new(_out(geo, 'Normal'), dot.inputs[1])
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        nt.links.new(_out(dot, 'Value'), inv.inputs[1])
        amp = nt.nodes.new('ShaderNodeMath'); amp.operation = 'MULTIPLY'; amp.inputs[1].default_value = 25.0
        nt.links.new(inv.outputs[0], amp.inputs[0])
        nz = _noise(nt, V, wear.get('noise', 45.0), 10.0, 0.6)
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        nt.links.new(amp.outputs[0], mul.inputs[0]); nt.links.new(nz, mul.inputs[1])
        e = _ramp(nt, mul.outputs[0], wear.get('lo', 0.55), wear.get('hi', 0.75))
        edge = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(e, edge.inputs[0]); edge = edge.outputs[0]
        C = _mix_rgb(nt, C, col(wear['color']), edge)
        M = _mix_f(nt, M, wear.get('metal', 1.0), edge)
        Rg = _mix_f(nt, Rg, wear.get('rough', 0.2), edge)

    cav = None
    if dirt:
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.inside = False; ao.samples = dirt.get('samples', 16)
        _inp(ao, 'Distance').default_value = dirt.get('distance', 0.02)
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        nt.links.new(_out(ao, 'AO'), inv.inputs[1])
        nz = _noise(nt, V, dirt.get('noise', 30.0), 6.0, 0.6)
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        nt.links.new(inv.outputs[0], mul.inputs[0]); nt.links.new(nz, mul.inputs[1])
        c = _ramp(nt, mul.outputs[0], dirt.get('lo', 0.35) * 0.5, dirt.get('hi', 0.75) * 0.5)
        cav = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(c, cav.inputs[0]); cav = cav.outputs[0]
        C = _mix_rgb(nt, C, col(dirt['color']), cav)
        M = _mix_f(nt, M, dirt.get('metal', 0.0), cav)
        Rg = _mix_f(nt, Rg, dirt.get('rough', 0.85), cav)

    if heat:
        sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(_out(tc, 'Object'), sep.inputs[0])
        hr = nt.nodes.new('ShaderNodeMapRange'); nt.links.new(sep.outputs['XYZ'.index(heat.get('axis', 'Y'))], _inp(hr, 'Value'))
        _inp(hr, 'From Min').default_value = heat['start']; _inp(hr, 'From Max').default_value = heat['end']
        hf = _out(hr, 'Result')
        C = _mix_rgb(nt, C, col(heat['color']), hf)
        Rg = _mix_f(nt, Rg, heat.get('rough', 0.7), hf)

    # normal: micro grain and/or stipple, chained bumps
    nrm = None
    for spec, kind in ((stipple, 'stipple'), (micro, 'micro')):
        if not spec: continue
        if kind == 'stipple':
            vo = nt.nodes.new('ShaderNodeTexVoronoi'); _inp(vo, 'Scale').default_value = spec.get('voronoi', 450)
            nt.links.new(V, _inp(vo, 'Vector'))
            half = nt.nodes.new('ShaderNodeValue'); half.outputs[0].default_value = 0.5
            h = _mix_f(nt, _out(vo, 'Distance'), _noise(nt, V, spec.get('noise', 250), 4.0, 0.6), half.outputs[0])
        else:
            h = _noise(nt, V, spec.get('scale', 350), 12.0, 0.6)
        b = nt.nodes.new('ShaderNodeBump')
        _inp(b, 'Strength').default_value = spec.get('strength', 0.05); _inp(b, 'Distance').default_value = spec.get('distance', 0.001)
        nt.links.new(h, _inp(b, 'Height'))
        if nrm is not None: nt.links.new(nrm, _inp(b, 'Normal'))
        nrm = _out(b, 'Normal')

    def _set(sock, v):
        if isinstance(v, (int, float, tuple)): sock.default_value = v
        else: nt.links.new(v, sock)
    if debug in ('edge', 'dirt'):
        mask = edge if debug == 'edge' else cav
        _set(_inp(P, 'Base Color'), (0, 0, 0, 1) if mask is None else _mix_rgb(nt, (0, 0, 0, 1), (1, 1, 1, 1), mask))
        _set(_inp(P, 'Metallic'), 0.0); _set(_inp(P, 'Roughness'), 0.8)
    else:
        _set(_inp(P, 'Base Color'), C); _set(_inp(P, 'Metallic'), M); _set(_inp(P, 'Roughness'), Rg)
    if nrm is not None: nt.links.new(nrm, _inp(P, 'Normal'))
    m.diffuse_color = bcol; m.metallic = float(metal); m.roughness = sum(rough) / 2
    return m

def apply_scale(objs):
    """Apply object scale into the mesh so procedural scales stay true. Children keep their world transform;
    meshes shared with other objects are skipped and returned."""
    from mathutils import Matrix
    skipped = []
    for o in objs:
        if o.type != 'MESH' or all(abs(s - 1.0) < 1e-6 for s in o.scale): continue
        if o.data.users > 1: skipped.append(o.name); continue
        kids = {c: c.matrix_world.copy() for c in o.children}
        o.data.transform(Matrix.Diagonal((*o.scale, 1.0))); o.data.update()
        o.scale = (1.0, 1.0, 1.0)
        bpy.context.view_layer.update()
        for c, mw in kids.items(): c.matrix_world = mw
    return skipped

def _metal_to_emit(mat):
    """Temporarily route the Metallic input into an Emission shader (for an EMIT bake). Returns an undo function."""
    nt = mat.node_tree
    P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    surf = out.inputs['Surface']; orig = surf.links[0].from_socket if surf.links else None
    em = nt.nodes.new('ShaderNodeEmission'); mi = _inp(P, 'Metallic')
    if mi.links: nt.links.new(mi.links[0].from_socket, em.inputs['Color'])
    else: em.inputs['Color'].default_value = (mi.default_value,) * 3 + (1.0,)
    nt.links.new(em.outputs[0], surf)
    def undo():
        if orig is not None: nt.links.new(orig, surf)
        nt.nodes.remove(em)
    return undo

def bake_pbr(objs, out_dir, size=2048, margin=16):
    """Bake BaseColor / Roughness / Metallic (via Emission) / Normal (OpenGL) with Cycles. Every object needs UVs.
    Output: <out_dir>/<object>_<channel>.png. Render engine and material links are restored afterwards."""
    import os
    sc = bpy.context.scene; old = sc.render.engine
    try:
        sc.render.engine = 'CYCLES'
        for o in objs:
            if not o.data.uv_layers: raise RuntimeError(f'{o.name}: no UV map')
            for ch, btype in (('BaseColor', 'DIFFUSE'), ('Roughness', 'ROUGHNESS'), ('Metallic', 'EMIT'), ('Normal', 'NORMAL')):
                img = bpy.data.images.new(f'{o.name}_{ch}', size, size, alpha=False,
                                          float_buffer=(ch == 'Normal'))
                if ch != 'BaseColor': img.colorspace_settings.name = 'Non-Color'
                for slot in o.material_slots:
                    nt = slot.material.node_tree
                    n = nt.nodes.get('_bake_target') or nt.nodes.new('ShaderNodeTexImage'); n.name = '_bake_target'
                    n.image = img; nt.nodes.active = n
                bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
                kw = dict(type=btype, margin=margin)
                if btype == 'DIFFUSE': kw['pass_filter'] = {'COLOR'}
                undos = [_metal_to_emit(s.material) for s in o.material_slots] if btype == 'EMIT' else []
                try:
                    bpy.ops.object.bake(**kw)
                finally:
                    for u in undos: u()
                img.filepath_raw = os.path.join(out_dir, f'{o.name}_{ch}.png'); img.file_format = 'PNG'; img.save()
    finally:
        sc.render.engine = old
        for o in objs:
            for s in o.material_slots:
                n = s.material.node_tree.nodes.get('_bake_target') if s.material else None
                if n: s.material.node_tree.nodes.remove(n)
