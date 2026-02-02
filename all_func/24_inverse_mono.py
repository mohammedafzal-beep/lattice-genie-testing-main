import numpy as np 
from skimage import measure 
from stl import mesh 
import os 
from concurrent.futures import ThreadPoolExecutor

def Inverse_Mono(a, b, c, r, alpha, beta, gamma, resolution = 200 , folder='all_files'): 
 
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
            [a, b, 0], [a, 0, c], [0, b, c], [a, b, c] 
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
 
    def generate_solid_volume(resolution, atom_positions, T, r, a, b, c, plane_equation):  
        v1 = atom_positions[1]   
        v2 = atom_positions[2]   
        v3 = atom_positions[3]   

        nx, ny, nz = int(a * resolution), int(b * resolution), int(c * resolution)

        # Create grid in unit cube space
        u = np.linspace(0, 1, nx)
        v = np.linspace(0, 1, ny)
        w = np.linspace(0, 1, nz)
        uu, vv, ww = np.meshgrid(u, v, w, indexing='ij')  # shape: (nx, ny, nz)

        # Vectorized transformation into 3D space
        x = uu * v1[0] + vv * v2[0] + ww * v3[0]
        y = uu * v1[1] + vv * v2[1] + ww * v3[1]
        z = uu * v1[2] + vv * v2[2] + ww * v3[2]

        values = np.full_like(x, np.inf)

        for pos in atom_positions:
            sphere = bravais_function(x, y, z, pos, r)
            values = np.minimum(values, sphere)

        for normal, D in plane_equation.values():
            plane_val = np.round(normal[0]*x + normal[1]*y + normal[2]*z + D, 3)
            values[plane_val == 0] = -1

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
 
    atom_radius_range = np.arange(0.65, 0.78, 0.02) 

    atom_positions, T = Lattice_atom_positions(a, b, c, alpha, beta, gamma) 
 
    positions = np.array(atom_positions) 
    faces = { 
        'bottom' : (positions[0], positions[1], positions[4]),  
        'top' : (positions[7], positions[5], positions[3]),  
        'front' : (positions[1], positions[5], positions[7]), 
        'back' : (positions[6], positions[3], positions[0]), 
        'right' : (positions[1], positions[0], positions[3]), 
        'left' : (positions[7], positions[6], positions[2]), 
    } 
 
    plane_equation = {} 
    for face_name, vertices in faces.items(): 
        normal_vector, D = plane_from_points(*vertices) 
        plane_equation[face_name] = (normal_vector, D) 
 
    filename = f"24Inverse_Mono_{a:.1f}_{b:.1f}_{c:.1f}_{r:.2f}_{alpha}_{beta}_{gamma}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(resolution, atom_positions, T, r, a, b, c, plane_equation)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file