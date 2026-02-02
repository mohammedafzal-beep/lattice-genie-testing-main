import streamlit as st

def nav_bar():
    st.sidebar.markdown(
        """
       <div class='center'>
            <p style='font-size:1.7rem; line-height:1.2; '>Navigation Bar</p>
        </div>
        <style>
            .stAlert { display: none; }
            .center { text-align: center; }
            section[data-testid="stSidebar"] * {
                font-size: 1.2rem;
            }
            /* Reduce gap above and below the horizontal rule */
            section[data-testid="stSidebar"] hr {
                margin-top: 0.5em;
                margin-bottom: 0.5em;
            }
            section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    display: flex !important;          /* make label and radio inline-flex */
    align-items: center !important;    /* vertical align text with radio circle */
    gap: 5px !important;               /* horizontal gap between circle and text */
    margin-bottom: 3px !important;     /* reduce vertical spacing between options */
    font-size: 1.2rem !important;      /* match your other sidebar font size */
}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")
    
