import asyncio
import random
import time
import argparse
from collections import deque, defaultdict
from urllib.parse import urlencode, urljoin
import statistics
from dotenv import load_dotenv
import sys
import os
import requests

import aiohttp

# Cache for simulation device IDs fetched from Traccar (lazy filled)
global_taken_ids = None

def seeded_rng(seed):
    rnd = random.Random()
    rnd.seed(seed)
    return rnd

def make_device_state(dev_id, rng):
    # Seed each device around a center (Cebu example) with slight offsets
    lat = 10.3157 + rng.uniform(-0.05, 0.05)
    lon = 123.8854 + rng.uniform(-0.05, 0.05)
    bearing = rng.uniform(0, 360)
    speed_kmh = rng.uniform(5, 40)  # moving-ish
    return {"id": dev_id, "lat": lat, "lon": lon, "bearing": bearing, "speed_kmh": speed_kmh}

def step_device(state, rng, dt_seconds):
    # Random walk with mild drift; wrap bearing 0..360
    turn = rng.uniform(-6, 6)
    state["bearing"] = (state["bearing"] + turn) % 360
    # Convert km/h to deg/sec approx (rough near equator; fine for load)
    # 1 km ~ 0.009 deg lat; scale lon by cos(lat).
    kmps = state["speed_kmh"] / 3600.0
    dlat = kmps * 0.009 * dt_seconds
    dlon = dlat * max(0.2, abs(math.cos(math.radians(state["lat"]))))
    # Move along bearing
    rad = math.radians(state["bearing"])
    state["lat"] += dlat * math.cos(rad)
    state["lon"] += dlon * math.sin(rad)
    # occasional stop/start
    if rng.random() < 0.02:
        state["speed_kmh"] = 0 if state["speed_kmh"] > 1 else rng.uniform(10, 40)

import math

class RateLimiter:
    def __init__(self, rate_per_sec):
        self.rate = rate_per_sec
        self.tokens = rate_per_sec
        self.updated = time.perf_counter()

    def allow(self):
        now = time.perf_counter()
        self.tokens += (now - self.updated) * self.rate
        self.updated = now
        if self.tokens > self.rate * 2:
            self.tokens = self.rate * 2
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

async def device_task(dev_id, session, base_url, interval, stop_time, stats, rng, args):
    state = make_device_state(dev_id, rng)
    next_send = time.monotonic()
    while time.monotonic() < stop_time:
        now = time.monotonic()
        if now < next_send:
            await asyncio.sleep(min(0.05, next_send - now))
            continue
        # step sim by 'interval'
        step_device(state, rng, interval)
        ts = int(time.time())
        params = {
            "id": f"{dev_id}",
            "lat": f"{state['lat']:.6f}",
            "lon": f"{state['lon']:.6f}",
            "timestamp": ts,
            "speed": f"{state['speed_kmh']*0.2778:.2f}",  # m/s
            "bearing": f"{state['bearing']:.1f}",
            # add anything else you’d like (hdop, altitude, input1, etc.)
        }
        url = f"{base_url.rstrip('/')}/?{urlencode(params)}"

        t0 = time.perf_counter()
        ok = False
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                body = await resp.read()  # small; ensures connection reuse
                status = resp.status
                ok = (200 <= status < 300)
                if not ok:
                    stats["statuses"][status] += 1
                    if args.print_failures and len(stats["failure_samples"]) < args.print_failures:
                        stats["failure_samples"].append(
                            f"dev={dev_id} status={status} body={body[:120]!r} url={url}"
                        )
                else:
                    stats["statuses"][status] += 1
            
        except Exception as e:
            stats["statuses"]["exception"] += 1
            if args.print_failures and len(stats["failure_samples"]) < args.print_failures:
                stats["failure_samples"].append(f"dev={dev_id} exception={type(e).__name__}:{e} url={url}")
            ok = False
        dt = (time.perf_counter() - t0) * 1000
        stats["latencies"].append(dt)
        if ok:
            stats["ok"] += 1
        else:
            stats["fail"] += 1
        stats["count"] += 1
        next_send += interval

async def runner(args, base_url:str):
    timeout = aiohttp.ClientTimeout(total=15, connect=5)
    connector = aiohttp.TCPConnector(limit=args.concurrency, ssl=False if args.insecure else None)
    headers = {"User-Agent": "osmand-sim/1.0"}

    stats = {
        "ok": 0, "fail": 0, "count": 0,
        "latencies": deque(maxlen=200000),  # keep a big rolling window
        "statuses": defaultdict(int),
        "failure_samples": [],
        "bandwidth_pub_out": float('nan'),  # will be populated once per run
        "bandwidth_pub_in": float('nan'),  # will be populated once per run
        "cpu_percent": float('nan'),  # will be populated once per run
        "memory_usage": float('nan'),  # will be populated once per run
        "load_1m": float('nan'),  # will be populated once per run
        "load_5m": float('nan'),  # will be populated once per run
        "load_15m": float('nan'),  # will be populated once per run
        "disk_usage_percent": float('nan')
    }

    stop_time = time.monotonic() + args.duration
    async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers=headers) as session:
        # Launch devices in waves, using an effective launch rate automatically boosted
        # to at least 1.5x (devices / duration) so that all devices start early in the run.
        tasks = []
        sim_device_ids = get_simulation_device_ids(args.devices)
        duration = max(1, args.duration)  # avoid div by zero
        default_min_rate = args.devices / duration
        adjusted_min_rate = default_min_rate * 1.1  # Add 10% headroom
        print(f"[LAUNCH] Default min launch rate: {default_min_rate:.2f} devices/sec, adjusted to {adjusted_min_rate:.2f} devices/sec")
        launch_rate = RateLimiter(rate_per_sec=adjusted_min_rate)  # devices/sec
        for id in sim_device_ids:
            if not launch_rate.allow():
                await asyncio.sleep(0.01)
            dev_rng = seeded_rng(args.seed + id)
            t = asyncio.create_task(device_task(id, session, base_url, args.interval, stop_time, stats, dev_rng, args))
            tasks.append(t)
        
        # Progress logging
        async def progress():
            last = 0
            last_ts = time.time()
            while time.monotonic() < stop_time:
                await asyncio.sleep(10)
                now = time.time()
                delta = stats["count"] - last
                rps = delta / (now - last_ts)
                line = f"[{time.strftime('%H:%M:%S')}] sent={stats['count']} ok={stats['ok']} fail={stats['fail']} rps={rps:.1f}"
                if args.status_summary:
                    # show top 3 statuses
                    top = sorted(stats["statuses"].items(), key=lambda x: (-x[1], str(x[0])))[:3]
                    line += " statuses=" + ",".join(f"{k}:{v}" for k,v in top)
                print(line)
                if args.debug and stats["failure_samples"]:
                    print("  sample failures:")
                    for s in stats["failure_samples"]:
                        print("   ", s)
                    # clear so we don't spam repeatedly
                    stats["failure_samples"].clear()
                last, last_ts = stats["count"], now

        pr = asyncio.create_task(progress())
        await asyncio.gather(*tasks)
        pr.cancel()

    # Fetch bandwidth once at end (still inside session for connection reuse)
    stats["bandwidth_pub_out"] = await fetch_droplet_bandwidth_kbps(stats, "outbound")
    stats["bandwidth_pub_in"] = await fetch_droplet_bandwidth_kbps(stats, "inbound")
    stats["memory_usage"] = await fetch_droplet_memory_usage()
    stats["load_1m"] = await fetch_droplet_load(1)
    stats["load_5m"] = await fetch_droplet_load(5)
    stats["load_15m"] = await fetch_droplet_load(15)
    stats["disk_usage_percent"] = await fetch_droplet_disk_usage()
    await fetch_droplet_cpu_usage(stats)

    # Summarize
    lats = list(stats["latencies"])
    lats.sort()
    def pct(p):
        if not lats:
            return float('nan')
        k = int(len(lats)*p/100)
        k = min(max(k, 0), len(lats)-1)
        return lats[k]
    total = stats["count"]
    print("\n=== Summary ===")
    print(f"Devices: {args.devices}, Interval: {args.interval}s, Duration: {args.duration}s")
    print(f"Total requests: {total}, OK: {stats['ok']}, Fail: {stats['fail']}")
    if args.duration > 0:
        total_rps = total / args.duration
        ok_rps = stats['ok'] / args.duration
        print(f"Average RPS over {args.duration}s: total={total_rps:.2f}, ok={ok_rps:.2f}")
    if stats["statuses"]:
        print("Status breakdown:")
        for k, v in sorted(stats["statuses"].items(), key=lambda x: (-x[1], str(x[0]))):
            print(f"  {k}: {v}")
    if total > 0:
        print(f"P50: {pct(50):.1f} ms, P90: {pct(90):.1f} ms, P99: {pct(99):.1f} ms")
    if not math.isnan(stats.get("bandwidth", float('nan'))):
        print(f"Outbound bandwidth (latest 1m sample): {stats['bandwidth']:.2f} kbps")
    # Attach percentile helper for reuse by ramp
    stats["_latencies_sorted"] = lats
    stats["pct"] = pct
    return stats

async def ramp_runner(args, base_url):
    """Incrementally increase devices/concurrency until failure threshold reached.

    Failure criteria:
      - fail_ratio > args.failure_threshold
      - ok < args.min_ok
    CSV columns: timestamp,level,devices,concurrency,duration,ok,fail,fail_ratio,rps_avg,rps_ok_avg,p50_ms,p90_ms,p99_ms,bandwidth_pub_out_kbps,bandwidth_pub_in_kbps,cpu_percent,memory_usage,load_1m,load_5m,load_15m,disk_usage_percent
    """
    import json, csv, os

    csv_path = args.csv or "ramp_report.csv"
    write_header = not os.path.exists(csv_path)
    levels = []
    devices = args.devices_start or args.devices
    concurrency = args.concurrency_start or args.concurrency or devices
    level = 0
    stop = False
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp","level","devices","concurrency","duration","ok","fail","fail_ratio","rps_avg","rps_ok_avg","p50_ms","p90_ms","p99_ms","bandwidth_pub_out_kbps","bandwidth_pub_in_kbps","cpu_percent","memory_usage","load_1m","load_5m","load_15m","disk_usage_percent"])
        while not stop and devices <= args.max_devices and concurrency <= args.max_concurrency:
            level += 1
            print(f"\n=== Level {level}: devices={devices} concurrency={concurrency} duration={args.duration_per_level}s ===")
            # Build a lightweight args clone for single run
            single = argparse.Namespace(**vars(args))
            single.devices = devices
            single.concurrency = concurrency
            single.duration = args.duration_per_level
            stats = await runner(single, base_url)
            total = stats['count'] or 1
            fail_ratio = stats['fail']/total
            p50 = stats['pct'](50)
            p90 = stats['pct'](90)
            p99 = stats['pct'](99)
            # average rps across run (total) and successful-only (ok)
            rps_avg = total / single.duration if single.duration > 0 else 0
            rps_ok_avg = stats['ok'] / single.duration if single.duration > 0 else 0
            statuses_json = json.dumps(dict(stats['statuses']))
            statuses = stats['statuses']
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            bandwith_pub_out = stats["bandwidth_pub_out"]
            bandwith_pub_in = stats["bandwidth_pub_in"]
            cpu_usage = stats.get("cpu_percent", float('nan'))
            memory_usage = stats.get("memory_usage", float('nan'))
            load_1m = stats.get("load_1m", float('nan'))
            load_5m = stats.get("load_5m", float('nan'))
            load_15m = stats.get("load_15m", float('nan'))
            disk_usage_percent = stats.get("disk_usage_percent", float('nan'))
            writer.writerow([timestamp,level, devices, concurrency, single.duration, stats['ok'], stats['fail'], 
                             f"{fail_ratio:.4f}", f"{rps_avg:.2f}", f"{rps_ok_avg:.2f}", f"{p50:.1f}", f"{p90:.1f}", f"{p99:.1f}", 
                             f"{bandwith_pub_out:.1f}", f"{bandwith_pub_in:.1f}", f"{cpu_usage:.1f}", 
                             f"{memory_usage:.1f}", f"{load_1m:.2f}", f"{load_5m:.2f}", f"{load_15m:.2f}", f"{disk_usage_percent:.2f}"])
            f.flush()
            print(f"Level {level} summary: ok={stats['ok']} fail={stats['fail']} fail_ratio={fail_ratio:.3f} rps_avg={rps_avg:.2f} rps_ok_avg={rps_ok_avg:.2f}")
            # Strict expected message count: each device should send ceil(duration/interval) messages
            expected_per_device = max(1, math.ceil(single.duration / single.interval)) if single.interval > 0 else 1
            expected_total = single.devices * expected_per_device
            observed_total = stats['count']
            if observed_total != expected_total:
                print(f"Stopping: expected {expected_total} messages (devices={single.devices} * {expected_per_device}) but observed {observed_total}.")
                print("Hint: increase --launch-rate, increase per-level duration, or use burst mode for exact single update per device.")
                break
            if fail_ratio > args.failure_threshold:
                print(f"Stopping: fail_ratio {fail_ratio:.3f} exceeded threshold {args.failure_threshold}")
                stop = True
            elif stats['ok'] < args.min_ok:
                print(f"Stopping: ok responses {stats['ok']} < min_ok {args.min_ok}")
                stop = True
            else:
                devices += args.devices_step
                concurrency += args.concurrency_step
                if concurrency > 5000:
                    print("Capping concurrency at 5000 to avoid aiohttp connector overload")
                    concurrency = 5000
    print(f"\nRamp complete. Report written to {csv_path}")

def get_simulation_device_ids(take: int) -> list[int]:
    """Return up to 'take' device IDs whose uniqueId starts with 'SIM'. Cached after first fetch.

    Environment variables required:
      TRACCAR_API_KEY, TRACCAR_BASE_URL
    """
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

async def fetch_droplet_bandwidth_kbps(stats, direction:str) -> float:
    """Fetch latest outbound public interface bandwidth sample (last 1 minute) in kbps.

    - Uses DigitalOcean Monitoring metrics endpoint.
    - Returns float('nan') if API key or droplet id missing, on HTTP error, or no samples.
    - Updates stats['statuses'] with outcome for visibility (bw_skipped, bw_http_<code>, bw_ok, bw_empty, bw_error).
    """
    api_key = os.getenv("DO_API_KEY")
    droplet_id = os.getenv("DO_DROPLET_ID")
    if not api_key or not droplet_id:
        stats["statuses"]["bw_skipped"] += 1
        return float('nan')
    end_time = int(time.time())
    start_time = end_time - 60  # last minute window
    print(f"start={start_time}&end={end_time}")
    url = (
        "https://api.digitalocean.com/v2/monitoring/metrics/droplet/bandwidth"
        f"?host_id={droplet_id}&interface=public&direction={direction}&start={start_time}&end={end_time}"
    )
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Accept": "application/json"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        stats["statuses"][f"bw_http_{resp.status_code}"] += 1
    except Exception as e:
        print(f"Error fetching devices: {e}", file=sys.stderr)
        stats["statuses"]["bw_error"] += 1
        return float('nan')
    json_response = resp.json()

    # Extract latest numeric sample; API usually returns data.result[0].values = [[ts, value], ...]
    try:
        results = (json_response or {}).get("data", {}).get("result", [])
        if len(results) == 0:
            stats["statuses"]["bw_empty"] += 1
            return float('nan')
        result = results[0] if isinstance(results, list) else None
        if not result:
            stats["statuses"]["bw_empty"] += 1
            return float('nan')
        values = result.get("values", [])
        if not values:
            stats["statuses"]["bw_empty"] += 1
            return float('nan')
        # Get the last value from values list
        last_value = values[-1] if isinstance(values, list) else None
        if not last_value or len(last_value) < 2:
            stats["statuses"]["bw_empty"] += 1
            return float('nan')
        latest_val_str = last_value[1]
        # DigitalOcean metric value is megabytes per second. Convert to kbps (1 MBps = 1000 kbps)
        latest_val_int = float(latest_val_str)
        latest_val = latest_val_int if not math.isnan(latest_val_int) else 0
        kbps = latest_val * 1000  # convert to kbps
        stats["statuses"]["bw_ok"] += 1
        return round(kbps, 1)
    except Exception:
        stats["statuses"]["bw_parse_error"] += 1
        return float('nan')

async def fetch_droplet_cpu_usage(stats):
    """Fetch latest CPU usage sample (last 1 minute) as percentage.

    - Uses DigitalOcean Monitoring metrics endpoint.
    - Returns float('nan') if API key or droplet id missing, on HTTP error, or no samples.
    - Updates stats['statuses'] with outcome for visibility (cpu_skipped, cpu_http_<code>, cpu_ok, cpu_empty, cpu_error).
    """
    api_key = os.getenv("DO_API_KEY")
    droplet_id = os.getenv("DO_DROPLET_ID")
    try:
        if not api_key or not droplet_id:
            raise RuntimeError("Missing DO_API_KEY or DO_DROPLET_ID")
        end_time = int(time.time())
        start_time = end_time - 120  # last minute window
        url = (
            "https://api.digitalocean.com/v2/monitoring/metrics/droplet/cpu"
            f"?host_id={droplet_id}&start={start_time}&end={end_time}"
        )
        headers = {
            "Authorization": f"Bearer {api_key}", 
            "Accept": "application/json"
        }
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching CPU usage: {e}", file=sys.stderr)
        stats["cpu_percent"] = float('nan')
        return

    json_response = resp.json()

    # Extract latest numeric sample; API usually returns data.result[0].values = [[ts, value], ...]
    try:
        results = (json_response or {}).get("data", {}).get("result", [])
        if len(results) == 0:
            raise RuntimeError("No CPU metrics returned from DigitalOcean (last 1m window)")
        idle_diff = 0
        cpu_diff = 0
        for result in results:
            metric = result.get("metric", {})
            values = result.get("values", [])
            if not values or len(values) < 2:
                continue

            if metric.get("mode") == "idle":
                idle_cpu_b = values[-1] if isinstance(values, list) else None
                idle_cpu_a = values[-2] if isinstance(values, list) else None
                if not idle_cpu_b or len(idle_cpu_b) < 2 or not idle_cpu_a or len(idle_cpu_a) < 2:
                    continue
                idle_diff = abs(float(idle_cpu_b[1]) - float(idle_cpu_a[1]))
                cpu_diff += idle_diff
            else:
                cpu_b = values[-1] if isinstance(values, list) else None
                cpu_a = values[-2] if isinstance(values, list) else None
                if not cpu_b or len(cpu_b) < 2 or not cpu_a or len(cpu_a) < 2:
                    continue
                cpu_diff += abs(float(cpu_b[1]) - float(cpu_a[1]))
        if cpu_diff <= 0:
            raise RuntimeError("No CPU usage delta found in DigitalOcean metrics")
        cpu_usage = (1 - (idle_diff / cpu_diff)) * 100
        stats["cpu_percent"] = round(cpu_usage, 2)
    except Exception as e:
        print("Error parsing CPU usage from DigitalOcean metrics: {e}", file=sys.stderr)
        stats["cpu_percent"] = float('nan')

async def fetch_droplet_load(load_minute) -> float:
    """
    Fetch latest load average sample (last 1 minute, 5 minute, or 15 minute) as float.
    """
    api_key = os.getenv("DO_API_KEY")
    droplet_id = os.getenv("DO_DROPLET_ID")
    if not api_key or not droplet_id:
        return float('nan')
    if load_minute not in (1, 5, 15):
        raise ValueError("load_minute must be 1, 5, or 15")
    end_time = int(time.time())
    start_time = end_time - 60  # last minute window
    url = (
        f"https://api.digitalocean.com/v2/monitoring/metrics/droplet/load_{load_minute}"
        f"?host_id={droplet_id}&start={start_time}&end={end_time}"
    )
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Accept": "application/json"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        return float('nan')
    
    json_response = resp.json()

    # Extract latest numeric sample; API usually returns data.result[0].values = [[ts, value], ...]
    try:
        results = (json_response or {}).get("data", {}).get("result", [])
        if len(results) == 0:
            return float('nan')
        result = results[0] if isinstance(results, list) else None
        if not result:
            return float('nan')
        values = result.get("values", [])
        if not values:
            return float('nan')
        # Get the last value from values list
        last_value = values[-1] if isinstance(values, list) else None
        if not last_value or len(last_value) < 2:
            return float('nan')
        return round(float(last_value[1]), 2)
    except Exception:
        return float('nan')
    
async def fetch_droplet_memory_usage() -> float:
    """
    Total memory: https://api.digitalocean.com/v2/monitoring/metrics/droplet/memory_total
    Available memory: https://api.digitalocean.com/v2/monitoring/metrics/droplet/memory_available 
    Both endpoints will return a JSON object with a data field. The data is an array of datapoint objects, each containing a value (in bytes) and a timestamp. 
    """
    api_key = os.getenv("DO_API_KEY")
    droplet_id = os.getenv("DO_DROPLET_ID")
    if not api_key or not droplet_id:
        return float('nan')
    end_time = int(time.time())
    start_time = end_time - 60  # last minute window
    url_total = (
        f"https://api.digitalocean.com/v2/monitoring/metrics/droplet/memory_total"
        f"?host_id={droplet_id}&start={start_time}&end={end_time}"
    )
    url_available = (
        f"https://api.digitalocean.com/v2/monitoring/metrics/droplet/memory_available"
        f"?host_id={droplet_id}&start={start_time}&end={end_time}"
    )
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Accept": "application/json"
    }
    try:
        resp_total = requests.get(url_total, headers=headers, timeout=20)
        resp_total.raise_for_status()
        resp_available = requests.get(url_available, headers=headers, timeout=20)
        resp_available.raise_for_status()
    except Exception as e:
        return float('nan')
    
    json_total = resp_total.json()
    json_available = resp_available.json()

    try:
        results_total = (json_total or {}).get("data", {}).get("result", [])
        results_available = (json_available or {}).get("data", {}).get("result", [])
        if len(results_total) == 0 or len(results_available) == 0:
            return float('nan')
        result_total = results_total[0] if isinstance(results_total, list) else None
        result_available = results_available[0] if isinstance(results_available, list) else None
        if not result_total or not result_available:
            return float('nan')
        values_total = result_total.get("values", [])
        values_available = result_available.get("values", [])
        if not values_total or not values_available:
            return float('nan')
        last_value_total = values_total[-1] if isinstance(values_total, list) else None
        last_value_available = values_available[-1] if isinstance(values_available, list) else None
        if not last_value_total or len(last_value_total) < 2 or not last_value_available or len(last_value_available) < 2:
            return float('nan')
        total_mem = float(last_value_total[1])
        available_mem = float(last_value_available[1])
        used_mem = total_mem - available_mem
        mem_percent = (used_mem / total_mem) * 100 if total_mem > 0 else float('nan')
        return round(mem_percent, 2)
    except Exception:
        return float('nan')
    
async def fetch_droplet_disk_usage() -> float:
    """
    Total disk: https://api.digitalocean.com/v2/monitoring/metrics/droplet/filesystem_free
    Used disk: https://api.digitalocean.com/v2/monitoring/metrics/droplet/filesystem_size 
    Both endpoints will return a JSON object with a data field. The data is an array of datapoint objects, each containing a value (in bytes) and a timestamp. 
    """
    api_key = os.getenv("DO_API_KEY")
    droplet_id = os.getenv("DO_DROPLET_ID")
    if not api_key or not droplet_id:
        return float("nan")
    end_time = int(time.time())
    start_time = end_time - 100  # last minute window
    url_free = (
        f"https://api.digitalocean.com/v2/monitoring/metrics/droplet/filesystem_free"
        f"?host_id={droplet_id}&start={start_time}&end={end_time}"
    )
    url_size = (
        f"https://api.digitalocean.com/v2/monitoring/metrics/droplet/filesystem_size"
        f"?host_id={droplet_id}&start={start_time}&end={end_time}"
    )
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Accept": "application/json"
    }
    try:
        resp_free = requests.get(url_free, headers=headers, timeout=20)
        resp_free.raise_for_status()
        resp_size = requests.get(url_size, headers=headers, timeout=20)
        resp_size.raise_for_status()
    except Exception as e:
        return float("nan")
    
    json_free = resp_free.json()
    json_size = resp_size.json()

    try:
        results_free = (json_free or {}).get("data", {}).get("result", [])
        results_size = (json_size or {}).get("data", {}).get("result", [])
        if len(results_free) == 0 or len(results_size) == 0:
            return float("nan")
        result_free = results_free[-1] if isinstance(results_free, list) else None
        result_size = results_size[-1] if isinstance(results_size, list) else None
        if not result_free or not result_size:
            return float("nan")
        values_free = result_free.get("values", [])
        values_size = result_size.get("values", [])
        if not values_free or not values_size:
            return float("nan")
        value_free = values_free[-1] if isinstance(values_free, list) else None
        value_size = values_size[-1] if isinstance(values_size, list) else None
        if not value_free or not value_size:
            raise "Invalid value"
        value_size_fl = float(value_size[-1])
        value_free_fl = float(value_free[-1])

        disk_usage_diff = value_size_fl - value_free_fl
        disk_usage_percent = disk_usage_diff / value_size_fl * 100
        return round(disk_usage_percent, 2)
    except Exception as e:
        print("Disk usage error: ", file=sys.stderr)
        return float("nan")

def parse_args():
    base_url = os.getenv("TRACCAR_BASE_URL")
    ap = argparse.ArgumentParser()
    ap.add_argument("--devices", type=int, default=30000)
    ap.add_argument("--interval", type=int, default=30, help="Seconds between messages per device")
    ap.add_argument("--duration", type=int, default=30, help="Total run time seconds")
    ap.add_argument("--concurrency", type=int, default=1000, help="Max simultaneous sockets")
    ap.add_argument("--launch-rate", type=float, default=1000, help="New devices per second at startup")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--insecure", action="store_true", help="Disable TLS verification (for testing)")
    ap.add_argument("--debug", action="store_true", help="Print sample failure details periodically")
    ap.add_argument("--print-failures", type=int, default=5, help="Max failure samples to print per interval when --debug enabled")
    ap.add_argument("--status-summary", action="store_true", help="Show top status codes in progress lines")
    ap.add_argument("--id-prefix", default="000", help="Prefix for device uniqueId (must match devices registered in Traccar)")
    # Ramp mode options
    ap.add_argument("--ramp", action="store_true", help="Enable ramp (incremental load) mode")
    ap.add_argument("--devices-start", type=int, default=10000, help="Starting devices (defaults to --devices if omitted)")
    ap.add_argument("--devices-step", type=int, default=0, help="Increment devices each level")
    ap.add_argument("--max-devices", type=int, default=30000, help="Maximum devices for ramp")
    ap.add_argument("--concurrency-start", type=int, default=1000, help="Starting concurrency (defaults to starting devices)")
    ap.add_argument("--concurrency-step", type=int, default=0, help="Increment concurrency each level")
    ap.add_argument("--max-concurrency", type=int, default=10000, help="Maximum concurrency for ramp")
    ap.add_argument("--duration-per-level", type=int, default=30, help="Duration seconds per level")
    ap.add_argument("--failure-threshold", type=float, default=0.5, help="Fail ratio > threshold stops ramp")
    ap.add_argument("--min-ok", type=int, default=10, help="Minimum OK responses required to continue ramp")
    ap.add_argument("--csv", help="CSV report output path (default ramp_report.csv)")
    return ap.parse_args()

if __name__ == "__main__":
    load_dotenv()
    args = parse_args()
    base_url = os.getenv("TRACCAR_BASE_URL")
    if not base_url:
        print("Environment variable TRACCAR_BASE_URL is required", file=sys.stderr)
        sys.exit(1)
    if args.ramp:
        asyncio.run(ramp_runner(args, base_url))
    else:
        asyncio.run(runner(args, base_url))

### test command:
# python3 ./sim_traccar_osmand_ramp.py --ramp --failure-threshold 1 --status-summary --csv ramp_report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_1.csv