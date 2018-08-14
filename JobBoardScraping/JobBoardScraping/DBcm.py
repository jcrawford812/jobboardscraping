import mysql.connector

class UseDatabase:
    
    def __init__(self, config: dict):
        self.configuartion = config

    def __enter__(self) -> 'cursor':
        self.conn = mysql.connector.connect(**self.configuartion)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        self.conn.commit()
        self.cursor.close()
        self.conn.close()




