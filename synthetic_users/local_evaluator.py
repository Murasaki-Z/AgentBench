"""
Batch Analytics Engine for Agent Performance.

This script reads production log files (`.jsonl` format), calculates a suite of
objective metrics for each interaction, and generates an aggregated summary report.

It is designed to be run on a schedule (e.g., hourly, daily) to provide
ongoing business intelligence about the agent's performance in the wild.
"""

# --- Standard Library Imports ---
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# --- Path Hack ---
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# --- Project Imports ---
from core_lib.metrics_engine import MetricEngine

# ==============================================================================
# --- CORE ANALYTICS ENGINE ---
# ==============================================================================

class AnalyticsEngine:
    """
    Reads agent interaction logs, calculates metrics, and generates reports.
    """

    def __init__(self, metrics_config_path: Path):
        """
        Initializes the engine with a path to the metric definitions.
        """
        self.metric_engine = MetricEngine(config_path=metrics_config_path)

    def analyze_log_file(self, log_file_path: Path, lookback_hours: float):
        """
        The main method to run the analysis on a given log file.
        """
        print(f"--- Batch Analyzer: Starting analysis ---")
        print(f" > Log file: {log_file_path.name}")
        print(f" > Analyzing logs from the last {lookback_hours} hours.")

        if not log_file_path.exists():
            print(f"--- WARNING: Log file not found at {log_file_path}. Exiting. ---")
            return

        # 1. Read and filter the log entries based on the lookback window
        recent_logs = self._get_recent_logs(log_file_path, lookback_hours)

        if not recent_logs:
            print("--- No new log entries to analyze in the specified time window. ---")
            return
        
        print(f" > Found {len(recent_logs)} new interactions to analyze.")
        
        # 2. Calculate metrics for each individual log entry
        all_results = []
        for log_entry in recent_logs:
            calculated_metrics = self.metric_engine.calculate_all(log_entry)
            
            # Add some metadata from the log itself
            calculated_metrics["timestamp_utc"] = log_entry.get("timestamp_utc")
            
            all_results.append({"metrics": calculated_metrics})

        # 3. Generate and print the final summary report
        self.print_summary(all_results, lookback_hours)

    def _get_recent_logs(self, log_file_path: Path, lookback_hours: float) -> list[dict]:
        """
        Reads a .jsonl file and returns a list of log entries within the
        lookback window.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        recent_logs = []
        with open(log_file_path, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    timestamp_str = log_entry.get("timestamp_utc")
                    if timestamp_str:
                        log_time = datetime.fromisoformat(timestamp_str)
                        if log_time > cutoff_time:
                            recent_logs.append(log_entry)
                except (json.JSONDecodeError, TypeError):
                    # Ignore malformed lines in the log file
                    continue
        return recent_logs

    def print_summary(self, all_results: list[dict], lookback_hours: float):
        """
        Calculates aggregate statistics and prints a summary report based on
        the metric definitions provided to the engine.
        """
        print("\n\n========== Batch Analysis Summary ==========")
        print(f"--- Report for the last {lookback_hours} hours ---")
        print(f"--- Total Interactions Processed: {len(all_results)} ---")

        # --- Step 1: Pre-categorize all defined metrics ---
        numeric_metric_names = set()
        categorical_metric_names = set()

        # The MetricEngine holds the definitions from the YAML file
        for metric_def in self.metric_engine.metric_definitions:
            m_name = metric_def["name"]
            # We'll assume types that produce numbers are numeric, the rest are categorical.
            # This is a simple but effective heuristic.
            if metric_def["type"] in ["ratio", "count_list", "count_unique_in_list"]:
                numeric_metric_names.add(m_name)
            else: # e.g., 'derive_path'
                categorical_metric_names.add(m_name)
        
        # Manually add our hardcoded latency metric
        numeric_metric_names.add("total_latency_ms")

        # --- Step 2: Aggregate results based on the pre-categorized lists ---
        numeric_results = defaultdict(list)
        categorical_results = defaultdict(lambda: defaultdict(int))

        for result in all_results:
            metrics = result.get("metrics", {})
            for name, value in metrics.items():
                if name in numeric_metric_names:
                    try:
                        numeric_results[name].append(float(value))
                    except (ValueError, TypeError):
                        continue # Ignore if value is not a valid number
                elif name in categorical_metric_names:
                    categorical_results[name][value] += 1
                # Any other fields in the log (like timestamp_utc) are now ignored.

        # --- Step 3: Print the cleaned and separated reports ---
        print("\n--- Objective Metrics (Averages) ---")
        if not numeric_results:
            print("No numeric metrics to display.")
        else:
            for name, values in sorted(numeric_results.items()):
                avg = sum(values) / len(values) if values else 0
                min_val = min(values) if values else 0
                max_val = max(values) if values else 0
                print(f"- {name:<30}: Avg={avg:<10.2f} | Min={min_val:<10.2f} | Max={max_val:<10.2f}")

        print("\n--- Categorical Metrics (Distribution) ---")
        if not categorical_results:
            print("No categorical data to display.")
        else:
            for name, value_counts in sorted(categorical_results.items()):
                print(f"- Metric: '{name}'")
                total_for_metric = sum(value_counts.values())
                for value, count in value_counts.items():
                    percent = (count / total_for_metric) * 100 if total_for_metric else 0
                    print(f"  - {str(value):<28}: {count} occurrences ({percent:.1f}%)")

        print("\n==========================================")


# ==============================================================================
# --- SCRIPT ENTRY POINT ---
# ==============================================================================

if __name__ == "__main__":
    # 1. Set up the command-line argument parser
    parser = argparse.ArgumentParser(
        description="Run batch analysis on agent production logs."
    )
    
    # Default log file path is the production log from our bot
    default_log_file = project_root / "projects/mexican_groceries/logs/production_log.jsonl"
    
    parser.add_argument(
        "--log-file",
        type=Path,
        default=default_log_file,
        help="Path to the .jsonl log file to analyze."
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=24,
        help="Lookback window in hours for log analysis."
    )
    
    args = parser.parse_args()

    # 2. Define the path to our metrics configuration file
    metrics_config = project_root / "projects/mexican_groceries/evaluation/metrics_definition.yaml"
    
    # 3. Initialize and run the engine
    engine = AnalyticsEngine(metrics_config_path=metrics_config)
    engine.analyze_log_file(log_file_path=args.log_file, lookback_hours=args.hours)