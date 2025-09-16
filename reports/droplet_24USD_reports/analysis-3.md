Here’s a **comprehensive summary** of the performance test data you provided:

---

## 🔍 **Test Overview**

* **Purpose:** Load testing across different levels of **device counts (1,000 to 30,000)** and **concurrency (1,000 and 2,000)** to assess system behavior.
* **Duration per level:** 30 seconds
* **Test phases:** Three distinct test batches (based on timestamps), progressively increasing in devices and load.

---

## ⚙️ **System Performance Highlights**

### ✅ **Success Rate**

* **Up to \~14,000–16,000 devices**: Near **100% success**, zero or very low fail ratios.
* **Above \~17,000 devices**: Gradual increase in **fail ratios**, peaking at:

  * **79.8% fail ratio** at **30,000 devices (13:03)** under 1,000 concurrency.
  * **31.4% fail ratio** at **25,000 devices (13:55)** under 2,000 concurrency.

---

## 📈 **Throughput & Latency**

### 🚀 **Requests Per Second (RPS)**

* Scaled **linearly** with device count up to \~20,000.
* **Max observed RPS**: \~1,000 at 30,000 devices.
* Performance **drops** or **plateaus** at higher levels due to failures.

### 🕒 **Latency (p50 / p90 / p99 in ms)**

* **p50 (median)** latency remained stable (\~60–80ms) in low to mid-level loads.
* Spikes seen at high loads:

  * **p90 / p99** exceeded **10,000ms** during high failure periods (e.g., 13:01–13:03).
  * Indicates **severe queuing or blocking** under load saturation.

---

## 📉 **Error Trends**

### ❌ **Failures**

* Mostly **0% fail ratio** up to 16,000 devices.
* **Sharp increase** in errors from 17,000–30,000 devices.
* Failures reached **\~24,000 out of 30,000 requests** during worst phase.

---

## 📡 **Bandwidth Usage (kbps)**

* **Outbound (`bandwidth_pub_out_kbps`)**:

  * Grew steadily with device count.
  * Peaked at over **4,500 kbps** at higher loads.

* **Inbound (`bandwidth_pub_in_kbps`)**:

  * Grew to \~950 kbps, indicating **increased message processing** at scale.

---

## 💻 **Resource Utilization**

### 🧠 **CPU & Memory**

* **CPU Usage:**

  * Stable and low (\~<10%) during low to mid-level loads.
  * Rose to **\~28%** at max loads, indicating **available headroom**.
* **Memory Usage:**

  * Rose from \~30MB to \~700–900MB at higher loads.
  * System handled memory scaling well.

### ⚖️ **System Load (`load_1m`, `load_5m`, `load_15m`)**

* Generally aligned with expected performance.
* Spikes during intense failure periods suggest **I/O or CPU queue buildup**.

---

## 🧱 **Disk Usage**

* Constant at **22.5%** across all tests — no disk bottleneck observed.

---

## 📌 **Key Observations**

1. ✅ **Scales well up to \~15,000 devices** with low latency and zero errors.
2. ⚠️ **Performance degrades** beyond **\~17,000 devices**.
3. ❌ At **30,000 devices**, failure ratio **spikes up to 80%**, and latency becomes **unusable**.
4. 🚥 Bottlenecks appear **not to be CPU, memory, or disk**, but possibly:

   * Message queuing
   * Application thread pool limits
   * Network saturation
5. 🧪 Results are consistent across both **1,000 and 2,000 concurrency** runs.

---

## 📊 Recommendations

* **System tuning needed beyond \~15k devices**, especially for:

  * Thread pools, async queues
  * Load balancers or brokers
  * Rate-limiting mechanisms
* Consider **horizontal scaling** or **sharding** above 15k devices.
* Investigate **latency spikes** and **request timeouts** at high concurrency.

---

Let me know if you want:

* **Visual charts**
* **Breakdown per phase (1k–10k, 10k–20k, etc.)**
* **Root cause analysis on failure spikes**
