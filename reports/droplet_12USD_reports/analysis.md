### ⚙️ **General Context**

Each section corresponds to a separate test run starting from:

* **Devices:** 1,000 up to 25,000
* **Concurrency:** Constant at 1,000
* **Duration:** 30s per test
* **Metrics Logged:** Requests, latencies (p50/p90/p99), failures, CPU/memory/load, and bandwidth

---

## 🔍 Key Observations

### 1. **System Scales Well Until \~16,000 Devices**

* **Zero or low fail ratios** (< 3%) up to **level 16** (\~16k devices)
* **RPS (requests per second)** grows linearly with device count.
* **Latency (p50/p90/p99)** remains within reasonable limits.

For example:

| Level | Devices | Fail Ratio | RPS | p50 (ms) | CPU (%) |
| ----- | ------- | ---------- | --- | -------- | ------- |
| 10    | 10,000  | 3.6%       | 333 | 64.0     | 23.6    |
| 16    | 16,000  | 2.2%       | 533 | 100.7    | 29.8    |

---

### 2. 📈 **Failures Increase Beyond 16k Devices**

From **level 17+**, performance deteriorates:

#### a. **Failure Ratios Spike**

| Level | Devices | Fail %       |
| ----- | ------- | ------------ |
| 17    | 17,000  | 2.5%         |
| 18    | 18,000  | 9.8%         |
| 20    | 20,000  | 11.7%        |
| 25    | 25,000  | **23.5%** 🔥 |

#### b. **Latency (p99) Skyrockets**

At **25k devices**, `p99` jumps from \~500ms to **30,000+ ms**, indicating:

* Severe bottlenecks
* Possibly **queueing delays** or **timeouts**

---

### 3. 📉 **RPS Drops at High Load**

Although more devices are added, **RPS flattens or drops**:

* Level 20: 667 RPS
* Level 25: 833 RPS average, but only 637 RPS OK (due to 23.5% failures)

This suggests the system is **overloaded**, and additional requests **fail or timeout**.

---

### 4. 🧠 **CPU and Memory Usage**

* **CPU Usage** increases gradually but stays within range until final levels.
* Memory also scales reasonably.
* However, **load average** increases sharply in later stages (e.g. 11.25 at level 25), which may indicate **CPU saturation** or **thread contention**.

---

### 5. 🔌 **Network Bandwidth Saturation**

* **`bandwidth_pub_out_kbps`** grows with device count.
* At 25k devices: Over **5 Mbps outgoing**
* **May be a factor in delay**, especially if constrained by NIC or shared resources.

---

## 🧠 Key Metrics Summary

| Metric              | Thresholds Reached                       |
| ------------------- | ---------------------------------------- |
| **Fail Ratio**      | > 10% at \~20k devices                   |
| **Latency p99**     | Exceeds 30s at 25k devices               |
| **Load Avg (1m)**   | > 4 at 20k+, suggesting saturation       |
| **Bandwidth (out)** | Peaks \~5 Mbps+                          |
| **RPS Deviation**   | Starts diverging from expected after 16k |

---

## ✅ Recommendations

1. **Capacity Planning:**

   * Consider **16,000 devices** as current **safe max capacity**.
   * Beyond that, plan for **horizontal scaling**, **load balancing**, or **resource provisioning**.

2. **Bottleneck Analysis:**

   * Investigate **request handling path**, especially network IO, DB, or queues.
   * Review **thread pool / event loop** limits.
   * Check for **GC pauses** if Java-based.

3. **Error Pattern Debugging:**

   * Analyze **failure types** (timeouts, 5xx, etc.)
   * Correlate with logs and system metrics (disk IO, memory pressure, etc.)

4. **Auto-Scaling Triggers:**

   * Base on **load average > 4**, **fail ratio > 5%**, or **p99 > 500ms**

5. **Tune RPS per Instance:**

   * RPS flattens around 500-700 per 1k concurrency.
   * Adjust **per-instance concurrency** or **instance count** accordingly.