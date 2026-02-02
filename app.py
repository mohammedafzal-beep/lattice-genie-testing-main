import streamlit as st
from utils.dataloader import load_data,log_event
from utils.session import init_state, reset_home_flag,init_state_dropdown_version
from utils.utils import cleanup_stl_files_and_update_drive
from page.home import render_home, render_home_dropdown_version
from page.generic import render_generic_page
from page.nav_bar import nav_bar
import atexit


def run_app():
    init_state()
    nav_bar()
    data = load_data()
    log_event("App opened", "Chat Mode")
    reset_home_flag('Chat mode')
    page = st.sidebar.radio('', data["pages"], key="current_page")
    st.sidebar.markdown("---")
    

    count = 0
    atexit.register(cleanup_stl_files_and_update_drive)
    if page == "Home":
        if count != 0:
            log_event(f'Radio button: Home','Chat mode')
        render_home(data)
        count += 1
    else:
        render_generic_page(page, data)
        log_event(f'Radio button: {page}','Chat mode')

def run_app_dropdown_version():
    init_state_dropdown_version()
    nav_bar()
    data = load_data()
    reset_home_flag('Pro mode')
    log_event("App opened", "Pro Mode")
    page = st.sidebar.radio('', data["pages"], key="current_page")
    atexit.register(cleanup_stl_files_and_update_drive)
    count = 0
    if page == "Home":
        if count != 0:
            log_event(f'Radio button: Home','Pro mode')
        render_home_dropdown_version(data)
        count += 1
    else:
        render_generic_page(page, data)
        log_event(f'Radio button: {page}','Pro mode')
