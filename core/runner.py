# -*- coding: utf-8 -*-
import glob
import importlib
import os
import time

from functions import convert_utf8
from .configuration import settings
from .logger import logger


class Runner:
    def __init__(self, web_api, queue_name):
        self.name = "Sbox Runner"
        self.web_api = web_api
        self.time_delay = settings.config["global"]["time_delay"]
        self.time_scan = None
        self.web_api.get_server_configurations()
        self.list_plugin = []
        self.plugin_name = queue_name
        self.plugin_dir = os.path.join(settings.current_path, self.plugin_name)
        self.url_info = {}
        self.task = {}
        self.is_link = False

    def start(self, url_id, is_link=False):
        # get link to service
        self.is_link = is_link
        self.url_info = self.web_api.get_url(url_id) if is_link else self.web_api.get_scanurl(url_id)
        print "here: " + str(self.url_info)
        if self.url_info is not None and isinstance(self.url_info, dict):
            # check scan by stop
            # print self.url_info.get('scan_finished')
            # print settings.config['plugins']['groups'] in self.url_info.get("plugins_scanned", [])
            # print self.url_info.get("task_status", 1)
            if self.url_info.get('scan_finished') or settings.config['plugins']['groups'] in self.url_info.get(
                    "plugins_scanned", []) or self.url_info.get("task_status", 1) >= 3:
                self.info_log("Stop by user")
                # return True
        else:
            self.info_log("Not find link {}".format(str(url_id)))
            return True
        self.info_log("Start scan")
        self.load_plugins()
        for plugin in self.list_plugin:
            check_error = self.create_new_job(plugin_module="{0}.{1}".format(self.plugin_name, plugin))
            if check_error > 0:
                self.error_log(message="Check {} error".format(str(plugin)))

        self.update_url()
        self.info_log("Finish scan")
        return True

    def special_scan(self, script_scan, link_id, is_link=True):
        self.time_scan = int(time.time())
        self.url_info = self.web_api.get_url(link_id) if is_link else self.web_api.get_scanurl(link_id)
        # print self.url_info
        self.info_log("Start scan.")
        plugin = "{0}.{1}".format(self.plugin_name, script_scan)
        self.create_new_job(plugin_module=plugin)
        self.info_log("Finish scan")
        return True

    # load all script in dir plugin
    def load_plugins(self):
        excluded_script = convert_utf8(settings.load_config("excluded_domain.json")["excluded_script"])
        self.list_plugin = [os.path.basename(x)[:-3] for x in glob.glob(os.path.join(self.plugin_dir, "*.py"))
                            if os.path.basename(x)[:-3] not in excluded_script]
        self.list_plugin.sort()
        # print str(self.list_plugin)
        return True

    def info_log(self, message=None):
        if self.url_info is None:
            logger.log(
                data=str(message), plugin=self.name)
        else:
            logger.log(
                data=str(message), plugin=self.name,
                target="Task {0}, Scan id {1}, url {2}".format(str(self.task.get("id", 0)),
                                                               str(self.url_info.get("id", 0)),
                                                               str(self.url_info.get("url", {}).get("path", ""))))

    def error_log(self, message=None):
        if self.url_info is None:
            logger.error(
                data=str(message), plugin=self.name)
        else:
            logger.error(
                data=str(message), plugin=self.name,
                target="Task {0}, Scan id {1}, url {2}".format(str(self.task.get("id", 0)),
                                                               str(self.url_info.get("id", 0)),
                                                               str(self.url_info.get("url", {}).get("path", ""))))

    def create_new_job(self, plugin_module):
        # try:
        plugin = importlib.import_module(str(plugin_module), package=None)
        sbox_plugin = plugin.SboxPlugin(link_info=self.url_info, web_api=self.web_api)
        check_error = sbox_plugin.scan()
        print("---------- check_error: {} ".format(str(check_error)))
        # except Exception as err:
        #     self.error_log("Start plugin {0} error {1}".format(str(plugin_module), str(err.message)))
        #     check_error = 1
        return check_error

    def update_url(self):
        data = {
            "id": self.url_info.get("id", 0),
            "plugins_scanned": settings.config['plugins']['groups'],
        }
        if self.is_link:
            self.web_api.put_crawl(data)
        else:
            self.web_api.put_scanurl(data)
        self.info_log("Update plugins_scanned")
