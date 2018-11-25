import youtube_dl
from DownBit import *
import spotipy
import sqlite3
import eyed3
from urllib.request import urlretrieve as download
from settings import spotify_token, song_download_path


class Spotify:
    def __init__(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # Connecting to Database
        self.conn = sqlite3.connect('../database')
        self.c = self.conn.cursor()

        self.c.execute('''CREATE TABLE IF NOT EXISTS `spotify_queue` ( `id` INTEGER PRIMARY KEY AUTOINCREMENT, `track_id` TEXT UNIQUE,
        `track_name` TEXT UNIQUE, `artist_name` TEXT, `album_name` TEXT, `album_artist` TEXT, `image` TEXT, `url` TEXT,
        `release_date` TIMESTAMP, `added_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `completed_time` TIMESTAMP,
        `downloaded_bytes` INTEGER DEFAULT -1, `total_bytes` INTEGER DEFAULT -1 )''')

        self.conn.commit()
        self.current_vid = None

    def crawler(self):
        try:
            self.c.execute("SELECT track_id FROM spotify_queue ORDER BY id DESC LIMIT 1")
            offset = self.c.fetchone()[0]

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

    def update_table(self, tracks, offset):
        for item in tracks['items']:
            track = item['track']
            if track['id'] == offset:
                return False
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'default_search': 'auto',
                'noplaylist': True,
                'source_address': '0.0.0.0'
            }

            file_size = 0
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                data = ydl.extract_info(f"{track['artists'][0]['name']} {track['name']} audio",
                                        download=False)

            if 'filesize' in data['entries'][0]:
                file_size = data['entries'][0]['filesize']

            artist_name = ''
            for artist in track['artists']:
                artist_name += artist['name'] + ', '

            artist_name.strip(', ')

            self.conn.execute('''INSERT INTO spotify_queue(track_id, track_name, artist_name, album_name, album_artist, image, url,
            release_date, total_bytes) VALUES(?, ?, ?, ?, ?, ?, ?, ?)''', (track['id'],
                                                                           track['name'], artist_name,
                                                                           track['album']['name'],
                                                                           track['album']['artists'][0]['name'],
                                                                           track['album']['images'][0]['url'],
                                                                           track['album']['release_date'],
                                                                           data['entries'][0]['webpage_url'],
                                                                           file_size))
        return True

    def downloader(self):
        for vid, track_name, artist_name, quality, album_name, image, url, album_artist, release_date in self.c.execute(
                "SELECT id, track_name, artist_name, album_name, image, url, album_artist, release_date FROM spotify_queue"):
            if not os.path.exists(song_download_path):
                os.mkdir(song_download_path)
            self.current_vid = vid
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'outtmpl': f'/{song_download_path}/{artist_name.split(",")[0]} - {track_name}.%(ext)s',
                'continuedl': True,
                'logger': logger,
                'progress_hooks': [self.youtube_progress_hook],
                'default_search': 'auto',
                'noplaylist': True,
                'source_address': '0.0.0.0'
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                data = ydl.extract_info(url)
                path = ydl.prepare_filename(data)

            dl_dir = "/tmp/{}-{}.jpg".format(track_name, artist_name)
            download(image, dl_dir)
            audio_file = eyed3.load(path)
            audio_file.tag.artist = u"{}".format(artist_name)
            audio_file.tag.album = u"{}".format(album_name)
            audio_file.tag.album_artist = u"{}".format(album_artist)
            audio_file.tag.title = u"{}".format(track_name)
            audio_file.tag.release_date = u"{}".format(release_date)
            audio_file.tag.images.set(3, open(dl_dir, "rb").read(), "image/jpeg", u"")
            audio_file.tag.save()

    def youtube_progress_hook(self, progress):
        if progress['status'] == 'downloading':
            downloaded_bytes = progress['status']['downloaded_bytes']
            total_bytes = progress['status']['total_bytes']
            if total_bytes is None:
                total_bytes = progress['status']['total_bytes_estimate']
            if total_bytes:
                self.c.execute("UPDATE `spotify_queue` SET downloaded_bytes=?, total_bytes=? WHERE id=?",
                               (downloaded_bytes, total_bytes, self.current_vid))
            else:
                self.c.execute("UPDATE `spotify_queue` SET downloaded_bytes=? WHERE id=?",
                               (downloaded_bytes, self.current_vid))

        elif progress['status'] == 'finished':
            self.c.execute("UPDATE `spotify_queue` SET completed_time=? WHERE id=?",
                           (datetime.datetime.now(), self.current_vid))
