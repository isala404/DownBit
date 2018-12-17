import re
import datetime
import os
import logging.handlers
import logging
import settings

logger = logging.getLogger(__name__)


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


def shell_exe(cmd):
    # logger.debug('executing cmd - ' + cmd)
    try:
        f = os.popen(cmd)
        out = f.read()
        # for line in out.split("\n"):
        #     logger.debug("output " + line)
        return out
    except Exception as e:
        logger.exception(e)


def create_logger(name, path='logs', save_log=0, log_level='Debug'):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_name = os.path.join(path, '{}.log'.format(name))

    formatter = logging.Formatter(
        fmt='%(asctime)-10s %(levelname)-10s: %(module)s:%(lineno)-d -  %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    log = logging.getLogger()
    if log_level.lower() == 'critical':
        log.setLevel(50)
    elif log_level.lower() == 'debug':
        log.setLevel(10)
    elif log_level.lower() == 'error':
        log.setLevel(40)
    elif log_level.lower() == 'warning':
        log.setLevel(30)
    else:
        log.setLevel(20)

    file_handler = logging.handlers.RotatingFileHandler(file_name, backupCount=save_log)
    file_handler.doRollover()
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    return log


def is_downloading_time():
    time = int(datetime.datetime.now().strftime('%H'))
    if time in settings.download_hours:
        return True
    else:
        return False
