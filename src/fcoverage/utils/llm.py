from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate


class LLMWrapper:
    def __init__(self, config: dict):
        self.model_name = config.get("llm-model", "gemini-2.0-flash")
        self.model_provider = config.get("llm-model-provider", "google")

    def prepare(self, prompts: list):
        self.init_model()
        self.prepare_prompt_template([("user", prompts)])

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
