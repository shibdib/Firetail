import sqlite3


async def select_pending(string):
    db = sqlite3.connect('../database/auth.sqlite')
    cursor = db.cursor()
    cursor.execute('''SELECT characterID FROM pendingUsers WHERE authString=''', (string,))
    return cursor.fetchone()
