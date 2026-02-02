import numpy as np
from skimage import measure
from stl import mesh
import os
from concurrent.futures import ThreadPoolExecutor

def Hexa(a, b, c,alpha,beta,gamma, r=0.75, resolution=200, folder='all_files'):
    def Lattice_atom_positions(a, b, c, alpha, beta, gamma):
        alpha_rad = np.deg2rad(alpha)
        beta_rad = np.deg2rad(beta)
        gamma_rad = np.deg2rad(gamma)

        T = np.array([
            [a, 0, 0],
            [b * np.cos(gamma_rad), b * np.sin(gamma_rad), 0],
            [c * np.cos(beta_rad),
             c * (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad),
             c * np.sqrt(1 + 2 * np.cos(alpha_rad) * np.cos(beta_rad) * np.cos(gamma_rad)
                         - np.cos(alpha_rad)**2 - np.cos(beta_rad)**2 - np.cos(gamma_rad)**2)
             / np.sin(gamma_rad)]
        ])

        positions = [
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
            [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]
        ]
        return [np.dot(T, pos) for pos in positions]

    def bravais_function(pos):
        dx = x - pos[0]
        dy = y - pos[1]
        dz = z - pos[2]
        return dx*dx + dy*dy + dz*dz - r*r

    def generate_solid_volume():
        u = np.linspace(0, 1, resolution)
        v = np.linspace(0, 1, resolution)
        w = np.linspace(0, 1, resolution)
        uu, vv, ww = np.meshgrid(u, v, w, indexing='ij')

        # Generate full grid using lattice vectors
        grid = uu[..., None] * v1 + vv[..., None] * v2 + ww[..., None] * v3
        global x, y, z
        x, y, z = grid[..., 0], grid[..., 1], grid[..., 2]

        with ThreadPoolExecutor() as executor:
            fields = list(executor.map(bravais_function, atom_positions))

        values = np.minimum.reduce(fields)

        # Clip faces
        values[0, :, :] = 1
        values[-1, :, :] = 1
        values[:, 0, :] = 1
        values[:, -1, :] = 1
        values[:, :, 0] = 1
        values[:, :, -1] = 1

        verts_idx, faces, _, _ = measure.marching_cubes(values, level=0)
        transform_matrix = np.stack([v1, v2, v3], axis=1)
        verts = verts_idx @ (transform_matrix / (resolution - 1))
        return verts, faces

    def create_stl_from_mesh(verts, faces, folder, filename):
        os.makedirs(folder, exist_ok=True)
        full_path = os.path.join(folder, filename)
        tpms_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            tpms_mesh.vectors[i] = verts[f]
        tpms_mesh.save(full_path)
        print(f"STL file saved: {full_path}")

    # Set lattice parameters and generate atomic positions
    atom_positions = Lattice_atom_positions(a, b, c, alpha, beta, gamma)
    v1, v2, v3 = atom_positions[1], atom_positions[2], atom_positions[3]

    filename = f"14Hexa_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{alpha}_{beta}_{gamma}_{resolution}.stl" 
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume()
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file