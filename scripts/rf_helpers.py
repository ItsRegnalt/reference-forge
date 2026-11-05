"""reference-forge: geometry helpers for Blender (bpy / bmesh).

Load inside Blender as a text block and exec it:
    exec(bpy.data.texts['rf_helpers.py'].as_string())

Conventions: +Y forward, +Z up, metres. Section functions return 2D point lists (x, z) in counter-clockwise order.
Every builder takes a collection name `col` (None = scene collection) and a material name `mat` (None = no material).
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

# Default revolve centre for lathe(): (x, y, z). Set to your model's main axis (e.g. bore height).
AXIS_CENTER = (0.0, 0.0, 0.0)
# Collections that hold the CURRENT version. An existing object with the same name inside them is replaced;
# anywhere else it is kept and renamed "<name>_old" so earlier work is never lost by a name clash.
CURRENT_ROOTS = []


def _in_current(o):
    for r in CURRENT_ROOTS:
        c = bpy.data.collections.get(r)
        if c and o.name in c.all_objects:
            return True
    return False


def _free(name):
    old = bpy.data.objects.get(name)
    if not old:
        return
    if _in_current(old):
        bpy.data.objects.remove(old, do_unlink=True)
    else:
        old.name = name + '_old'


def _col(col):
    return bpy.context.scene.collection if col is None else bpy.data.collections[col]


def _mk(name, bm, col, mat, smooth=True):
    _free(name)
    me = bpy.data.meshes.new(name); bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); _col(col).objects.link(o)
    if mat:
        o.data.materials.append(bpy.data.materials[mat])
    for p in me.polygons:
        p.use_smooth = smooth
    return o


def fix(bm):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


# ---------------------------------------------------------------- primitives

def profile(name, pts, x0, x1, col=None, mat=None):
    """Side-view polygon [(y, z)] extruded along X from x0 to x1."""
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x0, y, z)) for y, z in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(x1 - x0, 0, 0))
    fix(bm); return _mk(name, bm, col, mat)


def topview(name, pts, z0, z1, col=None, mat=None):
    """Top-view polygon [(x, y)] extruded along Z from z0 to z1."""
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, z0)) for x, y in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(0, 0, z1 - z0))
    fix(bm); return _mk(name, bm, col, mat)


def box(name, c, s, col=None, mat=None):
    """Axis-aligned box: centre c, size s."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=s, verts=bm.verts); bmesh.ops.translate(bm, vec=c, verts=bm.verts)
    return _mk(name, bm, col, mat)


def _ring_point(c, axis, t, u, v):
    if axis == 'Y': return (c[0] + u, c[1] + t, c[2] + v)
    if axis == 'X': return (c[0] + t, c[1] + u, c[2] + v)
    return (c[0] + u, c[1] + v, c[2] + t)


def lathe(name, prof, col=None, mat=None, n=16, axis='Y', c=None, cap=True, rot0=None):
    """Open profile [(t, r)] revolved around `axis` through centre c. r = 0 points close the ends."""
    c = AXIS_CENTER if c is None else c
    bm = bmesh.new(); rings = []
    a0 = math.pi / n if rot0 is None else rot0
    for t, r in prof:
        rings.append([bm.verts.new(_ring_point(c, axis, t, r * math.cos(a0 + 2 * math.pi * i / n),
                                               r * math.sin(a0 + 2 * math.pi * i / n))) for i in range(n)])
    for A, B in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            if (A[i].co - A[j].co).length < 1e-7 and (B[i].co - B[j].co).length < 1e-7:
                continue
            bm.faces.new((A[i], A[j], B[j], B[i]))
    if cap:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    fix(bm); return _mk(name, bm, col, mat)


def lathe_loop(name, prof, col=None, mat=None, n=32, axis='Y', c=None):
    """Closed profile loop [(t, r)] revolved: tubes, rings, hollow muzzle parts. Gives manifold input for booleans."""
    c = AXIS_CENTER if c is None else c
    bm = bmesh.new(); rings = []
    for t, r in prof:
        rings.append([bm.verts.new(_ring_point(c, axis, t, r * math.cos(math.pi / n + 2 * math.pi * i / n),
                                               r * math.sin(math.pi / n + 2 * math.pi * i / n))) for i in range(n)])
    m = len(rings)
    for k in range(m):
        A, B = rings[k], rings[(k + 1) % m]
        for i in range(n):
            j = (i + 1) % n; bm.faces.new((A[i], A[j], B[j], B[i]))
    fix(bm); return _mk(name, bm, col, mat)


def loft(name, secs, col=None, mat=None, cap=True):
    """secs [(y, [(x, z), ...])], equal point counts: cross-sections placed along Y."""
    bm = bmesh.new(); rings = [[bm.verts.new((x, y, z)) for x, z in s] for y, s in secs]
    n = len(rings[0])
    for A, B in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n; bm.faces.new((A[i], A[j], B[j], B[i]))
    if cap:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    fix(bm); return _mk(name, bm, col, mat)


def loft_path(name, frames, col=None, mat=None, cap=True):
    """frames [(origin, tangent, side, up, [(u, v)...])]: section u along `side`, v along `up` (curved parts)."""
    bm = bmesh.new()
    rings = [[bm.verts.new(o + sd * u + upv * v) for u, v in sec] for o, _, sd, upv, sec in frames]
    n = len(rings[0])
    for A, B in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n; bm.faces.new((A[i], A[j], B[j], B[i]))
    if cap:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    fix(bm); return _mk(name, bm, col, mat)


# ---------------------------------------------------------------- sections

def sell(hw, hh, n=24, e=2.5, cx=0.0, cz=0.0):
    """Superellipse section (half width hw, half height hh, exponent e: 2 = ellipse, higher = squarer)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + math.pi / n; co, si = math.cos(a), math.sin(a)
        pts.append((cx + hw * math.copysign(abs(co) ** (2 / e), co), cz + hh * math.copysign(abs(si) ** (2 / e), si)))
    return pts


def rrect(hw, hh, r, cx=0.0, cz=0.0, seg=4):
    """Rounded rectangle section, `seg` segments per corner."""
    pts = []
    for sx, sz, a0 in ((1, -1, -90), (1, 1, 0), (-1, 1, 90), (-1, -1, 180)):
        ox, oz = cx + sx * (hw - r), cz + sz * (hh - r)
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg); pts.append((ox + r * math.cos(a), oz + r * math.sin(a)))
    return pts


def catmull(P, per=6):
    """Resample a 2D path [(y, z)] with Catmull-Rom; returns Vectors in the YZ plane."""
    P = [Vector((0, y, z)) for y, z in P]; out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(per):
            t = k / per; t2 = t * t; t3 = t2 * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1]); return out


def sweep(name, P, sec, col=None, mat=None, per=6, offx=0.0):
    """Sweep a section (list, or callable u -> list) along a smooth YZ path (cables, guards, wires)."""
    pts = catmull(P, per); side = Vector((1, 0, 0)); fr = []
    for i, p in enumerate(pts):
        a = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        s = sec(i / (len(pts) - 1)) if callable(sec) else sec
        fr.append((p + Vector((offx, 0, 0)), a, side, Vector((0, -a.z, a.y)), s))
    o = loft_path(name, fr, col, mat); smooth_ang(o); return o


# ---------------------------------------------------------------- modifiers and edits

def bevel(o, w=0.0012, seg=1, ang=35, harden=True, limit='ANGLE'):
    m = o.modifiers.new('Bevel', 'BEVEL'); m.width = w; m.segments = seg; m.limit_method = limit
    m.angle_limit = math.radians(ang); m.harden_normals = harden; m.use_clamp_overlap = True
    if not any(x.type == 'WEIGHTED_NORMAL' for x in o.modifiers):
        o.modifiers.new('WN', 'WEIGHTED_NORMAL').keep_sharp = True
    return m


def smooth_ang(o, deg=35):
    for p in o.data.polygons:
        p.use_smooth = True
    if not any(x.type == 'WEIGHTED_NORMAL' for x in o.modifiers):
        o.modifiers.new('WN', 'WEIGHTED_NORMAL').keep_sharp = True


def boolcut(o, cutter, mode='DIFFERENCE', solver='MANIFOLD'):
    """Boolean with `cutter` (parented to `o`, hidden in render). Bevel / WeightedNormal stay last in the stack.
    MANIFOLD is more robust than EXACT; switch solver if a result comes back empty."""
    cutter.display_type = 'WIRE'; cutter.hide_render = True
    cutter.parent = o; cutter.matrix_parent_inverse = o.matrix_world.inverted()
    m = o.modifiers.new('Bool_' + cutter.name, 'BOOLEAN'); m.object = cutter; m.operation = mode
    try:
        m.solver = solver
    except TypeError:
        m.solver = 'EXACT'
    for mod in [x for x in o.modifiers if x.type in ('BEVEL', 'WEIGHTED_NORMAL')]:
        o.modifiers.move(list(o.modifiers).index(mod), len(o.modifiers) - 1)
    return m


def chamfer(o, pred, off, seg=1):
    """Bevel the mesh edges whose two vertex coordinates satisfy pred(a, b)."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    es = [e for e in bm.edges if pred(e.verts[0].co, e.verts[1].co)]
    if es:
        bmesh.ops.bevel(bm, geom=es, offset=off, segments=seg, affect='EDGES', profile=0.5)
    bm.to_mesh(o.data); bm.free(); o.data.update(); return len(es)


def near(a, b, t=1e-4):
    return abs(a - b) < t


def swapdata(o, tmp):
    """Replace o's mesh with tmp's mesh, keeping o's modifiers, parent and children. Deletes tmp."""
    old = o.data; o.data = tmp.data; bpy.data.objects.remove(tmp); bpy.data.meshes.remove(old)


def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(bpy.data.materials[m])


def bounds(o):
    """World bounding box of the evaluated mesh: ([min], [max], face_count)."""
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    vs = [e.matrix_world @ v.co for v in m.vertices]
    r = ([round(min(v[i] for v in vs), 4) for i in range(3)], [round(max(v[i] for v in vs), 4) for i in range(3)], len(m.polygons))
    e.to_mesh_clear(); return r


# ---------------------------------------------------------------- rails

# Picatinny-style rail cross-section (u across, v outward), metres.
RAIL_SEC = [(-0.0075, 0), (0.0075, 0), (0.0075, 0.0018), (0.0105, 0.0042), (0.0105, 0.0058), (0.0090, 0.0075),
            (-0.0090, 0.0075), (-0.0105, 0.0058), (-0.0105, 0.0042), (-0.0075, 0.0018)]


def make_rail(name, y0, y1, col=None, base_off=0.0, place=None, pitch=0.010, mat=None):
    """Rail along Y with recoil slots cut by an arrayed cutter (applied). `place`: Matrix moving it into position."""
    secs = [(y0, [(u, v + base_off) for u, v in RAIL_SEC]), (y1, [(u, v + base_off) for u, v in RAIL_SEC])]
    r = loft(name, secs, col, mat)
    c = box(name + '_CUTTER', (0, y0 + 0.002 + pitch / 2, base_off + 0.0075), (0.03, 0.0052, 0.0062), col, mat)
    a = c.modifiers.new('Array', 'ARRAY'); a.use_relative_offset = False; a.use_constant_offset = True
    a.constant_offset_displace = (0, pitch, 0); a.count = int((y1 - y0 - 0.004) / pitch)
    m = r.modifiers.new('Slots', 'BOOLEAN'); m.object = c; m.operation = 'DIFFERENCE'
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(r.evaluated_get(dg), depsgraph=dg)
    r.modifiers.clear(); old = r.data; r.data = me; bpy.data.meshes.remove(old)
    bpy.data.objects.remove(c, do_unlink=True)
    if place is not None:
        r.data.transform(place); r.data.update()
    bevel(r, 0.0004, 1, 40)
    return r


# ---------------------------------------------------------------- fasteners

def _axis_mesh(o, axis, sgn, center):
    """Fastener built along +X at the origin: rotate to axis/sign and move to `center`."""
    rot = {'X': Matrix.Identity(4), 'Y': Matrix.Rotation(math.pi / 2, 4, 'Z'), 'Z': Matrix.Rotation(-math.pi / 2, 4, 'Y')}[axis]
    if sgn < 0:
        rot = rot @ Matrix.Rotation(math.pi, 4, 'Z')
    o.data.transform(Matrix.Translation(center) @ rot); o.data.update()


def screw(name, center, axis='X', sgn=1, r=0.0026, h=0.0016, drive='hex', col=None, mat=None, head='cap'):
    """Screw head sitting on a surface at `center`, facing +axis*sgn.
    head: 'cap' | 'button' | 'flat'. drive: 'hex' | 'torx' | 'slot' | 'phillips'."""
    if head == 'cap': prof = [(0, 0), (0, r), (h * 0.75, r), (h, r * 0.82), (h, 0)]
    elif head == 'button': prof = [(0, 0), (0, r)] + [(h * math.sin(math.radians(x)), r * math.cos(math.radians(x))) for x in (20, 40, 60, 75)] + [(h, 0)]
    else: prof = [(0, 0), (0, r), (h * 0.4, r * 0.7), (h * 0.5, 0)]
    o = lathe(name, prof, col, mat, n=24, axis='X', c=(0, 0, 0))
    extra = []
    if drive in ('hex', 'torx'):
        k = 0.42 if drive == 'hex' else 0.40
        cut = lathe(name + '_DRV', [(h - 0.0011, 0), (h - 0.0011, r * k), (h + 0.001, r * k), (h + 0.001, 0)], col, mat, n=6, axis='X', c=(0, 0, 0), rot0=0)
    else:
        cut = box(name + '_DRV', (h, 0, 0), (0.0016, r * 2.4, r * 0.32), col, mat)
        if drive == 'phillips':
            c2 = box(name + '_DRV2', (h, 0, 0), (0.0016, r * 0.32, r * 2.4), col, mat); extra.append(c2)
            j = cut.modifiers.new('U', 'BOOLEAN'); j.object = c2; j.operation = 'UNION'
    m = o.modifiers.new('Drive', 'BOOLEAN'); m.object = cut
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    o.modifiers.clear(); old = o.data; o.data = me; bpy.data.meshes.remove(old)
    for x in [cut] + extra:
        bpy.data.objects.remove(x)
    _axis_mesh(o, axis, sgn, center)
    if mat: setmat(o, mat)
    for p in o.data.polygons:
        p.use_smooth = True
    bevel(o, 0.00015, 1, 40); return o


def nut(name, center, axis='X', sgn=1, s=0.0058, h=0.0026, col=None, mat=None, bolt_r=0.0016):
    """Hex nut (across flats s) with the bolt end poking out."""
    R = s / 2 / math.cos(math.pi / 6)
    o = lathe(name, [(0, 0), (0, R), (h * 0.8, R), (h, R * 0.86), (h, 0)], col, mat, n=6, axis='X', c=(0, 0, 0), rot0=0)
    e = lathe(name + '_End', [(h - 0.0005, 0), (h - 0.0005, bolt_r), (h + 0.0009, bolt_r), (h + 0.0012, bolt_r * 0.7), (h + 0.0012, 0)], col, mat, n=16, axis='X', c=(0, 0, 0))
    for x in (o, e):
        _axis_mesh(x, axis, sgn, center)
    bevel(o, 0.0002, 1, 30); return o


def thumbnut(name, center, axis='X', sgn=1, r=0.0048, h=0.0040, col=None, mat=None, knurl=18):
    """Knurled thumb nut / knob."""
    prof = [(0, 0), (0, r * 0.7), (0.0006, r), (h - 0.0006, r), (h, r * 0.8), (h, 0)]
    o = lathe(name, prof, col, mat, n=knurl * 2, axis='X', c=(0, 0, 0))
    for v in o.data.vertices:
        if abs((v.co.y ** 2 + v.co.z ** 2) ** 0.5 - r) < 1e-5:
            k = round((math.atan2(v.co.z, v.co.y) - math.pi / (knurl * 2)) / (math.pi / knurl))
            if k % 2:
                v.co.y *= 0.9; v.co.z *= 0.9
    _axis_mesh(o, axis, sgn, center)
    for p in o.data.polygons:
        p.use_smooth = True
    bevel(o, 0.0002, 1, 40); return o
