import sqlite3
import os
import logging
from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.vendor.memobase_server.connectors import init_db as init_memo_db, Session as MemoSession
from app.vendor.memobase_server.models.database import Project as MemoProject

# Configure logging
logger = logging.getLogger(__name__)

def run_migrations(alembic_cfg_path: str, db_url: str = None, tag: str = "main"):
    """Generic function to run alembic migrations."""
    print(f"Running Alembic migrations for [{tag}]...")
    try:
        if not os.path.exists(alembic_cfg_path):
            print(f"Warning: alembic.ini not found at {alembic_cfg_path}. Skipping migrations for {tag}.")
            return

        alembic_cfg = Config(alembic_cfg_path)
        if db_url:
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        # In case we are running from a different directory, adjust script_location if it is relative
        # script_location = alembic_cfg.get_main_option("script_location")
        # if not os.path.isabs(script_location):
        #     base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        #     alembic_cfg.set_main_option("script_location", os.path.join(base_dir, script_location))

        command.upgrade(alembic_cfg, "head")
        print(f"Alembic migrations for [{tag}] applied successfully.")
    except Exception as e:
        print(f"Error running Alembic migrations for [{tag}]: {e}")

def init_db():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    # --- 1. Main Database initialization ---
    db_path = os.path.join(settings.DATA_DIR, "doudou.db")
    sql_path = os.path.join(os.path.dirname(__file__), "init.sql")
    
    needs_init = not os.path.exists(db_path) or os.path.getsize(db_path) == 0
    if needs_init:
        print(f"Initializing main database at {db_path}...")
        try:
            conn = sqlite3.connect(db_path)
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            conn.executescript(sql_script)
            conn.commit()
            conn.close()
            print("Main database initialized successfully with init.sql.")
        except Exception as e:
            print(f"Error initializing main database: {e}")
            # If main init fails, we probably shouldn't continue
            return
    else:
        print("Main database already exists. Skipping SQL initialization.")

    # --- 2. Run Main Alembic Migrations ---
    main_alembic_cfg = os.path.join(base_dir, "alembic.ini")
    run_migrations(main_alembic_cfg, settings.SQLALCHEMY_DATABASE_URI, tag="main")

    # --- 3. Run Memobase SDK migrations ---
    memo_alembic_cfg = os.path.join(base_dir, "app", "vendor", "memobase_server", "alembic.ini")
    run_migrations(memo_alembic_cfg, settings.MEMOBASE_DB_URL, tag="memobase")

    # --- 4. Initialize Memobase Static Data ---
    print("Initializing Memobase static data...")
    try:
        init_memo_db(settings.MEMOBASE_DB_URL)
        with MemoSession() as session:
            MemoProject.initialize_root_project(session)
        print("Memobase static data initialized successfully.")
    except Exception as e:
        print(f"Error initializing Memobase static data: {e}")