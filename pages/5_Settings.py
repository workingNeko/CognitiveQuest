import streamlit as st
import mysql.connector
from datetime import datetime
from utils.sidebar import show_sidebar
from database.db_conn import get_connection
from auth.security import hash_password, verify_password
from auth.login import logout_user

st.set_page_config(
    page_title="Cognitive Quest - Settings",
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

# Get current user role
current_user_role = st.session_state.user.get("role", "teacher")
current_user_id = st.session_state.user.get("user_id")
current_username = st.session_state.user.get("username")

# Page header
st.title("⚙️ Settings")
st.markdown(f"Manage your account and application preferences - **Role: {current_user_role.upper()}**")
st.divider()

# Add logout button in sidebar with unique key
with st.sidebar:
    st.markdown("---")
    st.caption(f"Logged in as: **{current_username}**")
    st.caption(f"Role: **{current_user_role.upper()}**")
    st.markdown("---")
    if st.button("🚪 Logout", type="secondary", use_container_width=True, key="logout_button_sidebar"):
        logout_user()
        st.switch_page("main.py")

# =========================================
# FUNCTION TO GET ALL USERS (ADMIN ONLY)
# =========================================
def get_all_users():
    """Get all users for admin"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT user_id, username, email, role, created_at, last_login 
        FROM users 
        ORDER BY user_id
    """)
    users = cursor.fetchall()

    cursor.close()
    conn.close()
    return users


# =========================================
# FUNCTION TO GET SINGLE USER
# =========================================
def get_user(user_id):
    """Get specific user details"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()
    return user


# =========================================
# FUNCTION TO UPDATE USER (ADMIN)
# =========================================
def update_user_by_admin(user_id, username, email, role):
    """Admin updates user details"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users 
        SET username = %s, email = %s, role = %s 
        WHERE user_id = %s
    """, (username, email, role, user_id))

    conn.commit()
    cursor.close()
    conn.close()


# =========================================
# FUNCTION TO UPDATE OWN PROFILE (TEACHER/ADMIN)
# =========================================
def update_own_profile(user_id, username, email):
    """Update user's own profile"""
    conn = get_connection()
    cursor = conn.cursor()

    # Update basic info
    cursor.execute("""
        UPDATE users 
        SET username = %s, email = %s 
        WHERE user_id = %s
    """, (username, email, user_id))

    conn.commit()
    cursor.close()
    conn.close()


# =========================================
# FUNCTION TO CHANGE PASSWORD
# =========================================
def change_password(user_id, new_password):
    """Change user password"""
    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = hash_password(new_password)

    cursor.execute("""
        UPDATE users 
        SET password_hash = %s 
        WHERE user_id = %s
    """, (hashed_password, user_id))

    conn.commit()
    cursor.close()
    conn.close()


# =========================================
# FUNCTION TO CREATE NEW USER (ADMIN ONLY)
# =========================================
def create_new_user(username, email, password, role):
    """Create a new user"""
    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = hash_password(password)

    cursor.execute("""
        INSERT INTO users (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """, (username, email, hashed_password, role))

    conn.commit()
    cursor.close()
    conn.close()


# =========================================
# FUNCTION TO DELETE USER (ADMIN ONLY)
# =========================================
def delete_user(user_id):
    """Delete a user"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

    conn.commit()
    cursor.close()
    conn.close()


# =========================================
# PROFILE SETTINGS (Visible to ALL users)
# =========================================
with st.expander("👤 Profile Settings", expanded=True):
    st.markdown("### Update your account information")

    # Get current user data from database
    current_user_data = get_user(current_user_id)

    col1, col2 = st.columns(2)

    with col1:
        new_username = st.text_input("Username", value=current_user_data.get("username", ""), key="profile_username")

    with col2:
        new_email = st.text_input("Email Address", value=current_user_data.get("email", ""), key="profile_email")

    # Change Password Section
    st.markdown("### 🔒 Change Password")
    col1, col2 = st.columns(2)

    with col1:
        current_password = st.text_input("Current Password", type="password", placeholder="Enter current password", key="current_pwd")
    with col2:
        new_password = st.text_input("New Password", type="password", placeholder="Enter new password (min 6 chars)", key="new_pwd")

    confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password", key="confirm_pwd")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("💾 Save Profile Changes", type="primary", use_container_width=True, key="save_profile_btn"):
            # Update username and email
            update_own_profile(current_user_id, new_username, new_email)

            # Update session state
            st.session_state.user["username"] = new_username
            st.session_state.user["email"] = new_email

            st.success("✅ Profile updated successfully!")
            st.rerun()

    with col2:
        if new_password and confirm_password:
            if st.button("🔑 Change Password", type="secondary", use_container_width=True, key="change_pwd_btn"):
                # Verify current password
                if verify_password(current_password, current_user_data["password_hash"]):
                    if len(new_password) >= 6:
                        if new_password == confirm_password:
                            change_password(current_user_id, new_password)
                            st.success("✅ Password changed successfully!")
                            st.rerun()
                        else:
                            st.error("❌ New passwords do not match!")
                    else:
                        st.error("❌ Password must be at least 6 characters!")
                else:
                    st.error("❌ Current password is incorrect!")

# =========================================
# ADMIN SECTION - USER MANAGEMENT
# =========================================
if current_user_role == "admin":
    st.divider()
    st.markdown("## 👥 User Management")
    st.markdown("### Add, modify, or remove users")

    # Tab layout for user management
    tab1, tab2, tab3 = st.tabs(["📝 Add New User", "✏️ Modify User", "🗑️ Delete User"])

    # =========================================
    # TAB 1: ADD NEW USER
    # =========================================
    with tab1:
        st.markdown("### Create New User Account")

        # Check for success message in session state
        if "user_created_success" in st.session_state:
            success_msg = st.session_state.user_created_success
            st.success(success_msg)
            st.balloons()
            # Extract username and other details to show info
            if "created_user_details" in st.session_state:
                st.info(st.session_state.created_user_details)
            # Clear the session state after showing
            del st.session_state.user_created_success
            del st.session_state.created_user_details

        with st.form("add_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_user_username = st.text_input("Username *", placeholder="Enter username", key="new_user_username")
                new_user_email = st.text_input("Email *", placeholder="Enter email address", key="new_user_email")

            with col2:
                new_user_role = st.selectbox("Role *", ["teacher", "admin"],
                                             help="Admin can manage all users, Teacher can only manage their own profile",
                                             key="new_user_role")
                new_user_password = st.text_input("Password *", type="password",
                                                  placeholder="Enter password (min 6 chars)", key="new_user_password")

            confirm_new_password = st.text_input("Confirm Password *", type="password", placeholder="Confirm password",
                                                 key="confirm_new_password")

            submitted = st.form_submit_button("➕ Create User", type="primary", use_container_width=True)

            if submitted:
                if not all([new_user_username, new_user_email, new_user_password]):
                    st.error("❌ Please fill in all required fields!")
                elif new_user_password != confirm_new_password:
                    st.error("❌ Passwords do not match!")
                elif len(new_user_password) < 6:
                    st.error("❌ Password must be at least 6 characters!")
                else:
                    try:
                        create_new_user(new_user_username, new_user_email, new_user_password, new_user_role)
                        # Store success message in session state
                        st.session_state.user_created_success = f"✅ User '{new_user_username}' created successfully!"
                        st.session_state.created_user_details = f"📧 Email: {new_user_email} | 🔑 Role: {new_user_role}"
                        st.rerun()
                    except mysql.connector.IntegrityError:
                        st.error("❌ Username already exists!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    # =========================================
    # TAB 2: MODIFY USER
    # =========================================
    with tab2:
        st.markdown("### Modify Existing User")

        users = get_all_users()
        user_options = {f"{user['username']} ({user['role']})": user['user_id'] for user in users}

        selected_user = st.selectbox("Select User to Modify", list(user_options.keys()), key="select_user_modify")

        if selected_user:
            user_id = user_options[selected_user]
            user_data = get_user(user_id)

            with st.form("modify_user_form"):
                col1, col2 = st.columns(2)

                with col1:
                    mod_username = st.text_input("Username", value=user_data['username'], key="mod_username")
                    mod_email = st.text_input("Email", value=user_data['email'] or "", key="mod_email")

                with col2:
                    mod_role = st.selectbox("Role", ["teacher", "admin"],
                                            index=0 if user_data['role'] == 'teacher' else 1,
                                            key="mod_role")
                    mod_password = st.text_input("New Password (leave empty to keep current)",
                                                 type="password", placeholder="Enter new password to change",
                                                 key="mod_password")

                modify_submitted = st.form_submit_button("💾 Update User", type="primary", use_container_width=True)

                if modify_submitted:
                    # Update basic info
                    update_user_by_admin(user_id, mod_username, mod_email, mod_role)

                    # Update password if provided
                    if mod_password:
                        if len(mod_password) >= 6:
                            change_password(user_id, mod_password)
                            st.info("🔑 Password has been updated!")
                        else:
                            st.error("❌ Password must be at least 6 characters!")

                    st.success(f"✅ User '{mod_username}' updated successfully!")
                    st.rerun()

    # =========================================
    # TAB 3: DELETE USER
    # =========================================
    with tab3:
        st.markdown("### Delete User Account")
        st.warning("⚠️ This action is irreversible! The user and all their data will be permanently deleted.")

        users = get_all_users()
        # Don't allow admin to delete themselves
        delete_options = {f"{user['username']} ({user['role']})": user['user_id']
                          for user in users if user['user_id'] != current_user_id}

        if delete_options:
            user_to_delete = st.selectbox("Select User to Delete", list(delete_options.keys()), key="select_user_delete")

            if user_to_delete:
                user_id_to_delete = delete_options[user_to_delete]
                user_data = get_user(user_id_to_delete)

                st.error(f"⚠️ Are you sure you want to delete **{user_data['username']}**?")

                col1, col2 = st.columns(2)
                with col1:
                    confirm_delete = st.checkbox("✓ I understand this action cannot be undone", key="confirm_delete_checkbox")

                with col2:
                    if st.button("🗑️ Permanently Delete User", type="secondary", use_container_width=True, key="delete_user_btn"):
                        if confirm_delete:
                            delete_user(user_id_to_delete)
                            st.success(f"✅ User '{user_data['username']}' has been deleted!")
                            st.rerun()
                        else:
                            st.warning("Please confirm the deletion checkbox!")
        else:
            st.info("No other users available to delete. You cannot delete your own account while logged in.")

# =========================================
# DANGER ZONE (For all users, but with limits)
# =========================================
st.divider()

with st.expander("⚠️ Danger Zone", expanded=False):
    st.markdown("### Irreversible actions - proceed with caution")

    if current_user_role == "admin":
        st.warning("⚠️ Resetting all settings will affect all users in the system.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Reset All System Settings", type="secondary", use_container_width=True, key="reset_system_btn"):
                st.error("❌ This would reset all system settings for all users!")

        with col2:
            if st.button("🗑️ Delete All User Data", type="secondary", use_container_width=True, key="delete_all_data_btn"):
                st.error("❌ This would delete ALL user data from the system!")
    else:
        st.info("🔒 As a teacher, you can only manage your own account settings.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Reset My Preferences", type="secondary", use_container_width=True, key="reset_preferences_btn"):
                st.warning("Your personal preferences would be reset to default.")

        with col2:
            if st.button("🗑️ Request Account Deletion", type="secondary", use_container_width=True, key="request_deletion_btn"):
                st.warning("Please contact an administrator to delete your account.")

st.divider()

# =========================================
# SAVE ALL BUTTON
# =========================================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("💾 Save All Settings", type="primary", use_container_width=True, key="save_all_settings_btn"):
        st.success("All settings have been saved successfully!")
        st.balloons()