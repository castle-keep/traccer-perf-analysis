## 🔍 **Summary of Key Metrics**

Each test varies:

* **devices**: the number of connected clients/devices
* **concurrency**: constant at 1000 (seems like server worker threads or concurrency limit)
* **duration**: always 30 seconds
* **ok / fail / fail\_ratio**: core indicator of success
* **latencies** (p50, p90, p99), RPS, bandwidth, CPU, disk
* Later runs include **memory, load avg, and disk usage**

---

## 🧠 **What You Might Be Missing**

### ✅ **1. The system scales up to 4000–4500 devices well**

Across most runs:

* Up to **4000 devices**: **fail\_ratio is \~0**, latencies stay low, and CPU/IO are under control.
* At **4500 devices**:

  * Occasional minor errors start: e.g., 11 or 12 failures
  * But still **<0.003 fail ratio**, which is acceptable
  * Latencies remain stable (\~60–100 ms p50)

✅ **Conclusion**: **4000–4500 devices is within safe range**.

---

### ⚠️ **2. Instability begins at \~5000 devices**

* Starting at **5000 devices**, patterns emerge:

  * Failures rise quickly (e.g., 64 fails → thousands)
  * Latencies **spike dramatically** to 10,000+ ms
  * Disk read spikes (especially when no public request activity exists)
  * CPU ramps up sharply
* For example:

  * **2025-09-04 13:21:15** (5500 devices): only **3065 OK**, **fail ratio = 0.44**
  * **2025-09-04 13:21:45** (6000 devices): **fail ratio = 0.97**
  * **Disk reads >10,000 kbps** (i.e., >10 MB/s)
  * **p99 latency >10s**!

⚠️ **Conclusion**: Above **5000 devices**, **system becomes unreliable**.

---

### 🧨 **3. System enters pathological state >6000 devices**

* **7000+ devices**:

  * Requests mostly fail (fail ratios 0.6 → 1.0)
  * Latencies hit maxes: **p99 \~11s**, some timeouts
  * Even with 0 public traffic, **CPU and disk I/O spike hard** (which is suspicious)

    * Disk read up to **648 Mbps**
    * CPU idle = 0%
* These aren't just signs of load—**this could point to internal retry loops, I/O thrashing, or garbage collection (GC) storm**.

🛑 **This is dangerous**:

* Indicates **background systems** (like storage, queues, database, pub/sub) are **collapsing under load**.

---

### ❓ **4. Ghost activity after failure (The “Weird Spike”)**

> “Disk and CPU is weirdly spiking with no public request activity”

This is key:

* Suggests background processes (e.g., retry mechanisms, queue reprocessing, log flushes) **keep consuming CPU/disk** **after load is gone**
* Could be due to:

  * **Retry queues**, message brokers, logs
  * Inefficient GC or memory compaction
  * Buffer flushes that got delayed during overload

You’re missing that **post-failure spikes** mean your system:

* Doesn’t fail gracefully
* **Doesn’t throttle or cancel work under load**
* May get into a **non-recoverable state** (i.e., “latch” into a degraded mode)

---

### 📊 **5. You’re seeing saturation at multiple layers**

| Layer             | Symptom                               | Bottleneck Appears Around |
| ----------------- | ------------------------------------- | ------------------------- |
| **App layer**     | Failures rise, p99 > 10s              | 5000–5500 devices         |
| **Disk I/O**      | Read spikes up to 648 Mbps            | 6000+                     |
| **CPU**           | Near 100% utilization, stays elevated | 6000+                     |
| **Network**       | Bandwidth stable / increasing         | Not the limit here        |
| **Memory / Load** | Load avg increases / memory is stable | Load 15m climbs >3        |

Takeaway:

* **CPU and disk I/O are your real bottlenecks**
* **Network isn’t the main limiter**
* If you have a pub/sub system, **message reprocessing or queue flushes** are likely overwhelming disk

---

## 🧮 **Safe Device Range Estimation**

| Devices   | Result            | Notes                       |
| --------- | ----------------- | --------------------------- |
| 1000–4000 | ✅ Stable          | Clean success, low latency  |
| 4500      | ✅ Stable (barely) | Minor fail\_ratio (<0.003)  |
| 5000      | ⚠️ Borderline     | \~1% fail, rising latencies |
| 5500      | ❌ Unstable        | >40% fail, p99 > 10s        |
| 6000+     | 🚨 Collapsing     | >90% fail, system in pain   |

🧠 **Optimal target = 4000–4500 devices**

📉 **Soft limit = 5000 devices**
🔴 **Hard fail threshold = 5500–6000 devices**

---

## 🧩 **Hidden Insights**

### 1. **Latency rise is exponential after 5000**

* p99 latency jumps from \~500ms → **10s**
* Sign of queuing and contention, possibly in:

  * Task executor pool
  * Message queue
  * Disk I/O waiting
  * GC pause times

You might want to instrument:

* GC pause duration
* Queue depth
* Disk queue length
* Message backlogs

---

### 2. **The system does not degrade gracefully**

* Instead of slowing down or rejecting cleanly, it **keeps accepting work and starts failing catastrophically**
* Solutions:

  * Apply **load shedding** or **circuit breakers**
  * Introduce **backpressure**
  * Protect disk from being overwhelmed by queued background processes

---

### 3. **The retry/recovery behavior makes things worse**

You have evidence that **after failure**, CPU/disk keep climbing **even though load drops to zero**. That’s pathological:

* Indicates the system **doesn’t cancel failed work** effectively
* These could be:

  * Retry storms
  * Infinite backoffs
  * Delayed GC / compaction
  * Metrics collection overload
* A system in this state **can no longer process new requests**, even if load is back to normal

🧠 Consider:

* Investigating logs/error queues after overload
* Whether logs, metrics, or database writes spike after test ends

---

## 📌 **Next Steps and Recommendations**

### ✅ Immediate Action:

* Set **hard limit** at **4500 devices**
* Add **automatic throttle or admission control** at 5000 devices
* Investigate:

  * Disk flushing behavior
  * CPU usage during “idle” periods
  * Retry queues

### 📈 Medium-term:

* Profile performance for:

  * GC activity
  * Disk I/O by process
  * Background thread activity
* If using message queues/pubsub:

  * Tune retry/backoff
  * Add dead-letter queues
  * Implement rate control

### 🔧 Tooling:

* Collect:

  * GC logs
  * Disk I/O by process (`iotop`)
  * Thread dumps during spikes
* Consider integrating tools like:

  * Prometheus + Grafana for real-time monitoring
  * Flamegraphs for CPU usage
  * APM tools (e.g., Datadog, New Relic)

---

## 🧠 TL;DR — What You're Not Seeing:

| Insight                                                        | Meaning                                        |
| -------------------------------------------------------------- | ---------------------------------------------- |
| ✅ 4000–4500 devices is your **stable sweet spot**              | Above that, error rates spike sharply          |
| ⚠️ Failures and latencies increase **non-linearly** above 5000 | Suggests **resource contention** or saturation |
| 🔥 System doesn’t degrade gracefully — it **collapses**        | Need backpressure and circuit breakers         |
| 🧩 High post-failure CPU/disk usage = background storm         | Possibly from retries, flushes, or GC          |
| ❌ No safe recovery from overload                               | System may stay unusable until restart         |