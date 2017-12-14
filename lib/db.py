import sqlite3


async def database_management(logger):
    logger.info('Preparing Databases..... ')
    await create_database('database/firetail.sqlite', logger)
    await create_tables('database/firetail.sqlite', logger)
    logger.info('------')


async def create_connection(db_file, logger):
    """ create a database connection to the SQLite database
        specified by db_file
    :param logger:
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except:
        logger.error('Database: Unable to connect to the database at ' + db_file)

    return None


async def create_table(conn, create_table_sql, logger):
    """ create a table from the create_table_sql statement
    :param logger:
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except:
        logger.error('Database: Unable to create a table for the database')


async def select_pending(string):
    db = sqlite3.connect('database/auth.sqlite')
    cursor = db.cursor()
    cursor.execute('''SELECT characterID FROM pendingUsers WHERE authString=?''', (string,))
    data = cursor.fetchone()
    return data[0]


async def create_database(db_file, logger):
    """ create a database connection to a SQLite database """
    conn = await create_connection(db_file, logger)
    conn.close()


async def create_tables(db_file, logger):
    conn = await create_connection(db_file, logger)
    if conn is not None:
        # create zkill table
        zkill_table = """ CREATE TABLE IF NOT EXISTS zkill (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        channelid INTEGER NOT NULL,
                                        serverid INTEGER NOT NULL UNIQUE,
                                        groupid	INTEGER NOT NULL,
                                        ownerid INTEGER NOT NULL
                                    ); """
        await create_table(conn, zkill_table, logger)
    else:
        logger.error('Database: Unable to connect to the database at ' + db_file)

