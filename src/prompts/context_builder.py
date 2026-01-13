"""
Context Builder - Assembles LLM prompts for test generation based on GSD specifications.
"""
import json
import yaml
from typing import Any, Dict, List, Optional


def build_test_generation_context(
    spec: Dict[str, Any],
    target_function_code: str,
    few_shot_examples: List[Dict[str, str]] = None,
    previous_evaluation_results: Optional[Dict[str, Any]] = None # New argument for feedback
) -> str:
    """
    Assembles the complete context string for the LLM prompt based on
    the GSD specification, target function, optional few-shot examples,
    and previous evaluation results.
    """
    context_parts = []

    # 1. System Prompt / Role Definition (can be part of the main agent's prompt too)
    context_parts.append("You are an expert Python unit test developer. Your task is to generate comprehensive, correct, and robust unit tests based on the provided function code and test specifications.")
    context_parts.append("Your goal is to achieve high code coverage and a high bug detection rate, while ensuring no false positives.")
    context_parts.append("\n---")

    # 2. Target Function Information
    context_parts.append("<target_function>")
    # Include function name, signature, and docstring if available
    target_info = spec.get("target_function_info", {})
    if target_info.get("name"):
        context_parts.append(f"Function Name: {target_info['name']}")
    if target_info.get("signature"):
        context_parts.append(f"Function Signature: {target_info['signature']}")
    if target_info.get("docstring"):
        context_parts.append(f"Docstring:\n{target_info['docstring'].strip()}")
    
    context_parts.append("Function Source Code:")
    context_parts.append(target_function_code.strip())
    context_parts.append("</target_function>")
    context_parts.append("\n---")

    # 3. GSD Specifications
    context_parts.append("<specifications>")
    # Include the entire spec, excluding the target_function_info and llm_configuration
    filtered_spec = {k: v for k, v in spec.items() if k not in ["target_function_info", "llm_configuration"]}
    context_parts.append(yaml.dump(filtered_spec, sort_keys=False))
    context_parts.append("</specifications>")
    context_parts.append("\n---")

    # 4. Previous Evaluation Results (Feedback)
    if previous_evaluation_results:
        context_parts.append("<feedback>")
        context_parts.append("Here are the detailed evaluation results from the previous generation of tests:")
        context_parts.append(json.dumps(previous_evaluation_results, indent=2))
        context_parts.append("Analyze these results to identify weaknesses (e.g., missed bugs, low coverage, false positives) and propose modifications to the tests to improve their fitness.")
        context_parts.append("</feedback>")
        context_parts.append("\n---")

    # 5. Few-Shot Examples
    if few_shot_examples:
        context_parts.append("<examples>")
        context_parts.append("Here are some examples of well-written Python unit tests for similar functions. Use these as a reference for style and common testing patterns.")
        for i, example in enumerate(few_shot_examples):
            context_parts.append(f"### Example {i + 1}")
            context_parts.append("Function:")
            context_parts.append(example.get("function", "").strip())
            context_parts.append("Generated Tests:")
            context_parts.append(example.get("tests", "").strip())
            context_parts.append("---")
        context_parts.append("</examples>")
        context_parts.append("\n---")

    # 6. Final Instructions (derived from spec and task)
    framework = spec.get("test_specifications", {}).get("framework", "pytest")
    min_coverage = spec.get("test_specifications", {}).get("min_coverage_percentage", 80)
    problem_statement = spec.get("problem_statement", "Generate unit tests.")

    context_parts.append(f"Based on all the above information, {problem_statement}.")
    context_parts.append(f"Generate unit tests using the '{framework}' framework.")
    context_parts.append(f"Aim for at least {min_coverage}% code coverage.")
    context_parts.append("Provide only the Python code for the unit tests, no additional explanations or text, starting with `import` statements if necessary.")

    return "\n".join(context_parts)

# Example Few-Shot Data (remains the same)
FEW_SHOT_EXAMPLES = [
    {
        "function": """
def add(a: int, b: int) -> int:
    return a + b
""",
        "tests": """
import pytest

def test_add_positive_numbers():
    assert add(1, 2) == 3

def test_add_negative_numbers():
    assert add(-1, -2) == -3

def test_add_zero():
    assert add(0, 0) == 0

def test_add_positive_and_negative():
    assert add(1, -1) == 0
"""
    },
    {
        "function": """
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b
""",
        "tests": """
import pytest

def test_divide_positive_numbers():
    assert divide(10, 2) == 5.0

def test_divide_negative_numbers():
    assert divide(-10, -2) == 5.0

def test_divide_by_zero_raises_error():
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        divide(10, 0)

def test_divide_float_result():
    assert divide(10, 3) == pytest.approx(3.333333)
"""
    }
]
