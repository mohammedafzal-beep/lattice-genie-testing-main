import numpy as np
from stl import mesh
from skimage import measure
import os
from TPMS.All_kind_TPMS_Gen import generate_iso_mesh, snap_to_cube_planes, decimate_and_clean, build_end_caps, create_stl_from_mesh, rotate
import math
MAX_TRIS_FOR_STEP = 50000
SNAP_TOL = 1e-6
scale = 2 * math.pi
def Skeletal_FRD(C,  a1,a2, resolution = 200, folder='all_files'):
    
    
    V, F = generate_iso_mesh(1, resolution, scale, C, kind='fks', mode='skeletal')
    V, F = decimate_and_clean(V, F, MAX_TRIS_FOR_STEP)
    V, F = build_end_caps(V, F, tol=SNAP_TOL, kind='fks', direction='normal',mode='skeletal')
    rotate(V,a1,a2,0) 
    filename = f"41Skeletal_FRD_{C:.2f}_{a1}_{a2}.stl"  # Format filename with the c value
    cached_file = create_stl_from_mesh(V,F,folder,filename)
    return f"{folder}/{filename}"  