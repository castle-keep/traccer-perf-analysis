#!/usr/bin/env python3
"""
Performance Metrics Summary Generator
Analyzes CSV data from all droplet tiers and generates summary tables and metrics
"""

import pandas as pd
import os
import glob
from typing import Dict, List, Tuple

def analyze_droplet_tier(tier_dir: str) -> Dict:
    """Analyze performance data for a specific droplet tier"""
    csv_files = glob.glob(f'{tier_dir}*.csv')
    if not csv_files:
        return None
    
    # Read and combine all CSV files for this tier
    all_dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            all_dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not read {csv_file}: {e}")
            continue
    
    if not all_dfs:
        return None
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Extract tier information from directory name
    tier_name = tier_dir.split('/')[-2].replace('droplet_', '').replace('_reports', '')
    
    # Calculate key metrics
    metrics = {
        'tier': tier_name,
        'total_tests': len(combined_df),
        'min_devices': combined_df['devices'].min(),
        'max_devices': combined_df['devices'].max(),
        'max_fail_ratio': combined_df['fail_ratio'].max(),
        'max_cpu_percent': combined_df['cpu_percent'].max(),
        'max_load_1m': combined_df['load_1m'].max(),
        'max_p99_latency': combined_df['p99_ms'].max(),
    }
    
    # Find capacity thresholds (where fail_ratio > 0.05 or 5%)
    stable_data = combined_df[combined_df['fail_ratio'] <= 0.05]
    if len(stable_data) > 0:
        metrics['stable_capacity'] = stable_data['devices'].max()
    else:
        metrics['stable_capacity'] = combined_df['devices'].min()
    
    # Find performance degradation point (where fail_ratio > 0.10 or 10%)
    degraded_data = combined_df[combined_df['fail_ratio'] <= 0.10]
    if len(degraded_data) > 0:
        metrics['degradation_threshold'] = degraded_data['devices'].max()
    else:
        metrics['degradation_threshold'] = metrics['stable_capacity']
    
    # Average performance at stable capacity
    stable_perf = combined_df[
        (combined_df['devices'] <= metrics['stable_capacity']) & 
        (combined_df['fail_ratio'] <= 0.05)
    ]
    
    if len(stable_perf) > 0:
        metrics['avg_stable_cpu'] = stable_perf['cpu_percent'].mean()
        metrics['avg_stable_p50'] = stable_perf['p50_ms'].mean()
        metrics['avg_stable_p99'] = stable_perf['p99_ms'].mean()
        metrics['avg_stable_rps'] = stable_perf['rps_ok_avg'].mean()
    else:
        metrics['avg_stable_cpu'] = 0
        metrics['avg_stable_p50'] = 0
        metrics['avg_stable_p99'] = 0
        metrics['avg_stable_rps'] = 0
    
    return metrics

def generate_summary_tables():
    """Generate summary tables for all droplet tiers"""
    
    # Droplet tier specifications
    tier_specs = {
        '6USD': {'vcpu': 1, 'ram_gb': 1, 'cost': 6, 'cpu_type': 'Regular'},
        '8USD': {'vcpu': 1, 'ram_gb': 1, 'cost': 8, 'cpu_type': 'Premium Intel'},
        '12USD': {'vcpu': 1, 'ram_gb': 2, 'cost': 12, 'cpu_type': 'Regular'},
        '16USD': {'vcpu': 1, 'ram_gb': 2, 'cost': 16, 'cpu_type': 'Premium Intel'},
        '18USD': {'vcpu': 2, 'ram_gb': 2, 'cost': 18, 'cpu_type': 'Regular'},
        '24USD': {'vcpu': 2, 'ram_gb': 4, 'cost': 24, 'cpu_type': 'Regular'},
        '48USD': {'vcpu': 4, 'ram_gb': 8, 'cost': 48, 'cpu_type': 'Regular'},
    }
    
    report_dirs = glob.glob('reports/droplet_*_reports/')
    results = []
    
    for dir_path in sorted(report_dirs):
        metrics = analyze_droplet_tier(dir_path)
        if metrics:
            tier = metrics['tier']
            if tier in tier_specs:
                metrics.update(tier_specs[tier])
            results.append(metrics)
    
    if not results:
        print("No data found to analyze")
        return
    
    # Create DataFrame for easier manipulation
    df = pd.DataFrame(results)
    
    # Generate Performance Summary Table
    print("# Performance Analysis Summary Tables")
    print()
    print("## Droplet Configuration and Capacity Summary")
    print()
    print("| Tier | Cost/Mo | vCPU | RAM (GB) | CPU Type | Stable Capacity | Degradation Threshold | Cost per 1k Devices |")
    print("|------|---------|------|----------|----------|-----------------|----------------------|---------------------|")
    
    for _, row in df.iterrows():
        cost_per_1k = (row['cost'] / (row['stable_capacity'] / 1000)) if row['stable_capacity'] > 0 else 0
        print(f"| ${row['tier']} | ${row['cost']} | {row['vcpu']} | {row['ram_gb']} | {row['cpu_type']} | "
              f"{row['stable_capacity']:,} | {row['degradation_threshold']:,} | ${cost_per_1k:.2f} |")
    
    print()
    print("## Performance Metrics at Stable Load")
    print()
    print("| Tier | Avg CPU (%) | Avg P50 Latency (ms) | Avg P99 Latency (ms) | Avg RPS | Max Load Tested |")
    print("|------|-------------|---------------------|---------------------|---------|-----------------|")
    
    for _, row in df.iterrows():
        print(f"| ${row['tier']} | {row['avg_stable_cpu']:.1f}% | {row['avg_stable_p50']:.1f} | "
              f"{row['avg_stable_p99']:.1f} | {row['avg_stable_rps']:.0f} | {row['max_devices']:,} |")
    
    print()
    print("## System Limits and Failure Characteristics")
    print()
    print("| Tier | Max Fail Ratio | Max CPU (%) | Max Load Average | Max P99 Latency (ms) |")
    print("|------|----------------|-------------|------------------|---------------------|")
    
    for _, row in df.iterrows():
        print(f"| ${row['tier']} | {row['max_fail_ratio']:.3f} | {row['max_cpu_percent']:.1f}% | "
              f"{row['max_load_1m']:.2f} | {row['max_p99_latency']:.0f} |")
    
    print()
    print("## Key Observations")
    print()
    
    # Find best cost-performance ratio
    df['cost_efficiency'] = df['stable_capacity'] / df['cost']
    best_efficiency = df.loc[df['cost_efficiency'].idxmax()]
    
    print(f"- **Most Cost-Effective Tier**: ${best_efficiency['tier']} provides {best_efficiency['cost_efficiency']:.0f} devices per dollar")
    
    # Memory vs Performance analysis
    df_1gb = df[df['ram_gb'] == 1]
    df_2gb = df[df['ram_gb'] >= 2]
    
    if len(df_1gb) > 0 and len(df_2gb) > 0:
        avg_1gb_capacity = df_1gb['stable_capacity'].mean()
        avg_2gb_capacity = df_2gb[df_2gb['ram_gb'] == 2]['stable_capacity'].mean()
        print(f"- **Memory Impact**: 2GB RAM provides {avg_2gb_capacity/avg_1gb_capacity:.1f}x capacity improvement over 1GB")
    
    # CPU scaling analysis
    single_cpu = df[df['vcpu'] == 1]['stable_capacity'].mean()
    dual_cpu = df[df['vcpu'] == 2]['stable_capacity'].mean()
    quad_cpu = df[df['vcpu'] == 4]['stable_capacity'].mean()
    
    if not pd.isna(single_cpu) and not pd.isna(dual_cpu):
        print(f"- **CPU Scaling**: Dual CPU provides {dual_cpu/single_cpu:.1f}x capacity improvement")
    
    if not pd.isna(dual_cpu) and not pd.isna(quad_cpu):
        print(f"- **High-End Scaling**: Quad CPU provides {quad_cpu/dual_cpu:.1f}x capacity over dual CPU")
    
    print()
    print("---")
    print()
    print("*Data compiled from comprehensive load testing across all droplet tiers with empirical performance measurements.*")

if __name__ == "__main__":
    generate_summary_tables()