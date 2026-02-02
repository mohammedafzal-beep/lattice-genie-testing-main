import numpy as np
from skimage import measure
from stl import mesh
import os
def Inverse_Ortho_FCC(a, b, c, face_atom_radius=0.4, r=0.47, resolution=200, folder='all_files'):

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

        # Create a 3D grid
        # Step 1: Define parallelepiped edge vectors
        v1 = atom_positions[1]  # Example vector
        v2 = atom_positions[2]  # Example vector
        v3 = atom_positions[3]  # Example vector

        # Step 2: Create a regular 3D grid
        u, v, w = np.meshgrid(np.linspace(0, 1, int(a*resolution)), np.linspace(0, 1, int(b*resolution)), np.linspace(0, 1, int(c*resolution)), indexing = 'ij')

        # Step 3: Transform the grid
        # Initialize an array to hold the transformed grid points
        parallelepiped_grid = np.zeros((int(a*resolution), int(b*resolution), int(c*resolution), 3))

        for i in range(int(a*resolution)):
            for j in range(int(b*resolution)):
                for k in range(int(c*resolution)):
                    parallelepiped_grid[i, j, k] = u[i, j, k] * v1 + v[i, j, k] * v2 + w[i, j, k] * v3
        x = parallelepiped_grid[:,:,:,0]
        y = parallelepiped_grid[:,:,:,1]
        z = parallelepiped_grid[:,:,:,2]

        values1 = bravais_function(x, y, z, positions[0], atom_radius)
        values2 = bravais_function(x, y, z, positions[1], atom_radius)
        values3 = bravais_function(x, y, z, positions[2], atom_radius)
        values4 = bravais_function(x, y, z, positions[3], atom_radius)
        values5 = bravais_function(x, y, z, positions[4], atom_radius)
        values6 = bravais_function(x, y, z, positions[5], atom_radius)
        values7 = bravais_function(x, y, z, positions[6], atom_radius)
        values8 = bravais_function(x, y, z, positions[7], atom_radius)
        values9 = bravais_function(x, y, z, positions[8], face_atom_radius)
        values10 = bravais_function(x, y, z, positions[9], face_atom_radius)
        values11 = bravais_function(x, y, z, positions[10], face_atom_radius)
        values12 = bravais_function(x, y, z, positions[11], face_atom_radius)
        values13 = bravais_function(x, y, z, positions[12], face_atom_radius)
        values14 = bravais_function(x, y, z, position[13], face_atom_radius)

        values = np.minimum(values1, values2)
        values = np.minimum(values, values3)
        values = np.minimum(values, values4)
        values = np.minimum(values, values5)
        values = np.minimum(values, values6)
        values = np.minimum(values, values7)
        values = np.minimum(values, values8)
        values = np.minimum(values, values9)
        values = np.minimum(values, values10)
        values = np.minimum(values, values11)
        values = np.minimum(values, values12)
        values = np.minimum(values, values12)
        values = np.minimum(values, values13)
        values = np.minimum(values, values14)


        for face_name, (normal_vector, D) in plane_equation.items():
                values[np.round(normal_vector[0]*x + normal_vector[1]*y + normal_vector[2]*z + D,3) == 0] = -1
            
        # Extract the isosurface that represents the solid volume
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
        tpms_mesh.vectors[:, [0, 1]] = tpms_mesh.vectors[:, [1, 0]]
        tpms_mesh.update_normals()
        tpms_mesh.save(full_path)
        print(f"STL file saved as {full_path}")

 
    atom_positions, T = Lattice_atom_positions(a, b, c, 90, 90, 90)

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

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, face_atom_radius, a, b, c, plane_equation)
    filename = f"20Inverse_ortho_FCC_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{face_atom_radius:.2f}_{resolution}.stl"
    create_stl_from_mesh(verts, faces, folder, filename)
    cached_file = os.path.join(folder, filename) 
    return cached_file
"""import numpy as np
from skimage import measure
from stl import mesh
import os
from concurrent.futures import ThreadPoolExecutor

def Inverse_Ortho_FCC(a, b, c, face_atom_radius=0.4, r=0.47, resolution=200, folder='all_files'):

    def Lattice_atom_positions(a, b, c, alpha, beta, gamma):
        alpha_rad = np.deg2rad(alpha)
        beta_rad = np.deg2rad(beta)
        gamma_rad = np.deg2rad(gamma)

        T = np.array([
            [1, 0, 0],
            [np.cos(gamma_rad), np.sin(gamma_rad), 0],
            [np.cos(beta_rad), (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad),
             np.sqrt(1 - np.cos(beta_rad) ** 2 - ((np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad)) ** 2)]
        ])
        positions = [
            [0, 0, 0], [a, 0, 0], [0, b, 0], [0, 0, c],
            [a, b, 0], [a, 0, c], [0, b, c], [a, b, c],
            [0.5 * a, 0.5 * b, 0],
            [0.5 * a, 0, 0.5 * c],
            [0, 0.5 * b, 0.5 * c],
            [0.5 * a, 0.5 * b, 1 * c],
            [0.5 * a, 1 * b, 0.5 * c],
            [1 * a, 0.5 * b, 0.5 * c],
        ]
        return [np.dot(pos, T) for pos in positions], T

    #def bravais_function(pos, radius):
        #return (x - pos[0])**2 + (y - pos[1])**2 + (z - pos[2])**2 - radius**2

    def plane_from_points(p1, p2, p3):
        v1 = p3 - p2
        v2 = p1 - p2
        normal_vector = np.cross(v2, v1)
        D = -np.dot(normal_vector, p2)
        return normal_vector, D

    def generate_solid_volume():
        u = np.linspace(0, 1, resolution)
        v = np.linspace(0, 1, resolution)
        w = np.linspace(0, 1, resolution)
        uu, vv, ww = np.meshgrid(u, v, w, indexing='ij')

        grid = uu[..., None] * v1 + vv[..., None] * v2 + ww[..., None] * v3
        global x, y, z
        x, y, z = grid[..., 0], grid[..., 1], grid[..., 2]

        # Start as solid, then subtract spheres
        mask = np.ones_like(x, dtype=bool)
        for pos in atom_positions:
            dx, dy, dz = x - pos[0], y - pos[1], z - pos[2]
            inside_sphere = (dx**2 + dy**2 + dz**2) <= r**2
            mask &= ~inside_sphere  # subtract sphere

        # Convert binary mask to float field for marching cubes
        values = np.where(mask, 1.0, 0.0)

        # Clip faces
        values[0, :, :] = 0
        values[-1, :, :] = 0
        values[:, 0, :] = 0
        values[:, -1, :] = 0
        values[:, :, 0] = 0
        values[:, :, -1] = 0

        verts_idx, faces, _, _ = measure.marching_cubes(values, level=0.5)
        transform_matrix = np.stack([v1, v2, v3], axis=1)
        verts = verts_idx @ (transform_matrix / (resolution - 1))
        return verts, faces


    def create_stl_from_mesh(verts, faces, folder, filename):
        os.makedirs(folder, exist_ok=True)
        full_path = os.path.join(folder, filename)
        tpms_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))

        for i, f in enumerate(faces):
            tri = verts[f]
            normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            if np.linalg.norm(normal) == 0:
                normal = np.array([0.0, 0.0, 1.0])
            else:
                normal = normal / np.linalg.norm(normal)
            tpms_mesh.vectors[i] = tri
            tpms_mesh.normals[i] = normal

        tpms_mesh.save(full_path)
        print(f"STL file saved: {full_path}")



    alpha, beta, gamma = 90.0, 90.0, 90.0
    atom_positions, T = Lattice_atom_positions(a, b, c, alpha, beta, gamma)
    positions = np.array(atom_positions)
    v1, v2, v3 = positions[1], positions[2], positions[3]

    faces = {
        'bottom': (positions[0], positions[1], positions[4]),
        'top': (positions[7], positions[5], positions[3]),
        'front': (positions[1], positions[5], positions[7]),
        'back': (positions[6], positions[3], positions[0]),
        'right': (positions[1], positions[0], positions[3]),
        'left': (positions[7], positions[6], positions[2]),
    }
    plane_equation = {name: plane_from_points(*verts) for name, verts in faces.items()}

    filename = f"20Inverse_ortho_FCC_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{face_atom_radius:.2f}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume()
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file"""
