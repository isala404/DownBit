import analyzer
import sqlite3
import os
import datetime


class DownBit:
    def __init__(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.logger = analyzer.Logger('DownBit', path='logs', save_log=5, log_level='Debug')

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

    # transformers | age, of, extinction
    # 1080p | 4k, 8k
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

    def youtube_progress_hook(self, d):
        if d['status'] == 'finished':
            self.logger.info('Done downloading, now converting ...')

    @staticmethod
    def date():
        now = datetime.datetime.now()
        return '{}-{}-{}'.format(now.year, now.month, now.day)