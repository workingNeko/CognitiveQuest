import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

from utils.sidebar import show_sidebar
from services.import_service import import_service, detect_headers
from services.export_service import export_service
from database.student_repository import student_repo

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Cognitive Quest - Students",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CSS
# =========================================================
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }

        div[data-testid="stPopover"] {
            min-width: 300px;
            width: auto;
            max-width: 1200px;
        }

        div.stButton > button,
        div.stDownloadButton > button {
            width: auto !important;
            white-space: nowrap !important;
        }

        div[data-testid="stPopover"] button {
            width: auto !important;
            white-space: nowrap !important;
        }

        .stAlert {
            margin-top: 10px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# AUTH
# =========================================================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.stop()

show_sidebar()

# =========================================================
# SESSION STATE
# =========================================================
if "students_data" not in st.session_state:
    try:
        db_students = student_repo.get_all_students()
        data = []
        for s in db_students:
            data.append({
                "student_id": s["student_id"],
                "Name": f"{s['firstName']} {s['lastName']}",
                "Score": s["score"],
                "Progress": s["progress"],
                "Level": s["level"],
                "Status": s["status"]
            })

        if data:
            st.session_state.students_data = pd.DataFrame(data)
        else:
            st.session_state.students_data = pd.DataFrame(
                columns=["student_id", "Name", "Score", "Progress", "Level", "Status"]
            )
    except Exception as e:
        st.session_state.students_data = pd.DataFrame(
            columns=["student_id", "Name", "Score", "Progress", "Level", "Status"]
        )
        st.error(f"Error loading students: {str(e)}")

if "school_year" not in st.session_state:
    st.session_state.school_year = "2025-2026"

if "confirm_replace" not in st.session_state:
    st.session_state.confirm_replace = False

students = st.session_state.students_data.copy()

# =========================================================
# HEADER
# =========================================================
col1, col2, col3 = st.columns([6, 1.2, 1.2])

with col1:
    st.title("👨‍🎓 Students")
    st.write("Manage students with School Year & Batch System")

# =========================================================
# IMPORT
# =========================================================
with col2:
    with st.popover("📥 Import", use_container_width=True):
        st.subheader("Import Students")

        current_year = datetime.now().year
        school_years = [f"{y}-{y + 1}" for y in range(current_year, current_year + 5)]

        school_year = st.selectbox("School Year", school_years, index=0)
        st.session_state.school_year = school_year
        st.caption(f"Selected: {school_year}")

        st.divider()

        # FILE UPLOAD
        uploaded_file = st.file_uploader(
            "Upload CSV / Excel",
            type=["csv", "xlsx", "xls"],
            help="Supports CSV, Excel files. Any columns will be automatically mapped."
        )

        mode = st.radio("Import Mode", ["Append", "Replace"], horizontal=True)

        if mode == "Replace":
            st.warning(f"⚠️ Replace will archive existing students from {school_year} and import new ones")
            st.session_state.confirm_replace = st.checkbox("I confirm replace")

        if uploaded_file:
            try:
                df = import_service.read_uploaded_file(uploaded_file)

                st.write("### Preview (First 5 rows)")
                st.dataframe(df.head(), use_container_width=True)

                # Auto-detect and show column mapping
                mapping_analysis = detect_headers(df)

                if mapping_analysis.get("matched_columns"):
                    with st.expander("📋 Auto-detected Column Mapping", expanded=False):
                        for source, info in mapping_analysis["matched_columns"].items():
                            st.success(f"`{source}` → **{info['target']}**")

                if mapping_analysis.get("unmatched_columns"):
                    st.info(f"ℹ️ {len(mapping_analysis['unmatched_columns'])} columns will be stored as extra data")

                if st.button("🚀 Start Import", type="primary", use_container_width=True):
                    try:
                        if mode == "Replace" and not st.session_state.confirm_replace:
                            st.error("Please confirm replace by checking the box above.")
                            st.stop()

                        with st.spinner("Processing import..."):
                            # Process the import
                            processed, summary = import_service.process_student_import(df, mode)

                            # Show validation summary
                            if summary.get("validation_errors"):
                                st.warning(
                                    f"⚠️ Skipped {len(summary['validation_errors'])} rows due to validation errors")
                                with st.expander("View validation errors"):
                                    for error in summary["validation_errors"][:5]:
                                        error_messages = [e.get('message', str(e)) for e in error.get('errors', [])]
                                        st.error(f"Row {error['row']}: {', '.join(error_messages)}")

                            if not processed:
                                st.error("❌ No valid students to import. Please check your data format.")
                                st.info("Required fields: First Name (or any name column). Other fields are optional.")
                                st.stop()

                            # Insert students with school year
                            inserted = student_repo.insert_students(
                                processed,
                                mode=mode,
                                school_year=school_year
                            )

                            if inserted > 0:
                                # Refresh the data
                                db_students = student_repo.get_all_students()

                                # Update session state without # column
                                new_data = []
                                for s in db_students:
                                    new_data.append({
                                        "student_id": s["student_id"],
                                        "Name": f"{s['firstName']} {s['lastName']}",
                                        "Score": s["score"],
                                        "Progress": s["progress"],
                                        "Level": s["level"],
                                        "Status": s["status"]
                                    })

                                st.session_state.students_data = pd.DataFrame(new_data)
                                st.success(f"✅ Successfully imported {inserted} students for {school_year}!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.warning("No students were imported")

                    except Exception as e:
                        st.error(f"❌ Import failed: {str(e)}")
                        import traceback

                        with st.expander("Technical details"):
                            st.code(traceback.format_exc())

            except Exception as e:
                st.error(f"Error reading file: {str(e)}")

# =========================================================
# EXPORT
# =========================================================
with col3:
    with st.popover("📤 Export", use_container_width=True):
        st.subheader("Export Students")

        format_type = st.selectbox("Format", ["CSV", "Excel"])
        include_archived = st.checkbox("Include archived students", value=False)

        if st.button("Generate Export", type="primary", use_container_width=True):
            try:
                # Use the updated export function with include_archived parameter
                df_export = export_service.export_students(include_archived=include_archived)

                if df_export.empty:
                    st.warning("No students to export")
                else:
                    # Remove extra_data column if present
                    if 'extra_data' in df_export.columns:
                        df_export = df_export.drop(columns=['extra_data'])

                    # Rename columns for better readability
                    df_export = df_export.rename(columns={
                        'student_id': 'Student ID',
                        'firstName': 'First Name',
                        'lastName': 'Last Name',
                        'score': 'Score',
                        'progress': 'Progress (%)',
                        'level': 'Level',
                        'status': 'Status',
                        'added_on': 'Added On'
                    })

                    if format_type == "CSV":
                        csv_data = df_export.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_data,
                            file_name=f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                            df_export.to_excel(writer, index=False, sheet_name="Students")

                        st.download_button(
                            label="📥 Download Excel",
                            data=buffer.getvalue(),
                            file_name=f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    st.success(f"✅ Exported {len(df_export)} students!")

            except Exception as e:
                st.error(f"Export failed: {str(e)}")
# =========================================================
# SEARCH + FILTER
# =========================================================
search = st.text_input("🔍 Search student by name", placeholder="Type name here...")

filtered = students.copy()

if search:
    filtered = filtered[filtered["Name"].str.contains(search, case=False, na=False)]

col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"📊 Showing {len(filtered)} of {len(students)} students")
with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        try:
            db_students = student_repo.get_all_students()
            fresh_data = []
            for s in db_students:
                fresh_data.append({
                    "student_id": s["student_id"],
                    "Name": f"{s['firstName']} {s['lastName']}",
                    "Score": s["score"],
                    "Progress": s["progress"],
                    "Level": s["level"],
                    "Status": s["status"]
                })
            st.session_state.students_data = pd.DataFrame(fresh_data)
            st.rerun()
        except Exception as e:
            st.error(f"Refresh failed: {str(e)}")

if not filtered.empty:
    # Display without the student_id column and use dataframe index
    display_df = filtered.drop(columns=['student_id', 'Score']).copy()
    # Reset index to start from 1
    display_df.index = range(1, len(display_df) + 1)

    st.dataframe(display_df, use_container_width=True, height=400)
else:
    st.info("No students found. Use the Import button to add students.")

# =========================================================
# PROGRESS BARS
# =========================================================
if not filtered.empty:
    st.subheader("📈 Student Progress Overview")

    for _, row in filtered.head(10).iterrows():
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write(f"**{row['Name']}**")
        with col2:
            st.progress(int(row["Progress"]), text=f"{row['Progress']}%")

    if len(filtered) > 10:
        st.info(f"Showing first 10 of {len(filtered)} students")

# =========================================================
# STATISTICS
# =========================================================
st.subheader("📊 Statistics")

try:
    stats = student_repo.get_statistics()

    if stats["total_students"] > 0:
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("Total Students", stats["total_students"])
        with c2:
            st.metric("Average Score", f"{stats['avg_score']:.1f}")
        with c3:
            st.metric("Average Progress", f"{stats['avg_progress']:.1f}%")
        with c4:
            st.metric("Archived Students", stats["archived_count"])

        with st.expander("📈 Detailed Statistics"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Score Range**")
                st.metric("Min Score", stats["min_score"])
                st.metric("Max Score", stats["max_score"])

                if stats.get("level_distribution"):
                    st.write("**Level Distribution**")
                    for level in stats["level_distribution"]:
                        st.write(f"- {level['level']}: {level['count']} students")

            with col2:
                if stats.get("status_counts"):
                    st.write("**Status Distribution**")
                    for status in stats["status_counts"]:
                        st.write(f"- {status['status']}: {status['count']} students")

                if stats.get("schoolyear_distribution"):
                    st.write("**School Year Distribution**")
                    for sy in stats["schoolyear_distribution"]:
                        st.write(f"- {sy['school_year']}: {sy['count']} students")
    else:
        st.info("No student data available. Use the Import button to add students.")

except Exception as e:
    st.error(f"Error loading statistics: {str(e)}")