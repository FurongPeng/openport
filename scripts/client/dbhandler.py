import os
from pysqlite2 import dbapi2 as sqlite

class DBHandler():

    def __init__(self):
        self.connection = sqlite.connect(os.path.join(os.path.expanduser('~'), 'openport.db'))
        self.cursor = self.connection.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY,
            filePath VARCHAR(200),
            server VARCHAR(50),
            port INTEGER,
            pid INTEGER,
            active BOOLEAN
            )
            ''')

    def add_share(self,filePath, server, port, pid):
        self.cursor.execute('select * from shares where filePath = ?', (filePath,))
        if self.cursor.fetchall():
            self.cursor.execute('update shares set active = 0 where filePath = ?', (filePath,))
        self.cursor.execute('insert into shares (filePath, server, port, pid, active) values (?, ?, ?, ?, 1)',  (filePath, server, port, pid))
        self.connection.commit()
        return self.get_share(self.cursor.lastrowid)

    def remove_file(self, id):
        self.cursor.execute('delete from shares where id = ?',  (id,))
        self.connection.commit()

    def get_share(self, id):
        self.cursor.execute('select id, filePath, server, port, pid, active from shares where id = ?', (id,))
        row = self.cursor.fetchone()
        share = Share()
        share.id = row[0]
        share.filePath = row[1]
        share.server = row[2]
        share.server_port = row[3]
        share.pid = row[4]
        share.active = row[5]
        return share


    def get_shares(self):
        self.cursor.execute('select id, filePath, server, port, pid, active from shares where active = 1')

        result = []
        for row in self.cursor:
            share = Share()
            share.id = row[0]
            share.filePath = row[1]
            share.server = row[2]
            share.server_port = row[3]
            share.pid = row[4]
            share.active = row[5]
            result.append(share)

        return result

    def stop_share(self, share):
        self.cursor.execute('update shares set active = 0 where id = ?', (share.id,))
        self.connection.commit()


class Share():
    def __init__(self, id=-1, filePath='', server_ip='', server_port='', pid=-1, active=0):
        self.id = id
        self.filePath = filePath
        self.server = server_ip
        self.server_port = server_port
        self.pid = pid
        self.active = active

    def get_link(self):
        return 'http://%s:%s'%(self.server, self.server_port)

