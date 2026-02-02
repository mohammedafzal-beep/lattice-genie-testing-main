import numpy as np
from skimage import measure
from stl import mesh
import os
from concurrent.futures import ThreadPoolExecutor

def Cubic_Ortho(a, b, c, r, resolution=50, folder='all_files'):
    # 1. Define atom positions in Cartesian coords (8 corners)
    atom_positions = np.array([
        [0, 0, 0], [a, 0, 0], [0, b, 0], [0, 0, c],
        [a, b, 0], [a, 0, c], [0, b, c], [a, b, c]
    ])

    # 2. Build grid in Cartesian coords
    u = np.linspace(0, a, resolution)
    v = np.linspace(0, b, resolution)
    w = np.linspace(0, c, resolution)
    x, y, z = np.meshgrid(u, v, w, indexing='ij')

    # 3. Compute distance fields for each atom in parallel
    def sphere_field(pos):
        dx = x - pos[0]
        dy = y - pos[1]
        dz = z - pos[2]
        return dx*dx + dy*dy + dz*dz - r*r

    with ThreadPoolExecutor() as executor:
        fields = list(executor.map(sphere_field, atom_positions))
    values = np.minimum.reduce(fields)

    # 4. Clip at cell boundaries (keep interior only)
    values[0, :, :] = 1
    values[-1, :, :] = 1
    values[:, 0, :] = 1
    values[:, -1, :] = 1
    values[:, :, 0] = 1
    values[:, :, -1] = 1

    # 5. Marching cubes
    verts_idx, faces, _, _ = measure.marching_cubes(values, level=0)
    # Convert voxel indices to Cartesian
    spacing = np.array([a/(resolution-1), b/(resolution-1), c/(resolution-1)])
    verts = verts_idx * spacing

    # 6. Export STL
    
    os.makedirs(folder, exist_ok=True)
    filename = f"4Cubic_Ortho_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{resolution}.stl"
    fullpath = os.path.join(folder, filename) 
     
    stl_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        stl_mesh.vectors[i] = verts[f]
    stl_mesh.save(fullpath)
    print(f"STL file saved: {fullpath}")
    return fullpath