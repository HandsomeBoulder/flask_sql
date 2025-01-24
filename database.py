import sqlite3
import traceback
import sys

def create_table(DBname):
    """
    This is a function that creates SQL DB and a specific table for seg data input
    """
    try:
        sqlite_connection = sqlite3.connect(DBname)  # Подключение или создание ДБ
        # Составление запроса о создании таблицы seg_info
        sqlite_create_table_query = '''CREATE TABLE seg_info (
                                    id INTEGER PRIMARY KEY,
                                    word TEXT NOT NULL,
                                    transcription TEXT NOT NULL,
                                    f0_start TEXT NOT NULL,
                                    f0_middle TEXT NOT NULL,
                                    f0_end TEXT NOT NULL);'''

        cursor = sqlite_connection.cursor() # Подключение курсора
        cursor.execute(sqlite_create_table_query)  # Исполнение запроса
        sqlite_connection.commit()  # Приминение изменений в ДБ
        print("Table created")  # Печать логов в терминал
        cursor.close()  # Закрытие курсора

    except sqlite3.Error as error:
        print("Status:", error)  # Печать сообщения об ошибке
    finally:
        if (sqlite_connection):
            sqlite_connection.close()  # Закрытие соединения с ДБ

def add_info(DBname, number, word, transcription, f0_start, f0_middle, f0_end):
    """
    This is a function that adds seg data to a seg_info table in a SQLiteDB
    """
    flag = False  # Инициализация флага об ошибке
    try:
        sqlite_connection = sqlite3.connect(DBname)  # Подключение ДБ
        cursor = sqlite_connection.cursor()  # Открытие курсора
        # Составление запроса о добавлении данных на строки таблицы seg_info
        sqlite_insert_query = f"""INSERT INTO seg_info
                            (id, word, transcription, f0_start, f0_middle, f0_end)  VALUES  ({number}, "{word}", "{transcription}", "{f0_start}", "{f0_middle}", "{f0_end}")"""

        cursor.execute(sqlite_insert_query)  # Исполнение запроса
        sqlite_connection.commit()  # Приминение изменений
        print("Information added")  # Печать логов в терминал
        cursor.close()  # Закрытие курсора

    except sqlite3.Error as error:  # Если произошла ошибка
        print("Исключение", error.args)  # Печать логов исключения в терминал
        if "UNIQUE" in error.args[0]:
            flag = True  # Изменение флага об ошибке
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))  # Печать логов ошибки в терминал
    finally:
        if (sqlite_connection):
            sqlite_connection.close()  # Закрытие соединения с ДБ

    return flag  # Возвращение информации об ошибке

def read_sqlite_table(DBname):
    """
    This is a function that reads all data from seg_info table in a SQLiteDB
    """
    sqlite_connection = sqlite3.connect(DBname, timeout=20)  # Подключение к DB
    data = sqlite_connection.execute("SELECT * FROM seg_info")  # Формирование и исполнение запроса о выборе данных внутри DB
    sentences = []  # Инициализация хранилища строк из таблицы датабазы
    for row in data:  # Каждую строку в объекте дата
        sent = ' '.join(row[1:])  # Превратить в string, чтобы удобнее отображать в DOM
        sentences.append(sent)  # Добавить в список
    sqlite_connection.close()  # Закрыть соединение с DB
        
    return sentences