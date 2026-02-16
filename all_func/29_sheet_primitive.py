import numpy as np
import stl, pathlib
from stl import mesh
from skimage import measure
import os
from pathlib import Path
from TPMS.All_kind_TPMS_Gen import generate_iso_mesh, snap_to_cube_planes, decimate_and_clean, build_end_caps, create_stl_from_mesh, rotate
import math
MAX_TRIS_FOR_STEP = 50000
SNAP_TOL = 1e-6
scale = 2 * math.pi
def Sheet_Primitive(C, direction, a1,a2, resolution = 200, folder='all_files'):
    
    
    V, F = generate_iso_mesh(1, resolution, scale, C, kind='p', mode='sheet')
    V = snap_to_cube_planes(V, SNAP_TOL)
    V, F = decimate_and_clean(V, F, MAX_TRIS_FOR_STEP)
    V, F = build_end_caps(V, F, tol=SNAP_TOL, kind='p', direction=direction,mode='sheet')
    rotate(V,a1,a2,0) 
    filename = f"29Sheet_Primitive_{C:.2f}_{direction}_{a1}_{a2}.stl"  # Format filename with the c value
    cached_file = create_stl_from_mesh(V,F,folder,filename)
    return f"{folder}/{filename}"  


def rotation_matrix_x(angle):
    """Rotation matrix for rotation around the x-axis."""
    return np.array([
        [1, 0, 0],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle), np.cos(angle)]
    ])


def rotation_matrix_y(angle):
    """Rotation matrix for rotation around the y-axis."""
    return np.array([
        [np.cos(angle), 0, np.sin(angle)],
        [0, 1, 0],
        [-np.sin(angle), 0, np.cos(angle)]
    ])


def rotation_matrix_z(angle):
    """Rotation matrix for rotation around the z-axis."""
    return np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])


def rotate(verts, angle_x, angle_y, angle_z, degrees=True):
    ax, ay, az = (angle_x, angle_y, angle_z)  # Start of CHANGES: Covert Radian to Angle for Calculation of Rotation
    if degrees:
        ax, ay, az = np.deg2rad([ax, ay, az])  # End of CHANGES.
    rotation_x = rotation_matrix_x(ax)
    rotation_y = rotation_matrix_y(ay)
    rotation_z = rotation_matrix_z(az)
    rotated_verts = verts.dot(rotation_x).dot(rotation_y).dot(rotation_z)
    return rotated_verts