import sqlite3


db_name = 'places.db3'


def create_storage():
    """Создание таблиц User и Place в БД"""
    connection = sqlite3.connect(db_name)
    query = '''CREATE TABLE IF NOT EXISTS user (
                        chat_id INTEGER NOT NULL PRIMARY KEY
                        );

                CREATE TABLE IF NOT EXISTS place (
                        place_id TEXT NOT NULL PRIMARY KEY,
                        name TEXT NOT NULL,
                        address TEXT NOT NULL, 
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        photo_id TEXT,
                        visitor_id INTEGER NOT NULL REFERENCES user(chat_id)
                        );'''
    with connection:
        connection.executescript(query)
    connection.close()


def add_user(chat_id):
    connection = sqlite3.connect(db_name)
    with connection:
        connection.execute('''INSERT INTO user (chat_id) VALUES (?);''', (chat_id, ))
    connection.close()
    return chat_id


def add_place(data):
    connection = sqlite3.connect(db_name)
    query = '''
            INSERT INTO place (
                            place_id, 
                            name,
                            address, 
                            latitude,
                            longitude,
                            photo_id,
                            visitor_id) VALUES (?, ?, ?, ?, ?, ?, ?);
                   '''
    with connection:
        connection.executescript('''PRAGMA foreign_keys = ON;''')
        connection.execute(query, data)
    connection.close()


def get_places_names(chat_id):  # Для поиска мест поблизости
    connection = sqlite3.connect(db_name)
    query = '''SELECT place_id, name FROM place WHERE visitor_id = ?;'''
    with connection:
        result = [item for item in connection.execute(query, (chat_id, ))]  # [(place_id, name),...]
    connection.close()
    return result


def get_photo(chat_id, place_name):
    connection = sqlite3.connect(db_name)
    with connection:
        cursor = connection.cursor()
        cursor.execute('''SELECT photo_id FROM place WHERE visitor_id = ? AND name = ?''', (chat_id, place_name))
        photo = cursor.fetchone()
    cursor.close()
    connection.close()
    return photo


def show_list_of_places(chat_id):
    """Для вывода всего списка мест (без фотографий)"""
    connection = sqlite3.connect(db_name)
    with connection:
        cursor = connection.cursor()
        cursor.execute('''SELECT name, address, latitude, longitude FROM place WHERE visitor_id = ?;''', (chat_id, ))
        places = cursor.fetchall()
    cursor.close()
    connection.close()
    return places


def clear_list(chat_id):
    connection = sqlite3.connect(db_name)
    with connection:
        connection.execute('''DELETE FROM place WHERE visitor_id = ?;''', (chat_id, ))
    connection.close()
