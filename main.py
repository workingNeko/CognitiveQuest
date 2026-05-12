import streamlit as st
from database.db_conn import admin_exists, create_admin
from auth.login import login_user, logout_user, is_authenticated, check_session_expiry
import mysql.connector

# Page configuration
st.set_page_config(
    page_title="Cognitive Quest",
    page_icon="🎮",
    layout="wide"

)

if not st.session_state.get("logged_in", False):
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        .stApp {
            margin-left: 0;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None


# =========================================
# ADMIN CREATION DIALOG
# =========================================
@st.dialog("⚠️ Create Admin Account", width="small")
def admin_creation_dialog():
    st.markdown("No admin account detected. Please create one:")
    st.markdown("---")

    with st.form("admin_creation_form"):
        username = st.text_input("Username *", placeholder="Enter username")
        email = st.text_input("Email *", placeholder="Enter email address")
        password = st.text_input("Password *", type="password", placeholder="Enter password (min 6 characters)")
        confirm_password = st.text_input("Confirm Password *", type="password", placeholder="Confirm password")

        col1, col2 = st.columns(2)

        with col1:
            submit = st.form_submit_button("✅ Create Admin", type="primary", use_container_width=True)

        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            if not username or not email or not password:
                st.error("❌ Please fill in all fields.")
            elif password != confirm_password:
                st.error("❌ Passwords do not match.")
            elif len(password) < 6:
                st.error("❌ Password must be at least 6 characters long.")
            else:
                try:
                    create_admin(username, email, password)
                    st.success(f"✅ Admin account '{username}' created successfully!")
                    st.balloons()
                    st.rerun()
                except mysql.connector.IntegrityError:
                    st.error("❌ Username already exists. Please choose a different username.")
                except Exception as e:
                    st.error(f"❌ Error creating admin account: {str(e)}")

        if cancel:
            st.warning("Admin account is required to use the system.")
            st.rerun()


# =========================================
# MAIN LOGIC
# =========================================

# Check if admin exists
if not admin_exists():
    admin_creation_dialog()
    # Show disabled login form (blurred effect)
    st.markdown("""
        <style>
        .stApp {
            opacity: 0.5;
            filter: blur(2px);
            pointer-events: none;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🎮 Cognitive Quest")
    st.subheader("🔐 Login")
    st.text_input("Username", disabled=True)
    st.text_input("Password", type="password", disabled=True)
    st.button("Login", disabled=True, use_container_width=True)

    st.stop()

# Show login form if not authenticated
if not is_authenticated():
    st.title("🎮 Cognitive Quest")
    st.subheader("🔐 Login to Your Account")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("🔓 Login", type="primary", use_container_width=True):
                if username and password:
                    if login_user(username, password):
                        st.success(f"Welcome back, {st.session_state.user['name']}!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("Please enter both username and password")

        with col_btn2:
            if st.button("❌ Clear", use_container_width=True):
                st.session_state.login_username = ""
                st.session_state.login_password = ""
                st.rerun()

    st.divider()
    st.caption("🔒 Secure Login System | Cognitive Quest")

# Show main app if authenticated
elif is_authenticated():
    # Check session expiry
    if not check_session_expiry():
        st.warning("Session expired. Please login again.")
        logout_user()
        st.rerun()

    # Sidebar user info
    with st.sidebar:
        st.header("👤 User Profile")
        st.write(f"**Username:** {st.session_state.user['username']}")
        st.write(f"**Email:** {st.session_state.user.get('email', 'Not provided')}")
        st.write(f"**Role:** {st.session_state.user['role']}")
        st.write(f"**Member since:** {st.session_state.user['created_at']}")
        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()

    # Redirect to dashboard
    st.switch_page("pages/1_Dashboard.py")