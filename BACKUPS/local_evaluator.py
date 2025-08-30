"""
Local Evaluation Script for the AI Agent.
"""
import sys
import time
from pathlib import Path
from collections import defaultdict

# --- Path Hack ---
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# --- Project Imports ---
from projects.mexican_groceries.agent import graph
from projects.mexican_groceries.evaluation.test_cases import TEST_CASES
from core_lib.metrics_engine import MetricEngine
from core_lib.data_sinks import JSONDataSink

class EvaluationEngine:
    """A generic engine for running and evaluating agent test cases."""

    def __init__(self, agent_graph, test_cases: list[dict], metrics_config_path: Path):
        self.agent_graph = agent_graph
        self.test_cases = test_cases
        self.metric_engine = MetricEngine(config_path=metrics_config_path)
        log_file_path = project_root / "projects" / "mexican_groceries" / "logs" / "local_run_log.jsonl"
        self.data_sink = JSONDataSink(log_path=log_file_path)

    def run(self):
        """Runs the full evaluation suite."""
        print(f"--- Local Evaluation Engine: Starting Suite ---")
        all_results = []

        for i, case in enumerate(self.test_cases):
            print(f"\n----- Running Test Case {i+1}/{len(self.test_cases)}: {case['case_id']} -----")
            
            start_time = time.time()
            
            initial_state = {
                "request": case['query'],
                "intent": None,
                "ingredients_list": [],
                "store_search_results": [],
                "shopping_list": None,
                "missing_items": [],
                "clarification_question": None,
                "evaluation_grade": None,
            }

            final_state = self.agent_graph.invoke(initial_state)
            latency_ms = (time.time() - start_time) * 1000

            calculated_metrics = self.metric_engine.calculate_all(final_state)
            calculated_metrics["total_latency_ms"] = f"{latency_ms:.2f}"
            print("  > Metrics calculated via YAML config.")
            
            log_entry = {
                "test_case": case,
                "final_state": final_state,
                "metrics": calculated_metrics,
            }
            all_results.append(log_entry)
            self.data_sink.write(log_entry)

        self.print_summary(all_results)
    
    def print_summary(self, all_results: list[dict]):
        print("\n\n========== Local Evaluation Summary ==========")
        metric_totals = defaultdict(list)
        path_counts = defaultdict(int)

        for result in all_results:
            metrics = result.get("metrics", {})
            for name, value in metrics.items():
                try: 
                    metric_totals[name].append(float(value))
                except (ValueError, TypeError):
                    if name == "agent_path":
                        path_counts[value] += 1
        
        print("\n--- Objective Metrics (Averages) ---")
        for name, values in sorted(metric_totals.items()):
            avg = sum(values) / len(values) if values else 0
            print(f"- {name:<30}: {avg:.2f}")

        print("\n--- Agent Path Distribution ---")
        for path, count in path_counts.items():
            percent = (count / len(all_results)) * 100 if all_results else 0
            print(f"- {path:<30}: {count} runs ({percent:.1f}%)")

        print("\n==========================================")
        print("Evaluation complete. Check log file for detailed results.")

if __name__ == "__main__":
    metrics_config = project_root / "projects/mexican_groceries/evaluation/metrics_definition.yaml"
    
    engine = EvaluationEngine(
        agent_graph=graph,
        test_cases=TEST_CASES,
        metrics_config_path=metrics_config
    )
    engine.run()