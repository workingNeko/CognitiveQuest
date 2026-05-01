import streamlit as st
from auth.login import login_user, is_authenticated, get_current_user, check_session_expiry

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Cognitive Quest",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# Check session expiry
if st.session_state.logged_in:
    if not check_session_expiry():
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

# Hide sidebar ONLY on login page (before login)
if not st.session_state.logged_in:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
            [data-testid="collapsedControl"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)

# LOGIN FORM ONLY
if not st.session_state.logged_in:
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Cognitive Quest Login")
        st.write("")

        # Add a nice header
        st.markdown("### Welcome Back!")
        st.markdown("Please sign in to continue")
        st.write("")

        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

        # Remember me option
        remember_me = st.checkbox("Remember me", value=False)

        if st.button("Login", type="primary", use_container_width=True):
            if login_user(username, password):
                st.success(f"Welcome back, {st.session_state.user['name']}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

        # Demo credentials hint
        st.caption("Demo credentials: admin / admin123")

# AFTER LOGIN - Show main app
else:
    # Display user info in sidebar via sidebar.py
    from utils.sidebar import show_sidebar

    show_sidebar()

    # Redirect to dashboard
    st.switch_page("pages/1_Dashboard.py")