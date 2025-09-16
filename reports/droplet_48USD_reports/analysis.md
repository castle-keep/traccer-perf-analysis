### 📊 **Trend Analysis**

✅ Current Observations:

- Initial scaling looks smooth up to around ~15,000–20,000 devices.
- From ~20,000+ devices, failures start increasing, latency (P99) jumps dramatically, and fail ratios go up.
- Your failures peak around 30,000–35,000 devices, with high fail_ratio and latency (some p99_ms in the tens of thousands ms).
- CPU and memory usage remain relatively low, suggesting the bottleneck might not be CPU/memory, but:
  - I/O
  - DB connections
  - GC pauses
  - Network limits
  - Thread exhaustion
  - Single-threaded logic bottleneck

#### ✅ **1. Throughput Increases with Devices Until Saturation**

* `rps_avg` grows linearly with `devices` until about **33,000–36,000 devices**, then starts **plateauing or increasing slower**.
* Example:

  * Level 30 (30,000 devices): `rps_avg` = 1000.00
  * Level 40 (40,000 devices): `rps_avg` = 1333.33
  * Level 46 (46,000 devices): `rps_avg` = 1533.33
  * Level 50 (50,000 devices): `rps_avg` = 1666.67

#### ⚠️ **2. Failure Rate Starts Increasing Beyond \~27,000 Devices**

* Failure ratio stays **0%** up to **\~26,000 devices**
* After that, it spikes and stays elevated:

  * Level 27 (27,000): `fail_ratio` = 0.1246
  * Level 33 (33,000): `fail_ratio` = 0.0862
  * Level 50 (50,000): `fail_ratio` = 0.0474

This implies **system starts dropping or rejecting requests** due to resource saturation or bottlenecks beyond this point.

#### ⏱️ **3. Latency Degrades with Load**

* Latency (`p90_ms`, `p99_ms`) increases significantly at higher levels:

  * Level 10 (10k devices): `p99_ms` = 30,653.1 ms
  * Level 30 (30k devices): `p99_ms` = 21,413.3 ms
  * Level 50 (50k devices): `p99_ms` = 11,575.6 ms

Note: The large numbers here suggest that **some requests are hitting serious timeouts or queuing delays**.

#### 🧠 **4. Resource Usage Remains Surprisingly Flat**

* `cpu_percent` stays roughly **constant at \~22.55%** throughout
* `memory_usage`, `load averages`, and `disk usage` increase slightly but are **not the main bottlenecks**

This could indicate:

* Load is **not CPU-bound**
* **Network I/O or external systems (e.g., DB, queue)** may be the limiting factor
* Or resource metrics are being **collected from a central orchestrator node** not fully exposed to load

---

### 📉 **Degradation Point**

**System starts to degrade around**:

* 🔁 **26,000–30,000 devices**
* 📉 `fail_ratio` rises
* ⏳ Latencies spike
* ⚠️ RPS increases slow

---

### 📌 **Recommendations**

1. **Set a safe capacity threshold**: Operate below **25,000 devices** to maintain 0% failure and stable latency.
2. **Investigate request timeouts**: High `p99_ms` indicates slow response times — potentially backend/service delays or overload.
3. **Monitor external dependencies**: Since CPU/memory stay low, look at network I/O, databases, or message brokers.
4. **Run more targeted profiling** at high load to find bottlenecks.