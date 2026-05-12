# utils/sidebar.py
import streamlit as st
from auth.login import get_current_user, logout_user


def show_sidebar():
    """Display the sidebar navigation"""
    with st.sidebar:
        # User info section
        user = get_current_user()
        if user:
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;">
                <div style="font-size: 40px;">👤</div>
                <div style="color: white; font-weight: bold;">{user['name']}</div>
                <div style="color: rgba(255,255,255,0.8); font-size: 12px;">{user['role'].capitalize()}</div>
                <div style="color: rgba(255,255,255,0.6); font-size: 10px;">@{user['username']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("## 🧠 Cognitive Quest")
        st.caption(f" {user['role'].capitalize()} Dashboard" if user else "Dashboard")
        st.divider()

        # Navigation links
        st.page_link("pages/1_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/2_Students.py", label="👨‍🎓 Students")
        st.page_link("pages/3_Content.py", label="🎮 Game Content")
        st.page_link("pages/4_Analytics.py", label="📈 Analytics")
        st.page_link("pages/5_Settings.py", label="⚙️ Settings")

        st.divider()

        # Session info
        if user:
            with st.expander("ℹ️ Session Info"):
                st.caption(f"Logged in since: {user.get('login_time', 'Unknown')[:10]}")
                st.caption("Session expires: 24 hours")

        # Logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout_user()
            st.switch_page("main.py")