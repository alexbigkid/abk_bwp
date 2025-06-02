"""Bing Wallpaper DB definitions."""

from enum import Enum
import os
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
SQL_SELECT_EXISTING = f"SELECT {DBColumns.PAGE_ID.value}, {DBColumns.DATE.value} FROM {DB_BWP_TABLE}"  # noqa: S608
