
import streamlit as st
from utils.utils import labeled_slider,generate_stl
from utils.dataloader import log_event,log_slider_changes
import time
from utils.S_V_ratio import surface_area_to_volume_ratio, vol_ratio
from utils.dataloader import log_submission

def show_parameter_sliders(data,mode):
    if mode == 'Pro mode':
            dict_key = st.session_state['selected_dict_key']
    else:
        dict_key = int(st.session_state['dict_key'])
    
    with st.sidebar:
    
        with st.columns([2,6,1])[1]:
            st.markdown(
    "<h2 style=' color: #007BFF; font-size: 28px;'>Adjust parameters</h2>",
    unsafe_allow_html=True
    )
        st.session_state['struc_name'] = st.empty()
        with st.columns([2.74,6,1])[1]:
            button_placeholder = st.empty()

        with st.columns([1.4,7,1])[1]:   
            st.session_state['spinner'] = st.empty()
        
        with st.columns([1,13,1])[1]: 
            st.session_state['Scroll message'] = st.empty()

        with st.columns([1,13,1])[1]: 
            st.session_state['Struc error'] = st.empty()
        
        st.session_state['S_V_ratio'] = st.empty()
# Reserve space for the button right under the heading
        
        # --- Sliders ---
        struc_name = data['dict_key_map'].get(dict_key, 'Unknown Structure')
        with st.session_state['struc_name']:
                
                    # HTML with red dot if button not pressed
                st.markdown(f"""
            <div style="position: relative; display: inline-block; margin-bottom: 8px;">
                <h4 style="margin:0;">{struc_name}</h4>
                {(
                    "<span class='pulse-dot'></span>"
                ) }
            </div>

            <style>
            .pulse-dot {{
                position: absolute;
                top: 0;
                right: -10px;
                height: 12px;
                width: 12px;
                background: radial-gradient(circle, red, darkred);
                border-radius: 50%;
                display: inline-block;
                animation: pulse 1s infinite;
            }}

            @keyframes pulse {{
                0% {{ transform: scale(1); opacity: 1; }}
                50% {{ transform: scale(1.5); opacity: 0.6; }}
                100% {{ transform: scale(1); opacity: 1; }}
            }}
            </style>
            """, unsafe_allow_html = True)
        # Track which structure is currently shown
        if "last_dict_key" not in st.session_state:
            st.session_state["last_dict_key"] = None
        if "button_pressed" not in st.session_state:
            st.session_state["button_pressed"] = False

        # If the structure changed, reset button_pressed
        if st.session_state["last_dict_key"] != dict_key:
            st.session_state["button_pressed"] = False
            st.session_state["last_dict_key"] = dict_key
        
    
        schema = data["params_dict"].get(dict_key, 1)
        
        current_params = {}
        for param_key in schema:
            val = labeled_slider(param_key, schema[param_key], current_params)
            current_params[param_key] = val
        
        st.session_state['current_params'] = current_params
        log_slider_changes(current_params, mode)
        
        with st.session_state['spinner']:
            st.markdown(
"""
<div style="display:flex; align-items:center; gap:13px;">
<div class="loader" aria-hidden="true"></div>
<div style="font-size:19px; font-weight:600; color:#3366ff;">Generating STL</div>
</div>

<style>
:root{
--spinner-size: 36px;        /* overall outer diameter */
--spinner-thickness: 6px;    /* border width -> controls inner hole size */
--spinner-color: #3366ff;
--spinner-bg: rgba(0,0,0,0.08);
}

/* Spinner */
.loader {
width: var(--spinner-size);
height: var(--spinner-size);
border-radius: 50%;
box-sizing: border-box;                 /* include border in width/height */
border: var(--spinner-thickness) solid var(--spinner-bg); /* ring background */
border-top-color: var(--spinner-color); /* colored arc */
flex-shrink: 0;                         /* prevent sidebar from squishing it */
display: inline-block;
line-height: 0;
animation: spin 1s linear infinite;
transform-origin: center center;
}

/* optional: slightly smoother anti-aliasing for some browsers */
.loader { -webkit-backface-visibility: hidden; backface-visibility: hidden; }

/* spin animation */
@keyframes spin {
to { transform: rotate(360deg); }
}
</style>
""",
unsafe_allow_html=True
)

        path = generate_stl(dict_key, current_params)
        if path == 0:
            with st.session_state['Struc error']:
                st.markdown("<p style='font-size:17px'>❌ Generation is not possible with the set parameter values <br> \
                Please avoid extreme angle values (eg: 1, 360 etc) </p> ", unsafe_allow_html= True)
            else:
            with st.session_state['S_V_ratio']:
                st.markdown(f"""
    <div style="
        color: #ffffff;
        font-size: 19px;
        text-align: left;
        margin-bottom: 20px;
    ">
        <span style="font-weight: 600;">Volume Ratio (VR):</span>
        <span style="
            display: inline-block;
            padding: 4px 10px;
            background: #e0e0e0;
            color: #00aa00;
            border-radius: 6px;
            font-weight: bold;
            margin-left: 12px;
        ">
            {vol_ratio(path)}
        </span>
    </div>

    <div style="
        color: #ffffff;
        font-size: 19px;
        text-align: left;
        margin-bottom: 20px;
    ">
        <span style="font-weight: 600;">Surface Area to Volume (SA/V) Ratio:</span>
        <span style="
            display: inline-block;
            padding: 4px 10px;
            background: #e0e0e0;
            color: #00aa00;
            border-radius: 6px;
            font-weight: bold;
            margin-left: 12px;
        ">
            {surface_area_to_volume_ratio(path)}
        </span>
    </div>
    """, unsafe_allow_html=True)
            st.session_state['stl_path'] = path
            st.session_state["dict_key"] = dict_key
            st.session_state['stl_generated'] = True
            with st.session_state['struc_name']:
                st.markdown(f"""
                <div style="position: relative; display: inline-block; margin-bottom: 2px;">
                    <h3 style="margin:0;">{struc_name}</h3>
                
                </div>""", unsafe_allow_html = True)

            st.session_state['spinner'].empty()  # Clear the message after displaying



