import youtube_dl
from DownBit import *
import spotipy
import sqlite3
import eyed3
from urllib.request import urlretrieve as download
from settings import spotify_token, song_download_path
import logging
import time
import settings

logger = logging.getLogger(__name__)

eyed3.log.setLevel("ERROR")


class Spotify:
    def __init__(self):
        logger.info("Spotify Plugin : Loaded")
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # Connecting to Database
        self.conn = sqlite3.connect('../database')
        self.c = self.conn.cursor()

        self.c.execute('''CREATE TABLE IF NOT EXISTS `spotify_queue` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `track_id` TEXT UNIQUE,
        `track_name` TEXT, `artist_name` TEXT, `album_name` TEXT, `album_artist` TEXT, `image` TEXT, `url` TEXT,
        `release_date` TIMESTAMP, `added_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP,
        `downloaded_bytes` INTEGER DEFAULT -1, `total_bytes` INTEGER DEFAULT -1, 
        UNIQUE(`track_name`, `artist_name`) ON CONFLICT REPLACE )''')

        self.conn.commit()
        self.current_vid = None

    def crawler(self):
        logger.info("Spotify Plugin : Crawler Started")
        while True:
            try:
                self.c.execute("SELECT track_id FROM spotify_queue ORDER BY id DESC LIMIT 1")
                offset = self.c.fetchall()

                if not spotify_token:
                    logger.warning("Spotify Token is Empty, Fill the Token to Continue")
                    return False

                sp = spotipy.Spotify(auth=spotify_token)
                results = sp.current_user_saved_tracks()

                while True:
                    feedback = self.update_table(results, offset)
                    if not results['next'] or not feedback:
                        break
                    results = sp.next(results)

            except Exception as e:
                logger.critical("Critical Error While Phrasing Spotify Feed")
                logger.exception(e)

            time.sleep(settings.crawler_time_out)

    def update_table(self, tracks, offset):

        for item in tracks['items']:
            track = item['track']
            if offset:
                if track['id'] == offset[0][0] or track['id'] == offset[-1][0]:
                    return False

            # noinspection SpellCheckingInspection
            ydl_opts = {
                'format': 'bestaudio/best',
                'default_search': 'auto',
                'noplaylist': True,
                'source_address': '0.0.0.0',
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
            }

            file_size = 0
            logger.debug("Crawling Youtube for '{} {} audio'".format(track['artists'][0]['name'], track['name']))
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    data = ydl.extract_info("ytsearch:{} {} audio".format(track['artists'][0]['name'], track['name']),
                                            download=False)

                if 'filesize' in data['entries'][0]:
                    file_size = data['entries'][0]['filesize']

                self.c.execute('''INSERT INTO spotify_queue(track_id, track_name, artist_name, album_name,
                 album_artist, image, url, release_date, total_bytes) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (track['id'],
                                track['name'],
                                track['artists'][0]['name'],
                                track['album']['name'],
                                track['album']['artists'][0]['name'],
                                track['album']['images'][0]['url'],
                                data['entries'][0]['webpage_url'],
                                track['album']['release_date'],
                                file_size))

                self.conn.commit()
            except Exception as e:
                logger.error(
                    "Error While Crawling for '{} {} audio'".format(track['artists'][0]['name'], track['name']))
                logger.exception(e)
                continue

        return True

    def downloader(self):
        logger.info("Spotify Plugin : Downloader Started")
        while True:
            if not is_downloading_time():
                time.sleep(2)
                continue

            if not os.path.exists(song_download_path):
                os.makedirs(song_download_path)
            self.c.execute(
                "SELECT id, track_name, artist_name, album_name, album_artist, image, url, album_artist, release_date FROM spotify_queue WHERE completed_time IS NULL ")
            for vid, track_name, artist_name, album_name, album_artist, image, url, album_artist, release_date in self.c.fetchall():
                try:
                    self.current_vid = vid
                    # noinspection SpellCheckingInspection
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                        }],
                        'outtmpl': '{}{} - {} [%(id)s].%(ext)s'.format(song_download_path,
                                                                       safe_filename(artist_name.split(",")[0]),
                                                                       safe_filename(track_name)),
                        'continuedl': True,
                        'logger': logger,
                        'progress_hooks': [self.youtube_progress_hook],
                        'default_search': 'auto',
                        'noplaylist': True,
                        'source_address': '0.0.0.0',
                        'noprogress': True
                    }
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        data = ydl.extract_info(url)
                        path = ydl.prepare_filename(data)

                    if not os.path.exists(path):
                        path = '.'.join(path.split('.')[:-1]) + '.mp3'
                    if not os.path.exists(path):
                        path = '.'.join(path.split('.')[:-1]) + '.acc'
                    if not os.path.exists(path):
                        path = '.'.join(path.split('.')[:-1]) + '.wav'

                    if not os.path.exists(path):
                        logger.error('Audio File was not found')
                        logger.error(
                            '{}, {}, {}, {}, {}, {}, {}, {}, {}'.format(vid, track_name, artist_name, album_name,
                                                                        album_artist, image, url, album_artist,
                                                                        release_date))
                        continue

                    dl_dir = "/tmp/{}-{}.jpg".format(safe_filename(track_name), safe_filename(artist_name))
                    download(image, dl_dir)
                    audio_file = eyed3.load(path)
                    audio_file.tag.artist = u"{}".format(artist_name)
                    audio_file.tag.album = u"{}".format(album_name)
                    audio_file.tag.album_artist = u"{}".format(album_artist)
                    audio_file.tag.title = u"{}".format(track_name)
                    audio_file.tag.release_date = u"{}".format(release_date)
                    audio_file.tag.images.set(3, open(dl_dir, "rb").read(), "image/jpeg", u"")
                    audio_file.tag.save()
                except Exception as e:
                    logger.error("Error While Downloading a song")
                    logger.error(
                        '{}, {}, {}, {}, {}, {}, {}, {}, {}'.format(vid, track_name, artist_name, album_name, album_artist,
                                                                    image, url, album_artist, release_date))
                    self.c.execute("UPDATE `spotify_queue` SET completed_time=null WHERE id=?", (self.current_vid,))
                    self.conn.commit()
                    logger.exception(e)

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
                self.c.execute("UPDATE `spotify_queue` SET downloaded_bytes=?, total_bytes=? WHERE id=?",
                               (downloaded_bytes, total_bytes, self.current_vid))
                self.conn.commit()
            else:
                self.c.execute("UPDATE `spotify_queue` SET downloaded_bytes=? WHERE id=?",
                               (downloaded_bytes, self.current_vid))
                self.conn.commit()

        elif progress['status'] == 'finished':
            self.c.execute("UPDATE `spotify_queue` SET completed_time=? WHERE id=?",
                           (datetime.datetime.now(), self.current_vid))
            self.conn.commit()
