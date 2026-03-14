import numpy as np
from stl import mesh
from skimage import measure
import os
def Inverted_FKS(C,resolution = 200, folder='all_files'):
    def gyroid_function(x, y, z, scale=1, c=1.0):
        """FKS function."""
        return np.cos(2 * x * scale) * np.sin(y * scale) * np.cos(z * scale) + np.cos(x * scale) * np.cos(2 * y * scale) * np.sin(z * scale) + np.cos(2 * z * scale) * np.sin(x * scale) * np.cos(y * scale)-c

    def generate_solid_volume(size, resolution, scale, c):
        """Generate a mesh for the solid volume on one side of the gyroid surface within a cube."""
        x = np.linspace(-size / 2, size / 2, num=resolution)
        y = np.linspace(-size / 2, size / 2, num=resolution)
        z = np.linspace(-size / 2, size / 2, num=resolution)
        x, y, z = np.meshgrid(x, y, z)
        values = gyroid_function(x, y, z, scale, c)
        values[x == -size / 2] = -np.max(np.abs(values))
        values[x == size / 2] = -np.max(np.abs(values))
        values[y == -size / 2] = -np.max(np.abs(values))
        values[y == size / 2] = -np.max(np.abs(values))
        values[z == -size / 2] = -np.max(np.abs(values))
        values[z == size / 2] = -np.max(np.abs(values))
        verts, faces, _, _ = measure.marching_cubes(values, level=0)
        return verts, faces

    def create_and_invert_stl(verts, faces, folder, filename_base, c):
        """Create an STL file from vertices and faces, then create an inverted version and delete the original."""
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        filename = f"{filename_base}_c_{c:.1f}.stl"
        inverted_filename = f"{filename_base}_inverted_c_{c:.1f}.stl"
        full_path = os.path.join(folder, filename)
        inverted_full_path = os.path.join(folder, inverted_filename)
        
        # Create and temporarily save the original mesh
        solid_volume_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                solid_volume_mesh.vectors[i][j] = verts[f[j], :]
        solid_volume_mesh.save(full_path)

        # Invert the vectors to reverse the normals
        solid_volume_mesh.vectors[:, [0, 1]] = solid_volume_mesh.vectors[:, [1, 0]]
        solid_volume_mesh.update_normals()
        
        # Save the inverted mesh
        solid_volume_mesh.save(inverted_full_path)
        print(f"Inverted STL file saved as {inverted_full_path}")
        
        # Delete the original STL file
        os.remove(full_path)
        print(f"Deleted the original file: {full_path}")

    size = 10.0
    
    scale = 2 * np.pi / size
    filename = f"49Inverted_FKS_{resolution}"
    cached_file = os.path.join(folder, filename) 

    
    verts, faces = generate_solid_volume(size, resolution, scale, C)
    create_and_invert_stl(verts, faces, folder, filename, C)
    return cached_file