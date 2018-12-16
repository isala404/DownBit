from DownBit import create_logger, is_downloading_time
import os
import threading
import datetime
import time

logger = create_logger('DownBit', path='logs', save_log=5, log_level='Debug')

plugins = []

for plugin in os.listdir('plugins'):
    if not plugin.endswith('.py'):
        continue

    plugin = plugin.replace('.py', '')

    try:
        logger.info("Loading {} Plugin".format(plugin.title()))
        module = __import__('plugins.' + plugin, fromlist=["*"])
        my_class = getattr(module, dir(module)[0])
        instance = my_class()
        if 'crawler' in dir(instance) and 'downloader' in dir(instance):
            plugins.append(instance)
        else:
            logger.error(
                "Unloading {} Plugin due not implementing crawler or downloader methods".format(plugin.title()))

    except Exception as e:
        logger.error("Couldn't Load Plugin {}".format(plugin))
        logger.exception(e)

threads = []
for plugin in plugins:
    try:
        crawler = threading.Thread(target=plugin.crawler)
        crawler.start()
        threads.append(crawler)

        downloader = threading.Thread(target=plugin.downloader)
        downloader.start()
        threads.append(downloader)

    except Exception as e:
        logger.exception(e)

if not is_downloading_time:
    logger.info("All the Downloaders are Paused till the Downloading Hours")

while True:
    try:
        if str(datetime.datetime.now().strftime('%H:%M')) == '08:00':
            # TODO: Send Email
            pass
            time.sleep(120)

        time.sleep(20)
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt Stopping DownBit")
        logger.info("##########################################################")
        logger.info("################### Terminating ##########################")
        logger.info("##########################################################")
        break

