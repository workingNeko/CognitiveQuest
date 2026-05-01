import streamlit as st
import pandas as pd
from io import BytesIO

from utils.sidebar import show_sidebar

st.set_page_config(
    page_title="Cognitive Quest - Students",
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

# 🔐 Protect
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.stop()

show_sidebar()

# -----------------------------
# DATA INIT
# -----------------------------
if "students_data" not in st.session_state:
    st.session_state.students_data = pd.DataFrame([
        ["Emma Thompson", 92, 85, "Level 6", "Enrolled"],
        ["Liam Rodriguez", 78, 60, "Level 4", "Enrolled"],
        ["Sophia Chen", 98, 95, "Level 6", "Enrolled"],
        ["Noah Williams", 87, 75, "Level 5", "Enrolled"],
        ["Olivia Martinez", 65, 45, "Level 3", "Enrolled"],
    ], columns=["Name", "Score", "Progress", "Level", "Status"])

students = st.session_state.students_data.copy()

# -----------------------------
# HEADER WITH IMPORT/EXPORT BUTTONS (POPOVERS)
# -----------------------------
col1, col2, col3 = st.columns([6, 1, 1])

with col1:
    st.title("👨‍🎓 Students")
    st.write("Manage and track student performance")

# IMPORT POPOVER
with col2:
    with st.popover("📥 Import Data", use_container_width=True):
        st.subheader("Import Students")
        file = st.file_uploader("Choose CSV or Excel file", type=["csv", "xlsx", "xls"])
        mode = st.radio("Import Mode", ["Replace", "Append"], horizontal=True)
        import_clicked = st.button("✅ Import", type="primary", use_container_width=True)

        if import_clicked and file is not None:
            try:
                # Read file
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)

                # Clean column names
                df.columns = [col.strip() for col in df.columns]

                # --- Auto‑fix missing columns ---
                required_cols = ["Name", "Score", "Progress", "Level", "Status"]

                # 1. Name: combine First + Last if possible
                if "Name" not in df.columns:
                    if "First Name" in df.columns and "Last Name" in df.columns:
                        df["Name"] = df["First Name"].astype(str) + " " + df["Last Name"].astype(str)
                    else:
                        df["Name"] = "Unknown"

                # 2. Add any other missing columns with defaults
                defaults = {
                    "Score": 0,
                    "Progress": 0,
                    "Level": "Level 1",
                    "Status": "Enrolled"
                }
                for col in required_cols:
                    if col not in df.columns:
                        df[col] = defaults.get(col, "")

                # Keep only required columns (drop extras)
                df = df[required_cols]

                # Convert numeric columns
                df["Score"] = pd.to_numeric(df["Score"], errors="coerce").fillna(0)
                df["Progress"] = pd.to_numeric(df["Progress"], errors="coerce").fillna(0)

                # Drop rows with empty Name
                df = df.dropna(subset=["Name"])
                df["Name"] = df["Name"].astype(str).str.strip()
                df = df[df["Name"] != ""]

                if len(df) == 0:
                    st.error("❌ No valid student data found after processing.")
                else:
                    if mode == "Replace":
                        st.session_state.students_data = df.reset_index(drop=True)
                    else:  # Append
                        # Align columns (both dataframes have same required columns)
                        st.session_state.students_data = pd.concat(
                            [st.session_state.students_data, df],
                            ignore_index=True
                        )
                    st.success(f"✅ Import successful! {len(df)} students processed.")
                    st.rerun()

            except Exception as e:
                st.error(f"Error reading file: {e}")

        elif import_clicked:
            st.warning("Please upload a file first.")

# EXPORT POPOVER
with col3:
    with st.popover("📤 Export Data", use_container_width=True):
        st.subheader("Export Students")
        format_type = st.selectbox("Format", ["CSV", "Excel"], label_visibility="collapsed")
        export_clicked = st.button("📥 Generate File", type="primary", use_container_width=True)

        if export_clicked:
            if len(st.session_state.students_data) > 0:
                if format_type == "CSV":
                    csv = st.session_state.students_data.to_csv(index=False)
                    st.download_button(
                        "💾 Download CSV",
                        data=csv,
                        file_name="students_export.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        st.session_state.students_data.to_excel(writer, index=False)
                    st.download_button(
                        "💾 Download Excel",
                        data=buffer.getvalue(),
                        file_name="students_export.xlsx",
                        use_container_width=True
                    )
            else:
                st.warning("No data to export")

# -----------------------------
# SEARCH + FILTER
# -----------------------------
search = st.text_input("🔍 Search student")
status_filter = st.selectbox("Filter by Status", ["All", "Enrolled", "Unenrolled"])

filtered = students[
    students["Name"].str.contains(search, case=False, na=False)
]

if status_filter != "All":
    filtered = filtered[filtered["Status"] == status_filter]

# -----------------------------
# TABLE
# -----------------------------
st.subheader("Student List")

edited_df = st.data_editor(
    filtered,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Name": st.column_config.TextColumn("Name", required=True),
        "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100),
        "Progress": st.column_config.NumberColumn("Progress", min_value=0, max_value=100),
        "Level": st.column_config.TextColumn("Level"),
        "Status": st.column_config.TextColumn("Status")
    },
    key="student_editor"
)

# Save edits to session state
if not edited_df.equals(filtered):
    # Update the main dataframe with changes
    for idx in edited_df.index:
        if idx < len(st.session_state.students_data):
            st.session_state.students_data.loc[idx] = edited_df.loc[idx]
        else:
            # New rows added
            st.session_state.students_data = pd.concat(
                [st.session_state.students_data, pd.DataFrame([edited_df.loc[idx]])],
                ignore_index=True
            )

    # Remove deleted rows
    if len(edited_df) < len(st.session_state.students_data):
        st.session_state.students_data = st.session_state.students_data.loc[edited_df.index]

    st.rerun()

# -----------------------------
# PROGRESS OVERVIEW
# -----------------------------
st.subheader("Progress Overview")

if len(filtered) > 0:
    for _, row in filtered.iterrows():
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write(f"**{row['Name']}**")
        with col2:
            st.progress(int(row["Progress"]))
        st.caption(f"Score: {row['Score']} | Level: {row['Level']} | Status: {row['Status']}")
else:
    st.info("No students found")

# -----------------------------
# SUMMARY STATISTICS
# -----------------------------
st.subheader("📊 Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Students", len(st.session_state.students_data))

with col2:
    avg_score = st.session_state.students_data['Score'].mean() if len(st.session_state.students_data) > 0 else 0
    st.metric("Average Score", f"{avg_score:.1f}")

with col3:
    enrolled = len(st.session_state.students_data[st.session_state.students_data["Status"] == "Enrolled"])
    st.metric("Enrolled Students", enrolled)

with col4:
    avg_progress = st.session_state.students_data['Progress'].mean() if len(st.session_state.students_data) > 0 else 0
    st.metric("Average Progress", f"{avg_progress:.1f}%")