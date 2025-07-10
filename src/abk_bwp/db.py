"""Bing Wallpaper DB definitions."""

from contextlib import contextmanager
from enum import Enum
import os
import sqlite3
from typing import TypedDict


# -----------------------------------------------------------------------------
# SQLlite DB columns
# -----------------------------------------------------------------------------
class DBColumns(Enum):
    """DBColumns to use for the SQLite."""

    PAGE_ID = "pageId"
    COUNTRY = "country"
    DATE = "date"
    PAGE_URL = "pageUrl"


class DbEntry(TypedDict):
    """DbEntry typed dict."""

    pageId: int
    country: str
    date: str
    pageUrl: str


DEFAULT_DB_NAME = "bwp_metadata.db"
DB_BWP_FILE_NAME = os.getenv("BWP_DB_PATH") or os.path.join(os.path.dirname(__file__), DEFAULT_DB_NAME)  # noqa: E501
DB_BWP_TABLE = "pages"

SQL_CREATE_TABLE = f"""
    CREATE TABLE IF NOT EXISTS {DB_BWP_TABLE} (
        {DBColumns.PAGE_ID.value} INTEGER PRIMARY KEY,
        {DBColumns.COUNTRY.value} TEXT NOT NULL,
        {DBColumns.DATE.value} TEXT NOT NULL,
        {DBColumns.PAGE_URL.value} TEXT NOT NULL
    )
"""

SQL_SELECT_EXISTING = f"""
    SELECT {DBColumns.PAGE_ID.value}, {DBColumns.COUNTRY.value}, {DBColumns.DATE.value}
    FROM {DB_BWP_TABLE}
"""  # noqa:  S608

SQL_DELETE_OLD_DATA = f"""
    DELETE FROM {DB_BWP_TABLE}
    WHERE {DBColumns.PAGE_ID.value} NOT IN (
        SELECT {DBColumns.PAGE_ID.value} FROM {DB_BWP_TABLE}
        ORDER BY {DBColumns.PAGE_ID.value} DESC
        LIMIT ?
    )
"""  # noqa: S608


@contextmanager
def db_sqlite_connect(db_file_name: str):
    """Connect to the SQLite DB."""
    conn = None
    db_file = db_file_name
    try:
        conn = sqlite3.connect(db_file)
        yield conn
    finally:
        if conn:
            conn.close()


@contextmanager
def db_sqlite_cursor(conn: sqlite3.Connection):
    """Create a cursor for the SQLite DB."""
    cursor = None
    try:
        cursor = conn.cursor()
        yield cursor
    finally:
        if cursor:
            cursor.close()
