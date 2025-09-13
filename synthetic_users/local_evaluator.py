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
from core_lib.assertion_engine import AssertionEngine 
from core_lib.data_sinks import JSONDataSink


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
        self.assertion_engine = AssertionEngine(config_path=metrics_config_path)


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
            assertion_failures = self.assertion_engine.run_all(log_entry)
            
            # Add some metadata from the log itself
            # calculated_metrics["timestamp_utc"] = log_entry.get("timestamp_utc")

            
            all_results.append({
                "metrics": calculated_metrics,
                "assertion_failures": assertion_failures,
            })

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
        Calculates aggregate statistics and prints a summary report.
        This version automatically infers the type of each metric.
        """
        print("\n\n========== Batch Analysis Summary ==========")
        print(f"--- Report for the last {lookback_hours} hours ---")
        print(f"--- Total Interactions Processed: {len(all_results)} ---")

        # --- Step 1: Aggregate all results by metric name ---
        # We no longer need to pre-categorize. We'll figure out the type from the data.
        aggregated_results = defaultdict(list)

        total_assertion_failures = 0
        failed_assertion_counts = defaultdict(int)
        for result in all_results:
            failures = result.get("assertion_failures", [])
            if failures:
                total_assertion_failures += 1
                # We can also track which specific assertions failed most often
                for failure_reason in failures:
                    assertion_name = failure_reason.split("'")[1] # Extracts the name
                    failed_assertion_counts[assertion_name] += 1
        
        # --- NEW: Add the Assertion Summary section to the report ---
        pass_count = len(all_results) - total_assertion_failures
        pass_rate = (pass_count / len(all_results)) * 100 if all_results else 100
        print(f"\n--- Assertion Summary ---")
        print(f"- Pass Rate: {pass_rate:.1f}% ({pass_count}/{len(all_results)} passed checks)")
        if failed_assertion_counts:
            print("- Top Failing Assertions:")
            for name, count in sorted(failed_assertion_counts.items(), key=lambda item: item[1], reverse=True):
                print(f"  - '{name}': {count} failures")

        # --- Step 2: Dynamically create report sections ---
        numeric_reports = {}
        categorical_reports = defaultdict(lambda: defaultdict(int))
        list_reports = defaultdict(list)

        for name, values in aggregated_results.items():
            # Heuristic: If all values are lists, treat it as a list metric.
            if all(isinstance(v, list) for v in values):
                # Flatten the list of lists into one big list for analysis
                list_reports[name] = [item for sublist in values for item in sublist]
            # Heuristic: If any value is a number, treat it as a numeric metric.
            elif any(isinstance(v, (int, float)) for v in values):
                numeric_reports[name] = [v for v in values if isinstance(v, (int, float))]
            # Fallback: Treat as categorical.
            else:
                for value in values:
                    categorical_reports[name][value] += 1
        
        # --- Step 3: Print the reports ---
        print("\n--- Objective Metrics (Aggregated Numeric) ---")
        if not numeric_reports: print("No numeric metrics to display.")
        else:
            for name, values in sorted(numeric_reports.items()):
                avg = sum(values) / len(values) if values else 0
                min_val = min(values) if values else 0
                max_val = max(values) if values else 0
                print(f"- {name:<30}: Avg={avg:<10.2f} | Min={min_val:<10.2f} | Max={max_val:<10.2f}")

        print("\n--- Categorical Metrics (Distribution) ---")
        if not categorical_reports: print("No categorical data to display.")
        else:
            for name, value_counts in sorted(categorical_reports.items()):
                print(f"- Metric: '{name}'")
                total = sum(value_counts.values())
                # Show top 5 most common values for brevity
                for value, count in sorted(value_counts.items(), key=lambda item: item[1], reverse=True)[:5]:
                    percent = (count / total) * 100 if total else 0
                    print(f"  - {str(value):<28}: {count} occurrences ({percent:.1f}%)")
                if len(value_counts) > 5:
                    print(f"  - ... and {len(value_counts) - 5} more unique values.")

        print("\n--- List-Based Metrics (Value Distribution & Summary) ---")
        if not list_reports: print("No list-based metrics to display.")
        else:
            for name, all_values in sorted(list_reports.items()):
                print(f"- Metric: '{name}'")
                if not all_values:
                    print("  - No values found across all runs.")
                    continue
                
                # --- NEW: Show the distribution of the most common items in the list ---
                value_counts = defaultdict(int)
                for v in all_values: value_counts[v] += 1
                
                print("  - Top 5 Most Common Values:")
                for value, count in sorted(value_counts.items(), key=lambda item: item[1], reverse=True)[:5]:
                    percent = (count / len(all_values)) * 100
                    print(f"    - {str(value):<26}: {count} times ({percent:.1f}%)")
                if len(value_counts) > 5:
                    print(f"    - ... and {len(value_counts) - 5} more unique values.")

                # --- Secondary: Provide summary stats ---
                print("  - Overall Summary:")
                numeric_values = [v for v in all_values if isinstance(v, (int, float))]
                print(f"    - Total Items Collected: {len(all_values)}")
                print(f"    - Unique Items         : {len(value_counts)}")
                if numeric_values:
                    print(f"    - Numeric Avg          : {sum(numeric_values) / len(numeric_values):.2f}")

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
        default=4800,#hours
        help="Lookback window in hours for log analysis."
    )
    
    args = parser.parse_args()

    # 2. Define the path to our metrics configuration file
    metrics_config = project_root / "projects/mexican_groceries/evaluation/metrics_definition.yaml"
    
    # 3. Initialize and run the engine
    engine = AnalyticsEngine(metrics_config_path=metrics_config)
    engine.analyze_log_file(log_file_path=args.log_file, lookback_hours=args.hours)