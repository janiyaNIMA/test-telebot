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
            'is_premium': 'INTEGER DEFAULT 0',
            'is_banned': 'INTEGER DEFAULT 0'
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
        
        # Create admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY
            )
        ''')
        
        # Create settings table for global bot settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Create groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                name TEXT PRIMARY KEY
            )
        ''')
        
        # Create user_groups mapping table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_groups (
                user_id INTEGER,
                group_name TEXT,
                PRIMARY KEY (user_id, group_name),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (group_name) REFERENCES groups (name)
            )
        ''')

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

async def add_admin(admin_id: int):
    """Adds an admin to the admins table."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Check if already admin
        cursor.execute('SELECT 1 FROM admins WHERE admin_id = ?', (admin_id,))
        if cursor.fetchone():
            return False  # Already an admin
        cursor.execute('INSERT INTO admins (admin_id) VALUES (?)', (admin_id,))
        return True  # Successfully added

async def remove_admin(admin_id: int):
    """Removes an admin from the admins table."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE admin_id = ?', (admin_id,))
        return cursor.rowcount > 0  # Returns True if an admin was deleted

async def get_all_admins():
    """Returns a list of all admin IDs."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT admin_id FROM admins')
        return [row[0] for row in cursor.fetchall()]

async def is_admin_in_db(user_id: int):
    """Checks if a user is an admin."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE admin_id = ?', (user_id,))
        return cursor.fetchone() is not None

async def get_setting(key: str, default: str = None):
    """Gets a setting value from the settings table."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else default

async def set_setting(key: str, value: str):
    """Sets a setting value in the settings table."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))

async def get_users_by_filter(filter_type: str, filter_value: str = None):
    """Returns users based on a filter."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if filter_type == "all":
            cursor.execute('SELECT * FROM users')
        elif filter_type == "banned":
            cursor.execute('SELECT * FROM users WHERE is_banned = 1')
        elif filter_type == "lang":
            cursor.execute('SELECT * FROM users WHERE language_code = ?', (filter_value,))
        return [dict(row) for row in cursor.fetchall()]

async def toggle_user_ban(user_id: int, ban: bool):
    """Bans or unbans a user."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_banned = ? WHERE user_id = ?', (1 if ban else 0, user_id))
        return cursor.rowcount > 0

async def is_user_banned(user_id: int):
    """Checks if a user is banned."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False

async def add_group(name: str):
    """Creates a new group."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO groups (name) VALUES (?)', (name,))
            return True
        except sqlite3.IntegrityError:
            return False

async def remove_group(name: str):
    """Removes a group and its mappings."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_groups WHERE group_name = ?', (name,))
        cursor.execute('DELETE FROM groups WHERE name = ?', (name,))
        return cursor.rowcount > 0

async def get_all_groups():
    """Returns all group names."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM groups')
        return [row[0] for row in cursor.fetchall()]

async def get_users_in_group(group_name: str):
    """Returns all user IDs in a specific group."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM user_groups WHERE group_name = ?', (group_name,))
        return [row[0] for row in cursor.fetchall()]

async def add_user_to_group(user_id: int, group_name: str):
    """Adds a user to a group."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO user_groups (user_id, group_name) VALUES (?, ?)', (user_id, group_name))
            return True
        except sqlite3.IntegrityError:
            return False
