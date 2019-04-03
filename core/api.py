# -*- coding: utf-8 -*-
__author__ = 'TOANTV'

import json
from time import sleep

from requests import RequestException
from retrying import retry

from .configuration import settings
from .logger import logger
from .network_connector import NetworkConnection

plugin = "Agents API"


class SecurityboxAPI:
    _instance = None

    def __init__(self, get_configurations=True):
        self.network_connection = NetworkConnection(settings.config["service"]["host"],
                                                    settings.config["service"]["port"],
                                                    is_https=settings.config["service"]["https"])
        self.token = ""
        self.headers = {"one-token": self.token, "Content-Type": "application/json"}
        if self.token == "":
            self.login()
        if get_configurations:
            self.get_server_configurations()

    @retry(wait_random_min=15000, wait_random_max=30000)
    def login(self):
        """
        Login to web service API.
        Retry login if login fails
        :return:
        """
        auth = {"email": settings.config["service"]["username"],
                "password": settings.config["service"]["password"]
                }
        response = self.network_connection.connect("POST", "/auth/login", data=json.dumps(auth))
        status_code = response.status_code
        if status_code == 200:
            user_info = response.json()
            if "one-token" in user_info:
                self.token = user_info["one-token"]
                self.headers = {"one-token": self.token, "Content-Type": "application/json"}
                logger.log("Login Successful!", plugin=plugin)

        else:
            logger.error(("Web service: cannot login to web service, status code = " + str(status_code)), plugin=plugin)
            raise RequestException("Web service: cannot login to web service, retrying ....")

    def logout(self):
        r = self.connect("POST", "/auth/logout", headers=self.headers, data={})
        status_code = r.status_code
        if status_code != 200:
            logger.error("Not logout service", plugin=plugin)
        logger.log("Logout service", plugin=plugin)

    def get_server_configurations(self):
        logger.info("Get global settings from server!!!")
        # self.get_max_scan()
        self.get_proxy()
        logger.info("Finish global settings from server!!!")

    def get_max_scan(self):
        logger.info("Get max task configurations.")
        uri = "/systems/license"
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get license not found", plugin=plugin)
                return settings.config["global"]["max_scans"]
        if "max_scans" in r.json() and r.json()["max_scans"] is not None and r.json()["max_scans"] > 0:
            settings.config["global"]["max_scans"] = r.json()["max_scans"]
            return r.json()["max_scans"]
        return settings.config["global"]["max_scans"]

    def get_proxy(self):
        logger.info("Update proxy configurations.")
        uri = "/systems/networks/proxy"
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get proxy not found", plugin=plugin)
                return None
            return None
        else:
            if len(r.json().keys()) == 0:
                return None
            else:
                settings.config["proxy"] = r.json()
                return r.json()

    @retry(wait_random_min=15000, wait_random_max=30000)
    def connect(self, method, uri, headers=None, data=None, files=None, stream=None):
        r = self.network_connection.connect(method, uri, headers=self.headers, data=data, files=files, stream=stream)
        if r is not None:
            if r.status_code == 401:
                self.login()
                r = self.network_connection.connect(method, uri, headers=self.headers, data=data, files=files,
                                                    stream=stream)
            elif r.status_code >= 500:
                logger.error("Web service: Cannot connect to web service, retrying ...", plugin=plugin)
                # raise RequestException("Web service: Cannot connect to web service, retrying...")
        return r

    def get_new_target(self, plugins_group=settings.config["plugins"]["groups"]):
        return self.get_jobs(1, plugins_group)

    def get_continue_target(self, plugins_group=settings.config["plugins"]["groups"]):
        tasks = []
        # continue_jobs = self.get_jobs(6)
        # tasks.extend(continue_jobs)
        continue_jobs = self.get_jobs(2, plugins_group, agent_id=settings.config["global"]["agent_id"])
        tasks.extend(continue_jobs)
        # queue_jobs = self.get_jobs(1)
        # tasks.extend(queue_jobs)
        return tasks

    def get_jobs(self, status, plugins_group=settings.config["plugins"]["groups"], agent_id=''):
        offset = 0
        limit = 10
        count = 1
        jobs = []
        next = True
        while next:
            count = 0
            uri = "/agents/scans?status={0}&limit={1}&offset={2}&plguins_group={3}&agent_id={4}".format(status,
                                                                                                        str(limit),
                                                                                                        str(offset),
                                                                                                        str(
                                                                                                            plugins_group),
                                                                                                        str(agent_id))
            r = self.connect("GET", uri, headers=self.headers)
            status_code = r.status_code
            if status_code == 200 and type(r.json()) == type({}):
                if "results" in r.json() and type(r.json()["results"]) == type([]) and "count" in r.json():
                    count = r.json()["count"]
                    jobs.extend(r.json()["results"])
                    if count > (offset + limit):
                        offset += limit
                    else:
                        sleep(2)
                        next = False
        return jobs

    @retry(wait_random_min=5000, wait_random_max=10000)
    def create_exploit(self, scan_info):
        if "url_scan" in scan_info:
            uri = "/agents/pentest"
            r = self.connect("POST", uri, headers=self.headers, data=json.dumps(scan_info))
            print "Scan Info: " + str(scan_info)
            status_code = r.status_code
            print status_code
            if status_code == 201:
                return r.json()
            else:
                logger.error("Request {0} fails, error {1}.!".format(uri, 'Update Pentest'), plugin=plugin)
                return {'id': 'None'}
        else:
            logger.error("Update Pentest Error!", plugin=plugin)
            return {'id': 'None'}

    def update_exploit(self, scan_info, id_pentest):
        uri = "/agents/pentest/" + str(id_pentest)
        print "Uri: " + str(uri)
        # print "Scan Info: " + str(scan_info)
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(scan_info))
        status_code = r.status_code
        print status_code
        if status_code != 200:
            logger.error("Update pentest {0} fails, scan is deleted. Abort!".format(uri), plugin=plugin)
            # return {'status': status_code}
        return r.json()

    def get_scan(self, id):
        uri = "/agents/scans/" + str(id)
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get scan " + str(id) + " not found")
                return {"id": str(id), "status": 3, "start_id": -1}
            return None
        return r.json()

    def get_target(self, task):
        uri = "/targets/?task=" + str(task)
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error(("Get targets ?task=" + str(task) + " not found"), plugin=plugin)
                return {"id": id, "status": 3, "start_id": -1}
            return None
        return r.json()

    # @retry(wait_random_min=5000, wait_random_max=10000)
    def get_pgroups(self, plugins_group=settings.config["plugins"]["groups"]):
        uri = "/pgroups/{0}".format(str(plugins_group))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get plugin group not found", plugin=plugin)
                return None
            return None
        return r.json()

    def get_plugins(self, plugins_group=settings.config["plugins"]["groups"]):
        uri = "/pgroups/{0}/plugins?enabled=true".format(str(plugins_group))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get plugin not found", plugin=plugin)
                return None
            return None
        return r.json()

    def get_plugin_info(self, id):
        uri = "/plugins/{0}".format(str(id))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get plugin not found", plugin=plugin)
                return None
            return None
        return r.json()

    def get_scan_list(self, status='', plugins='', task=''):
        uri = "/agents/scans?status={0}&plugin={1}&task={2}".format(str(status),
                                                                    str(plugins),
                                                                    str(task))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get license not found", plugin=plugin)
                return {"status": 3, "start_id": -1}
            return None
        return r.json()

    def post_host(self, host_info):
        uri = "/agents/hosts"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(host_info))
        if r.status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return {"id": None}
        return r.json()

    def put_host(self, host_info, host_id):
        uri = "/agents/hosts/" + str(host_id)
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(host_info))
        if r.status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return {"id": None}
        return r.json()

    def update_target_info(self, target_id, data):
        uri = "/targets/{0}".format(str(target_id))
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, retrying.!".format(uri), plugin=plugin)
            return None
        else:
            return r.json()

    def get_host_list(self, task='', limit="", offset="", ip_addr=''):
        uri = "/agents/hosts?&task={0}&limit={1}&offset={2}&ip_addr={3}".format(
            str(task),
            str(limit), str(offset), str(ip_addr))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get host not found", plugin=plugin)
            return None
        return r.json()

    def get_host(self, host_id):
        uri = "/agents/hosts/{}".format(str(host_id))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get host not found", plugin=plugin)
                return None
            return {"id": host_id}
        return r.json()

    def get_host_details(self, host_id):
        uri = "/agents/hosts/{}/info".format(str(host_id))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code == 404:
                logger.error("Get host not found", plugin=plugin)
                return None

            return {"host": host_id}
        return r.json()

    def put_host_detail(self, data, host_id):
        if host_id is None:
            host_id = data["host"]
        uri = "/agents/hosts/" + str(host_id) + "/info"
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            return r.json()

    def post_host_service(self, data):
        uri = "/agents/services"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            if status_code == 400:
                return self.put_host_service(data=data)
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            return r.json()

    def put_host_service(self, data):
        service = self.get_host_service(data)
        if service is None:
            return None
        uri = "/agents/services/" + str(service["id"])
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            return r.json()

    def get_host_service(self, data):
        uri = "/agents/services?host={0}&port={1}".format(str(data["host"]), str(data["port"]))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            if status_code == 404:
                return None
            return data
        if isinstance(r.json(), list) and len(r.json()) > 0:
            return r.json()[0]
        return None

    def post_system_logging(self, data):
        uri = "/systems/loggings"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            return r.json()

    def post_vuln(self, data):
        uri = "/vulnerabilities"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            if status_code == 400:
                logger.info("Create vulnerabilities, status {}, error {}".format(str(status_code), str(r.json())))
                return self.get_vuln(name=data["name"], plugin_id=data["plugin_id"])
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            return r.json()

    def put_vuln(self, data):
        uri = "/vulnerabilities/{}".format(data["id"])
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 200:
            if status_code == 400:
                logger.info("Cannot update vuln, status {}, error {}".format(str(status_code), str(r.json())))
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            return r.json()

    def get_vuln(self, name, plugin_id):
        uri = "/vulnerabilities?name={0}&plugin_id={1}".format(str(name), str(plugin_id))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()[0]
                return []
            return r.json()

    def get_vuln_options(self, impact, plugin_id):
        uri = "/vulnerabilities?impact={0}&plugin_id={1}".format(str(impact), str(plugin_id))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()[0]
                return []
            return r.json()

    def post_host_vuln(self, data):
        uri = "/agents/vulns"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            logger.info("Create vuln, status {0}, error {1}".format(str(status_code), str(r.json())))
            if "id" in r.json():
                return r.json()
            else:
                return None
        else:
            return r.json()

    def get_host_vuln(self, id):
        uri = "/agents/vulns" + str(id)
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None

    def find_host_vuln(self, host_id, scanner_vuln_id, scanner_scan_id=None):
        uri = "/agents/vulns?host={0}&scanner_vuln_id={1}".format(str(host_id), str(scanner_vuln_id))
        if scanner_scan_id is not None:
            uri += "&scanner_scan_id={}".format(str(scanner_scan_id))

        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return []
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()[0]
                return []
            return r.json()

    def get_host_session(self, host_id, vuln_id, attack_time):
        uri = "/agents/sessions?host={0}&vulnerability={1}&time_attack=".format(str(host_id),
                                                                                str(vuln_id),
                                                                                str(attack_time))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()[0]
                return None
            return r.json()

    def post_host_session(self, data):
        uri = "/agents/sessions"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def find_website_subdomain(self, website_id, subdomain):
        uri = "/agents/subdomains?website={}&subdomain={}".format(str(website_id), str(subdomain))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()[0]
                return []
            return r.json()

    def post_website_subdomain(self, data):
        uri = "/agents/subdomains"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def create_config_vulnerbility(self, data):
        uri = "/agents/configvulns"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def post_databases(self, data):
        uri = "/agents/databases"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def post_crawl(self, data):
        uri = "/agents/crawldata"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            if status_code == 400:
                logger.info("Not create crawl path {}, found crawl url.!".format(data["path"]), plugin=plugin)
                return self.get_crawl(path=data["path"], website=data["website"])
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()
        # def update_vuln(self, data, id):

    @retry(wait_random_min=15000, wait_random_max=30000)
    def put_crawl(self, data):
        uri = "/agents/crawldata/{}".format(str(data["id"]))
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, retrying.!".format(uri), plugin=plugin)
            if status_code == 404:
                return None
            raise RequestException("Request {0} fails, retrying.!".format(uri))
        return r.json()

    @retry(wait_random_min=15000, wait_random_max=30000)
    def put_scanurl(self, data):
        uri = "/agents/urlscans/{}".format(str(data["id"]))
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, retrying.!".format(uri), plugin=plugin)
            if status_code == 404:
                return None
            raise RequestException("Request {0} fails, retrying.!".format(uri))
        return r.json()

    def get_url(self, id):
        uri = "/agents/crawldata/{}".format(str(id))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def get_scanurl(self, id):
        uri = "/agents/urlscans/{}".format(str(id))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    # def update_scan_url(self, data):
    #     uri = "/agents/scan-url/{}".format(str(data.get("id", 0)))
    #     r = self.connect("PUT", uri, data=json.dumps(data), headers=self.headers)
    #     status_code = r.status_code
    #     if status_code != 200:
    #         logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
    #         return None
    #     return r.json()

    def get_crawl(self, path, website, method="GET"):
        if "&" in path or "#" in path:
            return None
        uri = "/agents/crawldata?website={0}&path={1}&method={2}".format(str(website),
                                                                         str(path), str(method))
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            if status_code != 404:
                logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()[0]
        return None

    def get_list_link(self, task):
        offset = 0
        limit = 20
        count = 1
        jobs = []
        next = True
        while next:
            count = 0
            uri = "/agents/urlscans?url__website__task={0}&limit={1}&offset={2}".format(task, str(limit), str(offset), )
            r = self.connect("GET", uri, headers=self.headers)
            status_code = r.status_code
            if status_code == 200 and type(r.json()) == type({}):
                if "results" in r.json() and type(r.json()["results"]) == type([]) and "count" in r.json():
                    count = r.json()["count"]
                    jobs.extend(r.json()["results"])
                    if count > (offset + limit):
                        offset += limit
                    else:
                        sleep(2)
                        next = False
        return jobs

    def get_ip_address(self):
        uri = "/systems/networks"
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            return []
        return r.json()

    def post_technologies(self, data):
        uri = "/agents/technologies"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        if r.status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def post_webstatus(self, data):
        uri = "/agents/webstatus"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        if r.status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def post_msecurity(self, data):
        uri = "/agents/msecurity"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        if r.status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def post_mcontents(self, data):
        uri = "/agents/mcontents"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        if r.status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def post_blacklistdetect(self, data):
        uri = "/agents/blacklistdetect"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        if r.status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def post_phishingdetect(self, data):
        uri = "/agents/phishingdetect"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        if r.status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        return r.json()

    def post_google_hacking_db(self, data):
        uri = "/agents/ghdb"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()
                return None
        return r.json()

    def get_google_hacking_db(self, limit, offset):
        uri = "/agents/ghdb?limit={}&offset={}".format(limit, offset)
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()
                return None
        return r.json()

    def post_result_google_hacking_db(self, data):
        uri = "/agents/ghdbdetect"
        r = self.connect("POST", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 201:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return None
        else:
            if isinstance(r.json(), list):
                if len(r.json()) > 0:
                    return r.json()
                return None
        return r.json()

    def get_list_networks(self):
        uri = "/agents/networks"
        r = self.connect("GET", uri, headers=self.headers)
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return []
        return r.json()

    def detele_networks(self, data):
        uri = "/agents/networks"
        r = self.connect("DELETE", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return False
        return True

    def update_networks(self, data):
        uri = "/agents/networks"
        r = self.connect("PUT", uri, headers=self.headers, data=json.dumps(data))
        status_code = r.status_code
        if status_code != 200:
            logger.error("Request {0} fails, error {1}.!".format(uri, str(r.json())), plugin=plugin)
            return False
        return True
