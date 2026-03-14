import numpy as np
from stl import mesh
from skimage import measure
import os
def Skeletal_Gyroid(C,  resolution = 200, folder='all_files'):
    def gyroid_function(x, y, z, scale=1, c=1.0):
        return np.sin(x * scale) * np.cos(y * scale) + np.sin(y * scale) * np.cos(z * scale) + np.sin(z * scale) * np.cos(x * scale)-c

    def generate_solid_volume(size, resolution, scale, c):
        x = np.linspace(-size / 2, size / 2, num=resolution)
        y = np.linspace(-size / 2, size / 2, num=resolution)
        z = np.linspace(-size / 2, size / 2, num=resolution)
        x, y, z = np.meshgrid(x, y, z)

        values = gyroid_function(x, y, z, scale, c)
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
    #c_values = np.arange(-1.3, 1.4, 0.1)  # Define the range for c

    # for c in c_values:
    #     verts, faces = generate_solid_volume(size, resolution, scale, c)
    #     filename = f"skeletal_TPMS_gyroid_{c:.1f}.stl"  # Format filename with the c value
    #     create_stl_from_mesh(verts, faces, folder, filename)


    filename = f"37Skeletal_Gyroid_{C:.1f}_{resolution}.stl"
    cached_file = os.path.join(folder, filename) 

    
    verts, faces = generate_solid_volume(size, resolution, scale, C,)
    create_stl_from_mesh(verts, faces, folder, filename) 
    return cached_file