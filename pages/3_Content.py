import streamlit as st
import pandas as pd
import json
from decimal import Decimal
from database.db_conn import db
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
        /* Make the popover trigger button full width */
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
# DATABASE FUNCTIONS
# -----------------------------

def convert_decimal_to_float(data):
    """Convert Decimal objects to float for Streamlit compatibility"""
    if isinstance(data, dict):
        return {k: convert_decimal_to_float(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimal_to_float(item) for item in data]
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data


def load_games_from_db():
    """Load all games and their settings from database"""
    games = []

    try:
        with db.get_connection() as (conn, cursor):
            # Load all games with their levels
            cursor.execute("""
                SELECT g.*, COALESCE(gl.level_name, 'Bonus') as level
                FROM game g
                LEFT JOIN game_levels gl ON g.level_id = gl.level_id
                ORDER BY g.game_id
            """)
            games_data = cursor.fetchall()

            for game in games_data:
                game_id = game['game_id']
                game_name = game['game_name']

                # Convert to dictionary and add id field for compatibility
                game_dict = convert_decimal_to_float(dict(game))
                game_dict['id'] = game_id

                # Load Catch Game settings
                if game_name == 'Catch Game':
                    cursor.execute("SELECT * FROM catchgamesettings WHERE game_id = %s", (game_id,))
                    settings = cursor.fetchone()
                    if settings:
                        settings = convert_decimal_to_float(settings)
                        game_dict.update(settings)
                    else:
                        # Add default settings if none exist
                        game_dict.update({
                            'target_circles': 5,
                            'target_squares': 5,
                            'target_triangles': 5,
                            'starting_lives': 5,
                            'points_per_shape': 10,
                            'completion_percentage': 100,
                            'fall_speed_min': 4,
                            'fall_speed_max': 7,
                            'spawn_delay': 2.0,
                            'basket_speed': 12
                        })

                # Load Hidden Object settings
                elif game_name == 'Hidden Object':
                    cursor.execute("SELECT * FROM hiddenobjectsettings WHERE game_id = %s", (game_id,))
                    settings = cursor.fetchone()
                    if settings:
                        settings = convert_decimal_to_float(settings)
                        game_dict.update(settings)
                    else:
                        game_dict.update({
                            'toys_to_find': 5,
                            'idle_shake_timer': 3,
                            'shake_intensity': 4,
                            'shake_frequency_x': 12,
                            'shake_frequency_y': 15,
                            'points_per_object': 10,
                            'completion_percentage': 100
                        })

                # Load Mini Puzzle settings
                elif game_name == 'Mini Puzzle':
                    cursor.execute("SELECT * FROM minipuzzlesettings WHERE game_id = %s", (game_id,))
                    settings = cursor.fetchone()
                    if settings:
                        settings = convert_decimal_to_float(settings)
                        game_dict.update(settings)
                    else:
                        game_dict.update({
                            'puzzle_rows': 2,
                            'puzzle_cols': 2,
                            'points_per_piece': 25,
                            'completion_percentage': 100
                        })

                games.append(game_dict)

    except Exception as e:
        st.error(f"Error loading games from database: {e}")
        return []

    return games


def get_levels_from_db():
    """Load all levels from database"""
    try:
        with db.get_connection() as (conn, cursor):
            cursor.execute("SELECT level_id, level_name FROM game_levels ORDER BY level_id")
            levels = cursor.fetchall()
            return [level['level_name'] for level in levels]
    except Exception as e:
        st.error(f"Error loading levels: {e}")
        # Return default levels if table doesn't exist
        return ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Bonus"]


def get_level_id(level_name):
    """Get level_id from level_name"""
    try:
        with db.get_connection() as (conn, cursor):
            cursor.execute("SELECT level_id FROM game_levels WHERE level_name = %s", (level_name,))
            result = cursor.fetchone()
            return result['level_id'] if result else None
    except Exception:
        return None


def save_game_to_db(game):
    """Save or update game and its settings to database"""
    try:
        with db.get_connection() as (conn, cursor):
            game_id = game.get('game_id')
            game_name = game['game_name']
            level_id = get_level_id(game['level'])

            if game_id:  # Update existing game
                # Update game table
                cursor.execute("""
                    UPDATE game 
                    SET game_name = %s, description = %s, difficulty = %s, 
                        time_limit = %s, points = %s, level_id = %s
                    WHERE game_id = %s
                """, (game['game_name'], game['description'], game['difficulty'],
                      game['time_limit'], game['points'], level_id, game_id))

                # Update or insert Catch Game settings
                if game_name == 'Catch Game':
                    # Check if settings exist
                    cursor.execute("SELECT settings_id FROM catchgamesettings WHERE game_id = %s", (game_id,))
                    existing = cursor.fetchone()

                    if existing:
                        cursor.execute("""
                            UPDATE catchgamesettings 
                            SET target_circles = %s, target_squares = %s, target_triangles = %s,
                                starting_lives = %s, points_per_shape = %s, completion_percentage = %s,
                                fall_speed_min = %s, fall_speed_max = %s, spawn_delay = %s,
                                basket_speed = %s
                            WHERE game_id = %s
                        """, (game.get('target_circles', 5), game.get('target_squares', 5),
                              game.get('target_triangles', 5), game.get('starting_lives', 5),
                              game.get('points_per_shape', 10), game.get('completion_percentage', 100),
                              game.get('fall_speed_min', 4), game.get('fall_speed_max', 7),
                              game.get('spawn_delay', 2.0), game.get('basket_speed', 12), game_id))
                    else:
                        cursor.execute("""
                            INSERT INTO catchgamesettings 
                            (game_id, target_circles, target_squares, target_triangles, starting_lives,
                             points_per_shape, completion_percentage, fall_speed_min, fall_speed_max,
                             spawn_delay, basket_speed)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (game_id, game.get('target_circles', 5), game.get('target_squares', 5),
                              game.get('target_triangles', 5), game.get('starting_lives', 5),
                              game.get('points_per_shape', 10), game.get('completion_percentage', 100),
                              game.get('fall_speed_min', 4), game.get('fall_speed_max', 7),
                              game.get('spawn_delay', 2.0), game.get('basket_speed', 12)))

                # Update Hidden Object settings
                elif game_name == 'Hidden Object':
                    cursor.execute("SELECT settings_id FROM hiddenobjectsettings WHERE game_id = %s", (game_id,))
                    existing = cursor.fetchone()

                    if existing:
                        cursor.execute("""
                            UPDATE hiddenobjectsettings 
                            SET toys_to_find = %s, idle_shake_timer = %s, shake_intensity = %s,
                                shake_frequency_x = %s, shake_frequency_y = %s, points_per_object = %s,
                                completion_percentage = %s
                            WHERE game_id = %s
                        """, (game.get('toys_to_find', 5), game.get('idle_shake_timer', 3),
                              game.get('shake_intensity', 4), game.get('shake_frequency_x', 12),
                              game.get('shake_frequency_y', 15), game.get('points_per_object', 10),
                              game.get('completion_percentage', 100), game_id))
                    else:
                        cursor.execute("""
                            INSERT INTO hiddenobjectsettings 
                            (game_id, toys_to_find, idle_shake_timer, shake_intensity,
                             shake_frequency_x, shake_frequency_y, points_per_object, completion_percentage)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (game_id, game.get('toys_to_find', 5), game.get('idle_shake_timer', 3),
                              game.get('shake_intensity', 4), game.get('shake_frequency_x', 12),
                              game.get('shake_frequency_y', 15), game.get('points_per_object', 10),
                              game.get('completion_percentage', 100)))

                # Update Mini Puzzle settings
                elif game_name == 'Mini Puzzle':
                    cursor.execute("SELECT settings_id FROM minipuzzlesettings WHERE game_id = %s", (game_id,))
                    existing = cursor.fetchone()

                    if existing:
                        cursor.execute("""
                            UPDATE minipuzzlesettings 
                            SET puzzle_rows = %s, puzzle_cols = %s, points_per_piece = %s,
                                completion_percentage = %s
                            WHERE game_id = %s
                        """, (game.get('puzzle_rows', 2), game.get('puzzle_cols', 2),
                              game.get('points_per_piece', 25), game.get('completion_percentage', 100), game_id))
                    else:
                        cursor.execute("""
                            INSERT INTO minipuzzlesettings 
                            (game_id, puzzle_rows, puzzle_cols, points_per_piece, completion_percentage)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (game_id, game.get('puzzle_rows', 2), game.get('puzzle_cols', 2),
                              game.get('points_per_piece', 25), game.get('completion_percentage', 100)))

            return True

    except Exception as e:
        st.error(f"Error saving game to database: {e}")
        return False


def insert_default_data():
    """Insert default levels and games if database is empty"""
    try:
        with db.get_connection() as (conn, cursor):
            # Check and insert default levels
            cursor.execute("SELECT COUNT(*) as count FROM game_levels")
            result = cursor.fetchone()

            if result['count'] == 0:
                default_levels = [
                    "Level 1",
                    "Level 2",
                    "Level 3",
                    "Level 4",
                    "Level 5",
                    "Bonus"
                ]
                for level_name in default_levels:
                    cursor.execute("""
                        INSERT INTO game_levels (level_name)
                        VALUES (%s)
                    """, (level_name,))

            # Check if games exist
            cursor.execute("SELECT COUNT(*) as count FROM game")
            result = cursor.fetchone()

            if result['count'] == 0:
                # Get level IDs
                cursor.execute("SELECT level_id, level_name FROM game_levels")
                levels_map = {row['level_name']: row['level_id'] for row in cursor.fetchall()}

                default_games = [
                    {
                        "game_name": "Catch Game",
                        "description": "Catch falling objects to improve hand-eye coordination",
                        "difficulty": "Easy",
                        "time_limit": 60,
                        "points": 100,
                        "level_name": "Level 1",
                        "settings": {
                            "target_circles": 5,
                            "target_squares": 5,
                            "target_triangles": 5,
                            "starting_lives": 5,
                            "points_per_shape": 10,
                            "completion_percentage": 100,
                            "fall_speed_min": 4,
                            "fall_speed_max": 7,
                            "spawn_delay": 2.0,
                            "basket_speed": 12
                        }
                    },
                    {
                        "game_name": "Hidden Object",
                        "description": "Find hidden objects in complex scenes to enhance observation skills",
                        "difficulty": "Easy",
                        "time_limit": 90,
                        "points": 100,
                        "level_name": "Level 2",
                        "settings": {
                            "toys_to_find": 5,
                            "idle_shake_timer": 3,
                            "shake_intensity": 4,
                            "shake_frequency_x": 12,
                            "shake_frequency_y": 15,
                            "points_per_object": 10,
                            "completion_percentage": 100
                        }
                    },
                    {
                        "game_name": "Mini Puzzle",
                        "description": "Solve puzzles to improve problem-solving abilities",
                        "difficulty": "Medium",
                        "time_limit": 90,
                        "points": 100,
                        "level_name": "Level 3",
                        "settings": {
                            "puzzle_rows": 2,
                            "puzzle_cols": 2,
                            "points_per_piece": 25,
                            "completion_percentage": 100
                        }
                    },
                    {
                        "game_name": "Name and Remember",
                        "description": "Memory game to enhance recall and recognition",
                        "difficulty": "Medium",
                        "time_limit": 90,
                        "points": 100,
                        "level_name": "Level 4",
                        "settings": {}
                    },
                    {
                        "game_name": "Maze Game",
                        "description": "Navigate through mazes to improve spatial awareness",
                        "difficulty": "Hard",
                        "time_limit": 150,
                        "points": 100,
                        "level_name": "Level 5",
                        "settings": {}
                    },
                    {
                        "game_name": "Knowledge Game",
                        "description": "Test your knowledge with trivia questions",
                        "difficulty": "Hard",
                        "time_limit": 120,
                        "points": 100,
                        "level_name": "Bonus",
                        "settings": {}
                    }
                ]

                for game_data in default_games:
                    level_id = levels_map.get(game_data['level_name'])
                    cursor.execute("""
                        INSERT INTO game (game_name, description, difficulty, time_limit, points, level_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (game_data['game_name'], game_data['description'],
                          game_data['difficulty'], game_data['time_limit'],
                          game_data['points'], level_id))

                    game_id = cursor.lastrowid

                    if game_data['game_name'] == 'Catch Game':
                        settings = game_data['settings']
                        cursor.execute("""
                            INSERT INTO catchgamesettings 
                            (game_id, target_circles, target_squares, target_triangles, starting_lives,
                             points_per_shape, completion_percentage, fall_speed_min, fall_speed_max,
                             spawn_delay, basket_speed)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (game_id, settings['target_circles'], settings['target_squares'],
                              settings['target_triangles'], settings['starting_lives'],
                              settings['points_per_shape'], settings['completion_percentage'],
                              settings['fall_speed_min'], settings['fall_speed_max'],
                              settings['spawn_delay'], settings['basket_speed']))

                    elif game_data['game_name'] == 'Hidden Object':
                        settings = game_data['settings']
                        cursor.execute("""
                            INSERT INTO hiddenobjectsettings 
                            (game_id, toys_to_find, idle_shake_timer, shake_intensity,
                             shake_frequency_x, shake_frequency_y, points_per_object, completion_percentage)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (game_id, settings['toys_to_find'], settings['idle_shake_timer'],
                              settings['shake_intensity'], settings['shake_frequency_x'],
                              settings['shake_frequency_y'], settings['points_per_object'],
                              settings['completion_percentage']))

                    elif game_data['game_name'] == 'Mini Puzzle':
                        settings = game_data['settings']
                        cursor.execute("""
                            INSERT INTO minipuzzlesettings 
                            (game_id, puzzle_rows, puzzle_cols, points_per_piece, completion_percentage)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (game_id, settings['puzzle_rows'], settings['puzzle_cols'],
                              settings['points_per_piece'], settings['completion_percentage']))

    except Exception as e:
        st.error(f"Error inserting default data: {e}")


# -----------------------------
# HELPER FUNCTIONS FOR GAME SETTINGS
# -----------------------------

def render_catch_game_settings(prefix="", default_values=None):
    if default_values is None:
        default_values = {}

    # Ensure spawn_delay is float
    spawn_delay_value = float(default_values.get("spawn_delay", 2.0))

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
                                      value=spawn_delay_value, key=f"{prefix}delay")
        basket_speed = st.number_input("Basket speed", min_value=5, max_value=20,
                                       value=default_values.get("basket_speed", 12), key=f"{prefix}basket")

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
        "basket_speed": basket_speed
    }


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


def render_mini_puzzle_settings(prefix="", default_values=None):
    if default_values is None:
        default_values = {}

    def calculate_points_per_piece(rows, cols):
        total_pieces = rows * cols
        base_points = 100 / total_pieces
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
        auto_points = calculate_points_per_piece(puzzle_rows, puzzle_cols)
        st.markdown(f"**Points per Piece:** `{auto_points}` points")
        st.caption("✨ Points are automatically calculated based on puzzle size")
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
# INITIALIZE DATABASE AND LOAD DATA
# -----------------------------
insert_default_data()
levels = get_levels_from_db()

# Make sure levels is a list and not empty
if not levels:
    levels = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Bonus"]

st.session_state.games_data = load_games_from_db()

# Check for success message to display (from previous save operation)
if st.session_state.get('show_success', False):
    # Show balloon animation
    st.balloons()
    # Show success message
    st.success(st.session_state.success_message)
    # Clear the flag
    st.session_state.show_success = False
    st.session_state.success_message = ""

# -----------------------------
# DISPLAY GAMES BY LEVEL
# -----------------------------
st.subheader("📚 Game Library")

# Create tabs only if levels exist and is a list
if levels and isinstance(levels, list):
    tabs = st.tabs(levels)

    for idx, level in enumerate(levels):
        with tabs[idx]:
            level_games = [game for game in st.session_state.games_data if game.get("level") == level]
            if level_games:
                for game in level_games:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])
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

                        # EDIT BUTTON
                        with st.popover("✏️ Edit Game", use_container_width=True):
                            st.subheader(f"Edit {game['game_name']}")

                            col_a, col_b = st.columns(2)

                            with col_a:
                                edit_level = st.selectbox(
                                    "Level",
                                    levels,
                                    index=levels.index(game["level"]) if game["level"] in levels else 0,
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

                            # Game specific settings
                            catch_updates = None
                            hidden_updates = None
                            puzzle_updates = None

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
                                    "spawn_delay": float(game.get("spawn_delay", 2.0)),
                                    "basket_speed": game.get("basket_speed", 12)
                                }
                                catch_updates = render_catch_game_settings(
                                    prefix=f"edit_{game['id']}_",
                                    default_values=defaults
                                )

                            elif game["game_name"] == "Hidden Object":
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

                            elif game["game_name"] == "Mini Puzzle":
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

                            if st.button("💾 Save Changes", type="primary", key=f"save_{game['id']}"):
                                # Prepare game data for saving
                                game_data = {
                                    "game_id": game.get('game_id'),
                                    "level": edit_level,
                                    "game_name": edit_game_name,
                                    "description": edit_description,
                                    "difficulty": edit_difficulty,
                                    "time_limit": edit_time_limit,
                                    "points": edit_points
                                }

                                if catch_updates:
                                    game_data.update(catch_updates)
                                if hidden_updates:
                                    game_data.update(hidden_updates)
                                if puzzle_updates:
                                    game_data.update(puzzle_updates)

                                # Save to database
                                if save_game_to_db(game_data):
                                    # Store success message in session state
                                    st.session_state.show_success = True
                                    st.session_state.success_message = f"✅ {game['game_name']} has been updated successfully!"
                                    # Reload games from database
                                    st.session_state.games_data = load_games_from_db()
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to save game!")

                        st.divider()
            else:
                st.info(f"No games available for {level}")
else:
    st.error("No levels found in database. Please check your database connection.")

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