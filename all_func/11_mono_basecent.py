import numpy as np
from skimage import measure
from stl import mesh
import os
def Mono_BaseCent(a,b,c,r,alpha,beta,gamma,face_atom_radius=0.37,resolution = 200, folder='all_files'):
    def Lattice_atom_positions(a, b, c, alpha, beta, gamma):

        alpha_rad = np.deg2rad(alpha)
        beta_rad = np.deg2rad(beta)
        gamma_rad = np.deg2rad(gamma)

        T = np.array([
            [1, 0, 0],
            [np.cos(gamma_rad), np.sin(gamma_rad), 0],
            [np.cos(beta_rad), (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad), 
            np.sqrt(1 - np.cos(beta_rad)**2 - ((np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad))**2)]
        ])
        positions = [
            [0, 0, 0], [a, 0, 0], [0, b, 0], [0, 0, c],
            [a, b, 0], [a, 0, c], [0, b, c], [a, b, c],
            [0.5*a, 0.5*b, 1*c],      # Face-centered atom on xy-plane
            [0.5*a, 0.5*b, 0],      # Face-centered atom on yz-plane
        ]

        return [np.dot(pos, T) for pos in positions], T

    def plane_from_points(p1, p2, p3):
        v1 = p3 - p2
        v2 = p1 - p2
        normal_vector =  np.cross(v2, v1)
        D = -np.dot(normal_vector, p2)
        return normal_vector, D

    def bravais_function(x, y, z, position, r):
        return (x - position[0])**2 + (y - position[1])**2 + (z - position[2])**2 - r**2
        
    def plane(x, y, z, normal, D):
        a =  round(normal[0],5)*x + round(normal[1],5)*y + round(normal[2],5)*z +round(D,5)
        return np.round(a,3)

    def generate_solid_volume(resolution, position, T, atom_radius, face_atom_radius, a, b, c, plane_equation):
        v1 = atom_positions[1]
        v2 = atom_positions[2]
        v3 = atom_positions[3]

        # Grid size
        nx, ny, nz = int(a*resolution), int(b*resolution), int(c*resolution)

        # Create uniform grids u,v,w in [0,1]
        u = np.linspace(0, 1, nx)
        v = np.linspace(0, 1, ny)
        w = np.linspace(0, 1, nz)

        # Use meshgrid in 'ij' indexing
        U, V, W = np.meshgrid(u, v, w, indexing='ij')  # Shape (nx, ny, nz)

        # Vectorized linear combination for all points
        # shape will be (nx, ny, nz, 3)
        parallelepiped_grid = (U[..., None] * v1 +
                            V[..., None] * v2 +
                            W[..., None] * v3)

        x = parallelepiped_grid[..., 0]
        y = parallelepiped_grid[..., 1]
        z = parallelepiped_grid[..., 2]

        # Vectorized distance computations
        positions_arr = np.array(positions)

        # Pre-allocate values array with very large positive numbers
        values = np.full_like(x, np.inf, dtype=np.float32)

        # Compute bravais_function for all positions and take minimum
        for pos_idx, pos in enumerate(positions_arr):
            radius = face_atom_radius if pos_idx >= 8 else atom_radius
            dist_sq = (x - pos[0])**2 + (y - pos[1])**2 + (z - pos[2])**2 - radius**2
            values = np.minimum(values, dist_sq)

        # Apply plane constraints (vectorized)
        for face_name, (normal_vector, D) in plane_equation.items():
            plane_val = normal_vector[0]*x + normal_vector[1]*y + normal_vector[2]*z + D
            mask = np.isclose(plane_val, 0, atol=1e-3)
            values[mask] = 1  # Set to positive value (outside)

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
    # Set lattice parameters and generate atomic positions
    atom_radius_range = np.arange(0.47, 0.55, 0.01)  # Considered lower tolerance than 0.03 to generate atleast 4+ structures
    # face_atom_radius_range = np.arange(0.4, 0.48, 0.01) # if the tolerance taken for both corner and face atoms is kept same, unable to  generate more than 4 structures with all atoms and voids connected. SO used a diff tolerance of 0.005 for face atoms like below.
    face_atom_radius_range = np.arange(0.37, 0.43, 0.005)  # Considered lower tolerance than 0.03 to generate atleast 4+ structures
    
    atom_positions, T = Lattice_atom_positions(a, b, c, alpha, beta, gamma)

    # Convert to numpy array for easier manipulation and define faces
    positions = np.array(atom_positions)
    faces = {
        'bottom' : (positions[0], positions[1], positions[4]),  # Bottom face
        'top' : (positions[7], positions[5], positions[3]),  # Top face
        'front' : (positions[1], positions[5], positions[7]),
        'back' : (positions[6], positions[3], positions[0]),
        'right' : (positions[1], positions[0], positions[3]),
        'left' : (positions[7], positions[6], positions[2]),
    }

    # Calculate and store plane equations
    plane_equation = {}
    for face_name, vertices in faces.items():
        normal_vector, D = plane_from_points(*vertices)
        plane_equation[face_name] = (normal_vector, D)

    filename = f"11Mono_Basecent_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{face_atom_radius:.2f}_{alpha}_{beta}_{gamma}_{resolution}.stl" 
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, face_atom_radius, a, b, c, plane_equation)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file