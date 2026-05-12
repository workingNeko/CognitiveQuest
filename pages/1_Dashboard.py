import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.db_conn import db
from utils.sidebar import show_sidebar

st.set_page_config(
    page_title="Cognitive Quest - Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
/* Make cards look better */
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 10px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# 🔐 Auth
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.stop()

show_sidebar()

st.title("📊 Cognitive Quest Dashboard")


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
@st.cache_data(ttl=60)
def load_dashboard_data():
    """Load all dashboard data from database"""
    try:
        # Use the context manager for connections
        with db.get_connection() as (conn, cursor):
            # 1. Get all enrolled students
            cursor.execute("""
                SELECT student_id, firstName, lastName, score, progress, level, status
                FROM student 
                WHERE status = 'Enrolled'
                ORDER BY lastName, firstName
            """)
            students = cursor.fetchall()

            # 2. Get game sessions with student names
            cursor.execute("""
                SELECT 
                    gs.session_id,
                    gs.student_id,
                    CONCAT(s.firstName, ' ', s.lastName) as student_name,
                    g.game_name,
                    gs.score_earned,
                    gs.completion_percentage,
                    gs.status,
                    gs.start_time,
                    gs.end_time
                FROM gamesession gs
                JOIN student s ON gs.student_id = s.student_id
                JOIN game g ON gs.game_id = g.game_id
                WHERE gs.start_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY gs.start_time DESC
            """)
            sessions = cursor.fetchall()

            # 3. Get assessment data
            cursor.execute("""
                SELECT 
                    a.assessment_id,
                    a.student_id,
                    CONCAT(s.firstName, ' ', s.lastName) as student_name,
                    a.assessment_type,
                    a.assesment_score,
                    a.remarks,
                    a.assessed_at
                FROM assessment a
                JOIN student s ON a.student_id = s.student_id
                WHERE a.assessed_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ORDER BY a.assessed_at DESC
            """)
            assessments = cursor.fetchall()

            # 4. Get game logs for recent activity
            cursor.execute("""
                SELECT 
                    gl.log_id,
                    gl.session_id,
                    CONCAT(s.firstName, ' ', s.lastName) as student_name,
                    gl.event_type,
                    gl.event_value,
                    gl.timestamp
                FROM gamelog gl
                JOIN gamesession gs ON gl.session_id = gs.session_id
                JOIN student s ON gs.student_id = s.student_id
                WHERE gl.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY gl.timestamp DESC
                LIMIT 50
            """)
            game_logs = cursor.fetchall()

            # 5. Get game settings statistics
            cursor.execute("""
                SELECT 
                    g.game_name,
                    COUNT(gs.session_id) as total_plays,
                    AVG(gs.score_earned) as avg_score,
                    AVG(gs.completion_percentage) as avg_completion,
                    COUNT(CASE WHEN gs.status = 'completed' THEN 1 END) as completions
                FROM game g
                LEFT JOIN gamesession gs ON g.game_id = gs.game_id
                WHERE gs.start_time >= DATE_SUB(NOW(), INTERVAL 30 DAY) OR gs.start_time IS NULL
                GROUP BY g.game_id, g.game_name
            """)
            game_stats = cursor.fetchall()

            return {
                'students': students,
                'sessions': sessions,
                'assessments': assessments,
                'game_logs': game_logs,
                'game_stats': game_stats
            }

    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        return {
            'students': [],
            'sessions': [],
            'assessments': [],
            'game_logs': [],
            'game_stats': []
        }


def safe_numeric(value, default=0):
    """Safely convert value to numeric"""
    try:
        if value is None:
            return default
        if isinstance(value, dict):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


# Load data
data = load_dashboard_data()

# Convert to DataFrames with safe numeric conversion
students_df = pd.DataFrame(data['students']) if data['students'] else pd.DataFrame()
sessions_df = pd.DataFrame(data['sessions']) if data['sessions'] else pd.DataFrame()
assessments_df = pd.DataFrame(data['assessments']) if data['assessments'] else pd.DataFrame()
game_logs_df = pd.DataFrame(data['game_logs']) if data['game_logs'] else pd.DataFrame()
game_stats_df = pd.DataFrame(data['game_stats']) if data['game_stats'] else pd.DataFrame()

# Safely convert numeric columns
if not students_df.empty:
    if 'score' in students_df.columns:
        students_df['score'] = students_df['score'].apply(safe_numeric)
    if 'progress' in students_df.columns:
        students_df['progress'] = students_df['progress'].apply(safe_numeric)

if not sessions_df.empty:
    if 'score_earned' in sessions_df.columns:
        sessions_df['score_earned'] = sessions_df['score_earned'].apply(safe_numeric)
    if 'completion_percentage' in sessions_df.columns:
        sessions_df['completion_percentage'] = sessions_df['completion_percentage'].apply(safe_numeric)

if not assessments_df.empty:
    if 'assesment_score' in assessments_df.columns:
        assessments_df['assesment_score'] = assessments_df['assesment_score'].apply(safe_numeric)

if not game_stats_df.empty:
    if 'avg_score' in game_stats_df.columns:
        game_stats_df['avg_score'] = game_stats_df['avg_score'].apply(safe_numeric)
    if 'avg_completion' in game_stats_df.columns:
        game_stats_df['avg_completion'] = game_stats_df['avg_completion'].apply(safe_numeric)
    if 'total_plays' in game_stats_df.columns:
        game_stats_df['total_plays'] = game_stats_df['total_plays'].apply(safe_numeric)
    if 'completions' in game_stats_df.columns:
        game_stats_df['completions'] = game_stats_df['completions'].apply(safe_numeric)

# -----------------------------
# TOP METRICS
# -----------------------------
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_students = len(students_df)
    st.metric("📚 Total Students", total_students)

with col2:
    if not sessions_df.empty:
        total_plays = len(sessions_df)
        st.metric("🎮 Game Plays (30d)", total_plays)
    else:
        st.metric("🎮 Game Plays (30d)", 0)

with col3:
    if not sessions_df.empty:
        completed = len(sessions_df[sessions_df['status'] == 'completed'])
        completion_rate = (completed / len(sessions_df)) * 100 if len(sessions_df) > 0 else 0
        st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
    else:
        st.metric("✅ Completion Rate", "0%")

with col4:
    if not assessments_df.empty and 'assesment_score' in assessments_df.columns:
        avg_assessment = assessments_df['assesment_score'].mean()
        st.metric("📝 Avg Assessment", f"{avg_assessment:.1f}")
    else:
        st.metric("📝 Avg Assessment", "N/A")

with col5:
    if not students_df.empty and 'score' in students_df.columns:
        avg_student_score = students_df['score'].mean()
        st.metric("⭐ Avg Student Score", f"{avg_student_score:.1f}")
    else:
        st.metric("⭐ Avg Student Score", "0")

st.divider()

# -----------------------------
# TABS FOR DIFFERENT VIEWS
# -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Performance Overview",
    "🎮 Game Analytics",
    "📝 Assessments",
    "🕐 Recent Activity",
    "👥 Student List"
])

# ========== TAB 1: PERFORMANCE OVERVIEW ==========
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Student Score Distribution")
        if not students_df.empty and 'score' in students_df.columns and len(students_df['score'].dropna()) > 0:
            fig = px.histogram(
                students_df,
                x='score',
                nbins=20,
                title="Distribution of Student Scores",
                labels={'score': 'Score', 'count': 'Number of Students'},
                color_discrete_sequence=['#667eea']
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No student score data available yet")

    with col2:
        st.subheader("Progress Distribution")
        if not students_df.empty and 'progress' in students_df.columns and len(students_df['progress'].dropna()) > 0:
            fig = px.box(
                students_df,
                y='progress',
                title="Progress Range",
                labels={'progress': 'Progress (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No progress data available yet")

    # Level Performance
    st.subheader("Performance by Level")
    if not students_df.empty and 'level' in students_df.columns and 'score' in students_df.columns:
        level_perf = students_df.groupby('level').agg({
            'score': 'mean',
            'progress': 'mean'
        }).reset_index()

        if not level_perf.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Average Score',
                x=level_perf['level'],
                y=level_perf['score'],
                marker_color='#667eea'
            ))
            fig.add_trace(go.Bar(
                name='Average Progress (%)',
                x=level_perf['level'],
                y=level_perf['progress'],
                marker_color='#764ba2'
            ))
            fig.update_layout(
                title="Average Score and Progress by Level",
                barmode='group',
                xaxis_title="Level",
                yaxis_title="Value"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No level data available yet")
    else:
        st.info("No level data available yet")

# ========== TAB 2: GAME ANALYTICS ==========
with tab2:
    if not game_stats_df.empty:
        # Game popularity
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Most Played Games")
            # Filter out games with no plays
            played_games = game_stats_df[game_stats_df['total_plays'] > 0]
            if not played_games.empty:
                fig = px.bar(
                    played_games,
                    x='game_name',
                    y='total_plays',
                    title="Number of Plays per Game",
                    labels={'game_name': 'Game', 'total_plays': 'Total Plays'},
                    color='total_plays',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No game plays recorded yet")

        with col2:
            st.subheader("Game Success Rate")
            played_games = game_stats_df[game_stats_df['total_plays'] > 0].copy()
            if not played_games.empty:
                played_games['success_rate'] = (played_games['completions'] / played_games['total_plays'] * 100).fillna(
                    0)
                fig = px.pie(
                    played_games,
                    values='total_plays',
                    names='game_name',
                    title="Game Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No game data available")

        # Game performance metrics
        st.subheader("Game Performance Metrics")

        # Prepare display data
        display_stats = game_stats_df[game_stats_df['total_plays'] > 0].copy()
        if not display_stats.empty:
            display_stats['avg_score'] = display_stats['avg_score'].round(1)
            display_stats['avg_completion'] = display_stats['avg_completion'].round(1)
            display_stats['success_rate'] = (display_stats['completions'] / display_stats['total_plays'] * 100).round(1)

            st.dataframe(
                display_stats[[
                    'game_name', 'total_plays', 'completions',
                    'avg_score', 'avg_completion', 'success_rate'
                ]].rename(columns={
                    'game_name': 'Game',
                    'total_plays': 'Total Plays',
                    'completions': 'Completed',
                    'avg_score': 'Avg Score',
                    'avg_completion': 'Avg Completion (%)',
                    'success_rate': 'Success Rate (%)'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No game session data available yet. Students need to play games first!")
    else:
        st.info("No game session data available yet. Students need to play games first!")

# ========== TAB 3: ASSESSMENTS ==========
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Assessment Score Distribution")
        if not assessments_df.empty and 'assesment_score' in assessments_df.columns and len(
                assessments_df['assesment_score'].dropna()) > 0:
            fig = px.box(
                assessments_df,
                y='assesment_score',
                points="all",
                title="Assessment Scores",
                labels={'assesment_score': 'Score'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No assessment data available yet")

    with col2:
        st.subheader("Assessment Types")
        if not assessments_df.empty and 'assessment_type' in assessments_df.columns:
            assessment_counts = assessments_df['assessment_type'].value_counts()
            if not assessment_counts.empty:
                fig = px.pie(
                    values=assessment_counts.values,
                    names=assessment_counts.index,
                    title="Assessment Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No assessment data available")
        else:
            st.info("No assessment data available yet")

    # Recent assessments
    st.subheader("📋 Recent Assessments")
    if not assessments_df.empty:
        recent_assessments = assessments_df.head(10)[[
            'student_name', 'assessment_type', 'assesment_score', 'remarks', 'assessed_at'
        ]].copy()
        recent_assessments['assessed_at'] = pd.to_datetime(recent_assessments['assessed_at']).dt.strftime(
            '%Y-%m-%d %H:%M')

        st.dataframe(
            recent_assessments.rename(columns={
                'student_name': 'Student',
                'assessment_type': 'Type',
                'assesment_score': 'Score',
                'remarks': 'Remarks',
                'assessed_at': 'Date'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No assessments recorded yet")

# ========== TAB 4: RECENT ACTIVITY ==========
with tab4:
    # Recent game sessions
    st.subheader("🎮 Recent Game Sessions")
    if not sessions_df.empty:
        recent_sessions = sessions_df.head(20)[[
            'student_name', 'game_name', 'score_earned', 'completion_percentage', 'status', 'start_time'
        ]].copy()

        # Format the dataframe
        recent_sessions['start_time'] = pd.to_datetime(recent_sessions['start_time']).dt.strftime('%Y-%m-%d %H:%M')


        # Add color coding for status
        def color_status(status):
            if status == 'completed':
                return '✅ Completed'
            elif status == 'failed':
                return '❌ Failed'
            else:
                return '⏸️ ' + str(status)


        recent_sessions['status_display'] = recent_sessions['status'].apply(color_status)

        st.dataframe(
            recent_sessions[[
                'student_name', 'game_name', 'score_earned',
                'completion_percentage', 'status_display', 'start_time'
            ]].rename(columns={
                'student_name': 'Student',
                'game_name': 'Game',
                'score_earned': 'Score',
                'completion_percentage': 'Completion (%)',
                'status_display': 'Status',
                'start_time': 'Time'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No game sessions recorded yet")

    st.divider()

    # Game Logs (detailed activity)
    st.subheader("📝 Detailed Game Activity Logs")
    if not game_logs_df.empty:
        # Filter options
        event_filter = st.selectbox(
            "Filter by event type",
            ["All"] + list(game_logs_df['event_type'].unique())
        )

        filtered_logs = game_logs_df
        if event_filter != "All":
            filtered_logs = filtered_logs[filtered_logs['event_type'] == event_filter]

        # Display logs
        display_logs = filtered_logs.head(30)[[
            'student_name', 'event_type', 'event_value', 'timestamp'
        ]].copy()
        display_logs['timestamp'] = pd.to_datetime(display_logs['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

        st.dataframe(
            display_logs.rename(columns={
                'student_name': 'Student',
                'event_type': 'Event',
                'event_value': 'Details',
                'timestamp': 'Time'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No game logs available yet")

# ========== TAB 5: STUDENT LIST ==========
with tab5:
    if not students_df.empty:
        # Search/filter
        search = st.text_input("🔍 Search students", "")

        filtered_students = students_df.copy()
        if search:
            if 'firstName' in filtered_students.columns and 'lastName' in filtered_students.columns:
                filtered_students = filtered_students[
                    filtered_students['firstName'].str.contains(search, case=False, na=False) |
                    filtered_students['lastName'].str.contains(search, case=False, na=False)
                    ]

        # Display student list
        if 'firstName' in filtered_students.columns and 'lastName' in filtered_students.columns:
            display_students = filtered_students[[
                'firstName', 'lastName', 'score', 'progress', 'level', 'status'
            ]].copy()


            # Add performance badge
            def performance_badge(score):
                if score >= 90:
                    return "🏆 Excellent"
                elif score >= 75:
                    return "⭐ Good"
                elif score >= 60:
                    return "📖 Average"
                else:
                    return "⚠️ Needs Improvement"


            display_students['Performance'] = display_students['score'].apply(performance_badge)

            st.dataframe(
                display_students.rename(columns={
                    'firstName': 'First Name',
                    'lastName': 'Last Name',
                    'score': 'Score',
                    'progress': 'Progress (%)',
                    'level': 'Level',
                    'status': 'Status'
                }),
                use_container_width=True,
                hide_index=True
            )

            # Student statistics
            st.subheader("📊 Student Statistics")

            col1, col2, col3 = st.columns(3)

            with col1:
                score_ranges = pd.cut(display_students['score'], bins=[0, 60, 75, 90, 101],
                                      labels=['Below 60', '60-75', '75-90', '90+'])
                range_counts = score_ranges.value_counts()
                if not range_counts.empty:
                    fig = px.pie(values=range_counts.values, names=range_counts.index, title="Score Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No score data")

            with col2:
                progress_ranges = pd.cut(display_students['progress'], bins=[0, 25, 50, 75, 101],
                                         labels=['0-25%', '25-50%', '50-75%', '75-100%'])
                progress_counts = progress_ranges.value_counts()
                if not progress_counts.empty:
                    fig = px.bar(x=progress_counts.index, y=progress_counts.values, title="Progress Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No progress data")

            with col3:
                if 'level' in display_students.columns:
                    level_counts = display_students['level'].value_counts()
                    if not level_counts.empty:
                        fig = px.bar(x=level_counts.index, y=level_counts.values, title="Students by Level")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No level data")
        else:
            st.info("No student data available")
    else:
        st.info("No students enrolled yet")

# -----------------------------
# AUTO-REFRESH OPTION
# -----------------------------
st.divider()
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Refresh Dashboard Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("Data refreshes automatically every 60 seconds")