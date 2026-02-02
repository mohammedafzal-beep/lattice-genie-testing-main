import numpy as np
from skimage import measure
from stl import mesh
import os
def Inverse_FCC(r,face_atom_radius, resolution = 200, folder='all_files'):
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
            [0.5*a, 0.5*b, 0],      # Face-centered atom on xy-plane
            [0.5*a, 0, 0.5*c],      # Face-centered atom on xz-plane
            [0, 0.5*b, 0.5*c],      # Face-centered atom on yz-plane
            [0.5*a, 0.5*b, 1*c],      # Face-centered atom on yz-plane
            [0.5*a, 1*b, 0.5*c],      # Face-centered atom on yz-plane
            [1*a, 0.5*b, 0.5*c],      # Face-centered atom on yz-plane
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
    # Lattice vectors from atomic positions
        v1 = position[1]
        v2 = position[2]
        v3 = position[3]

        # Generate a 3D uniform grid in [0, 1] x [0, 1] x [0, 1]
        nx, ny, nz = int(a * resolution), int(b * resolution), int(c * resolution)
        u, v, w = np.meshgrid(
            np.linspace(0, 1, nx),
            np.linspace(0, 1, ny),
            np.linspace(0, 1, nz),
            indexing='ij'
        )

        # Vectorized coordinate transformation
        x = u * v1[0] + v * v2[0] + w * v3[0]
        y = u * v1[1] + v * v2[1] + w * v3[1]
        z = u * v1[2] + v * v2[2] + w * v3[2]

        # Accumulate all atom contributions with radius filtering
        def sphere_value(atom_pos, rad):
            return (x - atom_pos[0])**2 + (y - atom_pos[1])**2 + (z - atom_pos[2])**2 - rad**2

        # Use min for union of spheres (atomic volume)
        values = np.full_like(x, np.inf)

        # Corner atoms
        for i in range(8):
            values = np.minimum(values, sphere_value(position[i], atom_radius))

        # Face atoms
        for i in range(8, 14):
            values = np.minimum(values, sphere_value(position[i], face_atom_radius))

        # Apply boundary plane cutoffs (set to solid inside)
        for normal_vector, D in plane_equation.values():
            plane_dist = np.round(
                normal_vector[0]*x + normal_vector[1]*y + normal_vector[2]*z + D,
                3
            )
            values[plane_dist == 0] = -1  # Force inside

        # Isosurface extraction
        verts, faces, _, _ = measure.marching_cubes(values, level=0)
        verts = np.dot(verts, T)  # Transform vertices back

        return verts, faces


    def create_stl_from_mesh(verts, faces, folder, filename):
        if not os.path.exists(folder):
            os.makedirs(folder)
        full_path = os.path.join(folder, filename)
        
        tpms_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                tpms_mesh.vectors[i][j] = verts[f[j], :]
        tpms_mesh.vectors[:, [0, 1]] = tpms_mesh.vectors[:, [1, 0]]
        tpms_mesh.update_normals()
        tpms_mesh.save(full_path)
        print(f"STL file saved as {full_path}")

    # Set lattice parameters and generate atomic positions
    a, b, c = 1, 1, 1
    alpha, beta, gamma = 90.0, 90.0, 90.0
    atom_radius_range = np.arange(0.355, 0.40, 0.01)  # Considered lower tolerance than 0.03 to generate atleast 4+ structures
    face_atom_radius_range = np.arange(0.355, 0.40, 0.01)   # Considered lower tolerance than 0.03 to generate atleast 4+ structures

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

    filename = f"16Inverse_FCC_{r:.2f}_{face_atom_radius:.2f}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, face_atom_radius, a, b, c, plane_equation)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file