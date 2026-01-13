"""
Testing Environment - Manages isolated Python testing environments for evaluating generated tests.
"""
import json
import os
import shutil
import subprocess
import uuid
from typing import Tuple


class TestingEnvironment:
    """
    Manages an isolated Python testing environment for evaluating generated unit tests.
    """
    def __init__(self, base_dir="output/test_runs"):
        self.base_dir = base_dir
        self.run_dir = os.path.join(self.base_dir, str(uuid.uuid4()))
        os.makedirs(self.run_dir, exist_ok=True)
        print(f"Created testing environment at: {self.run_dir}")

    def _write_file(self, filename: str, content: str):
        file_path = os.path.join(self.run_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

    def setup_environment(self, source_code: str, test_code: str, source_filename="target_function.py", test_filename="test_target_function.py"):
        """
        Sets up the testing environment by writing the source and test code to files.
        """
        self.source_file_path = self._write_file(source_filename, source_code)
        self.test_file_path = self._write_file(test_filename, test_code)
        # Ensure __init__.py exists for Python to treat it as a package if needed
        self._write_file(os.path.join(os.path.dirname(source_filename), "__init__.py"), "")
        self._write_file(os.path.join(os.path.dirname(test_filename), "__init__.py"), "")

        print(f"Source code written to: {self.source_file_path}")
        print(f"Test code written to: {self.test_file_path}")

    def run_tests(self, framework="pytest") -> Tuple[int, str, str]:
        """
        Runs the unit tests and returns exit code, stdout, stderr.
        """
        if framework.lower() == "pytest":
            command = ["pytest", self.test_file_path, "-q", "--tb=short"]
        elif framework.lower() == "unittest":
            command = ["python", "-m", "unittest", self.test_file_path]
        else:
            raise ValueError(f"Unsupported test framework: {framework}")

        print(f"Running tests with command: {' '.join(command)} in {self.run_dir}")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.run_dir,
                timeout=60 # Extended timeout for tests
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Error: Test execution timed out."
        except FileNotFoundError:
            return 1, "", "Error: pytest/python executable not found."
        except Exception as e:
            return 1, "", f"Error running tests: {e}"

    def get_coverage(self, source_filename="target_function.py") -> Tuple[float, str]:
        """
        Calculates code coverage for the source file using the generated tests.
        Returns coverage percentage and the raw coverage report output.
        """
        # Ensure source_file_path is relative to run_dir for coverage.py
        relative_source_path = os.path.relpath(self.source_file_path, self.run_dir)
        
        # Clear previous coverage data
        subprocess.run(["coverage", "erase"], cwd=self.run_dir, capture_output=True)

        # Run tests with coverage measurement
        coverage_run_cmd = [
            "coverage", "run", "--source", relative_source_path,
            "-m", "pytest", self.test_file_path, "-q", "--tb=no"
        ]
        print(f"Running coverage with command: {' '.join(coverage_run_cmd)} in {self.run_dir}")
        run_result = subprocess.run(
            coverage_run_cmd,
            capture_output=True,
            text=True,
            cwd=self.run_dir,
            timeout=120 # Longer timeout for coverage + tests
        )

        if run_result.returncode != 0 and "Coverage.py warning" not in run_result.stderr:
            print(f"Coverage run failed (exit code {run_result.returncode}):\n{run_result.stdout}\n{run_result.stderr}")
            return 0.0, f"Coverage run failed: {run_result.stderr}"

        # Generate JSON report
        report_cmd = ["coverage", "json", "-o", "coverage.json"]
        report_result = subprocess.run(
            report_cmd,
            capture_output=True,
            text=True,
            cwd=self.run_dir,
            timeout=30
        )

        if report_result.returncode != 0:
            print(f"Coverage report generation failed (exit code {report_result.returncode}):\n{report_result.stdout}\n{report_result.stderr}")
            return 0.0, f"Coverage report failed: {report_result.stderr}"
        
        coverage_json_path = os.path.join(self.run_dir, "coverage.json")
        if not os.path.exists(coverage_json_path):
            return 0.0, "Coverage JSON report not generated."

        try:
            with open(coverage_json_path, 'r', encoding='utf-8') as f:
                coverage_data = json.load(f)
            
            total_covered = coverage_data.get('totals', {}).get('covered_lines', 0)
            total_missed = coverage_data.get('totals', {}).get('missing_lines', 0)
            total_lines = total_covered + total_missed
            
            if total_lines > 0:
                percentage = (total_covered / total_lines) * 100
                return round(percentage, 2), json.dumps(coverage_data, indent=2)
            else:
                return 0.0, "No executable lines found for coverage."
        except json.JSONDecodeError:
            return 0.0, "Failed to parse coverage JSON report."
        except Exception as e:
            return 0.0, f"Error processing coverage report: {e}"


    def cleanup(self):
        """
        Removes the temporary testing directory.
        """
        if os.path.exists(self.run_dir):
            shutil.rmtree(self.run_dir)
            print(f"Cleaned up testing environment at: {self.run_dir}")
