import spotipy
import youtube_dl
import eyed3
from urllib.request import urlretrieve as download
from DownBit import *

sp = spotipy.Spotify(
    auth='BQDfnPtqlmpUjr79xm8W6kfVR_GlSo0Lt6mbol3L9ZGHUMPb5ngkE-m-9vm3atsDvJr3omXL8fLWUCwaLw0GgxBt09yeuc_X9SX3NfGIpWk_K89P20kjKWfZmmAall0X99y2-QWoomM9a-2txCtLL3Bk77PeH-vdODPxh0QtKfVuVA')

results = sp.user_playlist_tracks('4G9wQldgTi2uWuI2i2yaWQ', '37i9dQZF1DXdxcBWuJkbcy')
tracks = results['items']
while results['next']:
    results = sp.next(results)
    tracks.extend(results['items'])

for item in tracks:
    track = item['track']
    vid = track['id'],
    track_name = track['name'],
    artist_name = track['artists'][0]['name'],
    album_name = track['album']['name'],
    album_artist = track['album']['artists'][0]['name'],
    image = track['album']['images'][0]['url'],
    release_date = track['album']['release_date']

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'outtmpl': '/root/Music/{} - {} [%(id)s].%(ext)s'.format(safe_filename(artist_name),
                                                                 safe_filename(track_name)),
        'continuedl': True,
        'logger': logger,
        'default_search': 'auto',
        'noplaylist': True,
        'source_address': '0.0.0.0',
        'noprogress': True
    }
    logger.info("[Spotify] Downloading {} by {}".format(track_name, artist_name))
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info("ytsearch:{} {} audio".format(track['artists'][0]['name'], track['name']),
                                download=False)
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
            '{}, {}, {}, {}, {}, {}, {}, {}'.format(vid, track_name, artist_name, album_name,
                                                    album_artist, image, album_artist,
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
