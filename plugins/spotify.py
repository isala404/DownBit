import feedparser
import youtube_dl
import DownBit
import spotipy

token = "BQAvCKYqC-bPBZlPLqLV3FckKQKHVt5gLrpY_ShJAsJqFJV_1WogUGi_5UZ4UJpxr3rtjLb4AdDpg0_TB" \
        "W7KhmIEi4txiq4YQnhRGUTE5fQIfOFshouxjHN7bB0k5CUrd_BJ4Fq9R8iCBZIk5MMPvaX1seUw_Q"


class Spotify(DownBit.DownBit):
    def crawler(self):
        try:
            self.c.execute("SELECT seq from sqlite_sequence WHERE name = 'spotify_queue'")
            offset = self.c.fetchone()[0]
            sp = spotipy.Spotify(auth=token)
            results = sp.current_user_saved_tracks()
            self.update_table(results)
            while results['next']:
                results = sp.next(results)
                self.update_table(results)

        except Exception as e:
            self.logger.critical("Critical Error While Phrasing Spotify Feed")
            self.logger.exception(e)

    def update_table(self, tracks):
        for item in tracks['items']:
            track = item['track']

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'logger': self.logger,
                'progress_hooks': [self.youtube_progress_hook],
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

            # TODO: Update Table Fields
            # self.conn.execute('''INSERT INTO spotify_queue(track_name, artist_name, album_name, image, url,
            # total_bytes) VALUES(?, ?, ?, ?, ?, ?)''', (d['entries'][y]['trackname'], d['entries'][y]['artistname'],
            #                                            d['entries'][y]['albumname'], d['entries'][y]['coverimage'],
            #                                            data['entries'][0]['webpage_url'], file_size))

