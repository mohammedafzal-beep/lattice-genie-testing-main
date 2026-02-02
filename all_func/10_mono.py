import numpy as np
from skimage import measure
from stl import mesh
import os

def Mono(a,b,c,r,alpha,beta,gamma,  resolution = 200, folder='all_files'):
    def Lattice_atom_positions(a, b, c, alpha, beta, gamma):
        alpha_rad = np.deg2rad(alpha)
        beta_rad = np.deg2rad(beta)
        gamma_rad = np.deg2rad(gamma)

        T = np.array([
            [1, 0, 0],
            [np.cos(gamma_rad), np.sin(gamma_rad), 0],
            [np.cos(beta_rad), (np.cos(alpha_rad) - np.cos(beta_rad)*np.cos(gamma_rad)) / np.sin(gamma_rad),
             np.sqrt(1 - np.cos(beta_rad)**2 - ((np.cos(alpha_rad) - np.cos(beta_rad)*np.cos(gamma_rad))/np.sin(gamma_rad))**2)]
        ])
        positions = [
            [0, 0, 0], [a, 0, 0], [0, b, 0], [0, 0, c],
            [a, b, 0], [a, 0, c], [0, b, c], [a, b, c]
        ]
        return [np.dot(pos, T) for pos in positions], T

    def plane_from_points(p1, p2, p3):
        v1 = p3 - p2
        v2 = p1 - p2
        normal_vector = np.cross(v2, v1)
        D = -np.dot(normal_vector, p2)
        return normal_vector, D

    def bravais_function(x, y, z, positions, r):
        # positions shape: (num_atoms, 3)
        # x,y,z shape: grid shape
        # Compute squared distance to all atom positions in vectorized manner
        grid_shape = x.shape
        coords = np.stack((x, y, z), axis=-1)  # shape: (..., 3)
        # Expand dims for broadcasting: coords -> (..., 1, 3), positions -> (1, num_atoms, 3)
        diff = coords[..., None, :] - positions[None, None, None, :, :]  # shape: (..., num_atoms, 3)
        dist_sq = np.sum(diff**2, axis=-1)  # shape: (..., num_atoms)
        values = dist_sq - r**2
        # Minimum over atoms at each grid point
        return np.min(values, axis=-1)

    def generate_solid_volume(resolution, atom_positions, T, r, a, b, c, plane_equation):
        v1 = atom_positions[1]
        v2 = atom_positions[2]
        v3 = atom_positions[3]

        # Create normalized grids u,v,w
        u = np.linspace(0, 1, int(a*resolution))
        v = np.linspace(0, 1, int(b*resolution))
        w = np.linspace(0, 1, int(c*resolution))

        # Create meshgrid for u,v,w with 'ij' indexing
        U, V, W = np.meshgrid(u, v, w, indexing='ij')  # shape: (Nx, Ny, Nz)

        # Vectorized parallelepiped grid computation: u*v1 + v*v2 + w*v3
        parallelepiped_grid = (U[..., None]*v1) + (V[..., None]*v2) + (W[..., None]*v3)  # shape: (Nx, Ny, Nz, 3)

        x = parallelepiped_grid[..., 0]
        y = parallelepiped_grid[..., 1]
        z = parallelepiped_grid[..., 2]

        # Vectorized distance to all atoms
        values = bravais_function(x, y, z, atom_positions, r)

        # Apply planes: set values near plane to 1 (exclude them)
        for face_name, (normal_vector, D) in plane_equation.items():
            plane_vals = np.round(normal_vector[0]*x + normal_vector[1]*y + normal_vector[2]*z + D, 3)
            values[np.isclose(plane_vals, 0)] = 1

        # Extract isosurface
        verts, faces, _, _ = measure.marching_cubes(values, level=0)
        verts = np.dot(verts, T)
        return verts, faces

    def create_stl_from_mesh(verts, faces, folder, filename):
        if not os.path.exists(folder):
            os.makedirs(folder)
        full_path = os.path.join(folder, filename)

        tpms_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                tpms_mesh.vectors[i][j] = verts[f[j], :]
        tpms_mesh.save(full_path)
        print(f"STL file saved as {full_path}")

  
    atom_positions, T = Lattice_atom_positions(a, b, c, alpha, beta, gamma)
    atom_positions = np.array(atom_positions)

    positions = np.array(atom_positions)

    faces = {
        'bottom': (positions[0], positions[1], positions[4]),
        'top': (positions[7], positions[5], positions[3]),
        'front': (positions[1], positions[5], positions[7]),
        'back': (positions[6], positions[3], positions[0]),
        'right': (positions[1], positions[0], positions[3]),
        'left': (positions[7], positions[6], positions[2]),
    }

    plane_equation = {}
    for face_name, vertices in faces.items():
        normal_vector, D = plane_from_points(*vertices)
        plane_equation[face_name] = (normal_vector, D)

    filename = f"10Mono_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{alpha}_{beta}_{gamma}_{resolution}.stl" 
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, a, b, c, plane_equation)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file