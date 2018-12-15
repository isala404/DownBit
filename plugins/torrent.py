from DownBit import *
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)


class Torrent:
    def __init__(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # Connecting to Database
        self.conn = sqlite3.connect('../database')
        self.c = self.conn.cursor()
        self.current_vid = None

        # Create Tables for Plugins supported by default if they are not present
        self.c.execute(
            '''CREATE TABLE IF NOT EXISTS `torrent_queue` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, `url` TEXT UNIQUE, `state` TEXT, `path` TEXT, `added_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP, `downloaded_bytes` INTEGER DEFAULT 0, `total_bytes` INTEGER DEFAULT -1 );''')

        self.conn.commit()

    def crawler(self):
        self.c.execute("SELECT id,url FROM torrent_queue")
        for tid, link in self.c.fetchall():
            torrent_id = re.search(r'\b([A-F\d]+)\b', link).group()
            data = shell_exe('deluge-console info').strip().split('\n')

            for idx, info in enumerate(data):
                if 'ID: ' in info:
                    if torrent_id == info.strip('ID: '):
                        torrent_state = data[idx + 1].strip('State: ')
                        downloaded_size = round(int(data[idx + 1].strip(' ')[1]) * 1048576)
                        total_size = round(int(data[idx + 1].strip(' ')[2].strip('MiB/')) * 1048576)

                        self.c.execute(
                            'UPDATE torrent_queue SET state = ?, downloaded_bytes = ?, total_bytes = ? WHERE ID = ?',
                            (torrent_state, downloaded_size, total_size, tid))
                        self.conn.commit()
                        break

    def downloader(self):
        self.c.execute("SELECT id, name, url, path FROM torrent_queue")
        for id, name, url, path in self.c.fetchall():
            data = shell_exe('deluge-console add "{}" -p "{}"'.format(url, path))

            if data == 'Torrent added!\n':
                self.c.execute("UPDATE torrent_queue SET completed_time=? WHERE id=?",
                               (datetime.datetime.now(), id))
                self.conn.commit()
            else:
                logger.error("couldn't add the {}[#{}] to deluge".format(name, id))
