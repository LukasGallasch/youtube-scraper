import mysql.connector


class DB():
    def __init__(self, connection):
        self.connect = connection

    def db_execute(self, cmd, all_rows=True):
        try:
            mydb = self.connect
            mycursor = mydb.cursor()
            mycursor.execute(cmd, multi=True)
            if all_rows is True:
                myresult = mycursor.fetchall()
            else:
                myresult = mycursor.fetchone()

            return myresult
        except Exception as e:
            print(e)


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

    def db_insertmany(self, sql, val):
        try:
            mydb = self.connect
            mycursor = mydb.cursor()
            mycursor.executemany(sql, val)
            mydb.commit()
            l_row = mycursor.lastrowid
            return l_row
        except Exception as e:
            print(e)

