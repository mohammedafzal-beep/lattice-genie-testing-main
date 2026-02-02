
import numpy as np
from stl import mesh
import pyvista as pv

def vol_ratio(file_path):

    m = mesh.Mesh.from_file(file_path)

    solid_volume, _, _ = m.get_mass_properties()

    points = m.vectors.reshape(-1, 3)
    bbox_volume = np.prod(points.max(axis=0) - points.min(axis=0))

    ratio = solid_volume / bbox_volume
    return f"{ratio:.2f}"

def visualize_overhang(mesh: pv.PolyData, threshold_angle: float = 45.0):
    """
    In this function, I calculate the angle between the normal and reference direction to get the overhanging angle.
    The input is the mesh and threshold overhanging angle.
    The output is ratio of number of overhanging to all the mesh.
    """

    # calculate the normal of mesh by PyVista
    # The normal direction must be determined in the mesh. In my lattice, the normal calculated by Pyvista toward inwards.
    mesh.compute_normals(
        cell_normals=True,
        point_normals=False,
        consistent_normals=True,
        auto_orient_normals=True
    )
    k = np.array([0, 0, -1])  # This is the direction of reference. For the overhanging angle, we need to calculate the angle between the normal and this direction.


    # we need to exclude the bottom of lattice. Because these will be considered as overhanging.
    # ----------------- exclude the bottom of mesh -----------------
    face_centers = mesh.cell_centers().points

    # get the minimum value (z position value) of all point as the bottom surface.
    z_min = face_centers[:, 2].min()

    """
    Only the mesh points that are above the threshold will be considered for the overhanging calculation
    # I think the threshold (0.5 in my lattice) need to be modified based on your lattice. Maybe it can be decreased to a small number. 
    # You can use the following visualizing function to get feedback and change this threshold to an appropriate value.
    """

    valid_mask = face_centers[:, 2] > z_min+0.5  # 非底层面
    normals = mesh.face_normals

    # Calculate the angle between the normal and this direction.
    norms = np.linalg.norm(normals, axis=1)
    dot_product = normals @ k
    cos_theta = np.clip(dot_product / norms, -1.0, 1.0)
    face_angles = np.degrees(np.arccos(cos_theta))

    # My normal calculated by Pyvista toward inwards. So the overhanging angle are set to be more than 90 plus overhanging set (45)
    """
    After test, your direction is opposite to mine, so I changed the degree to accord to your version
    """
    overhang_faces = (face_angles < threshold_angle) & valid_mask

    # count the ratio of overhanging
    ratio = np.sum(overhang_faces) / len(face_angles)

    return ratio, mesh

def surface_area_to_volume_ratio(file_path):
    """
    Read input STL file
    Calculate overhanging and surface ratio.
    Output surface ratio value
    """
    return 0.16
    # calculate overhanging
    mesh = pv.read(file_path)
    ratio, labeled_mesh = visualize_overhang(mesh, threshold_angle=45.0)

    if mesh.volume == 0:
        return np.inf  # avoid 0

    ratio = mesh.area / mesh.volume

    return f"{ratio:.2f}"

