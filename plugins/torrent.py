from DownBit import *
import os
import sqlite3
import logging
import time
import settings
import feedparser
import threading

logger = logging.getLogger(__name__)


class Torrent:
    def __init__(self):
        logger.info("Torrent Plugin : Loaded")
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # Connecting to Database
        self.conn = sqlite3.connect('../database.db', check_same_thread=False)
        c = self.conn.cursor()
        self.current_vid = None

        # Create Tables for Plugins supported by default if they are not present
        c.execute(
            '''CREATE TABLE IF NOT EXISTS `torrent_subscriptions` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, `url` TEXT, `path` TEXT DEFAULT '/mnt/', `includes` TEXT, `excludes` TEXT, `last_match` TEXT, `active` NUMERIC DEFAULT 1 );''')

        c.execute(
            '''CREATE TABLE IF NOT EXISTS `torrent_queue` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, `url` TEXT UNIQUE, `state` TEXT, `path` TEXT, `added_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP, `downloaded_bytes` INTEGER DEFAULT 0, `total_bytes` INTEGER DEFAULT -1 );''')

        self.conn.commit()

    def crawler(self):
        c = self.conn.cursor()
        logger.info("Torrent Plugin : Crawler Started")
        deluge_crawler = threading.Thread(target=self.deluge_crawler)
        deluge_crawler.start()
        while True:
            try:
                c.execute("SELECT * FROM torrent_subscriptions")
                for vid, name, url, path, includes, excludes, last_match, active in c.fetchall():
                    try:
                        rss = feedparser.parse(url)
                        if not active:
                            logger.debug("Skipping #{} {}".format(vid, name.strip()))
                            continue
                        logger.debug("Processing #{} {}".format(vid, name.strip()))

                        i = -1
                        for i, entry in enumerate(rss['entries']):
                            if entry['link'] == last_match:
                                break

                        for y in range(i, -1, -1):
                            if rss['entries'][y]['link'] == last_match:
                                continue

                            if is_match(rss['entries'][y]['title'], includes, excludes):
                                c.execute(
                                    'INSERT INTO torrent_queue(name, url, path) VALUES(?, ?, ?)',
                                    (rss['entries'][y]['title'], rss['entries'][y]['link'], path))

                                c.execute('UPDATE torrent_subscriptions SET last_match = ? WHERE ID = ?',
                                          (rss['entries'][y]['link'], vid))
                                self.conn.commit()

                    except Exception as e:
                        logger.error("Error while Processing RSS feed of {}[{}]".format(name, vid))
                        logger.exception(e)

            except Exception as e:
                logger.error("Error in Torrent crawler")
                logger.exception(e)

            time.sleep(settings.crawler_time_out)

    def deluge_crawler(self):
        c = self.conn.cursor()
        logger.info("Torrent Plugin : Deluge Crawler Started")
        while True:
            c.execute("SELECT id,url FROM torrent_queue")
            for tid, link in c.fetchall():
                torrent_id = re.search(r'\b([A-F\d]+)\b', link).group()
                data = shell_exe('deluge-console info').strip().split('\n')

                for idx, info in enumerate(data):
                    if 'ID: ' in info:
                        if torrent_id == info.strip('ID: '):
                            torrent_state = data[idx + 1].strip('State: ')
                            downloaded_size = round(int(data[idx + 1].strip(' ')[1]) * 1048576)
                            total_size = round(int(data[idx + 1].strip(' ')[2].strip('MiB/')) * 1048576)

                            c.execute(
                                'UPDATE torrent_queue SET state = ?, downloaded_bytes = ?, total_bytes = ? WHERE ID = ?',
                                (torrent_state, downloaded_size, total_size, tid))
                            self.conn.commit()
                            break
            if is_downloading_time():
                time.sleep(1)
            else:
                time.sleep(settings.crawler_time_out)

    def downloader(self):
        c = self.conn.cursor()
        logger.info("Torrent Plugin : Downloader Started")
        while True:
            if not is_downloading_time():
                time.sleep(2)
                continue

            c.execute("SELECT id, name, url, path FROM torrent_queue WHERE completed_time IS NULL")
            for ID, name, url, path in c.fetchall():
                if not is_downloading_time():
                    break
                data = shell_exe('deluge-console add "{}" -p "{}"'.format(url, path))

                if 'Torrent added!\n' in data:
                    logger.info("[Torrent] {} was added to deluge queue".format(name))
                    c.execute("UPDATE torrent_queue SET completed_time=? WHERE id=?",
                              (datetime.datetime.now(), ID))
                    self.conn.commit()
                else:
                    logger.error("couldn't add the {}[#{}] to deluge".format(name, ID))

                time.sleep(settings.downloader_time_out)
