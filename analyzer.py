import logging
import os
from logging.handlers import RotatingFileHandler


class Logger(object):
    def __init__(self, name, path='logs', save_log=0, log_level='Debug'):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.exists('logs'):
            os.makedirs('logs')
        file_name = os.path.join(path, '{}.log'.format(name))

        formatter = logging.Formatter(
            fmt='%(asctime)-10s %(levelname)-10s: %(module)s:%(lineno)-d -  %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

        self.log = logging.getLogger()
        if log_level.lower() == 'critical':
            self.log.setLevel(50)
        elif log_level.lower() == 'debug':
            self.log.setLevel(10)
        elif log_level.lower() == 'error':
            self.log.setLevel(40)
        elif log_level.lower() == 'warning':
            self.log.setLevel(30)
        else:
            self.log.setLevel(20)

        file_handler = RotatingFileHandler(file_name, backupCount=save_log)

        file_handler.setFormatter(formatter)
        self.log.addHandler(file_handler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.log.addHandler(console_handler)

    def info(self, message):
        self.log.info(message)

    def debug(self, message):
        self.log.debug(message)

    def critical(self, message):
        self.log.critical(message)

    def exception(self, message):
        self.log.exception(message)

    def warning(self, message):
        self.log.warning(message)
