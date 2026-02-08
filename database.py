import sqlite3

DB_PATH = 'users.db'

def init_db():
    """Initializes the SQLite database and users table with the full user model."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'en',
                is_premium INTEGER DEFAULT 0
            )
        ''')
        
        # Migration to add missing columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [info[1] for info in cursor.fetchall()]
        
        new_columns = {
            'username': 'TEXT',
            'first_name': 'TEXT',
            'last_name': 'TEXT',
            'language_code': "TEXT DEFAULT 'en'",
            'is_premium': 'INTEGER DEFAULT 0'
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")

async def get_user_language(user_id: int) -> str:
    """Fetches the user's language from the DB, defaulting to 'en'."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT language_code FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 'en'

async def check_and_register_user(user) -> bool:
    """
    Checks if a user exists. If not, adds them to the database with full profile.
    If they exists, it updates their profile. 
    Returns True if the user is new.
    """
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    language_code = user.language_code or 'en'
    is_premium = 1 if user.is_premium else 0

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, language_code, is_premium) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, language_code, is_premium))
            return True
        else:
            # Update existing user info to keep it fresh
            cursor.execute('''
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, is_premium = ?
                WHERE user_id = ?
            ''', (username, first_name, last_name, is_premium, user_id))
            return False

async def update_user_language(user_id: int, new_lang: str):
    """Updates the user's language preference in the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET language_code = ? WHERE user_id = ?', (new_lang, user_id))

async def get_all_users():
    """Returns a list of all registered user IDs."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        return [row[0] for row in cursor.fetchall()]

async def get_user_profile(user_id: int):
    """Returns the full profile of a user."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
