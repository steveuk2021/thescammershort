from contextlib import contextmanager
from typing import Iterator

import psycopg

from .config import settings


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set")
    with psycopg.connect(settings.database_url) as conn:
        yield conn
