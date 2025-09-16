### ⚙️ **Test Parameters Overview**

* **Concurrency** is constant at `1000` or `2000` across runs.
* **Devices** ramp from 1000 to 30000.
* Each test runs for `30 seconds`.
* The primary metrics of interest are:

  * `ok` / `fail` counts and `fail_ratio`
  * `rps_avg` (requests per second)
  * Latency metrics (`p50_ms`, `p90_ms`, `p99_ms`)
  * `bandwidth`, `cpu_percent`, `memory_usage`, and system load

---

### 📈 **General Trends by Device Count**

#### ✅ **Low Load (1000–7000 devices)**

* **Zero failures**, low latencies (p50 \~60ms), high success rate.
* `RPS` increases linearly with device count.
* **CPU usage is minimal** (\~0.7–8.5%) and **fail\_ratio = 0.0000**
* Bandwidth and load metrics remain stable.

#### ⚠️ **Moderate Load (8000–15000 devices)**

* Small **failure ratios** begin to appear (\~0.03 to 0.07).
* **Latency increases gradually**, e.g., p90\_ms reaches 300–500ms.
* `RPS` continues to scale well.
* **CPU climbs to \~12–23%**, memory grows modestly.
* Start seeing performance dips around **9000–11000** devices intermittently.

#### ❌ **High Load (16000–30000 devices)**

* **Failure ratios spike** beyond 0.3+ for some runs.
* **Huge latency spikes**, e.g., `p90_ms` over 10,000ms in some cases.
* **RPS flattens or drops**, especially with high fail counts.
* CPU continues to increase but not linearly — possibly throttled or saturated.
* Disk usage and memory remain stable, suggesting **network or CPU bottlenecks**.

---

### 🧠 **Key Observations**

#### 1. **Scaling Limit Detection**

* **Sweet spot appears to be \~15000 devices** — after which failure ratios start increasing non-linearly.
* Runs with **20000+ devices** often hit 10%–80% **failures** (e.g., test levels 17, 26, 30).

#### 2. **Performance Degradation Signs**

* **Latency explosions** (`p90_ms` & `p99_ms` > 10s).
* Sudden drop in `ok` requests despite consistent concurrency (bottleneck likely hit).
* Bandwidth saturates around **30,000 kbps**, possibly capping out.

#### 3. **CPU & System Load**

* CPU usage remains **under 30%**, suggesting system is **not CPU-bound**.
* However, spikes in **`load_1m/5m`** (e.g., >3.0) during failure-heavy runs indicate **resource contention or blocking**.

---

### 📊 **Visualizing for Deeper Insight**

If you'd like:

* I can create **charts or graphs** showing trends (e.g., fail ratio vs. device count, latency vs. RPS).
* You can also **upload this data as CSV or Excel**, and I can process it further.

---

### ✅ **Summary Recommendations**

* **Optimal device load** appears to be **<= 15000 devices**.
* Beyond that, failure rate and latency grow rapidly—indicating **system stress** or **scaling limit**.
* Investigate **network throughput**, **I/O**, and **queue backlogs** beyond this threshold.
* Monitor for **rate-limiting**, **connection saturation**, or **resource pool exhaustion** (e.g., threads, buffers).