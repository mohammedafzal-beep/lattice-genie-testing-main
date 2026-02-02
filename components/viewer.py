import streamlit as st
from streamlit_stl import stl_from_file

from utils.utils import backup


def show_stl_thumbnail_page(name, img_path, page=None):
    """
    Renders a rotating STL thumbnail for a given lattice/type page, using a
    per-page/per-structure camera distance override when available, then backs
    up the rendered output.

    Args:
        name: Structure name used to select camera settings within the page.
        img_path: Sequence where the STL file path is expected at index 0.
        page: Optional page/category name used to select camera settings.
    """
    cam_settings = {
        "Bravais": {
            "Rhombohedral": 640,
            "Simple Monoclinic": 500,
            "Triclinic": 500,
            "Hexagonal": 0,
            "Simple Orthorhombic": 0,
            "Face-Centered Orthorhombic": 450,
            "Body-Centered Orthorhombic": 500,
            "Body-Centered Tetragonal": 450,
            "Simple Tetragonal": 450,
        },
        "Inverse Bravais": {
            "Hexagonal": 500,
            "Rhombohedral": 550,
            "Simple Cubic": 350,
            "Face-Centered Orthorhombic": 0,
        },
    }

    # Default camera distance unless overridden by the (page, name) lookup above.
    cam_distance = 400
    if page in cam_settings and name in cam_settings[page]:
        cam_distance = cam_settings[page][name]

    display = stl_from_file(
        img_path[0],
        color="#336fff",
        auto_rotate=True,
        cam_distance=cam_distance,
        max_view_distance=1500,
        width=225,
        height=225,
        cam_h_angle=45,
        cam_v_angle=75,
    )
    backup(display, img_path)


def show_stl_thumbnail_home(name, img_path, page=None):
    """
    Renders a rotating STL thumbnail for the home view, using a camera distance
    override based on the structure/category name when available, then backs up
    the rendered output.

    Args:
        name: Structure/category name used to select camera settings.
        img_path: Sequence where the STL file path is expected at index 0.
        page: Unused optional parameter kept for API consistency.
    """
    cam_settings = {
        "Inverse Bravais": 388,
        "Sheet TPMS": 388,
    }

    # Default camera distance unless overridden by the name lookup above.
    cam_distance = 476
    if name in cam_settings:
        cam_distance = cam_settings[name]

    display = stl_from_file(
        img_path[0],
        color="#336fff",
        auto_rotate=True,
        cam_distance=cam_distance,
        max_view_distance=1500,
        width=225,
        height=225,
        cam_h_angle=45,
        cam_v_angle=75,
        shininess=0.3,
    )
    backup(display, img_path)
