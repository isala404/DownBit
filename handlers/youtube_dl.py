from __future__ import unicode_literals
import sys
import eyed3
from Youtube_DL import youtube_dl
if sys.version_info >= (2, 7):
    pass
else:
    import urllib.request


def youtube_download(name, url, path, quality='480p', mark_watched=False, playlist=False):
    ydl_opts = {'outtmpl': '{}/{} [%(id)s].%(ext)s'.format(path[:-1] if path.endswith('/') else path, name),
                'format': get_quality(quality)}

    if mark_watched:
        ydl_opts = {'username': '',
                    'password': ''}

    if playlist:
        ydl_opts += playlist
        ydl_opts['outtmpl'] = '{}/{}/%(playlist_index)s-%(title)s_[%(id)s].%(ext)s'.format(path[:-1]
                                                                                           if path.endswith('/')
                                                                                           else path, name)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def youtube_download_mp3(track_name, artist_name, album_name, cover_image, path):
    ydl_opts = {'outtmpl': '{}/{} - {} [%(id)s].%(ext)s'.format(path[:-1] if path.endswith('/') else path, artist_name,
                                                                track_name),
                'format': get_quality('MP3')}

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(['ytsearch:{} {} Audio'.format(artist_name, track_name)])

    song_path = \
        [i for i in os.listdir(path) if '{} - {}'.format(ArtistName, TrackName) in i and i.endswith('.mp3')][0]
    saved_name = os.path.join(path, song_path)
    audiofile = eyed3.load(saved_name)
    audiofile.tag.artist = u"{}".format(name.split(';;;')[1])
    audiofile.tag.album = u"{}".format(album)
    audiofile.tag.album_artist = u"{}".format(ArtistName)
    dl_dir = "/tmp/{}-{}.jpg".format(TrackName, ArtistName)
    urllib.request.urlretrieve(img_url, dl_dir)
    audiofile.tag.title = u"{}".format(TrackName)
    audiofile.tag.images.set(3, open(dl_dir, "rb").read(), "image/jpeg", u"")
    audiofile.tag.save()


def get_quality(s):
    if s == '720p':
        return 22
    elif s == 'MP3':
        return 140
    elif s == '480p':
        return '"bestvideo[height<=480][ext=mp4]+bestaudio/[height <=? 480]"'
    else:
        return 18
