"""reference-forge: gaps between parts that should touch (BVH nearest distance)."""
import bpy, itertools
from mathutils.bvhtree import BVHTree


def _bvh(o, dg):
    e = o.evaluated_get(dg); m = e.to_mesh()
    verts = [e.matrix_world @ v.co for v in m.vertices]; polys = [p.vertices[:] for p in m.polygons]
    e.to_mesh_clear()
    return (BVHTree.FromPolygons(verts, polys) if polys else None), verts


def gapcheck(objs, threshold=0.002, pairs=None, samples=400):
    """Nearest distance between mesh pairs that should be in contact.
    objs: objects. pairs: [(name_a, name_b)] to check only those (default: all pairs, slow on big sets).
    Returns [(a, b, distance, status)], status 'contact' | 'GAP' (0 < d < threshold) | 'far' (d >= threshold:
    a connecting part is missing, or the pair is not meant to touch)."""
    dg = bpy.context.evaluated_depsgraph_get()
    data = {o.name: _bvh(o, dg) for o in objs if o.type == 'MESH'}
    out = []
    for a, b in (pairs or list(itertools.combinations(list(data), 2))):
        (ta, va), (tb, vb) = data[a], data[b]
        if not ta or not tb: continue
        if ta.overlap(tb):
            out.append((a, b, 0.0, 'contact')); continue
        best = 9e9
        for tree, vs in ((tb, va), (ta, vb)):
            for v in vs[::max(1, len(vs) // samples)]:
                hit = tree.find_nearest(v)
                if hit[0] is not None: best = min(best, hit[3])
        out.append((a, b, round(best, 5), 'contact' if best < 1e-5 else ('GAP' if best < threshold else 'far')))
    return out
