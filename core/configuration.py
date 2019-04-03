
import json
import os
import sys

from .bcolors import bcolors
from .functions import singleton


class Configuration:
    _instance = None

    def __init__(self):
        self.current_path = os.path.normpath(os.path.join(os.path.realpath(__file__), '../../'))
        self.config_filename = 'application.json'
        # self.config_filename = 'application_test.json'
        self.config = self.load_config(self.config_filename)

    def create(self, config=None):
        """
        Create a new file config
        :param config: Dictionary contain config value
        :return: New file config is created.
        """
        if config is None:
            config = {}
        if len(config.keys()) == 0:
            config = {'logger': {"logs_folder": "logs", "loglevel": "info", "logs_file": "application.log"}}

        with open(self.config_filename, 'w') as f:
            json.dump(config, f)

    def load_config(self, config_filename):
        """
        Load config from file config
        :return: Dictionary contain config value is save in self.config
        """
        fconfig = os.path.join(self.current_path, "configs", config_filename)
        if not os.path.exists(fconfig):
            self.current_path = os.getcwd()
            fconfig = os.path.join(self.current_path, "configs", config_filename)
            if not os.path.exists(fconfig):
                bcolors.error("Cannot find file configuration: " + str(fconfig))
                sys.exit()
        try:
            with open(fconfig, 'r') as f:
                configurations = json.load(f)
        except Exception as ex:
            bcolors.error("Cannot load file configuration " + str(fconfig) + ": " + str(ex))
            sys.exit()
        return configurations

    def check_settings(self):
        bcolors.header("CHECK CONFIGURATION .....")
        config_ok = True
        if "logger" in self.config:
            if type(self.config["logger"]) != type({}):
                bcolors.error("logger config is not dictionary")
                config_ok = False

            if "logs_folder" not in self.config["logger"]:
                bcolors.error("log_folders directory is not in config")
                config_ok = False

            # Check logs_file config
            if "logs_file" not in self.config["logger"]:
                bcolors.error("logs_file filename is not in config")
                config_ok = False

            # Check loglevel config
            if "loglevel" not in self.config["logger"]:
                bcolors.error("loglevel filename is not in config")
                config_ok = False
        else:
            bcolors.error("logger config is not in config")
            config_ok = False

        # Proxy self
        if "proxy" in self.config:
            if not isinstance(self.config["proxy"], dict):
                bcolors.error("Proxy self config is not dictionary")
                config_ok = False
        else:
            bcolors.error("Cannot find proxy config in " + str(self.config_filename))
            config_ok = False

        if "service" in self.config:
            if not isinstance(self.config["service"], dict):
                bcolors.error("service self config is not dictionary")
                config_ok = False

            if "host" not in self.config["service"]:
                bcolors.error("Cannot find host config in service configuration.")
                config_ok = False

            if "port" not in self.config["service"]:
                bcolors.error("Cannot find port config in service configuration.")
                config_ok = False

            if "https" not in self.config["service"]:
                bcolors.error("Cannot find https config in service configuration.")
                config_ok = False

            if "username" not in self.config["service"]:
                bcolors.error("Cannot find username config in service configuration.")
                config_ok = False

            if "password" not in self.config["service"]:
                bcolors.error("Cannot find password config in service configuration.")
                config_ok = False
        else:
            bcolors.error("Cannot find service config in " + str(self.config_filename))
            config_ok = False

        if config_ok:
            return True
        else:
            return False


settings = singleton(Configuration)
