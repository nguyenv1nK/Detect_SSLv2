import os.path
import threading
import time
from datetime import datetime

from bcolors import bcolors
from configuration import settings
from .functions import singleton


class Logger:
    _instance = None

    def __init__(self):
        """
        Init function
        logs_folder: Logfile directory
        log_file: log filename
        log_level: Log level
        :return:
        """
        self.logs_folder = os.path.join(settings.current_path, settings.config["logger"]["logs_folder"],
                                        settings.config["plugins"]["plugin_dir"])
        if not os.path.exists(self.logs_folder):
            os.makedirs(os.path.realpath(self.logs_folder))
        if not os.path.exists(self.logs_folder):
            bcolors.error("Cannot create logs folder: " + str(self.logs_folder))
            exit()
        self.log_level = settings.config["logger"]["loglevel"]
        self.log_file = self.log_file = os.path.join(self.logs_folder,
                                                     settings.config["logger"]["logs_file"] + ".log")
        self.moniter_folder = os.path.join(settings.current_path, "moniter", settings.config["plugins"]["plugin_dir"])
        if not os.path.exists(self.moniter_folder):
            os.makedirs(os.path.realpath(self.moniter_folder))
        if not os.path.exists(self.moniter_folder):
            bcolors.error("Cannot create logs folder: " + str(self.moniter_folder))
            exit()
        self.moniter_file = ""
        self.write()
        self.write_moniter()

    def write_moniter(self):
        self.moniter_file = os.path.join(self.moniter_folder, time.strftime(
            "%Y-%m-%d") + ".log")
        if not os.path.exists(self.moniter_file):
            _writer = open(self.moniter_file, "w")
            _writer.close()

    def write(self):
        # logs_folder = os.path.join(self.logs_folder, settings.config["plugins"]["plugin_dir"])
        # if not os.path.exists(self.logs_folder):
        #     os.makedirs(os.path.realpath(self.logs_folder))
        #     if not os.path.exists(self.logs_folder):
        #         bcolors.error("Cannot create logs folder: " + str(self.logs_folder))
        #         exit()
        self.log_file = os.path.join(self.logs_folder, time.strftime(
            "%Y-%m-%d") + ".log")
        if not os.path.exists(self.log_file):
            _writer = open(self.log_file, "w")
            _writer.close()

    def log(self, data, plugin='SboxPlugin', target="_"):
        """
        Write info log functions
        :param target:
        :param plugin:
        :param data: log string
        :return: log string is write and print if log_level is info or all
        """
        try:
            self.write()
            if self.log_level.lower() != "all" and self.log_level.lower() != "info":
                return False
            threading.Lock()
            data_log = "\n{}\t{:<8}\t{:<20}\t{:<10}\t{}".format(str(datetime.now()), "LOG", str(plugin),
                                                                str(target), str(data))
            bcolors.header(data_log)
            _writer = open(self.log_file, "a+")
            _writer.write(data_log)
            _writer.close()
            threading.RLock()
        except Exception as ex:
            bcolors.error("Cannot write info log: " + str(ex))

    def error(self, data, plugin='SboxPlugin', target="_"):
        """
        Write error log functions
        :param target:
        :param plugin:
        :param data: log string
        :return: log string is write and print if log_level is error or all
        """
        try:
            self.write()
            if self.log_level.lower() != "all" and self.log_level.lower() != "error":
                return False
            threading.Lock()
            data_log = "\n{}\t{:<8}\t{:<20}\t{:<10}\t{}".format(str(datetime.now()), "ERROR", str(plugin),
                                                                str(target), str(data))
            # data_log = '\n%s\tERROR\t%20s\t%10s\t\t%s' % (
            #     str(datetime.now()), str(module), str(target), str(data))
            bcolors.error(data_log)
            _writer = open(self.log_file, "a+")
            _writer.write(data_log)
            _writer.close()
            threading.RLock()
        except Exception as ex:
            bcolors.error("Cannot write error log: " + str(ex))

    def info(self, data, plugin='SboxPlugin', target="_"):
        """
        Write error log functions
        :param target:
        :param plugin:
        :param data: log string
        :return: log string is write and print if log_level is error or all
        """
        try:
            self.write()
            if self.log_level.lower() != "all":
                return False
            data_log = "\n{}\t{:<8}\t{:<20}\t{:<10}\t{}".format(str(datetime.now()), "INFO", str(plugin),
                                                                str(target), str(data))
            bcolors.info(data_log)
        except Exception as ex:
            bcolors.error("Cannot write error log: " + str(ex))

    def moniter(self, data, plugin='SboxPlugin', target="_"):
        try:
            self.write_moniter()
            threading.Lock()
            data_log = "\n{}\t{:<10}\t{:<10}\t{}".format(str(datetime.now()), str(plugin), str(target), str(data))
            bcolors.warning(data_log)
            _writer = open(self.moniter_file, "a+")
            _writer.write(data_log)
            _writer.close()
            threading.RLock()
        except Exception as ex:
            bcolors.error("Cannot write info log: " + str(ex))

    def info_log(self, message=None):
        self.info(
            data=str(message), plugin="sbox_plugin")

    def error_log(self, message=None):

        self.error(
            data=str(message), plugin="sbox_plugin")

    def moniter_log(self, message=""):
        self.moniter(
            data=str(message), plugin="sbox_plugin")


logger = singleton(Logger)
