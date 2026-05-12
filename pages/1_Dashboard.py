import streamlit as st
import pandas as pd
import plotly.express as px

from utils.sidebar import show_sidebar

st.set_page_config(
    page_title="Cognitive Quest - Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# 🔐 Auth
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.stop()

show_sidebar()

st.title("📊 Dashboard")

# -----------------------------
# DATA INIT
# -----------------------------
if "students_data" not in st.session_state:
    st.session_state.students_data = pd.DataFrame([
        ["Emma", 92, 85, "Level 6", "Enrolled"],
        ["Liam", 78, 60, "Level 4", "Enrolled"],
        ["Sophia", 98, 95, "Level 6", "Enrolled"],
        ["Noah", 87, 75, "Level 5", "Enrolled"],
        ["Olivia", 65, 45, "Level 3", "Enrolled"],
    ], columns=["Name", "Score", "Progress", "Level", "Status"])

students = st.session_state.students_data.copy()

# -----------------------------
# METRICS
# -----------------------------
total_students = len(students)
avg_score = students["Score"].mean()
avg_progress = students["Progress"].mean()
passing_rate = len(students[students["Score"] >= 70]) / total_students * 100

col1, col2, col3, col4 = st.columns(4)

col1.metric("Students", total_students)
col2.metric("Avg Score", f"{avg_score:.1f}")
col3.metric("Avg Progress", f"{avg_progress:.1f}%")
col4.metric("Passing Rate", f"{passing_rate:.1f}%")

st.divider()

# -----------------------------
# LEVEL PERFORMANCE
# -----------------------------
level_scores = students.groupby("Level")["Score"].mean().reset_index()

fig = px.bar(
    level_scores,
    x="Level",
    y="Score",
    title="Average Score per Level",
    text_auto=True
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# PERFORMANCE CATEGORY
# -----------------------------
def categorize(score):
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Average"
    else:
        return "Needs Improvement"

students["Category"] = students["Score"].apply(categorize)

category_data = students["Category"].value_counts().reset_index()
category_data.columns = ["Category", "Count"]

fig2 = px.pie(category_data, names="Category", values="Count", title="Performance Distribution")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# STUDENT TABLE
# -----------------------------
st.subheader("Student Data")

# Make a copy to avoid modifying the original
display_df = students.copy()

# Reset index to start from 1
display_df.index = range(1, len(display_df) + 1)

# Optionally, hide the student_id column if it exists
if 'student_id' in display_df.columns:
    display_df = display_df.drop(columns=['student_id'])

st.dataframe(display_df, use_container_width=True)