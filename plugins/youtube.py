import youtube_dl
from DownBit import *
import feedparser
import os
import datetime
import sqlite3
import settings
import logging
import time

logger = logging.getLogger(__name__)


class Youtube:

    def __init__(self):
        logger.info("Youtube Plugin : Loaded")
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # Connecting to Database
        self.conn = sqlite3.connect('../database.db', check_same_thread=False)
        self.c = self.conn.cursor()
        self.current_vid = None

        # Create Tables for Plugins supported by default if they are not present

        self.c.execute('''CREATE TABLE IF NOT EXISTS "youtube_subscriptions" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, 
        `url` TEXT DEFAULT 'https://www.youtube.com/feeds/videos.xml?channel_id=' UNIQUE, `quality` TEXT DEFAULT 
        '720p', `path` TEXT, `includes` TEXT, `excludes` TEXT, `last_match` TEXT, `active` NUMERIC DEFAULT 1 )''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS "youtube_queue" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, 
        `url` TEXT UNIQUE, `path` TEXT DEFAULT '/mnt/Youtube/', `quality` TEXT DEFAULT '720p', `added_time` TIMESTAMP 
        DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP, `downloaded_bytes` INTEGER DEFAULT 0, `total_bytes` 
        INTEGER DEFAULT -1, `is_playlist` NUMERIC DEFAULT 0, `playlist_start` INTEGER DEFAULT 0, 
        `playlist_end` INTEGER DEFAULT -1 )''')

        self.conn.commit()

    def crawler(self):
        logger.info("Youtube Plugin : Crawler Started")
        while True:
            try:
                self.c.execute("SELECT * FROM youtube_subscriptions")
                for vid, name, url, quality, path, includes, excludes, last_match, active in self.c.fetchall():
                    try:
                        if not active:
                            logger.debug("Skipping #{} {}".format(vid, name.strip()))
                            continue
                        logger.debug("Processing #{} {}".format(vid, name.strip()))
                        rss = feedparser.parse(url)
                        i = -1
                        for i, entry in enumerate(rss['entries']):
                            if entry['link'] == last_match:
                                break

                        if i > 6 and last_match is not None:
                            i = 0

                        for y in range(i, -1, -1):
                            if rss['entries'][y]['link'] == last_match:
                                continue

                            if is_match(rss['entries'][y]['title'], includes, excludes):
                                ydl_opts = {
                                    'format': get_quality(quality),
                                    'outtmpl': '/tmp/%(extractor)s-%(id)s-%(title)s.%(ext)s',
                                    'source_address': '0.0.0.0',
                                    'ignoreerrors': True,
                                    'logtostderr': False,
                                    'quiet': True,
                                    'no_warnings': True,
                                    'noprogress': True
                                }
                                file_size = 0
                                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                    data = ydl.extract_info(rss['entries'][y]['link'], download=False)

                                if 'filesize' not in data and 'requested_formats' in data:
                                    for i in data['requested_formats']:
                                        if 'filesize' in i:
                                            file_size += i['filesize']
                                else:
                                    file_size = data['filesize']

                                if not path:
                                    path = "{}{}".format(settings.youtube_download_path, date())

                                self.c.execute(
                                    'INSERT INTO youtube_queue(name, url, path, quality, total_bytes) VALUES(?, ?, ?, ?, ?)',
                                    (rss['entries'][y]['title'], rss['entries'][y]['link'], path, quality, file_size))

                                self.c.execute('UPDATE youtube_subscriptions SET last_match = ? WHERE ID = ?',
                                               (rss['entries'][y]['link'], vid))
                                self.conn.commit()

                    except Exception as e:
                        logger.error("Error while Processing RSS feed of {}[{}]".format(url, vid))
                        logger.exception(e)

            except Exception as e:
                logger.error("Error in youtube crawler")
                logger.exception(e)

            time.sleep(settings.crawler_time_out)

    def downloader(self):
        logger.info("Youtube Plugin : Downloader Started")
        while True:
            if not is_downloading_time():
                time.sleep(2)
                continue

            self.c.execute("SELECT id, name, url, quality, path, is_playlist  FROM youtube_queue")
            for vid, name, url, quality, path, is_playlist in self.c.fetchall():
                self.current_vid = vid
                if not is_playlist:
                    if not os.path.exists(path):
                        os.mkdir(path)
                    self.current_vid = vid
                    ydl_opts = {
                        'format': get_quality(quality),
                        'outtmpl': '{}/%(uploader)s-%(title)s[%(id)s].%(ext)s'.format(path.rstrip('/')),
                        'logger': logger,
                        'continuedl': True,
                        'source_address': '0.0.0.0',
                        'progress_hooks': [self.youtube_progress_hook],
                        'noprogress': True
                    }

                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                # TODO: Handle for Playlist

            time.sleep(settings.downloader_time_out)

    def youtube_progress_hook(self, progress):
        if progress['status'] == 'downloading':
            downloaded_bytes = progress['downloaded_bytes']
            total_bytes = None

            if 'total_bytes' in progress:
                total_bytes = progress['total_bytes']
            elif 'total_bytes_estimate' in progress:
                total_bytes = progress['total_bytes_estimate']

            if total_bytes:
                self.c.execute("UPDATE `youtube_queue` SET downloaded_bytes=?, total_bytes=? WHERE id=?",
                               (downloaded_bytes, total_bytes, self.current_vid))
                self.conn.commit()
            else:
                self.c.execute("UPDATE `youtube_queue` SET downloaded_bytes=? WHERE id=?",
                               (downloaded_bytes, self.current_vid))
                self.conn.commit()

        elif progress['status'] == 'finished':
            self.c.execute("UPDATE `youtube_queue` SET completed_time=? WHERE id=?",
                           (datetime.datetime.now(), self.current_vid))
            self.conn.commit()
