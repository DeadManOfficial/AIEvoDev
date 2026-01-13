"""
LangChain Tools - Custom tools for the test generator agent.
"""
import json
import os
import subprocess
from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class ReadPythonFileSchema(BaseModel):
    file_path: str = Field(description="The path to the Python file to read.")


class WritePythonFileSchema(BaseModel):
    file_path: str = Field(description="The path to the Python file to write to.")
    content: str = Field(description="The content to write to the file.")


class ExecutePythonCodeSchema(BaseModel):
    code: str = Field(description="The Python code to execute.")
    working_dir: str = Field(description="The directory in which to execute the code.", default=".")


class RunTestsSchema(BaseModel):
    test_file_path: str = Field(description="The path to the Python test file or directory.")
    framework: str = Field(description="The test framework ('pytest' or 'unittest').", default="pytest")


class GetCodeCoverageSchema(BaseModel):
    source_file_path: str = Field(description="The path to the Python source file.")
    test_file_path: str = Field(description="The path to the Python test file.")


class ReadPythonFileTool(BaseTool):
    name: str = "read_python_file"
    description: str = "Reads the content of a Python file from the filesystem."
    args_schema: Type[BaseModel] = ReadPythonFileSchema

    def _run(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found at {file_path}"
        except Exception as e:
            return f"Error reading file {file_path}: {e}"


class WritePythonFileTool(BaseTool):
    name: str = "write_python_file"
    description: str = "Writes content to a Python file. Overwrites if exists."
    args_schema: Type[BaseModel] = WritePythonFileSchema

    def _run(self, file_path: str, content: str) -> str:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing to file {file_path}: {e}"


class ExecutePythonCodeTool(BaseTool):
    name: str = "execute_python_code"
    description: str = "Executes Python code and returns stdout/stderr."
    args_schema: Type[BaseModel] = ExecutePythonCodeSchema

    def _run(self, code: str, working_dir: str = ".") -> str:
        try:
            temp_script_path = os.path.join(working_dir, "__temp_exec_script__.py")
            with open(temp_script_path, "w", encoding='utf-8') as f:
                f.write(code)

            result = subprocess.run(
                ["python", temp_script_path],
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=10
            )
            os.remove(temp_script_path)

            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            return output
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out."
        except Exception as e:
            return f"Error executing code: {e}"


class RunTestsTool(BaseTool):
    name: str = "run_tests"
    description: str = "Runs Python unit tests using pytest or unittest."
    args_schema: Type[BaseModel] = RunTestsSchema

    def _run(self, test_file_path: str, framework: str = "pytest") -> str:
        try:
            if framework.lower() == "pytest":
                command = ["pytest", test_file_path, "-q", "--tb=short"]
            elif framework.lower() == "unittest":
                command = ["python", "-m", "unittest", test_file_path]
            else:
                return f"Error: Unsupported framework '{framework}'."

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(test_file_path) if os.path.isfile(test_file_path) else test_file_path,
                timeout=30
            )
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            return output
        except subprocess.TimeoutExpired:
            return "Error: Test execution timed out."
        except Exception as e:
            return f"Error running tests: {e}"


class GetCodeCoverageTool(BaseTool):
    name: str = "get_code_coverage"
    description: str = "Calculates code coverage for a Python source file."
    args_schema: Type[BaseModel] = GetCodeCoverageSchema

    def _run(self, source_file_path: str, test_file_path: str) -> str:
        try:
            if not os.path.exists(source_file_path):
                return f"Error: Source file not found at {source_file_path}"
            if not os.path.exists(test_file_path):
                return f"Error: Test file not found at {test_file_path}"

            result = subprocess.run(
                ["python", "-m", "coverage", "run", "--source", source_file_path,
                 "-m", "pytest", test_file_path, "-q", "--tb=no"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(source_file_path),
                timeout=30
            )

            if result.returncode != 0:
                return f"Coverage run failed: {result.stderr}"

            report_result = subprocess.run(
                ["python", "-m", "coverage", "report", "--format=json"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(source_file_path)
            )

            if report_result.returncode != 0:
                return f"Coverage report failed: {report_result.stderr}"

            coverage_data = json.loads(report_result.stdout)
            total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
            return f"Code Coverage: {total_coverage:.1f}%"

        except json.JSONDecodeError:
            return "Error decoding coverage JSON report."
        except subprocess.TimeoutExpired:
            return "Error: Coverage calculation timed out."
        except Exception as e:
            return f"Error calculating coverage: {e}"


class ValidateYAMLSpecTool(BaseTool):
    name: str = "validate_yaml_spec"
    description: str = "Validates a YAML specification file."
    args_schema: Type[BaseModel] = BaseModel

    def _run(self, yaml_file_path: str, schema_file_path: str = None) -> str:
        return f"YAML spec validation for {yaml_file_path} (placeholder: valid)."
