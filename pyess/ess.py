#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import logging
import re
import socket
import time

import requests

from zeroconf import Zeroconf

from pyess.constants import PREFIX, LOGIN_URL, TIMESYNC_URL, GRAPH_TIMESPANS, GRAPH_DEVICES, GRAPH_PARAMS, \
    GRAPH_TFORMATS, SWITCH_URL, STATE_URLS, RETRIES


class ESSException(Exception):
    pass


logger = logging.getLogger(__name__)


class ESS:
    def __init__(self, name, pw, ip=None):
        self.name = name
        self.pw = pw
        self.ip = self.update_ip()[0]
        self.auth_key = self.login()

    def login(self):
        url = LOGIN_URL.format(self.ip)
        logger.info("fetching auth key")
        r = requests.put(url, json={"password": self.pw}, verify=False, headers={"Content-Type": "application/json"})
        auth_key = r.json()["auth_key"]
        timesync_info = {
            "auth_key": auth_key,
            "by": "phone",
            "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        rt = requests.put(TIMESYNC_URL.format(self.ip), json=timesync_info, verify=False,
                          headers={"Content-Type": "application/json"})
        assert rt.json()['status'] == 'success', rt.__dict__
        self.auth_key = auth_key
        return auth_key

    def update_ip(self):
        """
        update IP by running mdns scan, return IP and server name (also update internal state)
        :return:
        """
        ip, server = get_ess_ip(self.name)
        self.ip = ip
        return self.ip, server

    def get_graph(self, device: str, timespan: str, date: datetime.datetime):
        """
        Get the time series data about a device
        :param device: the device in question ``["batt", "load", "pv"]``
        :param timespan: the timespan in question ``["day", "week", "month", "year"]``
        :param date: the date specifying the time span. (for week, month and year I guess any date within the timespan
                     of interest will suffice)
        :return:
        """
        assert device in GRAPH_DEVICES
        assert timespan in GRAPH_TIMESPANS
        url = f"https://{self.ip}/v1/user/graph/{device}/{timespan}"
        # r = requests.post(url, json=jsondata, verify=False, headers={"Content-Type": "application/json"})
        return self.post_json_with_auth(url, extra_json_data={
            GRAPH_PARAMS[timespan]: date.strftime(GRAPH_TFORMATS[GRAPH_PARAMS[timespan]])})

    def post_json_with_auth(self, url: str, retries: int = 0, extra_json_data: dict = None):
        """
        wrapper that posts json data after adding auth data. Optionally takes an extra_json_data argument.
        :param url: URL to fetch
        :param retries: internal parameter for recoursive calls
        :param extra_json_data: extra json data to pass
        :return:
        """
        json = {"auth_key": self.auth_key}
        error = False
        if extra_json_data:
            json.update(extra_json_data)
        try:
            r = requests.post(url, json=json, verify=False, headers={"Content-Type": "application/json"})
        except (requests.ConnectionError, requests.ConnectTimeout):
            error = True
        if not error and (r.status_code == 200 or (r.json() != {'auth': 'auth_key failed'})):
            return r.json()
        logger.info("seems we got logged out, retrying after {} seconds".format(retries))
        time.sleep(retries)
        self.login()
        return self.post_json_with_auth(url, retries=retries + 1, extra_json_data=None)

    def get_network(self):
        return self.get_state("network")

    def get_systeminfo(self):
        return self.get_state("systeminfo")

    def get_batt(self):
        return self.get_state("batt")

    def get_home(self):
        return self.get_state("home")

    def get_common(self):
        return self.get_state("common")

    def get_state(self, state):
        return self.post_json_with_auth(STATE_URLS[state].format(self.ip))

    def switch_on(self):
        """
        switch on operation.
        :return:
        """
        r = requests.put(SWITCH_URL, json={"auth_key": self.auth_key, "operation": "start"},
                         verify=False, headers={"Content-Type": "application/json"})

    def switch_off(self):
        """
        switch off operation.
        :return:
        """
        r = requests.put(SWITCH_URL, json={"auth_key": self.auth_key, "operation": "stop"},
                         verify=False, headers={"Content-Type": "application/json"})
        # if not r.json()["status"] == "success":
        #    raise ESSException("switching unsuccessful")


def get_ess_ip(name):
    zeroconf = Zeroconf()
    ess_info = zeroconf.get_service_info("_pmsctrl._tcp.local.", f"LGE_ESS-{name}._pmsctrl._tcp.local.")
    zeroconf.close()
    ip = [socket.inet_ntoa(ip) for ip in ess_info.addresses][0]
    return ip, ess_info.server


def get_ess_pw(ip="192.168.23.1"):
    """this method only works on the wifi provided by the box."""
    res = requests.post(f"https://{ip}/v1/user/setting/read/password", json={"key": "lgepmsuser!@#"},
                        headers={"Charset": "UTF-8", "Content-Type": "application/json"}, verify=False,
                        timeout=1).json()
    if res['status'] == 'success':
        return res['password']
    logger.exception("could not fetch password")
    raise LookupError("could not look up password")


def autodetect_ess():
    name = find_all_esses()[0]
    name = extract_name_from_zeroconf(name)

    zeroconf = Zeroconf()
    ess_info = zeroconf.get_service_info("_pmsctrl._tcp.local.", f"LGE_ESS-{name}._pmsctrl._tcp.local.")
    zeroconf.close()
    ip = [socket.inet_ntoa(ip) for ip in ess_info.addresses][0]
    return ip, name


def extract_name_from_zeroconf(name):
    name = re.sub(r"LGE_ESS-(.+)\._pmsctrl\._tcp\.local\.", r"\g<1>", name)
    return name


def find_all_esses():
    from zeroconf import ServiceBrowser, Zeroconf
    esses = []

    class MyListener:

        def remove_service(self, zeroconf, type, name):
            pass

        def add_service(self, zeroconf, type, name):
            info = zeroconf.get_service_info(type, name)
            esses.append(info.name)

    zeroconf = Zeroconf()
    listener = MyListener()
    # browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
    browser = ServiceBrowser(zeroconf, "_pmsctrl._tcp.local.", listener)
    time.sleep(3)
    zeroconf.close()

    if len(esses) == 0:
        raise ESSException("could not find any ESS devices via mdns")
    return esses


def mitm_for_ess(name):
    import socket
    info = ServiceInfo(
        "_pmsctrl._tcp.local.",
        f"LGE_ESS-{name}._pmsctrl._tcp.local.",
        addresses=[socket.inet_aton("192.168.1.24")],
        port=80,
        properties={b'Device': b'LGEESS', b'HWRevison': b'1.5'},
        server="myaddress.local.",
    )

    zeroconf = Zeroconf()
    print("Registration of a service, press Ctrl-C to exit...")
    zeroconf.unregister_service(info)
