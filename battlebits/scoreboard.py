import sqlite3


class Scoreboard(object):
    def __init__(self, fp):
        self.db = sqlite3.connect(fp)
        self.table_name = 'Scoreboard'
        self.table_name_fortego = 'FortegoScoreboard'
        self.create_table_if_not_exist(self.table_name)
        self.create_table_if_not_exist(self.table_name_fortego)

    def close(self):
        if self.db:
            self.db.close()

    def create_table_if_not_exist(self, table_name):
        cursor = self.db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS ' + table_name + '(id INTEGER PRIMARY KEY, '
                                                                    'game_num INTEGER NOT NULL, '
                                                                    'deck TEXT NOT NULL,'
                                                                    'name TEXT NOT NULL,'
                                                                    'seconds REAL NOT NULL,'
                                                                    'num_bytes INTEGER NOT NULL)')
        self.db.commit()

    def print_top_rows(self, num_rows):
        rows = self.get_top_rows(num_rows)
        for row in rows:
            print row

    def get_top_rows(self, num_rows):
        cursor = self.db.cursor()
        cursor.execute('SELECT game_num, deck, name, seconds, num_bytes FROM ' + self.table_name +
                       ' ORDER BY seconds ASC, num_bytes DESC LIMIT ' + str(num_rows))

        rows = cursor.fetchall()
        return rows

    def insert_row(self, table_name, game_num, deck, name, seconds, num_bytes):
        cursor = self.db.cursor()
        cursor.execute('INSERT INTO ' + table_name +
                       '(game_num, deck, name, seconds, num_bytes) VALUES(?,?,?,?,?)',
                       (game_num, deck, name, seconds, num_bytes))

        self.db.commit()
        return cursor.lastrowid

    def insert_row_anonymous(self, game_num, deck, name, seconds, num_bytes):
        return self.insert_row(self.table_name, game_num, deck, name, seconds, num_bytes)

    def get_last_game_num(self):
        cursor = self.db.cursor()
        cursor.execute('SELECT MAX(game_num) FROM ' + self.table_name)
        last_game_num = cursor.fetchone()[0]
        cursor.execute('SELECT MAX(game_num) FROM ' + self.table_name_fortego)
        last_game_num_fortego = cursor.fetchone()[0]
        result = max(last_game_num, last_game_num_fortego, 0)
        return result

    def get_game_rows(self, game_num):
        result = []
        cursor = self.db.cursor()
        cursor.execute('SELECT game_num, deck, name, seconds, num_bytes FROM ' + self.table_name +
                       ' WHERE game_num=? ORDER BY seconds ASC, num_bytes DESC', (game_num,))
        rows = cursor.fetchall()
        if rows:
            result.extend(rows)
        print('returning from get_game_rows %s' % result)
        return result

    def get_game_rows_fortego(self, game_num):
        result = []
        cursor = self.db.cursor()
        cursor.execute('SELECT game_num, deck, name, seconds, num_bytes FROM ' + self.table_name_fortego +
                       ' WHERE game_num=? ORDER BY seconds ASC, num_bytes DESC', (game_num,))
        rows = cursor.fetchall()
        if rows:
            result.extend(rows)
        return result

    def get_all_rows_fortego(self):
        result = []
        cursor = self.db.cursor()
        cursor.execute('SELECT game_num, deck, name, seconds, num_bytes FROM ' + self.table_name_fortego +
                       ' ORDER BY seconds ASC, num_bytes DESC')

        rows = cursor.fetchall()
        if rows:
            result.extend(rows)
        return result

    def insert_row_fortego(self, game_num, deck, name, seconds, num_bytes):
        return self.insert_row(self.table_name_fortego, game_num, deck, name, seconds, num_bytes)

    def get_fortego_row(self, name):
        cursor = self.db.cursor()
        cursor.execute('SELECT game_num, deck, name, seconds, num_bytes FROM ' + self.table_name_fortego +
                       ' WHERE name=? ORDER BY seconds ASC, num_bytes DESC', (name,))
        rows = cursor.fetchone()
        return rows

    def update_row_fortego(self, game_num, deck, name, seconds, num_bytes):
        cursor = self.db.cursor()
        cursor.execute('UPDATE ' + self.table_name_fortego +
                       ' SET game_num=?, deck=?, seconds=?, num_bytes=? WHERE name=?', (game_num, deck, seconds, num_bytes, name))

        self.db.commit()
        return cursor.lastrowid


FortegoNamesMap = {
    '241': 'Riley',    # f1
    '242': 'Jason',    # f2
    '243': 'Eric',    # f3
    '244': 'Chad',    # f4
    '245': 'Jeremy',    # f5
    '246': 'Randy',    # f6
    '247': 'Travis',    # f7
    '248': 'Matthew',    # f8
    '249': 'Andy',    # f9
    '250': 'Tracy',    # fa
    '251': 'Russ',    # fb
    '252': 'Jen',    # fc
    '253': 'Dan',    # fd
    '254': 'Kevin'    # fe
}

if __name__ == '__main__':
    sb = Scoreboard('test.db')
    print sb.insert_row('1', '35.23454', '10')
    print sb.insert_row('1', '31.6654', '10')
    print sb.insert_row('2', '45.0', '5')
    print sb.insert_row('2', '45.0', '7')
    sb.print_top_rows(20)