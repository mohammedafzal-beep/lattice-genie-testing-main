import numpy as np
from skimage import measure
from stl import mesh
import os
def Ortho_BaseCent(a,b,c,face_atom_radius=0.37,r=0.47,resolution = 50, folder='all_files'):
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

    def generate_solid_volume(resolution, atom_positions, T, atom_radius, face_atom_radius, a, b, c, plane_equation):
    # Use numpy arrays
        atom_positions = np.array(atom_positions)  # shape (num_atoms, 3)

        # Parallelepiped edge vectors (assuming these are lattice vectors)
        v1 = atom_positions[1]  # a vector
        v2 = atom_positions[2]  # b vector
        v3 = atom_positions[3]  # c vector

        # Create 3D grid in [0,1] domain
        u = np.linspace(0, 1, int(a * resolution))
        v = np.linspace(0, 1, int(b * resolution))
        w = np.linspace(0, 1, int(c * resolution))
        u, v, w = np.meshgrid(u, v, w, indexing='ij')  # shape: (aN, bN, cN)

        # Vectorized transformation of the grid points
        # parallelepiped_grid[i,j,k,:] = u[i,j,k]*v1 + v[i,j,k]*v2 + w[i,j,k]*v3
        parallelepiped_grid = (u[..., None] * v1) + (v[..., None] * v2) + (w[..., None] * v3)  # shape: (aN, bN, cN, 3)

        x = parallelepiped_grid[..., 0]
        y = parallelepiped_grid[..., 1]
        z = parallelepiped_grid[..., 2]

        # Prepare atom radii array matching atom positions
        # First 8 atoms use atom_radius, last 2 use face_atom_radius
        radii = np.array([atom_radius]*8 + [face_atom_radius]*2)

        # Calculate squared distances to all atoms simultaneously:
        # Shape broadcasting: (aN,bN,cN,1,3) - (1,1,1,num_atoms,3) -> (aN,bN,cN,num_atoms,3)
        coords = np.stack([x, y, z], axis=-1)[..., None, :]  # shape: (aN,bN,cN,1,3)
        positions = atom_positions[None, None, None, :, :]   # shape: (1,1,1,num_atoms,3)
        diff = coords - positions                             # shape: (aN,bN,cN,num_atoms,3)

        squared_dist = np.sum(diff ** 2, axis=-1)             # (aN,bN,cN,num_atoms)
        values = squared_dist - radii  ** 2                   # broadcast radii (num_atoms,)

        # Minimum value across all atoms (keep closest)
        values = np.min(values, axis=-1)                       # shape: (aN,bN,cN)

        # Apply plane cuts to clean surface by marking points exactly on plane to 1
        for face_name, (normal_vector, D) in plane_equation.items():
            # Calculate plane equation values on the grid
            plane_vals = normal_vector[0] * x + normal_vector[1] * y + normal_vector[2] * z + D
            mask = np.isclose(plane_vals, 0, atol=1e-3)
            values[mask] = 1

        # Extract mesh via marching cubes at level=0
        verts, faces, _, _ = measure.marching_cubes(values, level=0)

        # Transform vertices back to real space by applying T matrix
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
    alpha,beta,gamma=90,90,90
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
    filename = f"5Ortho_Basecent_{a:.1f}_{b:.1f}_{c:.1f}_{face_atom_radius:.2f}_{r:.2f}_{resolution}.stl" 
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, face_atom_radius, a, b, c, plane_equation)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file