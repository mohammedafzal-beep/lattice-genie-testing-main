import streamlit as st
from streamlit_stl import stl_from_file
from utils.dataloader import log_event, log_submission
from components.parameter_ui import labeled_slider
def right_column(data):
    st.markdown('<h3 style="display: flex; align-items: center; justify-content: center; margin-top: -20px; text-align:center;">📸 Preview </h3>', unsafe_allow_html=True)
    
    if st.session_state['stl_path']:
        
        current_params = st.session_state['current_params']
        stl_from_file(st.session_state['stl_path'],st.session_state.get('stl_color', '#336fff'), 
                auto_rotate=True, height=250,
                cam_distance=94*(current_params['resolution']/50),cam_h_angle=45,cam_v_angle=75)
        
            
        # Download button
        try:
            design_ques_tab = st.columns([1, 6, 1])
            design_ques_list = ["Task 1","Task 2","Task 3","Task 4"]
            with design_ques_tab[1]:
                design_ques = st.selectbox("Design Task", design_ques_list, index=0)
                log_event(design_ques,'Pro mode')
            download_submit_tab = st.columns([1,2,1.5,1])
            
            with open(st.session_state['stl_path'], 'rb') as f:
                
                with download_submit_tab[1]:
                    st.download_button('⬇️ Download STL', data=f.read(), file_name=st.session_state['stl_path'], mime='model/stl')
                    log_event('Download','Pro mode')
            
            with download_submit_tab[2]:
                if st.button('Submit'):
                    struc_info = st.session_state['dict_key'] + st.session_state['current_params']
                    log_submission(struc_info,
                    design_ques, 'Pro Mode')
                    
        except Exception:
            st.warning('STL file not available for download. Generate again.')
    else:
        placeholder = st.empty()
        placeholder.markdown(
"""
<div style="
    width: 525px;
    height:350px;
    border: 2px dashed #ccc;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;  /* center horizontally */
    text-align: center;
">
    Your STL will appear here
</div>
""",
unsafe_allow_html=True
)
