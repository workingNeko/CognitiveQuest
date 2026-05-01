import streamlit as st
from utils.sidebar import show_sidebar

st.set_page_config(
    page_title="Cognitive Quest",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide the default page navigation menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# 🔐 Protect page
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.stop()

show_sidebar()

# Page header
st.title("⚙️ Settings")
st.markdown("Manage your account and application preferences")

# -----------------------------
# PROFILE SETTINGS
# -----------------------------
with st.expander("👤 Profile Settings", expanded=True):
    st.markdown("Update your account information")

    col1, col2 = st.columns(2)

    with col1:
        first_name = st.text_input("First Name", value="Teacher")

    with col2:
        last_name = st.text_input("Last Name", value="Admin")

    email = st.text_input("Email Address", value="teacher@school.edu")
    school = st.text_input("School/Organization", value="Springfield Elementary")

    if st.button("💾 Save Profile Changes", type="primary"):
        st.success("Profile settings saved successfully!")

st.divider()


# -----------------------------
# DANGER ZONE
# -----------------------------
with st.expander("⚠️ Danger Zone", expanded=False):
    st.markdown("### Irreversible actions - proceed with caution")

    st.warning("Deleting your account will remove all your data permanently.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Delete Account", type="secondary"):
            st.error("Account deletion would require confirmation here")

    with col2:
        if st.button("🔄 Reset All Settings", type="secondary"):
            st.warning("All settings would be reset to default")

st.divider()

# -----------------------------
# SAVE ALL BUTTON
# -----------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        st.success("All settings have been saved successfully!")
        st.balloons()