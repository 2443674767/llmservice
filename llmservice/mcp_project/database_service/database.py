import sqlite3


class DatabaseService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_query(self, query: str):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        connection.close()
        return result
