from DownBit import create_logger
import os
import threading

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
        threads.append(crawler)
        crawler.start()

        downloader = threading.Thread(target=plugin.downloader)
        threads.append(downloader)
        downloader.start()

    except Exception as e:
        logger.exception(e)

for threads in threads:
    threads.join()

logger.error("All the Threads has existed")
