import numpy as np
from stl import mesh
from skimage import measure
import os
import threading
MAX_TRIS_FOR_STEP = 50000
SNAP_TOL = 1e-6

def Sheet_Gyroid(C, direction, a1,a2, resolution = 200, folder='all_files'):
    
    
    V, F = generate_iso_mesh(size, resolution, scale, C, kind='g', mode='sheet')
    V = snap_to_cube_planes(V, SNAP_TOL)
    V, F = decimate_and_clean(V, F, MAX_TRIS_FOR_STEP)
    V, F = build_end_caps(V, F, tol=SNAP_TOL, kind='g', direction=direction,mode='sheet')
    rotate(V,a1,a2,0) 
    filename = f"30Sheet_Gyroid_{C:.2f}_{direction}_{a1}_{a2}.stl"  # Format filename with the c value
    cached_file = create_stl_from_mesh(V,F,folder,filename)
    return cached_file   def gyroid_function(x, y, z, scale=1, c=1.0):
      """Gyroid function."""
      return np.sin(x * scale) * np.cos(y * scale) + np.sin(y * scale) * np.cos(z * scale) + np.sin(z * scale) * np.cos(x * scale)-c

   def generate_solid_volume(size, resolution, scale, c, t):
      """Generate a mesh for the solid volume on one side of the gyroid surface within a cube."""
      # Create a 3D grid
      x = np.linspace(-size / 2, size / 2, num=resolution)
      y = np.linspace(-size / 2, size / 2, num=resolution)
      z = np.linspace(-size / 2, size / 2, num=resolution)
      x, y, z = np.meshgrid(x, y, z)

      # Evaluate the Gyroid function
      values = gyroid_function(x, y, z, scale, c)
      values1 = -gyroid_function(x, y, z, scale, c-t)
      # # Modify values outside the cube to ensure one space is solid
      values[np.sin(x * scale) * np.cos(y * scale) + np.sin(y * scale) * np.cos(z * scale) + np.sin(z * scale) * np.cos(x * scale)<=c-t] =\
      values1[np.sin(x * scale) * np.cos(y * scale) + np.sin(y * scale) * np.cos(z * scale) + np.sin(z * scale) * np.cos(x * scale)<=c-t]
      values[(np.sin(x * scale) * np.cos(y * scale) + np.sin(y * scale) * np.cos(z * scale) + np.sin(z * scale) * np.cos(x * scale)>c-t) &
      (np.sin(x * scale) * np.cos(y * scale) + np.sin(y * scale) * np.cos(z * scale) + np.sin(z * scale) * np.cos(x * scale)<=c-t/2)] \
      = values1[(np.sin(x * scale) * np.cos(y * scale) + np.sin(y * scale) * np.cos(z * scale) + np.sin(z * scale) * np.cos(x * scale)>c-t) &
      (np.sin(x * scale) * np.cos(y * scale) + np.sin(y * scale) * np.cos(z * scale) + np.sin(z * scale) * np.cos(x * scale)<=c-t/2)] 

      values[x==-size / 2] = np.max(np.abs(values))
      values[x==size / 2] = np.max(np.abs(values))
      values[y==-size / 2] = np.max(np.abs(values))
      values[y==size / 2] = np.max(np.abs(values))
      values[z==-size / 2] = np.max(np.abs(values))
      values[z==size / 2] = np.max(np.abs(values))
      
      # Extract the isosurface that represents the solid volume
      verts, faces, _, _ = measure.marching_cubes(values, level=0)

      return verts, faces

   def create_stl_from_mesh(verts, faces, folder, filename="Sheet_Gyroid.stl"):
      """Create an STL file from vertices and faces."""
      if not os.path.exists(folder):
         os.makedirs(folder)
      # Full path for the file
      full_path = os.path.join(folder, filename)
      # Create the mesh
      solid_volume_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
      for i, f in enumerate(faces):
         for j in range(3):
            solid_volume_mesh.vectors[i][j] = verts[f[j], :]
      # Write the mesh to an STL file
      solid_volume_mesh.save(full_path)
      print(f"STL file saved as {full_path}")

   size = 10.0  # Spatial size
    # Grid resolution
   scale = 2 * np.pi / size  # Scale of the gyroid pattern

   #t_values = np.linspace(0.05, 2.7, 10)  # For example, iterating over t from 0.1 to 1.0 in 10 steps
   filename = f"30Sheet_Gyroid_{C:.1f}_{t:.1f}_{resolution}.stl"
   cached_file = os.path.join(folder, filename) 

   verts, faces = generate_solid_volume(size, resolution, scale, C, t)
   create_stl_from_mesh(verts, faces, folder, filename) 
   return cached_file

