# Droplet Specifications & Load Testing Data

This document describes the configuration of the DigitalOcean Droplets used for GPS Tracker load testing with **self-hosted Traccar**.

## Current Droplet Configurations

### Tier 1 - Droplet_6USD (Baseline 1)

- **vCPU:** 1
- **CPU Type:** Regular
- **Memory:** 1 GB  
- **Storage (SSD):** 25 GB  
- **Transfer:** 1 TB
- **Monthly Cost:** $6  
- **Dedicated Volume:** 100 GB ($10)
- **Reports Location:** `/reports/droplet_6USD_reports/`  
- **Total Monthly Cost:** $16

**Report Files:**  

- `reports/droplet_6USD_reports/report_1Gbmem_1vCPU_25Gbssd_1TB_6USD_1.csv`
- `reports/droplet_6USD_reports/report_1Gbmem_1vCPU_25Gbssd_1TB_6USD_2.csv`
- `reports/droplet_6USD_reports/report_1Gbmem_1vCPU_25Gbssd_1TB_6USD_3.csv`
- `reports/droplet_6USD_reports/report_1Gbmem_1vCPU_25Gbssd_1TB_6USD_4.csv`

---

### Tier 2 - Droplet_8USD (Baseline 2)

- **vCPU:** 1  
- **CPU Type:** Premium Intel
- **Memory:** 1 GB  
- **Storage (SSD):** 25 GB  
- **Transfer:** 1 TB  
- **Monthly Cost:** $8
- **Dedicated Volume:** 100 GB ($10)
- **Reports Location:** `/reports/droplet_8USD_reports/`  
- **Total Monthly Cost:** $18

**Report Files:**  

- `reports/droplet_8USD_reports/report_1Gbmem_1vCPU_25Gbssd_1TB_8USD_1.csv`
- `reports/droplet_8USD_reports/report_1Gbmem_1vCPU_25Gbssd_1TB_8USD_2.csv`
- `reports/droplet_8USD_reports/report_1Gbmem_1vCPU_25Gbssd_1TB_8USD_3.csv`
- `reports/droplet_8USD_reports/report_1Gbmem_1vCPU_25Gbssd_1TB_8USD_4.csv`

---

### Tier 3 - Droplet_12USD (Baseline 3)

- **vCPU:** 1  
- **CPU Type:** Regular
- **Memory:** 2 GB
- **Storage (SSD):** 25 GB
- **Transfer:** 2 TB
- **Monthly Cost:** $12
- **Dedicated Volume:** 100 GB ($10)
- **Reports Location:** `/reports/droplet_12USD_reports/`  
- **Total Monthly Cost:** $22

**Report Files:**  

- `reports/droplet_12USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_12USD_1.csv`
- `reports/droplet_12USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_12USD_2.csv`
- `reports/droplet_12USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_12USD_3.csv`
- `reports/droplet_12USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_12USD_4.csv`
- `reports/droplet_12USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_12USD_5.csv`

---

### Tier 4 - Droplet_16USD (Baseline 4)

- **vCPU:** 1  
- **CPU Type:** Premium Intel
- **Memory:** 2 GB
- **Storage (SSD):** 25 GB
- **Transfer:** 2 TB
- **Monthly Cost:** $16
- **Dedicated Volume:** 100 GB ($10)
- **Reports Location:** `/reports/droplet_16USD_reports/`  
- **Total Monthly Cost:** $26

**Report Files:**  

- `reports/droplet_16USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_16USD_1.csv`
- `reports/droplet_16USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_16USD_2.csv`
- `reports/droplet_16USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_16USD_3.csv`
- `reports/droplet_16USD_reports/report_2Gbmem_1vCPU_25Gbssd_2TB_16USD_4.csv`

---

### Tier 5 - Droplet_18USD (Medium 1)

- **vCPU:** 2
- **CPU Type:** Regular
- **Memory:** 2 GB
- **Storage (SSD):** 25 GB
- **Transfer:** 3 TB
- **Monthly Cost:** $18
- **Dedicated Volume:** 100 GB ($10)
- **Reports Location:** `/reports/droplet_18USD_reports/`  
- **Total Monthly Cost:** $28

**Report Files:**  

- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_1.csv`
- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_2.csv`
- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_3.csv`
- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_4.csv`
- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_5.csv`
- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_10k.csv`
- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_15k.csv`
- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_20k.csv`
- `reports/droplet_18USD_reports/report_2Gbmem_2vCPU_25Gbssd_3TB_18USD_25k.csv`

---

### Tier 6 - Droplet_24USD (Medium 2)

- **vCPU:** 2
- **CPU Type:** Regular
- **Memory:** 4 GB
- **Storage (SSD):** 25 GB
- **Transfer:** 4 TB
- **Monthly Cost:** $24
- **Dedicated Volume:** 100 GB ($10)
- **Reports Location:** `/reports/droplet_24USD_reports/`  
- **Total Monthly Cost:** $34

---

### Tier 7 - Droplet_48USD (High)

- **vCPU:** 4
- **CPU Type:** Regular
- **Memory:** 8 GB
- **Storage (SSD):** 25 GB
- **Transfer:** 5 TB
- **Monthly Cost:** $48
- **Dedicated Volume:** 100 GB ($10)
- **Reports Location:** `/reports/droplet_48USD_reports/`  
- **Total Monthly Cost:** $58

**Report Files:**  

- `reports/droplet_48USD_reports/report_8Gbmem_4vCPU_25Gbssd_5TB_48USD_1.csv`
- `reports/droplet_48USD_reports/report_8Gbmem_4vCPU_25Gbssd_5TB_48USD_2.csv`
- `reports/droplet_48USD_reports/report_8Gbmem_4vCPU_25Gbssd_5TB_48USD_3.csv`

## Data Organization

All reports are stored in **CSV format** inside the dedicated volume:

