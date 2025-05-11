import os
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate


class LLMWrapper:
    def __init__(self, config: dict):
        self.model_name = config.get("llm-model", "gemini-2.0-flash")
        self.model_provider = config.get("llm-model-provider", "google")
        self.api_key_env_var = config.get("llm-api-key-env-var", "LLM_API_KEY")

    def prepare(self, prompts: list):
        self.load_api_key()
        self.init_model()
        self.prepare_prompt_template([("user", prompts)])

    def load_api_key(self):
        match self.model_provider:
            case "google":
                os.environ["GOOGLE_API_KEY"] = os.environ.get(self.api_key_env_var)
            case "openai":
                os.environ["OPENAI_API_KEY"] = os.environ.get(self.api_key_env_var)
            case "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = os.environ.get(self.api_key_env_var)
            case _:
                raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def init_model(self):
        self.model = init_chat_model(
            self.model_name, model_provider=self.model_provider
        )

    def prepare_prompt_template(self, prompts: list):
        self.prompt_template = ChatPromptTemplate.from_messages(messages=prompts)

    def invoke(self, params: dict):
        prompt = self.prompt_template.invoke(params)

        response = self.model.invoke(prompt)
        return response
