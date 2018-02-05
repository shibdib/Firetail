import sqlite3
from sqlite3 import Error


async def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    finally:
        conn.close()

    return None


async def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    c = conn.cursor()
    c.execute(create_table_sql)


async def create_tables(db):
    if db is not None:
        # create general table
        firetail_table = """ CREATE TABLE IF NOT EXISTS firetail (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        entry TEXT NOT NULL UNIQUE,
                                        value TEXT NOT NULL,
                                        additional_value TEXT DEFAULT NULL
                                    ); """
        await create_table(db, firetail_table)
        # create zkill table
        zkill_table = """ CREATE TABLE IF NOT EXISTS add_kills (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        channelid INTEGER NOT NULL,
                                        serverid INTEGER NOT NULL,
                                        groupid	INTEGER NOT NULL,
                                        ownerid INTEGER NOT NULL,
                                        losses TEXT NOT NULL,
                                        threshold INTEGER NOT NULL
                                    ); """
        await create_table(db, zkill_table)
        # create sov_tracker table
        sov_tracker_table = """ CREATE TABLE IF NOT EXISTS sov_tracker (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        channel_id INTEGER NOT NULL,
                                        fight_type STRING NOT NULL,
                                        system_id INTEGER NOT NULL,
                                        defender_score INTEGER NOT NULL,
                                        attackers_score INTEGER NOT NULL
                                    ); """
        await create_table(db, sov_tracker_table)
        # create tokens table
        tokens_table = """ CREATE TABLE IF NOT EXISTS tokens (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        character_id INTEGER NOT NULL,
                                        discord_id INTEGER NOT NULL,
                                        token TEXT NOT NULL
                                    ); """
        await create_table(db, tokens_table)
    else:
        print('Database: Unable to connect to the database at ' + db_file)


async def select(sql, single = False):
    db = sqlite3.connect('firetail.sqlite')
    await create_tables(db)
    cursor = db.cursor()
    cursor.execute(sql)
    if single:
        data = cursor.fetchone()[0]
    else:
        data = cursor.fetchall()
    db.close()
    return data


async def execute_sql(sql, var=None):
    db = sqlite3.connect('firetail.sqlite')
    await create_tables(db)
    cursor = db.cursor()
    cursor.execute(sql, var)
    db.commit()
    db.close()
