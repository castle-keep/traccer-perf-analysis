**General Observations Across Runs:**

* Each test run increases the `devices` count (test scale).
* `concurrency` and `duration` are fixed: `1000` and `30` seconds respectively.
* `fail_ratio` and latencies (`p50_ms`, `p90_ms`, `p99_ms`) are important to spot breaking points.
* System health metrics (CPU, memory, load averages, disk usage) remain largely stable — disk usage is constant at 22.51%.

---

## 📈 **Performance Breakdown by Key Metrics:**

### ✅ **1. Success Rate (`ok`, `fail`, `fail_ratio`)**

* Up to around **level 14–15 (\~14,000–15,000 devices)**, the system handles load well with a **fail ratio below 3%**.
* Failures start to spike at:

  * **Level 17–18 (17,000–18,000 devices)** — sharp rise in fail ratio.

    * **fail\_ratio jumps to \~0.72** in one case.
  * **Beyond 25,000 devices**, fail ratio becomes inconsistent and often **exceeds 0.05**.

#### 🔥 **Potential Bottleneck Zone:**

* **17,000–19,000 devices** — transitional zone where failures rise rapidly.
* **30,000 devices** — fail ratio hits nearly **80%** in some test runs. Likely system collapse point.

---

### 🚀 **2. Throughput (`rps_avg`, `rps_ok_avg`)**

* RPS (requests per second) increases linearly with devices:

  * Starts from \~33 rps and scales up to **1000 rps** at 30,000 devices.
* However, **RPS does not scale linearly once failures start increasing**.

  * E.g., at 30,000 devices, you still see 1000 rps, but `ok` drops drastically (only \~6000 successful).

---

### 🕓 **3. Latency Trends (p50\_ms, p90\_ms, p99\_ms)**

* **Stable Latency (≤ 70 ms p50)** until \~14,000–15,000 devices.
* After 17,000 devices:

  * Latency metrics (especially **p99\_ms**) explode into **10,000+ ms** territory.
  * In many tests, **p99\_ms > 30,000 ms**, indicating extreme queuing or timeouts.

---

### 🧠 **4. Resource Usage**

#### CPU:

* Generally low throughout the test.

  * Even at max load, **CPU usage rarely exceeds \~27%**.
  * Indicates that CPU isn't the bottleneck.

#### Memory:

* Gradually increases but stays within acceptable range.
* Peak around **950 MB**, which seems sustainable.

#### Load Averages:

* As expected, **load increases with device count**, but not catastrophically.
* Load spikes (3.88 etc.) around level 25+ indicate rising pressure but not necessarily saturation.

---

### 🌐 **5. Network Throughput (Bandwidth)**

* `bandwidth_pub_out_kbps` and `bandwidth_pub_in_kbps` grow with device count.
* Massive spikes in outgoing bandwidth:

  * At 30,000 devices: **\~4500 kbps**.
* Huge bandwidth might be correlated with system bottlenecks (e.g., publisher overload or network congestion).

---

## 🧭 **Identifying System Capacity Thresholds**

| Metric        | Safe Range    | Warning     | Critical  |
| ------------- | ------------- | ----------- | --------- |
| `devices`     | ≤ 15000       | 16000–20000 | > 20000   |
| `fail_ratio`  | < 0.03        | 0.03–0.1    | > 0.1     |
| `p99_ms`      | < 200 ms      | 200–5000 ms | > 5000 ms |
| `rps_ok_avg`  | Linear growth | Plateaus    | Drops     |
| `cpu_percent` | < 25%         | 25–50%      | > 50%     |
| `load_1m`     | < 2.0         | 2.0–3.5     | > 3.5     |

---

## 📌 **Recommendations**

1. **Optimal Load Target:**

   * Keep **device count ≤ 15,000** for optimal performance.
   * Beyond that, system starts failing requests and latency spikes.

2. **Investigate Bottlenecks:**

   * Network (publishing) or internal message queues might be the bottleneck — given high latency and fail ratios even when CPU/memory are fine.

3. **Vertical Scaling Ineffective:**

   * Since CPU/memory remain low, throwing more resources at the server may not help unless the software stack is tuned.

4. **Load Spreading:**

   * Consider spreading load across multiple nodes or instances.

5. **Review Queue/Backpressure Mechanisms:**

   * System starts timing out rather than queueing well after saturation — may need better throttling or failover logic.

---

## 📊 Would you like a visualization?

I can help you generate:

* RPS vs Devices
* Fail Ratio vs Devices
* Latency (p50/p90/p99) vs Devices
* CPU/Memory/Load vs Devices

Just say the word or upload as CSV for plotting.

Let me know how you'd like to proceed.
