"""
LLM Provider - Configures and provides LLM clients for AIEvoDev.
Supports OpenAI and Google Gemini with optional Langsmith tracing.
"""
import os
import configparser
from dotenv import load_dotenv
from openai import OpenAI
from google import genai

# Load environment variables from .env file
load_dotenv()


class LLMProvider:
    """Provides configured LLM clients based on config file settings."""

    def __init__(self, config_path: str = 'config/llm_config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self._configure_langsmith()

    def _configure_langsmith(self):
        """Configure Langsmith tracing if enabled in config."""
        if self.config.has_section('langsmith') and self.config['langsmith'].getboolean('tracing_enabled', False):
            os.environ['LANGCHAIN_TRACING_V2'] = 'true'
            api_key_env_var = self.config['langsmith'].get('api_key_env_var', 'LANGCHAIN_API_KEY')
            project_name = self.config['langsmith'].get('project_name', 'default')

            langchain_api_key = os.getenv(api_key_env_var)
            if not langchain_api_key:
                print(f"Warning: Langsmith tracing enabled but API key not found: {api_key_env_var}")
            else:
                os.environ['LANGCHAIN_API_KEY'] = langchain_api_key
                os.environ['LANGCHAIN_PROJECT'] = project_name
                print(f"Langsmith tracing enabled for project: {project_name}")
        else:
            os.environ['LANGCHAIN_TRACING_V2'] = 'false'

    def get_openai_client(self, model: str = None, temperature: float = None, max_tokens: int = None) -> OpenAI:
        """Get configured OpenAI client."""
        api_key_env_var = self.config['openai'].get('api_key_env_var', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            raise ValueError(f"OpenAI API key not found in environment variable: {api_key_env_var}")
        return OpenAI(api_key=api_key)

    def get_gemini_client(self, model: str = None):
        """Get configured Gemini client using google-genai."""
        api_key_env_var = self.config['gemini'].get('api_key_env_var', 'GEMINI_API_KEY')
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            raise ValueError(f"Gemini API key not found in environment variable: {api_key_env_var}")

        client = genai.Client(api_key=api_key)
        return client

    def get_gemini_model_name(self) -> str:
        """Get the default Gemini model name from config."""
        return self.config['gemini'].get('default_model', 'gemini-2.0-flash')
