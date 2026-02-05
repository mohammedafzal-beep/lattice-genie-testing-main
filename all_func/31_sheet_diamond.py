import numpy as np
from stl import mesh
from skimage import measure
import os
import threading
MAX_TRIS_FOR_STEP = 50000
SNAP_TOL = 1e-6

def Sheet_Diamond(C, direction, a1,a2, resolution = 200, folder='all_files'):
    
    
    V, F = generate_iso_mesh(size, resolution, scale, C, kind='d', mode='sheet')
    V = snap_to_cube_planes(V, SNAP_TOL)
    V, F = decimate_and_clean(V, F, MAX_TRIS_FOR_STEP)
    V, F = build_end_caps(V, F, tol=SNAP_TOL, kind='d', direction=direction,mode='sheet')
    rotate(V,a1,a2,0) 
    filename = f"31Sheet_Neovius_{C:.2f}_{direction}_{a1}_{a2}.stl"  # Format filename with the c value
    cached_file = create_stl_from_mesh(V,F,folder,filename)
    return cached_file    
        