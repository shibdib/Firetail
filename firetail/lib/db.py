import sqlite3


async def database_management():
    print('Preparing Databases..... ')
    await create_database('/firetail/database/firetail.sqlite')
    await create_tables('/firetail/database/firetail.sqlite')
    print('------')


async def create_connection(db_file):
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
        print('Database: Unable to connect to the database at ' + db_file)

    return None


async def create_table(conn, create_table_sql):
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
        print('Database: Unable to create a table for the database')


async def create_database(db_file):
    """ create a database connection to a SQLite database """
    conn = await create_connection(db_file)
    conn.close()


async def create_tables(db_file):
    conn = await create_connection(db_file)
    if conn is not None:
        # create zkill table
        zkill_table = """ CREATE TABLE IF NOT EXISTS zkill (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        channelid INTEGER NOT NULL,
                                        serverid INTEGER NOT NULL UNIQUE,
                                        groupid	INTEGER NOT NULL,
                                        ownerid INTEGER NOT NULL
                                    ); """
        await create_table(conn, zkill_table)
    else:
        print('Database: Unable to connect to the database at ' + db_file)


async def select(sql):
    await database_management()
    db = await create_connection('database/firetail.sqlite')
    cursor = db.cursor()
    cursor.execute(sql)
    data = cursor.fetchall()
    db.close()
    return data


async def execute_sql(sql, var=None):
    await database_management()
    db = await create_connection('database/firetail.sqlite')
    cursor = db.cursor()
    cursor.execute(sql, var)
    db.commit()
    db.close()
