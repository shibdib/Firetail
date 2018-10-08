import asyncio
import logging
import os
import sqlite3
from functools import wraps

logger = logging.getLogger('firetail.db')

DATABASE = 'firetail.sqlite'
LOCK = asyncio.Lock()
HERE = os.path.dirname(__file__)


def db_access(func):
    def get_db():
        return sqlite3.connect(DATABASE)

    @wraps(func)
    async def access_control(*args, db=None, **kwargs):
        logger.info('Waiting for db access.')
        async with LOCK:
            logger.info('Aquired db access.')
            if not db:
                db = get_db()
            try:
                return func(*args, db=db, **kwargs)
            except sqlite3.Warning as e:
                logger.exception(type(e).__name__, exc_info=e)
                return None
            finally:
                db.close()
                logger.info('Closed db.')

    return access_control


@db_access
def create_tables(*, db=None):
    with open(os.path.join(HERE, 'sql', 'tables.sql'), 'r') as f:
        sql = f.read()
    db.executescript(sql)
    db.commit()


@db_access
def select(sql, single=False, *, db=None):
    cursor = db.cursor()
    cursor.execute(sql)
    if single:
        data = cursor.fetchone()[0]
    else:
        data = cursor.fetchall()
    return data


@db_access
def select_var(sql, var, single=False, *, db=None):
    cursor = db.cursor()
    cursor.execute(sql, var)
    if single:
        data = cursor.fetchone()[0]
    else:
        data = cursor.fetchall()
    return data


@db_access
def get_token(sql, single=False, *, db=None):
    cursor = db.cursor()
    cursor.execute(sql)
    if single:
        data = cursor.fetchone()[0]
    else:
        data = cursor.fetchall()
    return data


@db_access
def execute_sql(sql, var=None, *, db=None):
    cursor = db.cursor()
    cursor.execute(sql, var)
    db.commit()
