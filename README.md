# Lattice Genie

Lattice Genie is an interactive Streamlit-based application for generating, visualizing, and downloading a wide variety of 3D lattice structures (STL files) for research, engineering, and educational purposes. Users can explore Bravais lattices, inverse lattices, strut-based, sheet-based, and skeletal TPMS structures, configure parameters, and preview STL models in-browser.

## Features

- **Interactive Chat**: Guide users to select and configure lattice structures via a chat interface.
- **Parameter Sliders**: Dynamically adjust lattice parameters (e.g., lattice constants, angles, radii, resolution).
- **STL Preview**: Render and interact with 3D STL models directly in the browser.
- **Download STL**: Download generated STL files for use in CAD or 3D printing.
- **Rich Structure Library**: Includes Bravais, inverse, strut-based, sheet-based, and skeletal TPMS lattices.
- **Responsive UI**: STL previews and UI elements adapt to window resizing.

## Project Structure

```
.
├── app.py / main.py         # Entrypoint for Streamlit app
├── appv8.py                # Main Streamlit application logic
├── components/             # UI and chat components
├── all_func/               # Lattice generation functions (Python, STL output)
├── utils/                  # Utility functions (e.g., sliders, STL cleanup)
├── page/                   # Page rendering logic
├── all_files/              # Generated STL files (output)
├── def/, img/, crystal_img/ # STL and image assets
├── param_Dict.json         # Parameter schema for all lattice types
├── subtype_info.json       # Metadata for lattice subtypes
├── crystal_images.json     # Image paths for lattice categories
├── desc_dict.json          # Parameter descriptions
├── instruction.txt         # System prompt and instructions
├── req.txt                 # Python dependencies
└── README.md               # (This file)
```

## Installation

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd LATTICE_GENIE
   ```

2. **Install dependencies:**
   ```sh
   pip install -r req.txt
   ```

3. **Populate def/ and crystal_img/ folders**
   ```sh
   python gen_all_files.py
   ```

4. **Run the app:**
   ```sh
   streamlit run main.py
   ```   

## Usage

- **Home Page:** Browse lattice categories and preview representative structures.
- **Chat:** Ask for a lattice type or describe desired mechanical properties. The assistant will guide you to the right structure.
- **Parameter Adjustment:** Use sliders in the sidebar to fine-tune lattice parameters.
- **STL Preview & Download:** View the generated STL in 3D and download it for further use.

## Notes

- Temporary STL files are cleaned up automatically on exit.
- All parameter schemas and descriptions are defined in JSON files for easy extension.

## Requirements

- Python 3.8+
- See [req.txt](req.txt) for required packages.

## License

This project is for research and educational use. See LICENSE for details.

---

**Developed by:** Prof. Binyang Song, Afzal
