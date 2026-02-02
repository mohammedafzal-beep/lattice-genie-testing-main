import numpy as np
from skimage import measure
from stl import mesh
import os
def Truss_BFCC(d=0.05,  resolution = 200 , folder='all_files'):
    def cylinder_function(x, y, z, point1, point2, r):
        x1, y1, z1 = point1
        x2, y2, z2 = point2
        a = x2 - x1
        b = y2 - y1
        c = z2 - z1
        v = np.array([a, b, c])
        norm_v = np.linalg.norm(v)
        if norm_v == 0:
            return (x - x1)**2 + (y - y1)**2 + (z - z1)**2 - r**2
        else:
            return ((y - y1)*c - (z - z1)*b)**2 + ((z - z1)*a - (x - x1)*c)**2 + ((x - x1)*b - (y - y1)*a)**2 - r**2 * norm_v**2


    def generate_solid_volume(size, resolution, edges, r):
        x = np.linspace(0, size, num=resolution)
        y = np.linspace(0, size, num=resolution)
        z = np.linspace(0, size, num=resolution)
        x, y, z = np.meshgrid(x, y, z, indexing='ij')

        values = np.full(x.shape, np.inf)
        for point1, point2 in edges:
            cylinder_vals = cylinder_function(x, y, z, point1, point2, r)
            values = np.minimum(values, cylinder_vals)

        
        values[x==0] = 1
        values[x==size] = 1
        values[y==0] = 1
        values[y==size] = 1
        values[z==0] = 1
        values[z==size] = 1

        verts, faces, _, _ = measure.marching_cubes(values, level=0)
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

    # Parameters
    r_range = np.linspace(0.05, 0.15, 10)
   
    a,b,c=1,1,1
    alpha, beta, gamma = 90, 90, 90  # Angles in degrees
    alpha_rad, beta_rad, gamma_rad = np.radians([alpha, beta, gamma])
    T = np.array([
        [a, 0, 0],
        [b * np.cos(gamma_rad), b * np.sin(gamma_rad), 0],
        [c * np.cos(beta_rad), c * (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad),
        c * np.sqrt(1 + 2 * np.cos(alpha_rad) * np.cos(beta_rad) * np.cos(gamma_rad) - np.cos(alpha_rad)**2 - np.cos(beta_rad)**2 - np.cos(gamma_rad)**2) / np.sin(gamma_rad)]
    ])


    unit_edges = [
        ((0, 0, 0), (0.5, 0.5, 0.5)), ((0.5, 0.5, 0), (0.5, 0.5, 0.5)),
        ((1, 0, 0), (0.5, 0.5, 0.5)), ((0.5, 0, 0.5), (0.5, 0.5, 0.5)),
        ((0, 1, 0), (0.5, 0.5, 0.5)), ((0, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ((0, 0, 1), (0.5, 0.5, 0.5)), ((0.5, 0.5, 1), (0.5, 0.5, 0.5)),
        ((1, 1, 0), (0.5, 0.5, 0.5)), ((0.5, 1, 0.5), (0.5, 0.5, 0.5)),
        ((1, 0, 1), (0.5, 0.5, 0.5)), ((1, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ((0, 1, 1), (0.5, 0.5, 0.5)), 
        ((1, 1, 1), (0.5, 0.5, 0.5)),
    ]
    edges = [(np.dot(T, point1), np.dot(T, point2)) for point1, point2 in unit_edges]

    filename = f"52Truss_BFCC_{d:.2f}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 


    verts, faces = generate_solid_volume(max(T.flatten()), resolution, edges, d)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file