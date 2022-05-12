import mysql.connector

class DB():
    def __init__(self, connection):
        self.connect = connection

    def db_insert(self, sql, val, mute=False):
        try:
            mydb = self.connect
            mycursor = mydb.cursor()
            mycursor.execute(sql, val)
            mydb.commit()
            l_row = mycursor.lastrowid
            print("Added!")
            return l_row
        except Exception as e:
            if not mute:
                print(e)
                print((sql,val))

   
