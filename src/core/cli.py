"""
AIEvoDev CLI - Command-line interface for the self-optimizing test generator.
"""
import json
import os
import subprocess
import sys
import typer
import yaml
from typing_extensions import Annotated
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from dotenv import load_dotenv

# Adjust sys.path to ensure local imports work correctly
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.main_orchestrator import MainOrchestrator
from src.spec_parser.spec_parser import SpecificationParser
from src.llm_api_connectors.llm_provider import LLMProvider

# Initialize Typer app and Console
app = typer.Typer(help="AIEvoDev - Self-optimizing AI test generator")
console = Console()


def get_project_root() -> str:
    """Returns the project root directory."""
    return project_root


def get_specs_dir() -> str:
    """Returns the path to the specs directory."""
    return os.path.join(get_project_root(), "specs")


def get_output_dir() -> str:
    """Returns the path to the output directory."""
    return os.path.join(get_project_root(), "output")


@app.command()
def init():
    """Initialize the AIEvoDev project structure."""
    console.print(Panel("[bold blue]AIEvoDev Project Initializer[/bold blue]", expand=False))

    if os.path.exists(os.path.join(project_root, "src")) and os.path.exists(get_specs_dir()):
        console.print(f"[green]Project structure already exists at {project_root}.[/green]")
    else:
        console.print("[red]Project structure not found. Please ensure it's set up correctly.[/red]")
        raise typer.Exit(code=1)

    # Create example spec if it doesn't exist
    example_spec_path = os.path.join(get_specs_dir(), "example_test_spec.yaml")
    if not os.path.exists(example_spec_path):
        console.print(f"[yellow]Creating example_test_spec.yaml...[/yellow]")
        example_content = '''# Example Specification for Python Unit Test Generation
problem_statement: "Generate comprehensive unit tests for the 'calculate_average' function."

target_function_info:
  name: "calculate_average"
  file_path: "src/utils.py"
  signature: "def calculate_average(numbers: list[int]) -> float:"
  docstring: |
    Calculates the average of a list of numbers.
    Args:
        numbers: A list of integers.
    Returns:
        The average of the numbers as a float.
    Raises:
        ValueError: If the input list is empty.
  source_code: |
    def calculate_average(numbers: list[int]) -> float:
        if not numbers:
            raise ValueError("Input list cannot be empty.")
        return sum(numbers) / len(numbers)

test_specifications:
  framework: "pytest"
  min_coverage_percentage: 90
  test_cases_to_include:
    - functional_correctness:
        - "positive integers"
        - "negative integers"
        - "mixed positive and negative integers"
    - edge_cases:
        - "empty list (should raise ValueError)"
        - "single element list"
    - error_handling:
        - "non-list input"
  output_format: "single_file"

adversarial_goals:
  maximize_test_effectiveness: "Tests should detect regressions from subtle logic changes."
  minimize_false_positives: "Tests must pass when function is correctly implemented."
  maximize_bug_detection_rate: "Detect at least 80% of common implementation bugs."

llm_configuration:
  model_name: "gpt-4o-mini"
  temperature: 0.5
  max_tokens: 1000
'''
        with open(example_spec_path, 'w', encoding='utf-8') as f:
            f.write(example_content)
        console.print(f"[green]Example spec created at {example_spec_path}[/green]")
    else:
        console.print(f"[yellow]Example spec already exists at {example_spec_path}.[/yellow]")


@app.command(name="spec-create")
def spec_create(
    name: Annotated[str, typer.Option(help="Name of the new specification file.")],
    func_path: Annotated[str, typer.Option(help="Path to the Python file containing the function.")],
    func_name: Annotated[str, typer.Option(help="Name of the function to test.")],
    desc: Annotated[str, typer.Option(help="Description of desired test characteristics.")],
    llm: Annotated[str, typer.Option(help="LLM model to use.")] = "gpt-4o-mini"
):
    """Create a new GSD YAML specification using meta-prompting."""
    console.print(Panel(f"[bold blue]Creating Specification: {name}.yaml[/bold blue]", expand=False))

    try:
        with open(func_path, 'r', encoding='utf-8') as f:
            full_code = f.read()

        # Extract function source code
        function_code = ""
        in_function = False
        indent_level = 0
        for line in full_code.splitlines():
            if line.strip().startswith(f"def {func_name}("):
                in_function = True
                indent_level = len(line) - len(line.lstrip())
            if in_function:
                function_code += line + "\n"
                # Stop when we hit a line at same or lower indent (after getting content)
                if function_code.count('\n') > 2 and line.strip() and not line.startswith(' ' * (indent_level + 1)):
                    if not line.strip().startswith('def '):
                        continue
                    break

        if not function_code.strip():
            console.print(f"[red]Error: Could not find function '{func_name}' in '{func_path}'.[/red]")
            raise typer.Exit(code=1)

    except FileNotFoundError:
        console.print(f"[red]Error: File not found at '{func_path}'.[/red]")
        raise typer.Exit(code=1)

    generated_spec = f'''# Generated Specification for {func_name}
problem_statement: "{desc}"

target_function_info:
  name: "{func_name}"
  file_path: "{func_path}"
  source_code: |
    {function_code.strip()}

test_specifications:
  framework: "pytest"
  min_coverage_percentage: 80
  test_cases_to_include:
    - functional_correctness: ["basic inputs"]
    - edge_cases: ["boundary conditions"]

adversarial_goals:
  maximize_test_effectiveness: "Identify regressions effectively."
  minimize_false_positives: "Tests pass for correct implementations."

llm_configuration:
  model_name: "{llm}"
  temperature: 0.5
'''

    spec_path = os.path.join(get_specs_dir(), f"{name}.yaml")
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(generated_spec)

    console.print(f"[green]Specification saved to {spec_path}[/green]")
    console.print("[yellow]Please review and refine the generated spec.[/yellow]")


@app.command(name="spec-edit")
def spec_edit(
    name: Annotated[str, typer.Option(help="Name of the specification file to edit.")]
):
    """Edit an existing GSD YAML specification."""
    spec_path = os.path.join(get_specs_dir(), f"{name}.yaml")
    if not os.path.exists(spec_path):
        console.print(f"[red]Error: Specification '{spec_path}' not found.[/red]")
        raise typer.Exit(code=1)

    editor = os.getenv("EDITOR", "notepad.exe" if sys.platform == "win32" else "vi")
    console.print(f"[yellow]Opening {spec_path} in {editor}...[/yellow]")
    try:
        subprocess.run([editor, spec_path], check=True)
        console.print(f"[green]Specification '{name}.yaml' edited.[/green]")
    except FileNotFoundError:
        console.print(f"[red]Error: Editor '{editor}' not found.[/red]")
        raise typer.Exit(code=1)


@app.command()
def run(
    spec_name: Annotated[str, typer.Argument(help="Name of the GSD YAML specification file (e.g., my_function_tests).")],
    generations: Annotated[int, typer.Option("--generations", "-g", help="Number of evolution generations.", min=0)] = 5
):
    """Run the adversarial evolution workflow based on a GSD specification."""
    console.print(Panel(f"[bold blue]Running Evolution Workflow for '{spec_name}.yaml'[/bold blue]", expand=False))

    # Load environment variables
    dotenv_path = os.path.join(get_project_root(), '.env')
    load_dotenv(dotenv_path=dotenv_path)

    spec_file_path = os.path.join(get_specs_dir(), f"{spec_name}.yaml")

    if not os.path.exists(spec_file_path):
        console.print(f"[red]Error: Specification '{spec_file_path}' not found.[/red]")
        raise typer.Exit(code=1)

    try:
        orchestrator = MainOrchestrator(project_root_dir=get_project_root())
        final_results = orchestrator.run_evolution_workflow(
            gsd_spec_file_path=spec_file_path,
            max_generations=generations
        )

        console.print("\n[bold green]Evolution Workflow Finished![/bold green]")
        if final_results:
            console.print(Panel(
                f"[bold yellow]Final Best Fitness Score:[/bold yellow] {final_results['final_best_fitness']['total_score']:.2f}",
                expand=False
            ))

            output_tests_path = os.path.join(get_output_dir(), "final_evolved_tests", f"{spec_name}_final_tests.py")
            os.makedirs(os.path.dirname(output_tests_path), exist_ok=True)
            with open(output_tests_path, 'w', encoding='utf-8') as f:
                f.write(final_results['final_best_tests'])
            console.print(f"[green]Final tests saved to: {output_tests_path}[/green]")
        else:
            console.print("[red]No results returned from the evolution workflow.[/red]")

    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
def history(
    run_id: Annotated[str, typer.Argument(help="The unique ID of an evolution run (e.g., 20240113_123456).")]
):
    """View the evolution history of a specific run."""
    console.print(Panel(f"[bold blue]Evolution History for Run ID: {run_id}[/bold blue]", expand=False))

    history_file = os.path.join(get_output_dir(), "evolution_runs", run_id, "evolution_history.json")

    if not os.path.exists(history_file):
        console.print(f"[red]Error: History not found for run ID '{run_id}'.[/red]")
        raise typer.Exit(code=1)

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)

        for entry in history_data:
            console.print(f"\n[bold underline]Generation {entry['generation']}:[/bold underline]")
            console.print(f"  Timestamp: {entry['timestamp']}")
            console.print(f"  Status: {entry['status']}")
            fitness = entry.get('fitness_results', {})
            console.print(f"  Fitness Score: [yellow]{fitness.get('total_score', 'N/A'):.2f}[/yellow]")
            console.print(f"  Coverage: {fitness.get('code_coverage_percentage', 'N/A')}%")
            console.print(f"  Bug Detection: {fitness.get('bug_detection_rate', 'N/A')}%")

    except json.JSONDecodeError:
        console.print(f"[red]Error: Invalid JSON in history file.[/red]")
        raise typer.Exit(code=1)


@app.command()
def select(
    run_id: Annotated[str, typer.Argument(help="The unique ID of an evolution run.")],
    generation: Annotated[int, typer.Argument(help="The generation number to select.")]
):
    """Select an evolved test suite from a specific generation as final."""
    console.print(Panel(f"[bold blue]Selecting Tests: Run {run_id}, Gen {generation}[/bold blue]", expand=False))

    run_output_dir = os.path.join(get_output_dir(), "evolution_runs", run_id)
    tests_file = os.path.join(run_output_dir, f"tests_gen_{generation}.py")

    if not os.path.exists(tests_file):
        console.print(f"[red]Error: Test file not found for run '{run_id}', generation '{generation}'.[/red]")
        raise typer.Exit(code=1)

    try:
        with open(tests_file, 'r', encoding='utf-8') as f:
            selected_tests = f.read()

        final_dir = os.path.join(get_output_dir(), "selected_tests")
        os.makedirs(final_dir, exist_ok=True)

        output_filename = os.path.join(final_dir, f"selected_gen{generation}_{run_id}.py")
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(selected_tests)

        console.print(f"[green]Tests saved to: {output_filename}[/green]")
        console.print(Syntax(selected_tests, "python", theme="monokai", line_numbers=True))

    except Exception as e:
        console.print(f"[red]Error during selection: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
