from fcoverage.utils import prompts
from langchain.chat_models import init_chat_model


class TasksBase:
    def __init__(self, args):
        self.args = args

    def prepare(self):
        raise NotImplementedError("Subclasses must implement this method")

    def run(self):
        raise NotImplementedError("Subclasses must implement this method")

    def load_prompt(self, prompt_filename):
        return prompts.read_prompt_file(prompt_filename)

    def load_llm_model(self):
        model_name = self.args.get("llm-model")
        model_provider = self.config.get("llm-provider")

        self.model = init_chat_model(
            model_name,
            model_provider=model_provider,
        )
