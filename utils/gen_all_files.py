'''RUN THIS FILE FIRST TO POPULATE def AND crystal_img folders
'''

import os
import json
import importlib.util

# Your custom function mapping
func_dict = {
    1: "Cubic", 2: "Cubic_FCC", 3: "Cubic_BCC", 4: "Cubic_Ortho",
    5: "Ortho_BaseCent", 6: "Ortho_FCC", 7: "Ortho_BCC", 8: "Tetra",
    9: "Tetra_BCC", 10: "Mono", 11: "Mono_BaseCent", 12: "Triclinic",
    13: "Rhombo", 14: "Hexa", 15: "Inverse", 16: "Inverse_FCC",
    17: "Inverse_BCC", 18: "Inverse_Cubic_Ortho", 19: "Inverse_Ortho_BaseCent", 20:"Inverse_Ortho_FCC",
    21: "Inverse_Ortho_BCC", 22: "Inverse_Tetra", 23: "Inverse_Tetra_BCC", 24: "Inverse_Mono",
    25: "Inverse_Mono_BaseCent", 26: "Inverse_Triclinic", 27: "Inverse_Rhombo", 28: "Inverse_Hexa",
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

# Updating the dictionary
for key in func_dict:
    val = func_dict[key]
    lower_val = val.lower()
    new_path = f"all_func/{key}_{lower_val}.py"
    func_dict[key] = [val, new_path]

# Keys to run twice with different folders
run_twice_keys = {1, 22, 29, 36, 63}

# Folders to pass for those special cases
alt_folders = ["./def", "./crystal_img"]

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def extract_defaults(param_obj):
    """Flatten parameter dict by extracting `.default` values where applicable."""
    return {
        k: (v["default"] if isinstance(v, dict) and "default" in v else v)
        for k, v in param_obj.items()
    }

def call_function(key, func_name, file_path, raw_params, folder_value):
    # Import
    module_name = f"module_{key}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"❌ Failed to import {file_path}: {e}")
        return

    if not hasattr(module, func_name):
        print(f"❌ Function `{func_name}` not found in {file_path}")
        return

    func = getattr(module, func_name)

    # Extract defaults
    flat_params = extract_defaults(raw_params)

    if key==2:
        flat_params["r"] = 0.45  # Override radius to 0.65
    # Override resolution to 200
    flat_params["resolution"] = 200

    # Inject folder manually
    flat_params["folder"] = folder_value

    # Call
    print(f"🚀 Calling {func_name} from {file_path} with folder='{folder_value}'")
    try:
        func(**flat_params)
    except Exception as e:
        print(f"❗ Error calling `{func_name}`: {e}")

def main():
    param_dict = load_json("param_Dict.json")

    for key_str, raw_params in param_dict.items():
        try:
            key = int(key_str)
        except ValueError:
            print(f"⚠️ Skipping invalid key: {key_str}")
            continue

        if key not in func_dict:
            print(f"⚠️ No mapping found for key {key}")
            continue

        func_name, file_path = func_dict[key]

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue

        if key in run_twice_keys:
            for folder in alt_folders:
                call_function(key, func_name, file_path, raw_params, folder)
        else:
            call_function(key, func_name, file_path, raw_params, "def")

main()
