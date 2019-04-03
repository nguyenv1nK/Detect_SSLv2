# -*- coding: utf-8 -*-
import re
from urlparse import urlparse

__author__ = 'TOANTV'
from .logger import logger


class Plugin:
    def __init__(self, link_info, web_api):
        # link information
        self.link_info = link_info
        self.task = link_info.get("task")
        self.path = self.link_info.get("path", None) or self.link_info.get("url").get("path", "")
        self.id = link_info.get("url", {"id": None}).get("id", None) or link_info.get("id", 0)
        self.url_scan = self.link_info.get("id")
        self.params = self.link_info.get("params", {})
        self.request_body = self.link_info.get("request_body", {})
        self.method = self.link_info.get("method", "GET")
        self.website = link_info.get("url", {"website": None}).get("website", None) or link_info.get("website", 0)
        # configuration
        self.configuration = link_info.get("configuration", {})
        self.custom_cookies = self.configuration.get("custom_cookies", [])
        self.custom_headers = self.configuration.get("custom_headers", [])
        self.speed = self.configuration.get("speed", 3)
        self.target = self.configuration.get("target", 0)
        self.web_api = web_api
        self.host_vuln = self.link_info.get("host_vuln")
        # self.fi_url = ""
        # if "url" in self.attack_details:
        #     self.fi_url = self.attack_details.get("attack_details")
        # Update plugin options
        self.options = {}
        self.check_error = 0
        self.get_plugin_options()
        self.name = "Sbox plugin"

    def set_proxy(self):
        options_proxy = None
        try:
            proxy = self.web_api.get_proxy()
            if proxy:
                if proxy.get("enable", False):
                    if proxy.get("username") and proxy.get("password"):
                        options_proxy += "--proxy {0}://{1}:{2}@{3}:{4}".format(proxy.get("protocol"),
                                                                                proxy.get("username"),
                                                                                proxy.get("password"),
                                                                                proxy.get("address"), proxy.get("port"))
                    else:
                        options_proxy += "--proxy {0}://{1}:{2}".format(proxy.get("protocol"), proxy.get("address"),
                                                                        proxy.get("port"))
        except Exception as err:
            self.error_log(message="Proxy error {}".format(str(err)))
            return None
        return options_proxy

    def get_plugin_options(self):
        self.arguments = {}

    def parse_addr(self, domain):
        domain_check = re.compile("^(http|https)?[a-zA-Z0-9]+([\-\.]{1}[a-zA-Z0-9]+)*\.[a-zA-Z]{2,}$")
        http_check = re.compile(
            '^(?:http|ftp)s?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/?|[/?]\S+)$',
            re.IGNORECASE)

        if http_check.search(domain) or domain_check.match(domain):
            if not domain.startswith('http://') and not domain.startswith('https://'):
                domain = 'http://' + domain

            parsed_domain = urlparse(domain)
            return parsed_domain.hostname
        else:
            return None

    def check_stop(self):
        url_info = self.web_api.get_scanurl(self.link_info.get("id", 0))
        if url_info is None:
            return True
        if url_info.get('scan_finished') or url_info.get("task_status", 1) >= 3:
            self.info_log("Stop by user")
            return True
        return False

    def scan(self):
        """
        Start scan with plugins.
        :return:
        """
        pass

    def info_log(self, message=None):
        logger.info(
            data=str(message), plugin=self.name,
            target="Task {}, Link id {}, url {}".format(str(self.task), str(self.id), str(self.path)))

    def error_log(self, message=None):

        logger.error(
            data=str(message), plugin=self.name,
            target="Task {},  Link id {}, url {}".format(str(self.task), str(self.id), str(self.path)))

    def moniter_log(self, message=""):
        logger.moniter(
            data=str(message), plugin=self.name,
            target="Task {},  Link id {}, url {}".format(str(self.task), str(self.id), str(self.path)))

    def get_full_link(self):
        self.info_log(message="Get full link")
        list_param = []
        for param in self.params:
            value = self.params.get(param, [])
            if isinstance(value, list) and len(value) > 0:
                list_param.append("{0}={1}".format(param, value[0]))
            else:
                list_param.append("{0}={1}".format(param, "SBOX"))
        if len(list_param) > 0:
            return "{0}?{1}".format(self.path, "&".join(list_param))
        return self.path

    def get_requets_data(self):
        self.info_log(message="Get request data")
