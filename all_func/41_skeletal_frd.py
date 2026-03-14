import numpy as np
from stl import mesh
from skimage import measure
import os
def Skeletal_FRD(C,  resolution = 200, folder='all_files'):
    def FRD_function(x, y, z, scale=1, c=1.0):
        return 4 * np.cos(x * scale) * np.cos(y * scale) * np.cos(z * scale) - np.cos(2 * x * scale) * np.cos(2 * y * scale) - np.cos(2 * y * scale) * np.cos(2 * z * scale) - np.cos(2 * z * scale) * np.cos(2 * x * scale)-c
        
    def generate_solid_volume(size, resolution, scale, c):
        x = np.linspace(-size / 2, size / 2, num=resolution)
        y = np.linspace(-size / 2, size / 2, num=resolution)
        z = np.linspace(-size / 2, size / 2, num=resolution)
        x, y, z = np.meshgrid(x, y, z)

        values = FRD_function(x, y, z, scale, c)
        values[x==-size / 2] = np.max(np.abs(values))
        values[x==size / 2] = np.max(np.abs(values))
        values[y==-size / 2] = np.max(np.abs(values))
        values[y==size / 2] = np.max(np.abs(values))
        values[z==-size / 2] = np.max(np.abs(values))
        values[z==size / 2] = np.max(np.abs(values))

        verts, faces, _, _ = measure.marching_cubes(values, level=0)
        return verts, faces

    def create_stl_from_mesh(verts, faces, folder, filename):

        if not os.path.exists(folder):
            os.makedirs(folder)

            # Full path for the file
        full_path = os.path.join(folder, filename)


        solid_volume_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                solid_volume_mesh.vectors[i][j] = verts[f[j], :]

        solid_volume_mesh.save(full_path)
        print(f"STL file saved as {full_path}")

    size = 10.0
  
    scale = 2 * np.pi / size
    c_values = np.arange(-0.9, 1.0, 0.1)  # Define the range for c
    filename = f"41Skeletal_FRD_{C:.1f}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

 
    verts, faces = generate_solid_volume(size, resolution, scale, C,)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file