## 🔍 **High-Level Overview**

### Test Parameters

* **Concurrency:** Constant at 1000.
* **Duration:** Constant at 30 seconds.
* **Devices:** Ramped up from 1000 to 20500+.
* **Metrics Tracked:** Success/failure counts, latency (p50/p90/p99), RPS, bandwidth, CPU, memory, system load, disk usage.

---

## 📈 **Key Trends by Metric**

### ✅ Success & Failure Rates

* **Up to \~8000 devices**: All requests successful (`fail_ratio` = 0.0000).
* **Beyond 8000–12000 devices**: Small number of failures appear (e.g., \~2% fail ratio).
* **Past 13000 devices**: Failure rates increase significantly.

  * **Notable peaks:**

    * At 15500 devices: **41.94% failure**.
    * At 18500 devices: **38.82% failure**.
    * At 19000 devices: **18.01% failure**.
* **Stability returns** briefly after some high-failure tests, indicating system recovers when load drops or stabilizes.

### ⚡ RPS (Requests Per Second)

* **Scales linearly** with devices until about **level 30–33 (up to 16500 devices)**.
* Peaks around **666.67 RPS**, indicating a **RPS ceiling** (system limit).
* After \~level 33, **RPS plateaus or drops slightly** due to rising failure rates and saturation.

### ⏱ Latency (p50/p90/p99 in ms)

* **p50** hovers between **60–70 ms** until high failure levels, then spikes.
* **p90/p99**:

  * Stable in early tests.
  * Spikes at high load/failure levels:

    * **p99** hits **>10,000 ms (10s)** at times — significant queueing/delays.

### 🔄 Bandwidth (kbps)

* **Output (pub\_out)**:

  * Increases with devices.
  * Peaks around **30,000 kbps** during highest RPS.
* **Input (pub\_in)**:

  * Also scales with load.
  * Ranges from small values (e.g., 9.2 kbps) to **>700 kbps**.

### 🔧 CPU & Memory Usage

* **CPU (%)**:

  * Rises gradually with load.
  * At higher levels (e.g., 17000+ devices): peaks \~**30–40%**.
* **Memory Usage (GB)**:

  * Increases with load.
  * Reaches up to **\~1000+ MB (\~1 GB)** or more under heavy load.

### 📊 System Load

* **Load 1m / 5m / 15m**:

  * Correlates with device load and failures.
  * Peaks at **5.07 (1m)** during extreme tests (indicative of CPU strain or I/O bottlenecks).

---

## 🚨 **Problematic Levels**

| Level      | Devices             | Fail Ratio | Notable Issues                      |
| ---------- | ------------------- | ---------- | ----------------------------------- |
| 11 (6000)  | 5665 OK, 335 FAIL   | 5.6%       | First sign of failures.             |
| 21 (11000) | 8982 OK, 2018 FAIL  | 18.3%      | Latency spike & high bandwidth.     |
| 30 (15500) | 9000 OK, 6500 FAIL  | 41.9%      | Huge failure rate.                  |
| 36 (18500) | 11318 OK, 7182 FAIL | 38.8%      | Memory and latency spikes.          |
| 40 (20500) | 11907 OK, 8093 FAIL | 40.4%      | Load average high, system stressed. |

---

## 📌 Observations & Takeaways

### 🟢 What’s Working:

* The system handles **up to \~8000 devices with full success**.
* Latency remains within acceptable bounds (\~60–70ms p50) in low to moderate load scenarios.
* Bandwidth and CPU scale linearly with load initially.

### 🔴 What Needs Attention:

* **System degradation begins** around 10000–12000 devices.
* **Failure ratio >10%** starts to occur around **level 18–21**.
* **Beyond 15000 devices**, the system is **unstable** (30–40%+ failure).
* **Spikes in p99 latency (10s+)** during failure-heavy tests suggest **backlog/queuing problems** or **saturation at the service or database layer**.
* **Load averages >3-4** at high levels may indicate CPU or disk I/O bottlenecks.

---

## 📌 Recommendations

1. **Capacity Planning**:

   * Define a **safe operational limit around 8000–10000 devices**.
   * Beyond this, build in throttling, autoscaling, or load shedding mechanisms.

2. **Bottleneck Analysis**:

   * Investigate service logs or metrics during tests at **level 18+** (e.g., queue sizes, DB connections, thread pools).
   * Look into latency spikes — they often point to saturated resources or timeouts.

3. **Resource Scaling**:

   * Evaluate horizontal scaling strategies — CPU usage isn't maxed, but **load avg and latency suggest contention**.
   * Consider separating high-throughput pub/sub traffic into isolated components.

4. **Graceful Degradation**:

   * Implement fallbacks or retry policies when services are under stress.
   * Use circuit breakers to isolate failure-prone services.