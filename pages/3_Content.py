import streamlit as st
import pandas as pd
import json

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
        /* Make popovers wider */
        div[data-testid="stPopover"] {
            min-width: 800px;
            width: 90vw;
            max-width: 1200px;
        }
        /* Make the popover trigger button full width to match delete button */
        div[data-testid="stPopover"] button {
            width: 190px;
        }
    </style>
""", unsafe_allow_html=True)

# 🔐 Protect
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please login first.")
    st.stop()

show_sidebar()
st.title("🎮 Game Content")
st.write("Manage game levels and content")

# -----------------------------
# INITIALIZE GAMES DATA (with extended Catch Game, Hidden Object, and Mini Puzzle parameters)
# -----------------------------
if "games_data" not in st.session_state:
    st.session_state.games_data = [
        {
            "id": 1,
            "level": "Level 1",
            "game_name": "Catch Game",
            "description": "Catch falling objects to improve hand-eye coordination",
            "difficulty": "Easy",
            "time_limit": 60,
            "points": 100,
            "target_circles": 5,
            "target_squares": 5,
            "target_triangles": 5,
            "starting_lives": 5,
            "points_per_shape": 10,
            "completion_percentage": 100,
            "fall_speed_min": 4,
            "fall_speed_max": 7,
            "spawn_delay": 2.0,
            "basket_speed": 12,
            "question_mode_enabled": True,
            "questions": json.dumps([
                {"shape": "square", "correct": "green", "choices": ["green", "blue"]},
                {"shape": "triangle", "correct": "yellow", "choices": ["yellow", "pink"]},
                {"shape": "circle", "correct": "blue", "choices": ["blue", "green"]}
            ])
        },
        {
            "id": 2,
            "level": "Level 2",
            "game_name": "Hidden Object",
            "description": "Find hidden objects in complex scenes to enhance observation skills",
            "difficulty": "Easy",
            "time_limit": 90,
            "points": 100,
            "toys_to_find": 5,
            "idle_shake_timer": 3,
            "shake_intensity": 4,
            "shake_frequency_x": 12,
            "shake_frequency_y": 15,
            "points_per_object": 10,
            "completion_percentage": 100
        },
        {
            "id": 3,
            "level": "Level 3",
            "game_name": "Mini Puzzle",
            "description": "Solve puzzles to improve problem-solving abilities",
            "difficulty": "Medium",
            "time_limit": 90,
            "points": 100,
            "puzzle_rows": 2,
            "puzzle_cols": 2,
            "points_per_piece": 25,
            "completion_percentage": 100
        },
        {
            "id": 4,
            "level": "Level 4",
            "game_name": "Name and Remember",
            "description": "Memory game to enhance recall and recognition",
            "difficulty": "Medium",
            "time_limit": 90,
            "points": 100
        },
        {
            "id": 5,
            "level": "Level 5",
            "game_name": "Maze Game",
            "description": "Navigate through mazes to improve spatial awareness",
            "difficulty": "Hard",
            "time_limit": 150,
            "points": 100
        },
        {
            "id": 6,
            "level": "Bonus",
            "game_name": "Knowledge Game",
            "description": "Test your knowledge with trivia questions",
            "difficulty": "Hard",
            "time_limit": 120,
            "points": 100
        }
    ]


# Helper to render Catch Game specific fields
def render_catch_game_settings(prefix="", default_values=None):
    if default_values is None:
        default_values = {}
    col1, col2, col3 = st.columns(3)
    with col1:
        circles = st.number_input("Circles to catch", min_value=0, max_value=30,
                                  value=default_values.get("target_circles", 5), key=f"{prefix}circles")
        squares = st.number_input("Squares to catch", min_value=0, max_value=30,
                                  value=default_values.get("target_squares", 5), key=f"{prefix}squares")
        triangles = st.number_input("Triangles to catch", min_value=0, max_value=30,
                                    value=default_values.get("target_triangles", 5), key=f"{prefix}triangles")
    with col2:
        lives = st.number_input("Starting lives", min_value=1, max_value=10,
                                value=default_values.get("starting_lives", 5), key=f"{prefix}lives")
        points_per = st.number_input("Points per catch", min_value=5, max_value=100,
                                     value=default_values.get("points_per_shape", 10), key=f"{prefix}points_per_shape")
        completion = st.slider("Completion required (%)", 50, 100, default_values.get("completion_percentage", 100),
                               key=f"{prefix}completion")
    with col3:
        speed_min = st.number_input("Min fall speed", min_value=1, max_value=15,
                                    value=default_values.get("fall_speed_min", 4), key=f"{prefix}min")
        speed_max = st.number_input("Max fall speed", min_value=1, max_value=15,
                                    value=default_values.get("fall_speed_max", 7), key=f"{prefix}max")
        spawn_delay = st.number_input("Spawn delay (sec)", min_value=0.5, max_value=5.0, step=0.1,
                                      value=default_values.get("spawn_delay", 2.0), key=f"{prefix}delay")
        basket_speed = st.number_input("Basket speed", min_value=5, max_value=20,
                                       value=default_values.get("basket_speed", 12), key=f"{prefix}basket")
    # Question mode
    question_enabled = st.checkbox("Enable question mode (color/shape quiz)",
                                   value=default_values.get("question_mode_enabled", True), key=f"{prefix}q_enabled")

    # Handle questions JSON without showing UI
    if question_enabled:
        if default_values and "questions" in default_values:
            questions_json = default_values["questions"]
        else:
            default_questions = [
                {"shape": "square", "correct": "green", "choices": ["green", "blue"]},
                {"shape": "triangle", "correct": "yellow", "choices": ["yellow", "pink"]},
                {"shape": "circle", "correct": "blue", "choices": ["blue", "green"]}
            ]
            questions_json = json.dumps(default_questions)
    else:
        questions_json = "[]"

    return {
        "target_circles": circles,
        "target_squares": squares,
        "target_triangles": triangles,
        "starting_lives": lives,
        "points_per_shape": points_per,
        "completion_percentage": completion,
        "fall_speed_min": speed_min,
        "fall_speed_max": speed_max,
        "spawn_delay": spawn_delay,
        "basket_speed": basket_speed,
        "question_mode_enabled": question_enabled,
        "questions": questions_json
    }


# Helper to render Hidden Object Game specific fields
def render_hidden_object_settings(prefix="", default_values=None):
    if default_values is None:
        default_values = {}

    col1, col2, col3 = st.columns(3)

    with col1:
        toys_to_find = st.number_input(
            "Number of Toys to Find",
            min_value=3,
            max_value=15,
            value=default_values.get("toys_to_find", 5),
            key=f"{prefix}toys_to_find",
            help="Total number of hidden toys in the scene"
        )

        idle_shake_timer = st.number_input(
            "Idle Shake Timer (seconds)",
            min_value=1,
            max_value=10,
            value=default_values.get("idle_shake_timer", 3),
            key=f"{prefix}idle_shake",
            help="How long before toys start shaking when idle"
        )

    with col2:
        shake_intensity = st.slider(
            "Shake Intensity (pixels)",
            min_value=2,
            max_value=10,
            value=default_values.get("shake_intensity", 4),
            key=f"{prefix}shake_intensity",
            help="How much the toys shake when idle"
        )

        shake_frequency_x = st.slider(
            "Shake Frequency X (Hz)",
            min_value=5,
            max_value=25,
            value=default_values.get("shake_frequency_x", 12),
            key=f"{prefix}shake_freq_x",
            help="Horizontal shake speed"
        )

    with col3:
        shake_frequency_y = st.slider(
            "Shake Frequency Y (Hz)",
            min_value=5,
            max_value=25,
            value=default_values.get("shake_frequency_y", 15),
            key=f"{prefix}shake_freq_y",
            help="Vertical shake speed"
        )

        points_per_object = st.number_input(
            "Points per Object",
            min_value=5,
            max_value=100,
            value=default_values.get("points_per_object", 10),
            key=f"{prefix}points_per",
            help="Points awarded for finding each object"
        )

    # Completion percentage in a separate row
    st.markdown("### 🎯 Game Completion Settings")
    completion_percentage = st.slider(
        "Completion Required (%)",
        min_value=50,
        max_value=100,
        value=default_values.get("completion_percentage", 100),
        key=f"{prefix}completion",
        help="Percentage of toys needed to complete the game"
    )

    return {
        "toys_to_find": toys_to_find,
        "idle_shake_timer": idle_shake_timer,
        "shake_intensity": shake_intensity,
        "shake_frequency_x": shake_frequency_x,
        "shake_frequency_y": shake_frequency_y,
        "points_per_object": points_per_object,
        "completion_percentage": completion_percentage
    }


# Helper to render Mini Puzzle Game specific fields
def render_mini_puzzle_settings(prefix="", default_values=None):
    if default_values is None:
        default_values = {}

    # Calculate points per piece based on total pieces
    def calculate_points_per_piece(rows, cols):
        total_pieces = rows * cols
        # Base points: 100 / total_pieces, then round to nearest 5
        base_points = 100 / total_pieces
        # Round to nearest 5 (minimum 5, maximum 100)
        points = max(5, min(100, round(base_points / 5) * 5))
        return points

    col1, col2 = st.columns(2)

    with col1:
        puzzle_rows = st.selectbox(
            "Puzzle Rows",
            options=[1, 2, 3, 4],
            index=[1, 2, 3, 4].index(default_values.get("puzzle_rows", 2)),
            key=f"{prefix}rows",
            help="Number of rows in the puzzle grid"
        )

        puzzle_cols = st.selectbox(
            "Puzzle Columns",
            options=[1, 2, 3, 4],
            index=[1, 2, 3, 4].index(default_values.get("puzzle_cols", 2)),
            key=f"{prefix}cols",
            help="Number of columns in the puzzle grid"
        )

    with col2:
        total_pieces = puzzle_rows * puzzle_cols
        st.info(f"📊 **Total Pieces:** {total_pieces}")

        # Auto-calculate points per piece based on dimensions
        auto_points = calculate_points_per_piece(puzzle_rows, puzzle_cols)

        # Display as informational text (not editable)
        st.markdown(f"**Points per Piece:** `{auto_points}` points")
        st.caption(
            "✨ Points are automatically calculated based on puzzle size (100 ÷ total pieces, rounded to nearest 5)")

        # Show formula explanation
        st.markdown(f"*Formula: 100 ÷ {total_pieces} = {100 / total_pieces:.1f} → rounded to {auto_points}*")

    st.markdown("### 🎯 Game Completion Settings")
    completion_percentage = st.slider(
        "Completion Required (%)",
        min_value=50,
        max_value=100,
        value=default_values.get("completion_percentage", 100),
        key=f"{prefix}completion",
        help="Percentage of pieces needed to complete the puzzle"
    )

    # Calculate max possible points
    max_points = total_pieces * auto_points
    points_needed = int(max_points * (completion_percentage / 100))
    st.caption(f"💰 **Max Possible Points:** {max_points} points")
    st.caption(f"🎯 **Points needed for {completion_percentage}% completion:** {points_needed} points")

    return {
        "puzzle_rows": puzzle_rows,
        "puzzle_cols": puzzle_cols,
        "points_per_piece": auto_points,
        "completion_percentage": completion_percentage
    }


# -----------------------------
# DISPLAY GAMES BY LEVEL WITH WIDE POPOVER EDIT
# -----------------------------
st.subheader("📚 Game Library")
levels = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Bonus"]
tabs = st.tabs(levels)

for idx, level in enumerate(levels):
    with tabs[idx]:
        level_games = [game for game in st.session_state.games_data if game["level"] == level]
        if level_games:
            for game in level_games:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.markdown(f"### 🎮 {game['game_name']}")
                        st.caption(game['description'])
                    with col2:
                        st.markdown("**Difficulty**")
                        difficulty_color = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}
                        st.write(f"{difficulty_color.get(game['difficulty'], '⚪')} {game['difficulty']}")
                        st.markdown("**Time Limit**")
                        st.write(f"⏱️ {game['time_limit']} sec")
                    with col3:
                        st.markdown("**Points**")
                        st.write(f"⭐ {game['points']}")
                        # Show game-specific stats
                        if "target_circles" in game and game.get("game_name") == "Catch Game":
                            st.markdown("**Targets**")
                            st.write(
                                f"🔵 {game['target_circles']} 🟩 {game['target_squares']} 🔺 {game['target_triangles']}")
                        elif "toys_to_find" in game and game.get("game_name") == "Hidden Object":
                            st.markdown("**Toys**")
                            st.write(f"🧸 {game['toys_to_find']} items")
                            st.markdown("**Points per object**")
                            st.write(f"⭐ {game.get('points_per_object', 10)}")
                        elif "puzzle_rows" in game and game.get("game_name") == "Mini Puzzle":
                            total_pieces = game.get("puzzle_rows", 2) * game.get("puzzle_cols", 2)
                            st.markdown("**Puzzle Size**")
                            st.write(
                                f"🧩 {game.get('puzzle_rows', 2)}x{game.get('puzzle_cols', 2)} ({total_pieces} pieces)")
                            st.markdown("**Points per piece**")
                            st.write(f"⭐ {game.get('points_per_piece', 25)} (auto-calculated)")
                    with col4:
                        st.markdown("**Actions**")

                        # EDIT BUTTON (popover)
                        with st.popover("✏️ Edit", use_container_width=True):
                            st.subheader(f"Edit {game['game_name']}")

                            col_a, col_b = st.columns(2)

                            with col_a:
                                edit_level = st.selectbox(
                                    "Level",
                                    levels,
                                    index=levels.index(game["level"]),
                                    key=f"edit_level_{game['id']}"
                                )
                                edit_game_name = st.text_input(
                                    "Game Name",
                                    value=game["game_name"],
                                    key=f"edit_name_{game['id']}"
                                )
                                edit_description = st.text_area(
                                    "Description",
                                    value=game["description"],
                                    key=f"edit_desc_{game['id']}"
                                )

                            with col_b:
                                edit_difficulty = st.selectbox(
                                    "Difficulty",
                                    ["Easy", "Medium", "Hard"],
                                    index=["Easy", "Medium", "Hard"].index(game["difficulty"]),
                                    key=f"edit_difficulty_{game['id']}"
                                )
                                edit_time_limit = st.number_input(
                                    "Time Limit (seconds)",
                                    min_value=30,
                                    max_value=300,
                                    value=game["time_limit"],
                                    key=f"edit_time_{game['id']}"
                                )
                                edit_points = st.number_input(
                                    "Total Points",
                                    min_value=50,
                                    max_value=500,
                                    value=game["points"],
                                    key=f"edit_points_{game['id']}",
                                    help="Base points awarded for completing the game"
                                )

                            # Catch Game specific settings
                            if game["game_name"] == "Catch Game":
                                st.markdown("### 🎯 Catch Game Specific Settings")
                                defaults = {
                                    "target_circles": game.get("target_circles", 5),
                                    "target_squares": game.get("target_squares", 5),
                                    "target_triangles": game.get("target_triangles", 5),
                                    "starting_lives": game.get("starting_lives", 5),
                                    "points_per_shape": game.get("points_per_shape", 10),
                                    "completion_percentage": game.get("completion_percentage", 100),
                                    "fall_speed_min": game.get("fall_speed_min", 4),
                                    "fall_speed_max": game.get("fall_speed_max", 7),
                                    "spawn_delay": game.get("spawn_delay", 2.0),
                                    "basket_speed": game.get("basket_speed", 12),
                                    "question_mode_enabled": game.get("question_mode_enabled", True),
                                    "questions": game.get("questions", "[]")
                                }
                                catch_updates = render_catch_game_settings(
                                    prefix=f"edit_{game['id']}_",
                                    default_values=defaults
                                )
                            else:
                                catch_updates = None

                            # Hidden Object Game specific settings
                            if game["game_name"] == "Hidden Object":
                                st.markdown("### 🔍 Hidden Object Game Specific Settings")
                                defaults = {
                                    "toys_to_find": game.get("toys_to_find", 5),
                                    "idle_shake_timer": game.get("idle_shake_timer", 3),
                                    "shake_intensity": game.get("shake_intensity", 4),
                                    "shake_frequency_x": game.get("shake_frequency_x", 12),
                                    "shake_frequency_y": game.get("shake_frequency_y", 15),
                                    "points_per_object": game.get("points_per_object", 10),
                                    "completion_percentage": game.get("completion_percentage", 100)
                                }
                                hidden_updates = render_hidden_object_settings(
                                    prefix=f"edit_{game['id']}_",
                                    default_values=defaults
                                )
                            else:
                                hidden_updates = None

                            # Mini Puzzle Game specific settings
                            if game["game_name"] == "Mini Puzzle":
                                st.markdown("### 🧩 Mini Puzzle Specific Settings")
                                defaults = {
                                    "puzzle_rows": game.get("puzzle_rows", 2),
                                    "puzzle_cols": game.get("puzzle_cols", 2),
                                    "points_per_piece": game.get("points_per_piece", 25),
                                    "completion_percentage": game.get("completion_percentage", 100)
                                }
                                puzzle_updates = render_mini_puzzle_settings(
                                    prefix=f"edit_{game['id']}_",
                                    default_values=defaults
                                )
                            else:
                                puzzle_updates = None

                            if st.button("💾 Save Changes", type="primary", key=f"save_{game['id']}"):
                                game["level"] = edit_level
                                game["game_name"] = edit_game_name
                                game["description"] = edit_description
                                game["difficulty"] = edit_difficulty
                                game["time_limit"] = edit_time_limit
                                game["points"] = edit_points

                                if catch_updates:
                                    game.update(catch_updates)

                                if hidden_updates:
                                    game.update(hidden_updates)

                                if puzzle_updates:
                                    game.update(puzzle_updates)

                                for i, g in enumerate(st.session_state.games_data):
                                    if g["id"] == game["id"]:
                                        st.session_state.games_data[i] = game
                                        break

                                st.success("✅ Game updated successfully!")
                                st.rerun()

                        # DELETE BUTTON
                        if st.button("🗑️ Delete", key=f"delete_{game['id']}", use_container_width=True):
                            st.session_state.games_data = [
                                g for g in st.session_state.games_data if g["id"] != game["id"]
                            ]
                            st.rerun()

                    st.divider()
        else:
            st.info(f"No games available for {level}")

# -----------------------------
# STATISTICS SECTION
# -----------------------------
st.divider()
st.subheader("📊 Game Statistics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_games = len(st.session_state.games_data)
    st.metric("Total Games", total_games)
with col2:
    avg_points = sum(game["points"] for game in st.session_state.games_data) / total_games if total_games > 0 else 0
    st.metric("Average Points", f"{avg_points:.0f}")
with col3:
    easy_games = len([g for g in st.session_state.games_data if g["difficulty"] == "Easy"])
    st.metric("Easy Games", easy_games)
with col4:
    hard_games = len([g for g in st.session_state.games_data if g["difficulty"] == "Hard"])
    st.metric("Hard Games", hard_games)