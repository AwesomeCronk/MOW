import time
import requests
from threading import Thread

from __main__ import runFlag

def trackUptime():
    while runFlag:
        try:
            requests.get('https://hc-ping.com/a6be5080-daa8-4aec-80d8-bcfe4a92e3b9', timeout=10)
        except requests.RequestException as e:
            print('Failed to contact uptime monitor.')
        for i in range(360):
            time.sleep(5)
            if not runFlag: break

def StartUptimeTracking():
    server = Thread(target=trackUptime)
    server.start()