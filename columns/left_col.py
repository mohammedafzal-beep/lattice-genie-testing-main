import streamlit as st
import sys
import os
from utils.utils import subtype_selection_to_dict_key
from utils.dataloader import log_event
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Mode switch area (top)
def left_column(data):
    
    st.markdown(
    """
    <div style='text-align:center;'>
    <h3 style='margin-top:-20px;'>✨ Generation Mode </h3>
    </div>
    """,
    unsafe_allow_html=True,
    )
    # Structure selection block
    # Build dropdowns from data. We expect params_dict schemas have meta.type and meta.subtype.
    # Collect unique types and subtypes
    subtype_selection_to_dict_key(data)

    if 'dict_key_list' not in st.session_state:
        st.session_state['dict_key_list'] = [0]
    if st.session_state['selected_dict_key'] != st.session_state['dict_key_list'][-1]:
        st.session_state['dict_key_list'].append(st.session_state['selected_dict_key'])
    #selection_pane=st.columns([.7,5.3,1,4.5,1])
    
