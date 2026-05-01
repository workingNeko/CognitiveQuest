import streamlit as st
import pandas as pd
import plotly.express as px

from utils.sidebar import show_sidebar

st.set_page_config(
    page_title="Cognitive Quest - Analytics",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# 🔐 Auth
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Login first.")
    st.stop()

show_sidebar()

st.title("📊 Analytics")

students = st.session_state.students_data.copy()

# -----------------------------
# SCORE DISTRIBUTION
# -----------------------------
st.subheader("Score Distribution")

bins = [0, 60, 70, 80, 90, 100]
labels = ["Below 60", "60-69", "70-79", "80-89", "90-100"]

students["Score Range"] = pd.cut(students["Score"], bins=bins, labels=labels)

dist = students["Score Range"].value_counts().sort_index().reset_index()
dist.columns = ["Range", "Students"]

fig = px.bar(dist, x="Range", y="Students", text_auto=True)
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# LEVEL ENGAGEMENT
# -----------------------------
st.subheader("Level Engagement")

level_engagement = students.groupby("Level").agg({
    "Name": "count",
    "Progress": "mean"
}).reset_index()

level_engagement.columns = ["Level", "Students", "Avg Progress"]

fig2 = px.bar(level_engagement, x="Level", y="Avg Progress", text_auto=True)
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# PERFORMANCE SUMMARY
# -----------------------------
st.subheader("Performance Summary")

avg_score = students["Score"].mean()

if avg_score >= 80:
    st.success("Overall performance is high")
elif avg_score >= 60:
    st.warning("Performance is moderate")
else:
    st.error("Performance is low")

# -----------------------------
# PASSING ANALYSIS
# -----------------------------
passing = students["Score"] >= 70
pass_rate = passing.sum() / len(students) * 100

st.metric("Passing Rate", f"{pass_rate:.1f}%")