"""
Fitness Evaluator - Evaluates generated test suites using adversarial testing.
"""
import os
from typing import Dict, Any
from src.environment.testing_env import TestingEnvironment
from src.utils.fault_injector import inject_simple_fault


class FitnessEvaluator:
    """Evaluates test fitness based on GSD specification metrics."""

    def __init__(self, project_root_dir: str):
        self.project_root_dir = project_root_dir

    def evaluate_tests(
        self,
        original_function_code: str,
        generated_test_code: str,
        test_spec: Dict[str, Any],
        num_fault_injections: int = 3
    ) -> Dict[str, Any]:
        """Evaluate generated tests against original and fault-injected functions."""
        results = {
            "test_pass_rate_correct_function": 0.0,
            "code_coverage_percentage": 0.0,
            "bug_detection_rate": 0.0,
            "false_positives_detected": False,
            "test_suite_run_output": "",
            "test_suite_error_output": "",
            "coverage_report_raw": "",
            "total_score": 0.0
        }

        min_coverage_spec = test_spec.get("test_specifications", {}).get("min_coverage_percentage", 0)
        framework = test_spec.get("test_specifications", {}).get("framework", "pytest")

        # 1. Evaluate against CORRECT function
        print("\n--- Evaluating tests against the CORRECT function ---")
        env_correct = TestingEnvironment(base_dir=os.path.join(self.project_root_dir, "output", "test_runs"))
        try:
            env_correct.setup_environment(original_function_code, generated_test_code)
            return_code, stdout, stderr = env_correct.run_tests(framework=framework)
            results["test_suite_run_output"] += f"--- Tests vs. Correct Function ---\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}\n"

            if return_code == 0:
                results["test_pass_rate_correct_function"] = 100.0
            else:
                results["false_positives_detected"] = True
                results["test_pass_rate_correct_function"] = 0.0

            coverage_percentage, coverage_report = env_correct.get_coverage()
            results["code_coverage_percentage"] = coverage_percentage
            results["coverage_report_raw"] = coverage_report

        except Exception as e:
            print(f"Error during evaluation against correct function: {e}")
            results["test_suite_error_output"] += f"Error: {e}\n"
        finally:
            env_correct.cleanup()

        # 2. Evaluate Bug Detection Rate (Adversarial)
        print("\n--- Evaluating Bug Detection Rate ---")
        detected_bugs = 0
        total_faults_attempted = 0

        for i in range(num_fault_injections):
            print(f"  Fault injection {i+1}/{num_fault_injections}...")
            mutated_function_code = inject_simple_fault(original_function_code, num_faults=1)

            if mutated_function_code.strip() == original_function_code.strip():
                print(f"    No change from fault injection {i+1}, skipping.")
                continue

            total_faults_attempted += 1
            env_mutated = TestingEnvironment(base_dir=os.path.join(self.project_root_dir, "output", "test_runs"))
            try:
                env_mutated.setup_environment(mutated_function_code, generated_test_code, source_filename=f"mutated_function_{i}.py")
                return_code, stdout, stderr = env_mutated.run_tests(framework=framework)
                results["test_suite_run_output"] += f"--- Tests vs. Mutated {i+1} ---\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}\n"

                if return_code != 0:
                    detected_bugs += 1
                    print(f"    Bug detected for mutation {i+1}.")
                else:
                    print(f"    Bug NOT detected for mutation {i+1}.")

            except Exception as e:
                print(f"Error evaluating mutation {i+1}: {e}")
                results["test_suite_error_output"] += f"Error mutation {i+1}: {e}\n"
            finally:
                env_mutated.cleanup()

        if total_faults_attempted > 0:
            results["bug_detection_rate"] = (detected_bugs / total_faults_attempted) * 100
        else:
            results["bug_detection_rate"] = 0.0

        # 3. Calculate Total Score
        score = 0.0

        if results["false_positives_detected"]:
            score -= 100.0

        score += results["test_pass_rate_correct_function"] * 0.5

        if results["test_pass_rate_correct_function"] == 100.0:
            score += results["code_coverage_percentage"] * 0.3
            if results["code_coverage_percentage"] < min_coverage_spec:
                score -= (min_coverage_spec - results["code_coverage_percentage"]) * 0.5
        else:
            score -= results["code_coverage_percentage"] * 0.1

        if results["test_pass_rate_correct_function"] == 100.0 and not results["false_positives_detected"]:
            score += results["bug_detection_rate"] * 0.2

        results["total_score"] = max(0.0, score)

        print(f"\n--- Evaluation Summary ---")
        print(f"Test Pass Rate: {results['test_pass_rate_correct_function']}%")
        print(f"False Positives: {results['false_positives_detected']}")
        print(f"Coverage: {results['code_coverage_percentage']}% (Target: {min_coverage_spec}%)")
        print(f"Bug Detection: {results['bug_detection_rate']}%")
        print(f"Total Score: {results['total_score']}")

        return results
