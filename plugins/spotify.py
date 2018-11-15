import youtube_dl
import DownBit


class Spotify(DownBit.DownBit):
    def on_startup(self):
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
