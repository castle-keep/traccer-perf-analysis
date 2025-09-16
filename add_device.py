import aiohttp
import asyncio
import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
import argparse
import requests

def create_device_async(api_key, missing):
    base_url = os.getenv("TRACCAR_BASE_URL")
    api_hdrs = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    create_url = f"{base_url}/api/devices"

    async def create_all():
        timeout = aiohttp.ClientTimeout(total=15)
        sem = asyncio.Semaphore(1000)  # limit burst concurrency
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async def create_one(name):
                payload = {
                    "name": name,
                    "uniqueId": name,
                    "status": "online",
                    "lastUpdate": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                }
                for attempt in range(3):
                    try:
                        async with sem:
                            async with session.post(create_url, headers=api_hdrs, json=payload) as resp:
                                if resp.status in (200, 201):
                                    print(f"[{resp.status}] {name} created")
                                    return True
                                txt = await resp.text()
                                print(f"[{resp.status}] {name} attempt {attempt+1}: {txt[:100]}")
                    except Exception as e:
                        print(f"[EXC] {name} attempt {attempt+1}: {e}")
                        await asyncio.sleep(0.5 * (attempt + 1))
                return False

            started = time.time()
            results = await asyncio.gather(*(asyncio.create_task(create_one(n)) for n in missing))
            ok = sum(results)
            print(f"Created {ok}/{len(missing)} devices in {time.time() - started:.1f}s")

    asyncio.run(create_all())

def get_existing_device_names(api_key):
    base_url = os.getenv("TRACCAR_BASE_URL")
    api_hdrs = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    url = f"{base_url.rstrip('/')}/api/devices"
    try:
        resp = requests.get(url, headers=api_hdrs, timeout=10)
        resp.raise_for_status()
        devices = resp.json()
        names = {d["name"] for d in devices if "name" in d}
        return names
    except Exception as e:
        print(f"Error fetching existing devices: {e}")
        return set()


def generate_alphanumeric_names(range_length:int, existing_names:list[str]) -> set:
    """
    Generate 6 alphanumeric character combinations (0-9, A-Z).
    """
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    names = set()
    i = 1
    for i in range(36**6):
        name = f"SIMU{''.join([chars[(i // (36**j)) % 36] for j in range(5)])}"
        if name not in existing_names:
            names.add(name)
        if len(names) >= range_length:
            break
    return names
    

if __name__ == "__main__":
    load_dotenv()  # load environment variables from .env file if present

    api_key = os.getenv("TRACCAR_API_KEY")

    device_limit = 100100  # max devices to create

    device_names = get_existing_device_names(api_key)
    total_existing = len(device_names)
    if total_existing >= device_limit:
        print(f"Device limit reached ({total_existing}/{device_limit}). No new devices will be created.")
        exit(0)
    to_be_created = device_limit - total_existing
    print(f"Total existing devices: {len(device_names)}")
    print(f"Existing device names sample: {list(device_names)[:5]} ... {list(device_names)[-5:]}")

    # Generate expected device names
    expected_device_names = {i for i in generate_alphanumeric_names(to_be_created, device_names)}
    print(f"Generated {len(expected_device_names)} expected device names")
    print(f"Sample names: {list(expected_device_names)[:5]} ... {list(expected_device_names)[-5:]}")

    create_device_async(api_key, expected_device_names)