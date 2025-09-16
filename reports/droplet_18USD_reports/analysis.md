## 📈 **Key Observations**

### 1. **Scalability Trend**

* **Up to \~15,000 devices**, the system scales **almost linearly**, with RPS and `ok` requests increasing proportionally.
* After **\~16,000 devices**, we start seeing:

  * **Failures** and increased **fail ratios**
  * **Increased latency**, especially `p99_ms`
  * High and eventually erratic **bandwidth usage**

### 2. **Performance Breakdown Zones**

| Device Count | Behavior                  | Notes                                                                    |
| ------------ | ------------------------- | ------------------------------------------------------------------------ |
| **1K–15K**   | Stable, efficient scaling | `fail_ratio` \~0%, RPS increases linearly                                |
| **16K–20K**  | Minor instability         | Failures begin (\~2–4%), `p99_ms` increases                              |
| **20K–30K**  | Moderate degradation      | Fail ratio rises (10–45%), bandwidth & latency spikes                    |
| **30K–50K**  | Severe degradation        | Fail ratios exceed 50% at points; some recoveries noted but inconsistent |

---

### 3. **Failure Patterns**

* **Fail ratio exceeds 40–50%** several times after 30K devices.
* For example:

  * At **45K devices**, `fail_ratio = 0.5494` (54.9%)
  * At **42K devices**, it drops to 0.0200 temporarily, but later spikes again
* Indicates **threshold** beyond which the system struggles significantly.

---

### 4. **Latency Trends**

* **`p50_ms`** remains under 100ms early on.
* Surges in `p50_ms`, `p90_ms`, and `p99_ms` start around **Level 12–14 (12K–14K devices)**.
* Example:

  * At 12K: `p99_ms = 15798.1`
  * At 14K: `p99_ms = 30758.7` – huge jump.

---

### 5. **CPU & Memory**

* CPU rises gradually:

  * From **\~4% to 36%**, then **up to 62%**
  * CPU percent seems **well-managed**, suggesting CPU isn't the main bottleneck.
* Memory usage increases but remains within operational range.

---

### 6. **System Load**

* `load_1m`, `load_5m`, `load_15m` increase in proportion to device count.
* Spikes >3 in `load_1m` suggest potential **queuing or threading issues** under heavy load.

---

### 7. **Bandwidth**

* Outbound/inbound bandwidth scales with load.
* Noticeable jumps at:

  * **Level 8 (8K devices)**: \~870 kbps → surge starts
  * **Level 20+**: Exceeds **3–6 Mbps** outbound
  * Peaks around **8 Mbps**

---

## 🔍 **Anomalies or Noteworthy Patterns**

* **Saturation Point**: After \~16K devices, success rate becomes unreliable. True saturation might be around **17K–20K devices**.
* **Recovery Attempts**: There are intervals where the system appears to **recover briefly** (e.g., Level 26–28), before failing again under continued load.
* **p99 Latency Spikes** can reach **30,000+ ms** — major issue for user experience.

---

## 📌 Recommendations

1. **Set Soft Limit: \~15–17K Devices**

   * Above that, risk of failure grows rapidly.

2. **Investigate Failure Causes**

   * Likely causes: thread pool exhaustion, DB bottlenecks, queue backlogs, or API rate limits.
   * Enable detailed logging during failures.

3. **Tune Queuing & Concurrency Models**

   * Check thread pool sizes, connection limits, timeouts.

4. **Load Test with Variable Concurrency**

   * Try different `concurrency` levels to identify optimal throughput vs. latency tradeoffs.

5. **Auto-scaling (if cloud-based)**

   * Consider horizontal scaling or load balancing.

6. **Monitor Garbage Collection (if applicable)**

   * Especially since latency spikes may point to GC pauses or memory pressure.
