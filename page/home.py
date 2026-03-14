import streamlit as st
from components.viewer import show_stl_thumbnail_home
from components.chat import handle_user_input
from components.parameter_ui import show_parameter_sliders
from columns.left_col import left_column
from columns.right_col import right_column
from utils.dataloader import log_slider_changes
from streamlit_stl import stl_from_file
import time
def render_home(data):
    st.markdown("""
    <div class='center'>
      <h1 class='padding'>✨ Lattice Genie</h1>
      <h5 class='center unbold bottom-margin'>A comprehensive tool for 3D lattice structure generation</h5>
    </div>
                <style>block-container, section.main > div {
  padding-top: 0 !important;
  margin-top: 0 !important;
}
.bottom-margin {margin-bottom: -23px !important;}
/* your element move */
.padding {
  margin-top: -57px !important;
    }
  .center { text-align: center; }
    .unbold { font-weight: normal !important; }
    .padding {padding-top: 20px}

</style>

    """, unsafe_allow_html=True)
    display_thumbnails(data["crystal_images"],'Chat mode')
    st.markdown("---")
    st.markdown("<div class='center' style='margin-bottom:5px;'><h2 >💬 Ask to configure lattice:</h2></div>", unsafe_allow_html=True)
   
    with st.container():
      handle_user_input(data)
      show_parameter_sliders(data,'Chat')
      display_stl()

def display_stl():
  if st.session_state.get('stl_generated'):
    SCALING_FACTOR = 100
    if st.session_state['dict_key'] == 4:
            SCALING_FACTOR = 2.4
    elif st.session_state['dict_key'] == 29:
            SCALING_FACTOR = 1.58
    current_params = st.session_state['current_params']    
    stl_from_file(st.session_state['stl_path'],st.session_state.get('stl_color', '#336fff'), 
                    auto_rotate=True, height=500,cam_distance=SCALING_FACTOR*(current_params['resolution']/50),
                    cam_h_angle=45,cam_v_angle=75)
                
    with st.session_state['Scroll message']:
            st.markdown("<p style='font-size:17px'>✅ STL Generated! Scroll down to view <br> \
            ⬇️ Download using button below </p> ", unsafe_allow_html= True)
    
    time.sleep(4)
    st.session_state['Scroll message'].empty()
    
    download_submit_tab = st.columns([1.7, 1, 1])
    
            
    with open(st.session_state['stl_path'], 'rb') as f:
        
        with download_submit_tab[1]:
            st.download_button('⬇️ Download STL', data=f.read(), file_name=st.session_state['stl_path'], mime='model/stl')
            
            log_event("Download", 'Chat mode')

def render_home_dropdown_version(data):
    
    st.markdown("""
    <div class='center'>
      <h1 class='padding'>✨ Lattice Genie</h1>
      <h5 class='center unbold bottom-margin'>A comprehensive tool for 3D lattice structure generation</h5>
    </div>
                <style>block-container, section.main > div {
  padding-top: 0 !important;
  margin-top: 0 !important;
}

/* your element move */
.padding {
  margin-top: -57px !important;
    }
  .center { text-align: center; }
    .unbold { font-weight: normal !important; } .bottom-margin {margin-bottom: -36px !important;}
  .stDownloadButton button { display: block; margin-left: auto; margin-right: auto; }
  [data-testid='stHeaderActionElements'] {display: none;}

</style>
    """, unsafe_allow_html=True)
    display_thumbnails(data["crystal_images"],'Pro mode')

    st.markdown("---")
    left_col, right_col = st.columns([1,2])
# Use the functions inside the with blocks
    with left_col:
        left_column(data)
    
    with st.sidebar:
      show_parameter_sliders(data,'Pro mode')
      
      
    with right_col:
       right_column(data)
    
    
def display_thumbnails(images,mode):
    cols = st.columns(len(images))
    for idx, (name, img_path) in enumerate(images.items()):
        with cols[idx]:
            try:
                show_stl_thumbnail_home(name, img_path)
            except:
                st.error(f"Couldn't load {name} image.")
            #st.markdown(f"<h4 style='text-align:center;font-weight: normal !important;'>{name}</h4>", unsafe_allow_html=True)
            with st.columns([1,17,1])[1]:
              if st.button(name,key=f'btn_{name}'):
                st.session_state[f'go_{name}'] = True
                st.rerun()
    
