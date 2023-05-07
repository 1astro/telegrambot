import sqlite3, threading, os

db_local = threading.local()

class Database:
    def __init__(self):
        self.sql = 'INSERT INTO pizzas (name, description, quantity, price) VALUES (?, ?, ?, ?)'
        self.database_name = 'pizzas.db'

    @classmethod
    def get_database(cls, name):
        if not os.path.isfile(name):
            with sqlite3.connect(name) as db:
                cursor = db.cursor()
                cursor.execute('CREATE TABLE pizzas (name TEXT, description TEXT, quantity INTEGER, price REAL)')
                db.commit()

        if not hasattr(db_local, 'db'):
            db_local.db = sqlite3.connect(name)
        if not hasattr(db_local, 'cursor'):
            db_local.cursor = db_local.db.cursor()

        return db_local.db

    @classmethod
    def table_exists(cls, database_name, table_name):
        with sqlite3.connect(database_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))

            return cursor.fetchone() is not None

    def add_item(self, values):
        try:
            with self.get_database(self.database_name) as db:
                cursor = db.cursor()

                # Check if pizza already exist
                cursor.execute("SELECT name FROM pizzas")
                if values[0] in [row[0] for row in cursor.fetchall()]: return False

                # Add the pizza
                cursor.execute(self.sql, values)
                db.commit()

                return True
        except:
            pass

    def remove_item(self, item_name):
        with self.get_database(self.database_name) as db:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM pizzas WHERE name=?', (item_name,))
                        
            if cursor.fetchone():
                cursor.execute("DELETE FROM pizzas WHERE name=?", (item_name,))
                db.commit()

                return True
            else:
                pass

    def update_item(self, item_name, type, value):
        with self.get_database(self.database_name) as db:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM pizzas WHERE name = ?', (item_name,))

            result = cursor.fetchone()

            if not result: return

            cursor.execute(f'UPDATE pizzas SET {type} = ? WHERE name = ?', (value, item_name))
            db.commit()

            return True

    def list_items(self):
        with self.get_database(self.database_name) as db:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM pizzas')
                        
            return cursor.fetchall()