import os
import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.getenv("DATABASE_PATH", "data/app.db"))
SCHEMA_PATH = BASE_DIR / "app" / "database" / "init.sql"


def _dict_factory(cursor: sqlite3.Cursor, row: Tuple[Any, ...]) -> Dict[str, Any]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def ensure_database_initialized() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    created = not DB_PATH.exists()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.commit()


@contextmanager
def get_connection(row_factory_dict: bool = True) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        if row_factory_dict:
            conn.row_factory = _dict_factory  # type: ignore[assignment]
        yield conn
    finally:
        conn.close()


def query_one(sql: str, params: Optional[Iterable[Any]] = None) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params or ()))
        return cur.fetchone()  # type: ignore[return-value]


def query_all(sql: str, params: Optional[Iterable[Any]] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params or ()))
        return list(cur.fetchall())  # type: ignore[return-value]


def execute(sql: str, params: Optional[Iterable[Any]] = None) -> int:
    with get_connection() as conn:
        cur = conn.execute(sql, tuple(params or ()))
        conn.commit()
        return int(cur.lastrowid)


def executemany(sql: str, seq_of_params: Iterable[Iterable[Any]]) -> int:
    with get_connection() as conn:
        cur = conn.executemany(sql, list(map(tuple, seq_of_params)))
        conn.commit()
        return cur.rowcount


def smoke_test() -> bool:
    with get_connection() as conn:
        cur = conn.execute("SELECT 1 AS ok")
        row = cur.fetchone()
        return bool(row and row.get("ok") == 1)  # type: ignore[union-attr]


def ensure_admin_user_exists() -> None:
    """Проверяет наличие администратора и создает его при необходимости"""
    import os
    from app.auth.security import hash_password
    
    admin_email = os.getenv("DATABASE_ROOT")
    admin_password = os.getenv("DATABASE_ROOT_PASS")
    
    if not admin_email or not admin_password:
        logging.warning("DATABASE_ROOT or DATABASE_ROOT_PASS not set, skipping admin user creation")
        return
    
    # Проверяем, есть ли уже пользователь с таким email
    existing_user = query_one("SELECT id FROM users WHERE email = ?", (admin_email,))
    if existing_user:
        logging.info(f"Admin user {admin_email} already exists")
        return
    
    # Создаем администратора
    try:
        password_hash = hash_password(admin_password)
        user_id = execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (admin_email, password_hash, "admin")
        )
        logging.info(f"Created admin user {admin_email} with ID {user_id}")
    except Exception as e:
        logging.error(f"Failed to create admin user: {e}")
        raise


