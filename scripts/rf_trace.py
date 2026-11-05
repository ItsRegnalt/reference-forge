"""reference-forge: slice reference meshes and loft new bodies from the slices.

Needs rf_helpers.py loaded first (uses sell, loft).
"""
import bpy, numpy as np


def refverts(names):
    """World-space vertices of the named objects as an (N, 3) array."""
    out = []
    for n in names:
        o = bpy.data.objects[n]; M = np.array(o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get('co', co)
        out.append(co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])
    return np.concatenate(out)


def trace(V, yr, zr=(-9, 9), xr=(-9, 9), dy=0.002):
    """Slice vertices along Y every dy inside the box: rows (y, zmin, zmax, xmin, xmax)."""
    m = (V[:, 1] >= yr[0]) & (V[:, 1] <= yr[1]) & (V[:, 2] >= zr[0]) & (V[:, 2] <= zr[1]) & (V[:, 0] >= xr[0]) & (V[:, 0] <= xr[1])
    P = V[m]; rows = []; y = yr[0]
    while y <= yr[1] + 1e-9:
        S = P[(P[:, 1] >= y) & (P[:, 1] < y + dy)]
        if len(S) >= 2:
            rows.append((y + dy / 2, S[:, 2].min(), S[:, 2].max(), S[:, 0].min(), S[:, 0].max()))
        y += dy
    return rows


def loft_trace(name, rows, col=None, mat=None, e=2.6, inset=0.0, n=32, zpad=0.0, smooth=1):
    """Superellipse loft through trace() rows. `smooth` = moving-average radius on the extents."""
    R = np.array(rows)
    if len(R) < 2:
        raise ValueError(f'loft_trace({name}): need at least 2 slices, got {len(R)} (widen yr or lower dy)')
    if smooth > 0 and len(R) > 4:
        k = np.ones(2 * smooth + 1) / (2 * smooth + 1)
        for j in range(1, 5):
            R[:, j] = np.convolve(np.pad(R[:, j], smooth, mode='edge'), k, 'valid')
    secs = []
    for y, z0, z1, x0, x1 in R:
        hw = max(0.0006, (x1 - x0) / 2 - inset); hh = max(0.0006, (z1 - z0) / 2 - inset + zpad)
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        secs.append((y, [(cx + u, cz + v) for u, v in sell(hw, hh, n, e)]))
    return loft(name, secs, col, mat)
