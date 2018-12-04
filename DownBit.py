import re
import analyzer
import sqlite3
import os
import datetime

logger = analyzer.Logger('DownBit', path='logs', save_log=5, log_level='Debug')


class DownBit:

    def __init__(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Connecting to Database
        self.conn = sqlite3.connect('database')
        self.c = self.conn.cursor()

        # Create Tables for Plugins supported by default if they are not present

        self.c.execute('''CREATE TABLE IF NOT EXISTS `showrss_subscription` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, 
        `name` TEXT, `url` TEXT UNIQUE, `path` TEXT DEFAULT '/mnt/Movies/', `quality` TEXT DEFAULT '720p', 
        `includes` TEXT, `excludes` TEXT, `active` NUMERIC DEFAULT 1 )''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS `torrent_queue` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, 
        `name` TEXT, `source` TEXT, `magnet_link` TEXT UNIQUE, `path` TEXT DEFAULT '/mnt/', `added_time` TIMESTAMP 
        DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP, `downloaded_bytes` INTEGER DEFAULT -1, `total_bytes` 
        INTEGER DEFAULT -1 )''')

        self.c.execute('''CREATE TABLE IF NOT EXISTS "yts_subscription" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, 
        `name` TEXT, `url` TEXT UNIQUE, `path` TEXT DEFAULT '/mnt/Movies/', `quality` TEXT DEFAULT '720p', 
        `includes` TEXT, `excludes` TEXT, `active` NUMERIC DEFAULT 1 )''')

        # Commit Changes
        self.conn.commit()


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


def get_quality(quality):
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
        logger.warning("{} is a Unknown Quality setting Quality to 360p".format(quality))
        return "18"


def date():
    now = datetime.datetime.now()
    return '{}-{}-{}'.format(now.year, now.month, now.day)


def safe_filename(name):
    name = name.replace('"', '')
    name = name.replace('/', '')
    name = name.replace('\\', '')
    name = name.replace("'", '')
    name = name.encode('ascii', errors='ignore').decode()
    return re.sub(' +', ' ', name)
