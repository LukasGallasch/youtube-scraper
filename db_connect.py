class DB:
    def __init__(self, connection):
        self.connect = connection

    def db_insert(self, sql, val):
        try:
            mydb = self.connect
            mycursor = mydb.cursor()
            mycursor.execute(sql, val)
            mydb.commit()
            rows = mycursor.rowcount
            return rows
        except Exception as e:
            print(e)
            print((sql, val))
            exit()

    def db_insertmany(self, sql, val):
        try:
            mydb = self.connect
            mycursor = mydb.cursor()
            mycursor.executemany(sql, val)
            mydb.commit()
            rows = mycursor.rowcount
            return rows
        except Exception as e:
            print(e)
            print(sql, val)
            exit()
