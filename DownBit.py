import analyzer
import sqlite3
import os
import datetime

logger = analyzer.Logger('DownBit', path='logs', save_log=5, log_level='Debug')


class DownBit:
    def __init__(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.logger = logger

        # Connecting to Database
        self.conn = sqlite3.connect('database')
        self.c = self.conn.cursor()

        # Create Tables for Plugins supported by default if they are not present

        self.c.execute('''CREATE TABLE IF NOT EXISTS "youtube_subscriptions" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, 
        `url` TEXT DEFAULT 'https://www.youtube.com/feeds/videos.xml?channel_id=' UNIQUE, `quality` TEXT DEFAULT 
        '720p', `path` TEXT, `includes` TEXT, `excludes` TEXT, `last_match` TEXT, `mark_watched` NUMERIC DEFAULT 0, 
        `active` NUMERIC DEFAULT 1 )''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS "youtube_queue" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `name` TEXT, 
        `url` TEXT UNIQUE, `path` TEXT DEFAULT '/mnt/Youtube/', `quality` TEXT DEFAULT '720p', `added_time` TIMESTAMP 
        DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP, `downloaded_bytes` INTEGER DEFAULT 0, `total_bytes` 
        INTEGER DEFAULT -1, `mark_watched` NUMERIC DEFAULT 0, `is_playlist` NUMERIC DEFAULT 0, `playlist_start` 
        INTEGER DEFAULT 0, `playlist_end` INTEGER DEFAULT -1 )''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS `showrss_subscription` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, 
        `name` TEXT, `url` TEXT UNIQUE, `path` TEXT DEFAULT '/mnt/Movies/', `quality` TEXT DEFAULT '720p', 
        `includes` TEXT, `excludes` TEXT, `active` NUMERIC DEFAULT 1 )''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS `spotify_queue` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, 
        `track_name` INTEGER UNIQUE, `artist_name` INTEGER, `album_name` INTEGER, `image` INTEGER UNIQUE, 
        `added_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP, `downloaded_bytes` INTEGER 
        DEFAULT -1, `total_bytes` INTEGER DEFAULT -1 )''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS `torrent_queue` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, 
        `name` TEXT, `source` TEXT, `magnet_link` TEXT UNIQUE, `path` TEXT DEFAULT '/mnt/', `added_time` TIMESTAMP 
        DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP, `downloaded_bytes` INTEGER DEFAULT -1, `total_bytes` 
        INTEGER DEFAULT -1 )''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS "yts_subscription" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, 
        `name` TEXT, `url` TEXT UNIQUE, `path` TEXT DEFAULT '/mnt/Movies/', `quality` TEXT DEFAULT '720p', 
        `includes` TEXT, `excludes` TEXT, `active` NUMERIC DEFAULT 1 )''')

        # Commit Changes
        self.conn.commit()

    @staticmethod
    def is_match(title, includes, excludes):
        if not includes and not excludes:
            return True

        title.replace(':', '')
        good_entry = True

        if includes:
            for includes_ in includes.split("|"):
                for word in includes_.split(','):
                    if word.strip().lower() in title.strip().lower():
                        good_entry = True
                    else:
                        good_entry = False
                        break

        if not good_entry:
            return False

        if excludes:
            for excludes_ in excludes.split("|"):
                for word in excludes_.split(','):
                    if word.strip().lower() not in title.strip().lower():
                        good_entry = True
                        break
                    else:
                        good_entry = False
                if not good_entry:
                    return False

        return good_entry

    def get_quality(self, quality):
        if quality == '720p':
            return "bestvideo[height<=720]+bestaudio/best[height<=720]"
        if quality == '1080p':
            return "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        elif quality == 'MP3':
            return "140"
        elif quality == '480p':
            return "bestvideo[height<=480]+bestaudio/best[height<=480]"
        elif quality == '360p':
            return "18"
        else:
            self.logger.warning("{} is a Unknown Quality setting Quality to 360p".format(quality))
            return "18"

    def youtube_progress_hook(self, progress, table, vid):
        if progress['status'] == 'downloading':
            downloaded_bytes = progress['status']['downloaded_bytes']
            total_bytes = progress['status']['total_bytes']
            if total_bytes is None:
                total_bytes = progress['status']['total_bytes_estimate']
            if table == 'youtube':
                if total_bytes:
                    self.c.execute("UPDATE `youtube_queue` SET downloaded_bytes=?, total_bytes=? WHERE id=?",
                                   (downloaded_bytes, total_bytes, vid))
                else:
                    self.c.execute("UPDATE `youtube_queue` SET downloaded_bytes=? WHERE id=?",
                                   (downloaded_bytes, vid))
            # TODO: Update Here when Spotify plugin is Done

        elif progress['status'] == 'finished':
            self.c.execute("UPDATE `youtube_queue` SET completed_time=? WHERE id=?",
                           (datetime.datetime.now(), vid))

    @staticmethod
    def date():
        now = datetime.datetime.now()
        return '{}-{}-{}'.format(now.year, now.month, now.day)
