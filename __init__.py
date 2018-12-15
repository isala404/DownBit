from DownBit import create_logger

from plugins import showrss

logger = create_logger('DownBit', path='logs', save_log=5, log_level='Debug')

sp = showrss.ShowRSS()
sp.crawler()
