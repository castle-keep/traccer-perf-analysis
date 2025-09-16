#!/usr/bin/env python3

import json
import random
import time
import urllib.parse
import urllib.request
import http.client
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import os
import sys
import requests

global_taken_ids = None

def send_message(conn: http.client.HTTPConnection, uid: str):
    params = urllib.parse.urlencode({
        "id":  uid,
        "lat": random.uniform(59.0, 61.0),
        "lon": random.uniform(29.0, 31.0),
    })
    try:
        conn.request("GET", f"?{params}")
        conn.getresponse().read()
        print(f"Sent position for device {uid}")
    except Exception as ex:
        print(f"Error sending position for device {uid}: {ex}", file=sys.stderr)
        conn.close()
        conn.connect()

def position_worker(uid: str):
    server_host = os.getenv("TRACCAR_SERVER")
    if not server_host:
        print("Environment variable TRACCAR_SERVER is required", file=sys.stderr)
        sys.exit(1)
    SEND_INTERVAL = 1.0
    conn = http.client.HTTPConnection(server_host, timeout=20)
    while True:
        send_message(conn, uid)
        time.sleep(SEND_INTERVAL)

def get_simulation_device_ids(take: int) -> list[int]:
    global global_taken_ids
    if global_taken_ids is not None and len(global_taken_ids) >= take:
        print(f"Reusing {len(global_taken_ids)} previously fetched device IDs")
        return global_taken_ids[:take]

    api_key = os.getenv("TRACCAR_API_KEY")
    base_url = os.getenv("TRACCAR_BASE_URL")
    if not api_key or not base_url:
        print("Environment variables TRACCAR_API_KEY and TRACCAR_BASE_URL are required", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    url = f"{base_url.rstrip('/')}/api/devices"
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching devices: {e}", file=sys.stderr)
        sys.exit(1)

    devices = resp.json()
    print(f"Fetched {len(devices)} devices from Traccar")
    sim_devices = [d for d in devices if d.get('uniqueId', '').startswith('SIM')]
    if not sim_devices:
        print("No devices with 'SIM' prefix found", file=sys.stderr)
        sys.exit(1)
    global_taken_ids = [d['id'] for d in sim_devices]
    print(f"Caching {len(global_taken_ids)} SIM devices; returning first {take}")
    return global_taken_ids[:take]

def main():
    load_dotenv()
    base_url = os.getenv("TRACCAR_BASE_URL")

    take_devices = 200
    ids = get_simulation_device_ids(take_devices)

    print(f"Starting position workers for {len(ids)} devices")

    for uid in ids:
        t = threading.Thread(target=position_worker, args=(uid,), daemon=True)
        t.start()

    try:
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
