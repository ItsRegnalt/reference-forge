"""reference-forge: silhouette IoU, difference maps, outlines and relief (depth) maps.

Images are written to OUT (set it, or the RF_OUT environment variable; default Blender's temp dir).
Axes: 0 = X, 1 = Y, 2 = Z. A view is (name, [horizontal_axis, vertical_axis]).
"""
import bpy, numpy as np, os

OUT = os.environ.get('RF_OUT') or bpy.app.tempdir
VIEWS = (('side', [1, 2]), ('top', [1, 0]), ('front', [0, 2]))


def tris_of(objs):
    """World-space triangles of evaluated meshes: (N, 3, 3)."""
    dg = bpy.context.evaluated_depsgraph_get(); out = []
    for o in objs:
        e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); n = len(m.vertices)
        if n:
            co = np.empty(n * 3, np.float64); m.vertices.foreach_get('co', co)
            M = np.array(e.matrix_world); co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
            idx = np.empty(len(m.loop_triangles) * 3, np.int64); m.loop_triangles.foreach_get('vertices', idx)
            if len(idx):
                out.append(co[idx.reshape(-1, 3)])
        e.to_mesh_clear()
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def raster(T, ax, lo=(-0.5, -0.5), cell=0.002, N=(500, 500)):
    """Rasterise triangles onto a boolean grid in the plane of axes `ax` (origin lo, cell size, N cells)."""
    A = T[:, :, ax]; lo = np.array(lo); G = np.zeros(N, bool)
    e1 = A[:, 1] - A[:, 0]; e2 = A[:, 2] - A[:, 0]
    L = np.maximum(np.linalg.norm(e1, axis=1), np.linalg.norm(e2, axis=1))
    k = np.clip(np.ceil(L / cell * 1.6), 1, 80).astype(int)
    for kk in np.unique(k):
        sel = k == kk
        u, v = np.meshgrid(np.arange(kk + 1), np.arange(kk + 1)); m = (u + v) <= kk; u = u[m] / kk; v = v[m] / kk
        P = A[sel, 0][:, None, :] + u[None, :, None] * e1[sel][:, None, :] + v[None, :, None] * e2[sel][:, None, :]
        ij = np.floor((P.reshape(-1, 2) - lo) / cell).astype(int)
        ok = (ij[:, 0] >= 0) & (ij[:, 1] >= 0) & (ij[:, 0] < N[0]) & (ij[:, 1] < N[1]); G[ij[ok, 0], ij[ok, 1]] = True
    return G


def dil(G):
    H = G.copy(); H[1:] |= G[:-1]; H[:-1] |= G[1:]; H[:, 1:] |= G[:, :-1]; H[:, :-1] |= G[:, 1:]; return H


def collection_meshes(cols):
    """Visible, renderable meshes of the given collections (skips CUT_* cutters and wire display)."""
    out = []
    for c in cols:
        for o in bpy.data.collections[c].all_objects:
            if (o.type == 'MESH' and not o.name.startswith('CUT_') and not o.hide_render and o.display_type != 'WIRE'
                    and not any(uc.hide_render for uc in o.users_collection)):
                out.append(o)
    return out


def _crop(G):
    ii = np.where(G.any(1))[0]; jj = np.where(G.any(0))[0]
    return max(ii[0] - 5, 0), min(ii[-1] + 6, G.shape[0]), max(jj[0] - 5, 0), min(jj[-1] + 6, G.shape[1])


def _save(rgb, name):
    h, w = rgb.shape[:2]; img = bpy.data.images.get(name)
    if img: bpy.data.images.remove(img)
    img = bpy.data.images.new(name, w, h, alpha=True); img.pixels[:] = rgb.ravel()
    img.filepath_raw = os.path.join(OUT, name + '.png'); img.file_format = 'PNG'; img.save()
    return img.filepath_raw


def silcheck(ref, mdl, views=VIEWS, lo=(-0.5, -0.5), cell=0.002, N=(500, 500), grid=0.05, S=3, tag='', save=True):
    """IoU of reference vs model silhouettes per view, plus a difference image per view:
    grey = overlap, red = in reference only (missing), green = in model only (extra).
    ref / mdl: lists of objects or object names. Returns [(view, IoU, missing_cells, extra_cells, png_path)]."""
    get = lambda L: [bpy.data.objects[x] if isinstance(x, str) else x for x in L]
    TR, TM = tris_of(get(ref)), tris_of(get(mdl)); rep = []
    for name, ax in views:
        gr = raster(TR, ax, lo, cell, N); gm = raster(TM, ax, lo, cell, N)
        miss = gr & ~dil(gm); extra = gm & ~dil(gr)
        iou = round((gr & gm).sum() / max(1, (gr | gm).sum()), 3); path = None
        if save and (gr | gm).any():
            a0, a1, b0, b1 = _crop(gr | gm)
            rgb = np.zeros((a1 - a0, b1 - b0, 4), np.float32); rgb[..., 3] = 1
            rgb[(gr & gm)[a0:a1, b0:b1]] = (0.55, 0.55, 0.55, 1)
            rgb[miss[a0:a1, b0:b1]] = (1, 0.15, 0.15, 1); rgb[extra[a0:a1, b0:b1]] = (0.1, 1, 0.2, 1)
            for i in range(a0, a1):
                if abs(((i * cell + lo[0]) + 1e-9) % grid) < cell: rgb[i - a0, :, :3] = np.maximum(rgb[i - a0, :, :3], 0.2)
            for j in range(b0, b1):
                if abs(((j * cell + lo[1]) + 1e-9) % grid) < cell: rgb[:, j - b0, :3] = np.maximum(rgb[:, j - b0, :3], 0.2)
            rgb = np.repeat(np.repeat(np.transpose(rgb, (1, 0, 2)), S, 0), S, 1)
            path = _save(rgb, 'sil_' + name + tag)
        rep.append((name, iou, int(miss.sum()), int(extra.sum()), path))
    return rep


def profile_of(names, ax=(1, 2), yr=(-0.5, 0.6), cr=(-0.5, 0.5), cell=0.001, clip=None):
    """Per-column silhouette extents [(h, vmin, vmax)] and the grid. clip: [(axis, lo, hi)] filter on tri centroids."""
    T = tris_of([bpy.data.objects[n] for n in names])
    for a, l, h in (clip or []):
        c = T[:, :, a].mean(1); T = T[(c >= l) & (c <= h)]
    N = (int((yr[1] - yr[0]) / cell), int((cr[1] - cr[0]) / cell))
    G = raster(T, list(ax), lo=(yr[0], cr[0]), cell=cell, N=N); out = []
    for i in range(N[0]):
        jj = np.where(G[i])[0]
        if len(jj):
            out.append((round(yr[0] + (i + 0.5) * cell, 4), round(cr[0] + jj[0] * cell, 4), round(cr[0] + (jj[-1] + 1) * cell, 4)))
    return out, G


def _dp(P, tol):
    P = np.array(P, float)
    if len(P) < 3: return P.tolist()
    a, b = P[0], P[-1]; d = b - a; L = np.linalg.norm(d)
    dist = np.linalg.norm(P - a, axis=1) if L < 1e-12 else np.abs(d[0] * (P[:, 1] - a[1]) - d[1] * (P[:, 0] - a[0])) / L
    i = int(np.argmax(dist))
    if dist[i] > tol: return _dp(P[:i + 1], tol)[:-1] + _dp(P[i:], tol)
    return [a.tolist(), b.tolist()]


def outline(names, clip=None, ax=(1, 2), yr=(-0.5, 0.6), cr=(-0.5, 0.5), cell=0.001, tol=0.0006, med=2):
    """Simplified silhouette polygon (column extremes + Douglas-Peucker). Breaks on undercuts: draw those by hand."""
    prof, _ = profile_of(names, ax, yr, cr, cell, clip)
    if not prof: return []
    P = np.array(prof)
    if med > 0 and len(P) > 2 * med + 1:
        for j in (1, 2):
            c = P[:, j].copy(); P[:, j] = [np.median(c[max(0, i - med):i + med + 1]) for i in range(len(c))]
    top = [(y, c1) for y, c0, c1 in P]; bot = [(y, c0) for y, c0, c1 in P]
    y0, y1 = P[0, 0] - cell / 2, P[-1, 0] + cell / 2
    top = [(y0, top[0][1])] + top + [(y1, top[-1][1])]; bot = [(y0, bot[0][1])] + bot + [(y1, bot[-1][1])]
    poly = _dp(bot, tol) + _dp(top, tol)[::-1][1:-1]
    return [(round(a, 4), round(b, 4)) for a, b in poly]


def relief(objs, side=1, yr=(-0.15, 0.15), zr=(-0.15, 0.15), cell=0.0005, clipx=None):
    """Depth map of the face looking along X (side=+1 right, -1 left): outermost X per (y, z) cell, NaN = empty."""
    T = tris_of(objs)
    if clipx:
        c = T[:, :, 0].mean(1); T = T[(c >= clipx[0]) & (c <= clipx[1])]
    Ny, Nz = int((yr[1] - yr[0]) / cell), int((zr[1] - zr[0]) / cell)
    flat = np.full(Ny * Nz, np.nan)
    e1 = T[:, 1] - T[:, 0]; e2 = T[:, 2] - T[:, 0]
    L = np.maximum(np.linalg.norm(e1[:, 1:], axis=1), np.linalg.norm(e2[:, 1:], axis=1))
    k = np.clip(np.ceil(L / cell * 1.5), 1, 120).astype(int)
    for kk in np.unique(k):
        sel = k == kk
        u, v = np.meshgrid(np.arange(kk + 1), np.arange(kk + 1)); m = (u + v) <= kk; u = u[m] / kk; v = v[m] / kk
        P = (T[sel, 0][:, None, :] + u[None, :, None] * e1[sel][:, None, :] + v[None, :, None] * e2[sel][:, None, :]).reshape(-1, 3)
        iy = np.floor((P[:, 1] - yr[0]) / cell).astype(int); iz = np.floor((P[:, 2] - zr[0]) / cell).astype(int)
        ok = (iy >= 0) & (iy < Ny) & (iz >= 0) & (iz < Nz); idx = iy[ok] * Nz + iz[ok]; val = side * P[ok, 0]
        flat[idx] = np.fmax(flat[idx], val)
    return flat.reshape(Ny, Nz)


def relief_png(H, name, lo, hi):
    """Shaded, depth-coloured image of a relief() map. Use the same lo/hi for reference and model."""
    A = np.nan_to_num(np.clip((H - lo) / (hi - lo), 0, 1), nan=-1)
    rgb = np.zeros(H.shape + (4,), np.float32); rgb[..., 3] = 1; m = A >= 0
    gy, gz = np.gradient(np.nan_to_num(H, nan=0)); sh = np.clip(0.5 + (-gy + gz) * 400, 0, 1)
    rgb[m, 0] = 0.25 + 0.75 * A[m] * sh[m]; rgb[m, 1] = 0.25 + 0.55 * A[m] * sh[m]; rgb[m, 2] = 0.35 + 0.3 * (1 - A[m]) * sh[m]
    rgb[::40, :, :3] = np.maximum(rgb[::40, :, :3], 0.15); rgb[:, ::40, :3] = np.maximum(rgb[:, ::40, :3], 0.15)
    return _save(np.transpose(rgb, (1, 0, 2)), name)
