## 🔍 **Overview: What This Data Shows**

* **Test Inputs**: Device count, concurrency (always 1000), duration (30s)
* **Results Metrics**: OK/fail counts, fail ratio, response times (p50, p90, p99), RPS (requests per second), bandwidth, CPU, disk usage, memory, load averages, etc.
* **Patterns**: Several test cycles with increasing load (`devices` from 1000 to 15000), and then the system eventually hits failure thresholds.

---

## 📈 **Key Trends Observed**

### 1. **Good Performance Up to \~4000 Devices**

* **Fail ratio = 0**
* **Latency (p50) = \~60ms**
* **CPU/disk/memory usage remain stable**
* **RPS scales linearly** with device count.
* ✅ **System scales well** under moderate load.

---

### 2. **Performance Degradation Begins \~4500–7000 Devices**

* **Small fail ratios appear** (\~0.005–0.03), increasing with load.
* **p99 latency spikes** in some cases (e.g., up to 10,000+ ms).
* **Bandwidth usage and disk I/O increase sharply.**
* **System still handles most traffic**, but degradation is clear.

---

### 3. **System Collapses Around 7500–9000+ Devices**

* **High fail ratios**: up to 99.9% (`fail_ratio ~ 1.0`)
* **RPS still attempted (up to 500), but very few successes**
* **p50/p90/p99 latency = 30,000+ ms**
* **Disk usage spikes** (e.g., 120,000 kbps or more)
* **CPU hits 100%+** in some runs.
* ❌ **System can't sustain the load anymore.**

---

### 4. **Recovery Between Test Sessions**

* You restart tests (e.g., from 1000 devices) and performance goes back to normal.
* Suggests the system **recovers well** once pressure is lifted, possibly via restart or memory/disk clearance.

---

## ⚠️ **Bottlenecks Identified**

### A. **CPU Saturation**

* CPU usage grows with load, peaking at 100–108%.
* Once saturated, system response time degrades heavily.
* Some runs mention CPU peaks at specific timestamps.

### B. **Disk I/O Saturation**

* Disk read peaks: 905 Mbps, 120000 kbps (\~120 MBps)
* Very high read rates correlate with **high latency and failure rates**.
* Disk appears to be **a bottleneck under high load**.

### C. **Memory Usage & Load Average**

* Load averages increase significantly at high device counts.
* Some runs show **load\_1m over 15**, suggesting **multi-thread contention** and CPU/memory pressure.

---

## 📌 **Notable Events and Anomalies**

* `Stopping: ok responses 0 < min_ok 1`: Indicates a **test condition breach**, typically meaning the system is **non-functional at that level**.
* High `p99` latency often exceeds **10,000 ms** (10 sec) — unacceptable for most real-time systems.
* At some points:

  * `ok = 0`, `fail = N`, `fail_ratio = 1.0` — total failure.
  * Yet, `rps_avg` is still high — shows **incoming load is consistent**, but system can't handle/respond.

---

## ✅ **Takeaways and Recommendations**

### 🟢 What’s Working Well:

* Solid linear scalability **up to \~4000–5000 devices**
* Low latency, no failure at moderate loads
* System appears resilient (recovers fully between tests)

### 🔴 What Needs Attention:

1. **Optimize Disk I/O**

   * Consider:

     * Faster storage (SSD/NVMe)
     * Reducing disk writes per message
     * Write batching or async logging

2. **Improve CPU Efficiency**

   * Profile bottlenecks: garbage collection, serialization, etc.
   * Look into **parallelism/multi-threading improvements**

3. **Memory Management**

   * Investigate **GC behavior or memory leaks**
   * Use object pooling if allocations are high-frequency

4. **Throttling / Backpressure Mechanisms**

   * Implement rate limiting earlier to **prevent system overload**
   * Queue or shed load gracefully

5. **Benchmark Isolation**

   * Ensure background tasks/logging/monitoring don’t interfere during peak tests.

6. **Horizontal Scaling**

   * Consider adding more nodes or containers beyond 1 instance to handle more devices.