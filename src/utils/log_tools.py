# !usr/bin/env python
# encoding: utf-8

import logging
import logging.config
import logging.handlers
from logging import LogRecord
import os
import re
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


class ParallelTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, when='M', interval=1, backupCount=10, encoding=None, delay=False, utc=False,
                 postfix=".log"):
        super().__init__(filename=filename, when=when, interval=interval, backupCount=backupCount, encoding=encoding,
                         delay=delay, utc=utc)
        self.origFileName = filename
        self.when = when.upper()
        self.interval = interval
        self.backupCount = backupCount
        self.utc = utc
        self.postfix = postfix

        if self.when == 'S':
            self.interval = 1  # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$"
        elif self.when == 'M':
            self.interval = 60  # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$"
        elif self.when == 'H':
            self.interval = 60 * 60  # one hour
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24  # one day
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7  # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        currenttime = int(time.time())
        logging.handlers.BaseRotatingHandler.__init__(self, self.calculateFileName(currenttime), 'a', encoding, delay)

        self.extMatch = re.compile(self.extMatch)
        self.interval = self.interval * interval  # multiply by units requested

        self.rolloverAt = self.computeRollover(currenttime)

    def calculateFileName(self, currenttime):
        if self.utc:
            timeTuple = time.gmtime(currenttime)
        else:
            timeTuple = time.localtime(currenttime)

        return self.origFileName.replace(".log", "") + "-" + time.strftime(self.suffix, timeTuple) + self.postfix

    def getFilesToDelete(self, newFileName):
        dirName, fName = os.path.split(self.origFileName)
        dName, newFileName = os.path.split(newFileName)
        if not dirName:
            dirName = './'
        fileNames = os.listdir(dirName)
        result = []
        prefix = fName + "."
        postfix = self.postfix
        prelen = len(prefix)
        postlen = len(postfix)
        for fileName in fileNames:
            if fileName[:prelen] == prefix and fileName[-postlen:] == postfix and len(
                    fileName) - postlen > prelen and fileName != newFileName:
                suffix = fileName[prelen:len(fileName) - postlen]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        currentTime = self.rolloverAt
        newFileName = self.calculateFileName(currentTime)
        newBaseFileName = os.path.abspath(newFileName)
        self.baseFilename = newBaseFileName
        self.mode = 'a'
        self.stream = self._open()

        if self.backupCount > 0:
            for s in self.getFilesToDelete(newFileName):
                try:
                    os.remove(s)
                except:
                    pass

        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval

        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    newRolloverAt = newRolloverAt - 3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    newRolloverAt = newRolloverAt + 3600
        self.rolloverAt = newRolloverAt


class _InfoFilter(logging.Filter):
    def filter(self, record):
        """only use INFO

        筛选, 只需要 INFO 级别以上的log

        :param record:
        :return:
        """
        if logging.INFO <= record.levelno:
            # 已经是INFO级别了
            # 然后利用父类, 返回 1
            return super().filter(record)
        else:
            return 0


class _DebugFilter(logging.Filter):
    def filter(self, record):
        """only use debug

        筛选, 只需要 debug 级别的log

        :param record:
        :return:
        """
        if logging.DEBUG == record.levelno:
            # 已经是INFO级别了
            # 然后利用父类, 返回 1
            return super().filter(record)
        else:
            return 0


class ColorFormatter(logging.Formatter):
    log_colors = {
        'CRITICAL': '\033[0;31m',
        'ERROR': '\033[0;33m',
        'WARNING': '\033[0;35m',
        'INFO': '\033[0;32m',
        'DEBUG': '\033[0;00m',
    }

    def format(self, record: LogRecord) -> str:
        s = super().format(record)

        level_name = record.levelname
        if level_name in self.log_colors:
            return self.log_colors[level_name] + s + '\033[0m'
        return s


def _get_filename(basename='app.log', log_level='info'):
    date_str = datetime.today().strftime('%Y%m%d')
    return ''.join((
        basename, '-', log_level, '.log'))


# @six.add_metaclass(metaclass=Singleton)
class LogFactory(object):
    # 每个日志文件，使用 2GB
    _SINGLE_FILE_MAX_BYTES = 2 * 1024 * 1024 * 1024
    # 轮转数量是 60 个
    _BACKUP_COUNT = 60

    def __init__(self, basename=None):
        # 基于 dictConfig，做再次封装
        self._log_config_dict = {
            'version': 1,

            'disable_existing_loggers': True,

            'formatters': {
                'color': {
                    '()': ColorFormatter,
                    'format': ('[%(asctime)s] [%(levelname)-8s] [pid: %(process)-5d] '
                               '[%(filename)s %(lineno)s %(funcName)s] %(message)s')
                },
                # 开发环境下的配置
                'dev': {
                    'class': 'logging.Formatter',
                    'format': ('[%(asctime)s] [%(levelname)-8s] [pid: %(process)-5d] '
                               '[%(filename)s %(lineno)s %(funcName)s] %(message)s')
                },
                # 生产环境下的格式(越详细越好)
                'prod': {
                    'class': 'logging.Formatter',
                    'format': ('[%(asctime)s] [%(levelname)-8s] [pid: %(process)-5d] '
                               '[%(filename)s %(lineno)s %(funcName)s] %(message)s')
                }

                # 使用UTC时间!!!

            },

            # 针对 LogRecord 的筛选器
            'filters': {
                'info_filter': {
                    '()': _InfoFilter,

                },
                'debug_filter': {
                    '()': _DebugFilter,
                }
            },

            # 处理器(被loggers使用)
            'handlers': {
                'console': {  # 按理来说, console只收集ERROR级别的较好
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'color'
                },

                'file': {
                    'level': 'INFO',
                    '()': ParallelTimedRotatingFileHandler,
                    'filename': _get_filename(basename=basename, log_level='info'),
                    # 'maxBytes': self._SINGLE_FILE_MAX_BYTES,  # 2GB
                    'encoding': 'UTF-8',
                    'when': 'MIDNIGHT',
                    'backupCount': self._BACKUP_COUNT,
                    'formatter': 'dev',
                    'delay': True,
                    'filters': ['info_filter', ]  # only INFO, no ERROR
                },
                'file_error': {
                    'level': 'ERROR',
                    '()': ParallelTimedRotatingFileHandler,
                    'filename': _get_filename(basename=basename, log_level='error'),
                    # 'maxBytes': self._SINGLE_FILE_MAX_BYTES,  # 2GB
                    'encoding': 'UTF-8',
                    'when': 'MIDNIGHT',
                    'backupCount': self._BACKUP_COUNT,
                    'formatter': 'dev',
                    'delay': True,
                },
                'file_debug': {
                    'level': 'DEBUG',
                    '()': ParallelTimedRotatingFileHandler,
                    'filename': _get_filename(basename=basename, log_level='debug'),
                    # 'maxBytes': self._SINGLE_FILE_MAX_BYTES,  # 2GB
                    'encoding': 'UTF-8',
                    'when': 'MIDNIGHT',
                    'backupCount': self._BACKUP_COUNT,
                    'formatter': 'dev',
                    'delay': True,
                    'filters': ['debug_filter', ]  # only DEBUG
                },

            },

            # 真正的logger(by name), 可以有丰富的配置
            'loggers': {
                # 'debug': {
                #     # 输送到3个handler，它们的作用分别如下
                #     #   1. console：控制台输出，方便我们直接查看，只记录ERROR以上的日志就好
                #     #   2. file： 输送到文件，记录INFO以上的日志，方便日后回溯分析
                #     #   3. file_error：输送到文件（与上面相同），但是只记录ERROR级别以上的日志，方便研发人员排错
                #     'handlers': ['file_debug'],
                #     'level': 'DEBUG'
                # },
                # ''代表默认设置
                '': {
                    # 输送到3个handler，它们的作用分别如下
                    #   1. console：控制台输出，方便我们直接查看，只记录ERROR以上的日志就好
                    #   2. file： 输送到文件，记录INFO以上的日志，方便日后回溯分析
                    #   3. file_error：输送到文件（与上面相同），但是只记录ERROR级别以上的日志，方便研发人员排错
                    #   4. file_debug：输送debug等级的日志到文件
                    'handlers': ['console', 'file', 'file_error', 'file_debug'],
                    'level': 'DEBUG'
                },
                # 'zmq_server.py': {
                #     # 输送到3个handler，它们的作用分别如下
                #     #   1. console：控制台输出，方便我们直接查看，只记录ERROR以上的日志就好
                #     #   2. file： 输送到文件，记录INFO以上的日志，方便日后回溯分析
                #     #   3. file_error：输送到文件（与上面相同），但是只记录ERROR级别以上的日志，方便研发人员排错
                #     'handlers': ['console', 'file', 'file_error'],
                #     'level': 'INFO'
                # },

            },
        }

        logging.config.dictConfig(self._log_config_dict)

    @classmethod
    def get_logger(cls, logger_name):
        return logging.getLogger(logger_name)


def get_logger(file_name, logger_name):
    return LogFactory(file_name).get_logger(logger_name)


if __name__ == '__main__':
    SAMPLE_LOGGER = LogFactory('xxx').get_logger('xxx')
    SAMPLE_LOGGER.info("this is info")
    SAMPLE_LOGGER.warning("this is warning")
    SAMPLE_LOGGER.error("this is error")
    SAMPLE_LOGGER.critical("this is critical")
    SAMPLE_LOGGER.debug("this is debug")