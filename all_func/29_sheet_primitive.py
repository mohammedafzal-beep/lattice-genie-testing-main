import numpy as np
import stl, pathlib
from stl import mesh
from skimage import measure
import os
from pathlib import Path
from TPMS.All_kind_TPMS_Gen import (generate_iso_mesh, snap_to_cube_planes, rotate, 
decimate_and_clean, build_end_caps, create_stl_from_mesh, rotate)
import math
MAX_TRIS_FOR_STEP = 50000
SNAP_TOL = 1e-6
scale = 2 * math.pi
def Sheet_Primitive(C, direction, a1,a2, resolution = 200, folder='all_files'):
    
    
    V, F = generate_iso_mesh(1, resolution, scale, C, kind='p', mode='sheet')

    V, F = build_end_caps(V, F, tol=SNAP_TOL, kind='p', direction=direction,mode='sheet')
    rotate(V,a1,a2,0) 
    filename = f"29Sheet_Primitive_{C:.2f}_{direction}_{a1}_{a2}.stl"  # Format filename with the c value
    cached_file = create_stl_from_mesh(V,F,folder,filename)
    return f"{folder}/{filename}"  
import numpy as np

def remove_duplicate_vertices(V, F, tol=1e-6):
    """
    Robust, order-preserving deduplication with tolerance.
    Works even if V is accidentally (N,1,3) from np.append usage.

    Returns:
        V2: (N2,3) float64
        F2: (M2,3) int32
    """
    V = np.asarray(V)
    F = np.asarray(F)

    # ---- Normalize V to strict (N,3) float64 ----
    if V.ndim == 3 and V.shape[1] == 1 and V.shape[2] == 3:
        V = V[:, 0, :]
    elif V.ndim != 2 or V.shape[-1] != 3:
        V = V.reshape(-1, 3)

    V = np.asarray(V, dtype=np.float64)

    # ---- Normalize F to strict (M,3) int64 ----
    if F.ndim != 2 or F.shape[1] != 3:
        F = F.reshape(-1, 3)
    F = np.asarray(F, dtype=np.int64)

    if tol <= 0:
        raise ValueError("tol must be > 0")

    # ---- Bounds check (fail fast instead of corrupting) ----
    if len(V) == 0:
        return V, F.astype(np.int32)
    if F.size and (F.min() < 0 or F.max() >= len(V)):
        raise ValueError(f"Face index out of bounds: F in [{F.min()},{F.max()}], V has {len(V)} verts")

    # ---- Quantize for tolerance-based merging ----
    Q = np.round(V / tol).astype(np.int64)

    # ---- Stable mapping (first-seen order preserved) ----
    key_to_new = {}
    inverse = np.empty(len(V), dtype=np.int64)
    new_verts = []

    for i, key in enumerate(map(tuple, Q)):
        j = key_to_new.get(key)
        if j is None:
            j = len(new_verts)
            key_to_new[key] = j
            new_verts.append(V[i])   # keep first occurrence
        inverse[i] = j

    V2 = np.asarray(new_verts, dtype=np.float64)

    # ---- Remap faces ----
    F2 = inverse[F]

    # ---- Drop degenerate triangles (repeated vertex indices) ----
    nondeg = (F2[:, 0] != F2[:, 1]) & (F2[:, 1] != F2[:, 2]) & (F2[:, 0] != F2[:, 2])
    F2 = F2[nondeg]

    # ---- Drop duplicate triangles (ignoring winding) ----
    Fs = np.sort(F2, axis=1)
    _, keep = np.unique(Fs, axis=0, return_index=True)
    F2 = F2[np.sort(keep)].astype(np.int32)

    return V2, F2

