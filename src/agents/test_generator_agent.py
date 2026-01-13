"""
Test Generator Agent - LangChain ReAct agent for generating unit tests.
"""
import os
import yaml
from typing import Dict, Any, Optional
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from .tools import (
    ReadPythonFileTool, WritePythonFileTool, ExecutePythonCodeTool,
    RunTestsTool, GetCodeCoverageTool
)
from ..llm_api_connectors.llm_provider import LLMProvider
from ..prompts.context_builder import build_test_generation_context, FEW_SHOT_EXAMPLES


class TestGeneratorAgent:
    """LangChain ReAct agent specialized in generating Python unit tests."""

    def __init__(self, llm_provider: LLMProvider, llm_model_name: str = "gpt-4o-mini"):
        # Initialize LLM based on model name
        if "gpt" in llm_model_name.lower() or "openai" in llm_model_name.lower():
            api_key = os.getenv(llm_provider.config['openai'].get('api_key_env_var', 'OPENAI_API_KEY'))
            self.llm = ChatOpenAI(model=llm_model_name, temperature=0.5, api_key=api_key)
        elif "gemini" in llm_model_name.lower():
            api_key = os.getenv(llm_provider.config['gemini'].get('api_key_env_var', 'GEMINI_API_KEY'))
            self.llm = ChatGoogleGenerativeAI(model=llm_model_name, temperature=0.5, google_api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM model: {llm_model_name}")

        self.tools = [
            ReadPythonFileTool(),
            WritePythonFileTool(),
            ExecutePythonCodeTool(),
            RunTestsTool(),
            GetCodeCoverageTool(),
        ]

        self.agent_prompt_template = """You are an expert Python unit test developer.
Your goal is to generate comprehensive, correct, and robust unit tests based on specifications.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Context Information:
{input}

Begin!

{agent_scratchpad}"""

        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain ReAct agent."""
        prompt = PromptTemplate.from_template(self.agent_prompt_template)
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )

    def generate_tests(
        self,
        spec_yaml_content: str,
        target_function_code: str,
        task: str = "Generate Python unit tests based on the provided specifications.",
        previous_evaluation_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate Python unit tests for a function based on a specification.

        Args:
            spec_yaml_content: The test specification in YAML format.
            target_function_code: The source code of the function to test.
            task: The specific task for the agent.
            previous_evaluation_results: Optional feedback from previous evaluation.

        Returns:
            The generated Python unit test code as a string.
        """
        parsed_spec = yaml.safe_load(spec_yaml_content)

        full_context = build_test_generation_context(
            spec=parsed_spec,
            target_function_code=target_function_code,
            few_shot_examples=FEW_SHOT_EXAMPLES,
            previous_evaluation_results=previous_evaluation_results
        )

        combined_input = f"{task}\n\n{full_context}"
        response = self.agent_executor.invoke({"input": combined_input})
        return response['output']
