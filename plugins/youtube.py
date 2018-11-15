import youtube_dl
import DownBit
import feedparser


class Youtube(DownBit.DownBit):

    def on_start(self):
        self.logger.info("Starting Youtube Plugin")

    def crawler(self):
        try:
            for vid, name, url, quality, path, includes, excludes, last_match, mark_watched, active in self.c.execute(
                    "SELECT * FROM youtube_subscriptions"):
                try:
                    if not active:
                        self.logger.debug(f"Skipping #{vid} {name.strip()}")
                        continue
                    self.logger.debug(f"Processing #{vid} {name.strip()}")
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

                        if self.is_match(name, includes, excludes):
                            ydl_opts = {
                                'format': self.get_quality(quality),
                                'outtmpl': '/tmp/%(extractor)s-%(id)s-%(title)s.%(ext)s',
                                'logger': self.logger,
                                'source_address': '0.0.0.0',
                                'ignoreerrors': False,
                                'logtostderr': False,
                                'quiet': True,
                                'no_warnings': True
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
                                path = f"/mnt/Youtube/{self.date()}"

                            self.c.execute(
                                'INSERT INTO youtube_queue(name, url, path, quality, total_bytes, '
                                'mark_watched) VALUES(?, ?, ?, ?, ?, ?)',
                                (rss['entries'][y]['title'], rss['entries'][y]['link'], path,
                                 quality, file_size, mark_watched))
                            self.c.execute('UPDATE youtube_subscriptions SET last_match = ? WHERE ID = ?',
                                           (rss['entries'][y]['link'], vid))
                            self.conn.commit()

                except Exception as e:
                    self.logger.error(f"Error while Processing RSS feed of {url}[{vid}]")
                    self.logger.exception(e)

        except Exception as e:
            self.logger.error("Error in crawler")
            self.logger.exception(e)
