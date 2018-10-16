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
    """Decorator to ensure sync access to the sqlite db.

    Functions decorated with this will have it's access to the sqlite db
    controlled by a global lock to ensure only one access at a time.
    If it's being accessed by another call, it will wait until it's turn
    for aquiring access.

    .. note::

        As the wait is controlled by an asyncio.Lock, the returned
        function is a coroutine, so must be awaited.

    SQlite exceptions are caught by the wrapper, logged, and the data
    returned as `None`.

    A wrapped function must have the optional ``db`` keyword-only
    argument, as it will inject the sqlite3 connection instance for the
    default db, or if an alternative is provided, it will pass it
    instead.

    Example
    -------

    .. code-block:: python3

        @db_access
        def create_tables(*, db=None):
            ...

    """
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
    """Creates the tables required by the bot if not already existing.

    Access is controlled with a coroutine wrapper, so this function
    must be awaited when used.

    Parameters
    ----------
    db: sqlite.Connection, optional
        The sqlite database connection. Not required unless not using
        the default database for Firetail.
    """
    with open(os.path.join(HERE, 'sql', 'tables.sql'), 'r') as f:
        sql = f.read()
    db.executescript(sql)
    db.commit()


@db_access
def select(sql, single=False, *, db=None):
    """Executes a given select query to the sqlite database.

    Access is controlled with a coroutine wrapper, so this function
    must be awaited when used.

    Parameters
    ----------
    sql: `str`
        SQL statement to be executed.
    single: `bool`, optional
        Indicates if a single row and single column is to be returned.
        Default is `False`.
    db: `sqlite.Connection`, optional
        The sqlite database connection. Not required, unless not using
        the default database for Firetail.

    Returns
    -------
    List[Tuple[Any]], Any
        If not `single`, returns a list of tuples of all returned record
        values.
        If `single`, returns the first value from the first record.
        If no returned records, returns None.
    """
    cursor = db.cursor()
    cursor.execute(sql)
    if single:
        data = cursor.fetchone()
        data = data[0] if data else None
    else:
        data = cursor.fetchall()
    return data


@db_access
def select_var(sql, var, single=False, *, db=None):
    """Executes a given select query to the sqlite database with
    placeholder variables.

    Access is controlled with a coroutine wrapper, so this function
    must be awaited when used.

    Parameters
    ----------
    sql: `str`
        SQL statement to be executed.
    var: `tuple`
        Tuple of values to replace placeholders.
    single: `bool`, optional
        Indicates if a single row and single column is to be returned.
        Default is `False`.
    db: `sqlite.Connection`, optional
        The sqlite database connection. Not required, unless not using
        the default database for Firetail.

    Returns
    -------
    List[Tuple[Any]], Any
        If not `single`, returns a list of tuples of all returned record
        values.
        If `single`, returns the first value from the first record.
        If no returned records, returns None.
    """
    cursor = db.cursor()
    cursor.execute(sql, var)
    if single:
        data = cursor.fetchone()
        data = data[0] if data else None
    else:
        data = cursor.fetchall()
    return data


@db_access
def execute_sql(sql, var=None, *, db=None):
    """Executes a given query to the sqlite database with optional
    placeholder variable support.

    Access is controlled with a coroutine wrapper, so this function
    must be awaited when used.

    Parameters
    ----------
    sql: `str`
        SQL statement to be executed.
    var: `tuple`, optional
        Tuple of values to replace placeholders.
    db: `sqlite.Connection`, optional
        The sqlite database connection. Not required, unless not using
        the default database for Firetail.

    Returns
    -------
    List[Tuple[Any]]
        Returns a list of tuples of all returned record values.
        If no returned records, returns an empty list.
    """
    cursor = db.cursor()
    cursor.execute(sql, var)
    db.commit()
