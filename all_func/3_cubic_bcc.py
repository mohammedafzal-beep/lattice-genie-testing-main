import numpy as np 
from skimage import measure 
from stl import mesh 
import os 
def Cubic_BCC(r,centre_radius, resolution = 50, folder='all_files'): 
    """ 
    Generate a BCC lattice structure and save it as an STL file. 
    """ 
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
            [a, b, 0], [a, 0, c], [0, b, c], [a, b, c], [(0.5*a), (0.5*b), (0.5*c)] 
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
 
    def generate_solid_volume(resolution, position, T, atom_radius, center_atom_radius, a, b, c, plane_equation):
    # Define the 3 lattice edge vectors
        v1 = position[1]
        v2 = position[2]
        v3 = position[3]

        # Grid shape
        nx, ny, nz = int(a * resolution), int(b * resolution), int(c * resolution)

        # Create regular 3D grid of unit cube
        u, v, w = np.meshgrid(np.linspace(0, 1, nx),
                            np.linspace(0, 1, ny),
                            np.linspace(0, 1, nz),
                            indexing='ij')

        # Transform grid into parallelepiped coordinates
        parallelepiped_grid = u[..., None] * v1 + v[..., None] * v2 + w[..., None] * v3
        x = parallelepiped_grid[..., 0]
        y = parallelepiped_grid[..., 1]
        z = parallelepiped_grid[..., 2]

        # Compute scalar field for each atom
        values = bravais_function(x, y, z, position[0], atom_radius)
        for i in range(1, 8):  # atoms 1 to 7
            values = np.minimum(values, bravais_function(x, y, z, position[i], atom_radius))
        values = np.minimum(values, bravais_function(x, y, z, position[8], center_atom_radius))  # center atom

        # Enforce boundary planes (hard clipping to the unit cell)
        for normal_vector, D in plane_equation.values():
            clip_mask = np.round(normal_vector[0]*x + normal_vector[1]*y + normal_vector[2]*z + D, 3) == 0
            values[clip_mask] = 1

        # Extract mesh using marching cubes
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
    a, b, c = 1,1,1 
    alpha, beta, gamma = 90.0, 90.0, 90.0 
    atom_radius = r  
    atom_radius_range = np.arange(0.33, 0.50, 0.01) # Considered lower tolerance than 0.03 to generate atleast 4+ structures 

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
 
    
    filename = f"3Cubic_BCC_{r:.2f}_{centre_radius}_{resolution}.stl" 
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, atom_radius, centre_radius, a, b, c, plane_equation) 
    create_stl_from_mesh(verts, faces, folder, filename) 
    cached_file = os.path.join(folder, filename) 
    return cached_file
   