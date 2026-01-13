"""
Main Orchestrator - High-level workflow coordinator for AIEvoDev.
Drives the GSD-DRQ-AILaunchpad test generation and evolution pipeline.
"""
import os
import json
import yaml
from src.spec_parser.spec_parser import SpecificationParser
from src.llm_api_connectors.llm_provider import LLMProvider
from src.drq_engine.evolution_orchestrator import EvolutionOrchestrator


class MainOrchestrator:
    """High-level orchestrator that drives the entire evolution workflow."""

    def __init__(self, project_root_dir: str, llm_config_path: str = 'config/llm_config.ini'):
        self.project_root_dir = project_root_dir
        self.spec_parser = SpecificationParser()
        self.llm_provider = LLMProvider(os.path.join(project_root_dir, llm_config_path))
        print(f"Main Orchestrator initialized. Project root: {self.project_root_dir}")

    def run_evolution_workflow(self, gsd_spec_file_path: str, max_generations: int = 5):
        """Execute the full test evolution workflow for a given GSD specification."""
        print(f"\n--- Running Evolution Workflow for spec: {gsd_spec_file_path} ---")

        # 1. Load and Parse GSD Specification
        try:
            full_spec = self.spec_parser.load_spec(gsd_spec_file_path)
            gsd_spec_yaml_content = yaml.dump(full_spec, sort_keys=False)
            print("GSD Specification loaded successfully.")
        except FileNotFoundError as e:
            print(f"Error: Specification file not found - {e}")
            return None
        except yaml.YAMLError as e:
            print(f"Error: Invalid YAML in specification file - {e}")
            return None
        except Exception as e:
            print(f"Unexpected error loading specification: {e}")
            return None

        # Extract target function code
        target_function_code = full_spec.get("target_function_info", {}).get("source_code")
        if not target_function_code:
            print("Error: 'source_code' not found in 'target_function_info'.")
            return None

        # Determine LLM model name from spec or default
        llm_model_name = full_spec.get("llm_configuration", {}).get("model_name", "gpt-4o-mini")

        # 2. Initialize Evolution Orchestrator
        try:
            evolution_orchestrator = EvolutionOrchestrator(
                project_root_dir=self.project_root_dir,
                llm_provider=self.llm_provider,
                llm_model_name=llm_model_name
            )
            print(f"Evolution Orchestrator initialized with LLM: {llm_model_name}")
        except Exception as e:
            print(f"Error initializing Evolution Orchestrator: {e}")
            return None

        # 3. Run the Evolution Loop
        print(f"\nInitiating adversarial evolution for {max_generations} generations...")
        final_results = evolution_orchestrator.evolve_tests(
            target_function_code=target_function_code,
            gsd_spec_yaml=gsd_spec_yaml_content,
            max_generations=max_generations
        )

        # 4. Report Final Results
        print("\n=== Evolution Workflow Completed ===")
        print("\n--- Final Best Tests ---")
        print(final_results.get("final_best_tests", "No tests generated."))

        print("\n--- Final Best Fitness ---")
        print(json.dumps(final_results.get("final_best_fitness", {}), indent=2))

        history_file = os.path.join(evolution_orchestrator.output_dir, "evolution_history.json")
        print(f"\nDetailed evolution history saved to: {history_file}")

        return final_results
