from DownBit import *
import feedparser
import os
import sqlite3
import settings
import logging
import time

logger = logging.getLogger(__name__)


class ShowRSS:
    def __init__(self):
        logger.info("ShowRSS Plugin : Loaded")
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # Connecting to Database
        self.conn = sqlite3.connect('../database.db', check_same_thread=False)
        self.c = self.conn.cursor()
        self.current_vid = None

        # Create Tables for Plugins supported by default if they are not present

        self.c.execute(
            '''CREATE TABLE IF NOT EXISTS `showrss_subscriptions` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, `path` TEXT DEFAULT '/mnt/Tv Series/', `includes` TEXT, `excludes` TEXT, `last_match` TEXT, `active` NUMERIC DEFAULT 1 );''')

        self.c.execute(
            '''CREATE TABLE IF NOT EXISTS `torrent_queue` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, `url` TEXT UNIQUE, `state` TEXT, `path` TEXT DEFAULT '/mnt/Tv Series/', `added_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP, `downloaded_bytes` INTEGER DEFAULT 0, `total_bytes` INTEGER DEFAULT -1 );''')

        self.conn.commit()

    def crawler(self):
        logger.info("ShowRSS Plugin : Crawler Started")
        while True:
            try:
                self.c.execute("SELECT * FROM showrss_subscriptions")
                rss = feedparser.parse(settings.showrss_url)
                for vid, name, path, includes, excludes, last_match, active in self.c.fetchall():
                    try:
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
                                self.c.execute(
                                    'INSERT INTO torrent_queue(name, url, path) VALUES(?, ?, ?)',
                                    (rss['entries'][y]['title'], rss['entries'][y]['link'], path))

                                self.c.execute('UPDATE showrss_subscriptions SET last_match = ? WHERE ID = ?',
                                               (rss['entries'][y]['link'], vid))
                                self.conn.commit()

                    except Exception as e:
                        logger.error("Error while Processing RSS feed of {}[{}]".format(name, vid))
                        logger.exception(e)

            except Exception as e:
                logger.error("Error in showRSS crawler")
                logger.exception(e)

            time.sleep(settings.crawler_time_out)

    def downloader(self):
        pass
