# AIEvoDev

### AI That Writes Tests, Then Makes Them Better

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![LangChain](https://img.shields.io/badge/LangChain-Powered-orange.svg)](https://langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991.svg)](https://openai.com/)
[![Google](https://img.shields.io/badge/Google-Gemini-4285F4.svg)](https://deepmind.google/technologies/gemini/)

> **Stop writing tests manually.** Let AI generate them, then watch it improve them through adversarial evolution until they catch real bugs.

---

## Why AIEvoDev?

- **Save hours** - Generate comprehensive test suites in minutes
- **Catch more bugs** - Adversarial evolution finds edge cases you'd miss
- **Self-improving** - Tests get better each generation through mutation testing
- **Production-ready** - Outputs clean pytest code you can commit directly

## How It Works

AIEvoDev generates Python unit tests using LLMs (GPT-4 or Gemini), then improves them through an evolutionary loop:

1. **Generate** - AI creates initial test suite from your specification
2. **Evaluate** - Tests are run against correct code and mutated (buggy) versions
3. **Evolve** - AI analyzes results and generates improved tests
4. **Repeat** - Loop continues until tests achieve target fitness

## Quick Start (5 minutes)

### 1. Clone

```bash
git clone https://github.com/DeadManOfficial/AIEvoDev.git
cd AIEvoDev
```

### 2. Install

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .
```

### 3. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add at least one API key:

```env
OPENAI_API_KEY=sk-your-key-here
# OR
GEMINI_API_KEY=your-gemini-key-here
```

### 4. Run

```bash
# Initialize project structure
aievodev init

# Try the example
aievodev run specs/example_test_spec.yaml src/utils.py
```

## Usage

### Create a Test Specification

```bash
aievodev spec-create my_function
```

This creates `specs/my_function_spec.yaml`. Edit it to define:
- Target function details
- Test coverage requirements
- Edge cases to cover
- Framework (pytest/unittest)

### Run Test Generation

```bash
aievodev run specs/my_spec.yaml path/to/your_function.py
```

Options:
- `--generations 5` - Number of evolution iterations (default: 5)
- `--model gpt-4o-mini` - LLM model to use

### View Results

```bash
# List all evolution runs
aievodev history

# Select best tests from a run
aievodev select <run_id>
```

## Example Specification

```yaml
problem_statement: "Generate tests for calculate_average function"

target_function_info:
  name: "calculate_average"
  signature: "def calculate_average(numbers: list[int]) -> float:"

test_specifications:
  framework: "pytest"
  min_coverage_percentage: 90
  test_cases_to_include:
    - functional_correctness:
        - "positive integers"
        - "negative integers"
    - edge_cases:
        - "empty list (should raise ValueError)"
        - "single element"

adversarial_goals:
  maximize_bug_detection_rate: "Tests should catch common bugs"
  minimize_false_positives: "Tests must pass on correct implementation"
```

## Project Structure

```
AIEvoDev/
├── config/
│   └── llm_config.ini      # LLM settings
├── specs/                  # Your test specifications
│   └── example_test_spec.yaml
├── output/                 # Generated tests (created at runtime)
│   └── evolution_runs/
├── src/
│   ├── agents/             # LangChain ReAct agent
│   ├── core/               # CLI and orchestration
│   ├── drq_engine/         # Evolution loop
│   ├── environment/        # Test execution sandbox
│   ├── llm_api_connectors/ # LLM providers
│   ├── prompts/            # Prompt templates
│   ├── spec_parser/        # YAML parsing
│   └── utils/              # Fault injection
├── .env.example            # Environment template
├── pyproject.toml          # Package config
└── requirements.txt        # Dependencies
```

## How the Evolution Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Generate  │────▶│   Evaluate   │────▶│   Score Tests   │
│    Tests    │     │  vs Correct  │     │                 │
└─────────────┘     │  vs Mutants  │     │ - Pass rate     │
       ▲            └──────────────┘     │ - Coverage      │
       │                                 │ - Bug detection │
       │            ┌──────────────┐     └────────┬────────┘
       └────────────│   Improve    │◀─────────────┘
                    │   (if better)│
                    └──────────────┘
```

**Fitness Score** combines:
- Test pass rate on correct code (no false positives)
- Code coverage percentage
- Bug detection rate (catches injected faults)

## Supported LLMs

| Provider | Models | Config Key |
|----------|--------|------------|
| OpenAI | gpt-4o-mini, gpt-4o, gpt-4-turbo | OPENAI_API_KEY |
| Google | gemini-2.0-flash, gemini-pro | GEMINI_API_KEY |

## Requirements

- Python 3.10+
- OpenAI or Google Gemini API key
- pytest, coverage (installed automatically)

## Troubleshooting

**"API key not found"**
- Check your `.env` file has the correct key
- Ensure the key name matches `config/llm_config.ini`

**"Module not found"**
- Run `pip install -e .` from the project root
- Ensure your virtual environment is activated

**Tests timeout**
- Increase timeout in `src/environment/testing_env.py`
- Check for infinite loops in generated tests

## License

MIT
