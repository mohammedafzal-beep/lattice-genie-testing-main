"""
Lattice Genie Utilities Module
------------------------------

This module provides utility functions and UI components for the Lattice Genie Streamlit app,
which dynamically generates STL files for various lattice structures based on user-defined parameters.

Includes:
- STL cleanup
- Parameter sliders with dynamic ranges
- Dynamic function importing
- STL generation wrapper
"""

import importlib
import os
import glob
import streamlit as st
from PIL import Image
from streamlit_stl import stl_from_file
import streamlit.components.v1 as components
import json
from openai import OpenAI
import datetime
from stl import mesh
import numpy as np
from utils.dataloader import log_event
from utils.dataloader import log_to_drive,log_close_app, process_log_submission
def clear_temporary_log():
    src_path = '.logs/log_slider_changes_temporary.jsonl'
        # Read the existing content (if any)
    with open(src_path, 'r', encoding='utf-8') as src_file:
        content = src_file.read()

    # Clear the original file
    open(src_path, 'w').close()

# --- Delete all STL files in the 'all_files/' directory to ensure a clean state before generation ---
def cleanup_stl_files_and_update_drive():
    for f in glob.glob("all_files/*.stl"):
        try:
            os.remove(f)
        except Exception as e:
            print(f"Could not delete {f}: {e}")
    
    clear_temporary_log()

    ALL_LOGS, CHAT_HISTORY = '.logs/all_logs.jsonl', '.logs/chat_history.jsonl'
    BUTTON_HISTORY = '.logs/button_history.jsonl'
    LOG_SLIDER_CHANGES_PERMANENT = '.logs/log_slider_changes_permanent.jsonl'
    LOG_SUBMISSION = '.logs/log_submission.jsonl'
    LOG_SUBMISSION_FINAL = '.logs/log_submission_final.jsonl'

    LOG_FILES_LIST = [ALL_LOGS, CHAT_HISTORY, BUTTON_HISTORY, LOG_SLIDER_CHANGES_PERMANENT, 
    LOG_SUBMISSION, LOG_SUBMISSION_FINAL]

    process_log_submission()
    ALL_LOGS_drive, CHAT_HISTORY_drive = "1eTJ0qRUJNLrlHkS9uZkc5UbTr5Ax5vxQ", "1ojmP_z1W1Q41velLHAjmhL1XmN-Sz7xt"
    BUTTON_HISTORY_drive = '1GU9Wg2bDDt2zhjqZNodwKr4oZeK-5_RB'
    LOG_SLIDER_CHANGES_PERMANENT_drive = '1jjcXv9vuy07ED1NSjJsdgP4NrgYk0bru'
    LOG_SUBMISSION_DRIVE = '1g8LWArYUFgTE0Js4DgUM9ei9gMvA5vDG'
    LOG_SUBMISSION_FINAL_drive = '1DpmkvIHFNmHfxnjzYmbflKNfKRp2vI19'

    DRIVE_FILES_LIST = [ALL_LOGS_drive, CHAT_HISTORY_drive, BUTTON_HISTORY_drive, 
    LOG_SLIDER_CHANGES_PERMANENT_drive, LOG_SUBMISSION_DRIVE, LOG_SUBMISSION_FINAL_drive]
    
    
    for i in range(len(LOG_FILES_LIST)):
        log_to_drive(LOG_FILES_LIST[i], DRIVE_FILES_LIST[i])
        print(f"{DRIVE_FILES_LIST[i]} updated")
    print("drive jsonl files updated")
# --- Display a fallback image if STL rendering fails ---
def backup(display, img_path):
    if not display:
        st.image(Image.open(img_path[1]).resize((256, 256)), use_container_width=True)



def surface_area_to_volume_ratio(stl_file_path):
    """
    Calculate the surface area to volume ratio of a 3D mesh from an STL file.

    Parameters
    ----------
    stl_file_path : str
        Path to the STL file.

    Returns
    -------
    dict
        A dictionary containing surface area, volume, and surface area to volume ratio.
    """
    # Load the mesh from file
    model_mesh = mesh.Mesh.from_file(stl_file_path)

    # Calculate surface area
    surface_area = np.sum(model_mesh.areas)

    # Calculate volume
    # The signed volume of a triangular mesh can be computed from:
    # V = (1/6) * sum((v0 × v1) · v2)
    vectors = model_mesh.vectors
    cross_prod = np.cross(vectors[:, 1] - vectors[:, 0], vectors[:, 2] - vectors[:, 0])
    volume = np.abs(np.sum(np.einsum('ij,ij->i', vectors[:, 0], cross_prod)) / 6.0)

    # Avoid division by zero
    if volume == 0:
        ratio = np.inf
    else:
        ratio = surface_area / volume

    return ratio

# Example usage:
# result = surface_area_to_volume_ratio("example.stl")
# print(result)

# --- Slider UI component that supports both static and C-dependent dynamic ranges ---
def labeled_slider(param_key, cfg, current_params):
  # Define all supported dynamic range functions
  
  def body_atom_radius_range(r):
    radius_range_map = {0.33: (0.545, 0.595, 0.01), 0.34: (0.535, 0.585, 0.01), 0.35: (0.525, 0.585, 0.01), 0.36: (0.515, 0.575, 0.01), 0.37: (0.505, 0.575, 0.01), 0.38: (0.495, 0.565, 0.01), 0.39: (0.485, 0.565, 0.01), 0.4: (0.475, 0.555, 0.01), 0.41: (0.465, 0.555, 0.01), 0.42: (0.455, 0.545, 0.01), 
0.43: (0.445, 0.545, 0.01), 0.44: (0.445, 0.545, 0.01), 0.45: (0.455, 0.535, 0.01), 0.46: (0.465, 0.535, 0.01), 0.47: (0.475, 0.525, 0.01), 
0.48: (0.485, 0.525, 0.01), 0.49: (0.495, 0.525, 0.01), 0.5: (0.505, 0.515, 0.01)}
    return radius_range_map[r]

  def face_atom_radius_range(r):
    radius_range_map = {0.4: (0.315, 0.415, 0.01), 0.41: (0.305, 0.415, 0.01), 0.42: (0.295, 0.395, 0.01), 0.43: (0.285, 0.385, 0.01), 0.44: (0.275, 0.365, 0.01), 
0.45: (0.265, 0.355, 0.01), 0.46: (0.255, 0.345, 0.01), 0.47: (0.245, 0.325, 0.01), 0.48: (0.235, 0.315, 0.01), 0.49: (0.225, 0.295, 0.01), 
0.5: (0.215, 0.285, 0.01), 0.51: (0.205, 0.275, 0.01), 0.52: (0.205, 0.255, 0.01), 0.53: (0.205, 0.245, 0.01), 0.54: (0.205, 0.225, 0.01), 0.55: (0.205, 0.215, 0.01), 0.56: (0.205, 0.205, 0.01)}
    return radius_range_map[r]

  RANGE_FUNC_MAP = {
      "body_atom_radius_range": body_atom_radius_range,
      "face_atom_radius_range": face_atom_radius_range,
  }

  # Units for each param
  unit_map = {
      "a": "Å", "b": "Å", "c": "Å", "r": "Å", "C": "Å", "t": "Å", "d": "Å",
      "face_atom_radius": "Å", "center_atom_radius": "Å",
      "alpha": "°", "beta": "°", "gamma": "°", "resolution": ""
  }

  # Display names (Greek where applicable)
  greek_map = {
  "alpha":              "Rotation along a axis (α in degrees)",
  "beta":               "Rotation along b axis (β in degrees)",
  "gamma":              "Rotation along c axis (γ in degrees)",
  "face_atom_radius":   "Face atom radius",
  "a": "Edge length a",
  "b": "Edge length b",
  "c": "Edge length c",
  "C": "Level set constant C",
  "t": "Sheet thickness t",
  "d": "Distance between sheets d",
  "r": "Atomic radius",
  "center_atom_radius": "Center atom radius",
  "resolution": "Mesh resolution",
}


  # Tooltip descriptions
  descriptions_dict = {
      'a': 'Lattice constant',
      'b': 'Lattice constant',
      'c': 'Lattice constant',
      'C': 'Influences the volume fraction',
      't': 'Sheet thickness',
      'd': 'Strut diameter',
      'r': 'Radius of the spheres at the corners of the unit cell',
      'alpha': 'Angle between b and c',
      'beta': 'Angle between a and c',
      'gamma': 'Angle between a and b',
      'face_atom_radius': 'Radius of atoms at face centers in FCC',
      'centre_atom_radius': 'Radius of center atom in BCC',
      'resolution': 'Number of pixels used',
  }


  # Render label with unit and tooltip
  unit = unit_map.get(param_key, "")
  display_key = greek_map.get(param_key, param_key)
  label = f"{display_key} ({unit})" if unit else f"{display_key}"
  help_text = descriptions_dict.get(param_key, "")


  # Handle dynamic range functions (e.g., t depends on C)
  if "range_func" in cfg:
      range_func = cfg["range_func"]
      if isinstance(range_func, str):
          range_func = RANGE_FUNC_MAP.get(range_func)
      if not callable(range_func):
          st.warning(f"Invalid range_func for {param_key}")
          return None
      if 'C' in current_params:
        C_val = current_params.get("C")

        min_val, max_val, step = range_func(C_val)
      else:
            r = current_params.get('r')
            min_val, max_val, step = range_func(r)
      
  else:
      # Static range
      min_val = cfg.get("min")
      max_val = cfg.get("max")
      step = cfg.get("step", 0.01)
 
  if param_key == 'direction':
    return st.sidebar.selectbox("Direction", ('normal','reverse'))
  
  default_val = cfg.get("default")
  prev_val = st.session_state.get(param_key, current_params.get(param_key, default_val))
  clamped_val = max(cfg.get("min"), min(prev_val, cfg.get("max")))
  st.session_state[param_key] = clamped_val  # store current value
  st.markdown("""
<style>
/* Slider label spacing */
div[data-testid="stSlider"] label {
    margin-bottom: 12px;

</style>
""", unsafe_allow_html=True)
  return st.sidebar.slider(
        label=label,
        min_value=min_val,
        max_value=max_val,
        value=default_val,
        step=step,
        key=param_key,
        help=help_text,
        label_visibility="visible"
    )


# --- Compute a clamped max to ensure range endpoints align with slider steps ---
def get_adjusted_max(min_val, max_val, step):
    k = int((max_val - min_val) // step)
    return min_val + k * step

# --- Dynamically import a function (e.g., structure generator) from a module in a folder ---
def dynamic_import(folder_name: str, module_name: str, variable_name: str):
    module_path = f"{folder_name}.{module_name}"
    module = importlib.import_module(module_path)
    return getattr(module, variable_name)
"""
# --- Initialize session state for the app ---
def init_state():
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'confirmed_params' not in st.session_state:
        st.session_state['confirmed_params'] = None
    if 'stl_path' not in st.session_state:
        st.session_state['stl_path'] = None
    if 'last_assistant_msg' not in st.session_state:
        st.session_state['last_assistant_msg'] = None"""

# --- Generate STL file using structure-specific generation function ---
def generate_stl(dict_key, params):
    # Maps structure key to its function name (used to dynamically import and call)
    func_dict = {
        1: "Cubic", 2: "Cubic_FCC", 3: "Cubic_BCC", 4: "Cubic_Ortho",
        5: "Ortho_BaseCent", 6: "Ortho_FCC", 7: "Ortho_BCC", 8: "Tetra",
        9: "Tetra_BCC", 10: "Mono", 11: "Mono_BaseCent", 12: "Triclinic",
        13: "Rhombo", 14: "Hexa", 15: "Inverse", 16: "Inverse_FCC",
        17: "Inverse_BCC", 18: "Inverse_Cubic_Ortho", 19: "Inverse_Ortho_BaseCent", 20: "Inverse_Ortho_FCC",
        21: "Inverse_Ortho_BCC", 22: "Inverse_Tetra", 23: "Inverse_Tetra_BCC", 24: "Inverse_Mono",
        25: "Inverse_Mono_BaseCent", 26: "Inverse_Rhombo", 27: "Inverse_Triclinic", 28: "Inverse_Hexa",
        29: "Sheet_Primitive", 30: "Sheet_Gyroid", 31: "Sheet_Diamond", 32: "Sheet_IWP",
        33: "Sheet_FKS", 34: "Sheet_FRD", 35: "Sheet_Neovius", 36: "Skeletal_Primitive",
        37: "Skeletal_Gyroid", 38: "Skeletal_Diamond", 39: "Skeletal_IWP", 40: "Skeletal_FKS",
        41: "Skeletal_FRD", 42: "Skeletal_Neovius", 43: "Inverted_Diamond", 44: "Inverted_FRD",
        45: "Inverted_Gyroid", 46: "Inverted_IWP", 47: "Inverted_Neovius", 48: "Inverted_Primitive",
        49: "Inverted_FKS", 50: "Truss_Cubic", 51: "Truss_BCC", 52: "Truss_BFCC",
        53: "Truss_Octet", 54: "Truss_AFCC", 55: "Truss_Iso", 56: "Truss_BCCZ",
        57: "Truss_Tetra", 58: "Truss_FCC", 59: "Truss_FCCZ", 60: "Truss_G7",
        61: "Truss_Octa", 62: "Truss_FBCCZ", 63: "Truss_FBCCXYZ",
    }

    #try:
    func_name = func_dict.get(int(dict_key))
    """if not func_name:
        st.error("Invalid structure key.")
        return None"""
    # Import the structure function dynamically from its module
    func = dynamic_import('all_func', f'{dict_key}_' + func_name.lower(), func_name)
    filepath = func(**params)
    return filepath
def subtype_selection_to_dict_key(data):
    # data: full data dict from data.json
      # returns dict_key for the selected type/subtype in session_state
  subtypes_info = data.get("subtypes_info", {})
  types = {}
  global_count = 1
  for type,subtypes_info in subtypes_info.items():
      local_count= 0
      subtype_list=subtypes_info['items']
      
      for local_count in range(len(subtype_list)):
          subtype = subtype_list[local_count][0]
          types.setdefault(type, {})[subtype] = global_count
          local_count+=1
          global_count+=1
  type_list = list(types.keys()) if types else ['Unknown']
  
  selected_type = st.selectbox('Structure type', type_list, index=0)
  if 'selected_type_list' not in st.session_state:
     st.session_state['selected_type_list'] = []
  if 'selected_subtype_list' not in st.session_state:
     st.session_state['selected_subtype_list'] = []
  subtype_list = list(types.get(selected_type, {}).keys()) if types.get(selected_type) else ['Default']
  selected_subtype = st.selectbox('Subtype', subtype_list, index=0)

  # derive dict_key
  dict_key = types[selected_type][selected_subtype]
  st.session_state['selected_type'] = selected_type
  st.session_state['selected_subtype'] = selected_subtype
  st.session_state['selected_dict_key'] = dict_key
  

  if len(st.session_state['selected_type_list']) >= 1:
    if st.session_state['selected_subtype'] != st.session_state['selected_subtype_list'][-1] or \
              st.session_state['selected_type'] != st.session_state['selected_type_list'][-1]:
      st.session_state['selected_subtype_list'].append(st.session_state['selected_subtype'])
      st.session_state['selected_type_list'].append(st.session_state['selected_type'])
      log_event(f"Selected type: {st.session_state['selected_type_list'][-1]}", "Pro Mode")
      log_event(f"Selected subtype: {st.session_state['selected_subtype_list'][-1]}", "Pro Mode")
  else:
    st.session_state['selected_subtype_list'].append(st.session_state['selected_subtype'])
    st.session_state['selected_type_list'].append(st.session_state['selected_type'])
    log_event(f"Selected type: {st.session_state['selected_type_list'][-1]}", "Pro Mode")
    log_event(f"Selected subtype: {st.session_state['selected_subtype_list'][-1]}", "Pro Mode")
