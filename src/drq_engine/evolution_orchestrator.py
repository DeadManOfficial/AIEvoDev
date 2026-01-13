"""
Evolution Orchestrator - Manages the adversarial evolution loop for test generation.
"""
import json
import os
import yaml
from datetime import datetime
from typing import Dict, Any, Optional

from src.agents.test_generator_agent import TestGeneratorAgent
from src.drq_engine.fitness_evaluator import FitnessEvaluator
from src.llm_api_connectors.llm_provider import LLMProvider


class EvolutionOrchestrator:
    """Orchestrates the adversarial evolution loop for generating robust unit tests."""

    def __init__(self, project_root_dir: str, llm_provider: LLMProvider, llm_model_name: str = "gpt-4o-mini"):
        self.project_root_dir = project_root_dir
        self.test_generator_agent = TestGeneratorAgent(llm_provider, llm_model_name)
        self.fitness_evaluator = FitnessEvaluator(project_root_dir)
        self.evolution_history = []
        self.current_best_tests: Optional[str] = None
        self.current_best_fitness: Dict[str, Any] = {}
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join(self.project_root_dir, "output", "evolution_runs", self.run_id)
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Evolution run output directory: {self.output_dir}")

    def _save_generation_data(self, generation: int, tests: str, fitness_results: Dict[str, Any], status: str):
        """Save data for a given generation to the evolution history."""
        entry = {
            "generation": generation,
            "timestamp": datetime.now().isoformat(),
            "tests_content_hash": hash(tests),
            "tests_content_summary": tests[:200] + "..." if len(tests) > 200 else tests,
            "fitness_results": fitness_results,
            "status": status
        }
        self.evolution_history.append(entry)

        # Save tests to file
        tests_filename = os.path.join(self.output_dir, f"tests_gen_{generation}.py")
        with open(tests_filename, 'w', encoding='utf-8') as f:
            f.write(tests)

        # Save history
        history_filename = os.path.join(self.output_dir, "evolution_history.json")
        with open(history_filename, 'w', encoding='utf-8') as f:
            json.dump(self.evolution_history, f, indent=2)

    def evolve_tests(self, target_function_code: str, gsd_spec_yaml: str, max_generations: int = 5) -> Dict[str, Any]:
        """Run the adversarial evolution loop to generate robust unit tests."""
        parsed_gsd_spec = yaml.safe_load(gsd_spec_yaml)
        func_name = parsed_gsd_spec.get('target_function_info', {}).get('name', 'unknown_function')
        print(f"Starting evolution for {func_name}...")

        # Initial Generation
        print("\n--- Generation 0: Initial Test Generation ---")
        initial_tests = self.test_generator_agent.generate_tests(gsd_spec_yaml, target_function_code)
        initial_fitness = self.fitness_evaluator.evaluate_tests(
            original_function_code=target_function_code,
            generated_test_code=initial_tests,
            test_spec=parsed_gsd_spec
        )
        self.current_best_tests = initial_tests
        self.current_best_fitness = initial_fitness
        self._save_generation_data(0, initial_tests, initial_fitness, "initial_generation")
        print(f"Generation 0 Fitness Score: {initial_fitness['total_score']}")

        # Evolution Loop
        for gen in range(1, max_generations + 1):
            print(f"\n--- Generation {gen} ---")

            try:
                candidate_tests = self.test_generator_agent.generate_tests(
                    spec_yaml_content=gsd_spec_yaml,
                    target_function_code=target_function_code,
                    previous_evaluation_results=self.current_best_fitness
                )
            except Exception as e:
                print(f"Error during test generation in Generation {gen}: {e}")
                self._save_generation_data(gen, "ERROR_GENERATION", {}, "error")
                continue

            candidate_fitness = self.fitness_evaluator.evaluate_tests(
                original_function_code=target_function_code,
                generated_test_code=candidate_tests,
                test_spec=parsed_gsd_spec
            )
            print(f"Generation {gen} Candidate Fitness Score: {candidate_fitness['total_score']}")

            # Selection (Elitism)
            if candidate_fitness["total_score"] > self.current_best_fitness["total_score"]:
                print(f"  New best! Score: {self.current_best_fitness['total_score']} -> {candidate_fitness['total_score']}")
                self.current_best_tests = candidate_tests
                self.current_best_fitness = candidate_fitness
                self._save_generation_data(gen, candidate_tests, candidate_fitness, "new_best")
            else:
                print(f"  Not fitter. Keeping previous best.")
                self._save_generation_data(gen, candidate_tests, candidate_fitness, "not_best")

        print("\n--- Evolution Complete ---")
        print(f"Final Best Fitness Score: {self.current_best_fitness['total_score']}")
        return {
            "final_best_tests": self.current_best_tests,
            "final_best_fitness": self.current_best_fitness,
            "evolution_history": self.evolution_history
        }
