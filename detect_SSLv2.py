import subprocess
import json
import os

class detect_SSLv2:
    def __init__(self):
        self.host = ""
        self.current_path = os.path.dirname(__file__)

    def scan_object(self):
        data = json.load(open("input.json", "r"))
        host = data["request_header"]["host"]
        if self.detect(host):
            self.get_result(host)

    def detect(self, host):
        host = "ol.dnse.com.vn"
        path_script = "sslscan/start.py"
        command = "python3 {0} scan --scan=server.ciphers --ssl2 {1} ".format(path_script, host)
        out_put = subprocess.check_output( command, shell = True)
        if b"Supported Server Cipher(s)" in out_put:
            return True
        else:
            return False

    def get_result(self, host):
        attack_details_vuln = {"Type": "SSL 2.0 deprecated protocol"}
        affects_vuln = host
        request_vuln = ""
        param_vuln = ""
        output_vuln = ""
        data_vuln = {
            "attack_details": attack_details_vuln,
            "affects": affects_vuln,
            "requests": request_vuln,
            "param": param_vuln,
            "response": output_vuln,
            "port": 443
        }
        try:
            with open("output.json", "w+") as output_file:
                json.dump(data_vuln, output_file)
            output_file.close()
            print("Successful Data Export !!!")
        except:
            print("Error When Open Output file !!!")

a = detect_SSLv2()
a.scan_object()