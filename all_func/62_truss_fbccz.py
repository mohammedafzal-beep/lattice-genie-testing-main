import numpy as np
from skimage import measure
from stl import mesh
import os
def Truss_FBCCZ(a=1.,b=1.,c=1.,alpha=90,beta=90,gamma=90,d=0.05,resolution = 200, folder='all_files'):
       
    # Define the cylinder function
    def cylinder_function(x, y, z, point1, point2, r):
        x1, y1, z1 = point1[0], point1[1], point1[2]
        x2, y2, z2 = point2[0], point2[1], point2[2]
        a = x2 - x1
        b = y2 - y1
        c = z2 - z1
        v = np.array([a, b, c])
        norm_v = np.linalg.norm(v)
        if norm_v == 0:
            return (x - x1)**2 + (y - y1)**2 + (z - z1)**2 - r**2
        else:
            return ((y - y1)*c - (z - z1)*b)**2 + ((z - z1)*a - (x - x1)*c)**2 + ((x - x1)*b - (y - y1)*a)**2 - r**2 * norm_v**2

    # Define the function to generate the solid volume
    def generate_solid_volume(size, resolution, vertices, r):
        """Generate a mesh for the solid volume."""
        # Create a 3D grid
        x = np.linspace(0, size, num=resolution)
        y = np.linspace(0, size, num=resolution)
        z = np.linspace(0, size, num=resolution)
        x, y, z = np.meshgrid(x, y, z, indexing='ij')

        # Initialize the scalar field
        values = np.full(x.shape, np.inf)

        # Connect corner atoms to their immediate next atoms along the edges

        body_diagonals = [ 
            (4, 3), (1, 6),  
            (0, 7), (5, 2)
        ]

        face_diagonals = [ 
            (6, 3), (7, 2),  
            (4, 1), (0, 5),
            (5, 3), (7, 1),  
            (4, 2), (0, 6)
        ]
        

        # Apply cylinder influence for each edge
        for start_index, end_index in face_diagonals + body_diagonals:
            start_pos = vertices[start_index]
            end_pos = vertices[end_index]
            values = np.minimum(values, cylinder_function(x, y, z, start_pos, end_pos, r))
            
        # Apply boundary conditions to enclose the structure
        values[x==0] = 1
        values[x==size] = 1
        values[y==0] = 1
        values[y==size] = 1
        values[z==0] = 1
        values[z==size] = 1

        # Extract the isosurface that represents the solid volume
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
    


    alpha_rad = np.deg2rad(alpha)
    beta_rad = np.deg2rad(beta)
    gamma_rad = np.deg2rad(gamma)
    T = np.array([
        [a, 0, 0],
        [b * np.cos(gamma_rad), b * np.sin(gamma_rad), 0],
        [c * np.cos(beta_rad), c * (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad),
        c * np.sqrt(1 + 2 * np.cos(alpha_rad) * np.cos(beta_rad) * np.cos(gamma_rad) - np.cos(alpha_rad)**2 - np.cos(beta_rad)**2 - np.cos(gamma_rad)**2) / np.sin(gamma_rad)]
    ])

    # Define the vertices of the unit cube
    unit_vertices = np.array([
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
        [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1], 
        [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5],  # Bottom and sides
        [0.5, 0.5, 1], [0.5, 1, 0.5], [1, 0.5, 0.5],
    ])

    vertices = np.dot(unit_vertices, T.T)

    filename = f"62Truss_FBCCZ_{d:.2f}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

    verts, faces = generate_solid_volume(max(T.flatten()), resolution, vertices, d)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file