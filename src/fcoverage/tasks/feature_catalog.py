import json
import os
from typing import List, Literal
from pydantic import BaseModel, Field
from fcoverage.utils.prompts import escape_markdown
from .base import TasksBase
from fcoverage.utils.http import get_github_repo_details
from langchain_core.prompts import PromptTemplate


class FeatureItem(BaseModel):
    name: str = Field(description="A short name or title for the feature.")
    description: str = Field(
        description="Provide a clear and complete explanation and answer these questions for the feature: what the feature is, how it works, who it is for, and the value it provides. Include all important details and use complete sentences that are informative, avoiding overly brief explanations."
    )
    entry_point: str = Field(
        description="A description of how a user might access this feature (e.g., 'Through the 'Export' button on the user profile page', or 'Via the `/api/v2/report` endpoint'). If unknown, state 'Unknown'."
    )
    keywords: List[str] = Field(
        description="list of relevant searchable keywords. You expect to see these keywords in the name of related files, classes, methods, functions. To be used in find or grep to discover these code portions."
    )
    queries: List[str] = Field(
        description="list of relevant RAG queries to use similarity search for retrieve related production code."
    )
    priority: Literal["High", "Medium", "Low"] = Field(
        description="Testing priority for this feature: High, Medium, or Low.",
        enum=["High", "Medium", "Low"],
    )


class ProjectFeatures(BaseModel):
    project_name: str = Field(
        description="The official or working name of the software project."
    )
    project_description: str = Field(
        description="The full description or summary of the project."
    )
    features: List[FeatureItem] = Field(
        description="A list of structured feature records."
    )


class FeatureCatalogTask(TasksBase):

    def __init__(self, args, config):
        super().__init__(args, config)

    def prepare(self):
        self.load_llm_model()

    def run(self):
        documents = self.load_documents()
        prompt = self.load_feature_extraction_prompt(documents)
        features_list = self.invoke_llm(prompt)
        out = self.args["out"]
        if not out:
            out = "feature-catalog.json"
        with open(out, "w") as file:
            file.write(json.dumps(features_list.model_dump(mode="json"), indent=2))
        return True

    def load_documents(self):
        result = []
        for doc in self.args["docs"]:
            filename = os.path.join(self.args["project"], doc)
            with open(filename, "r") as file:
                content = file.read()

            result.append(f"File: {filename}")
            result.append("Content:")
            result.append("```")
            result.append(escape_markdown(content))
            result.append("```")

        return "\n".join(result)

    def load_feature_extraction_prompt(self, documents):
        feature_extraction_prompt_template = PromptTemplate.from_template(
            self.load_prompt("feature_extraction.txt")
        )

        project_name = "not available"
        project_description = "not available"
        if "github" in self.args:
            github_details = get_github_repo_details(self.args["github"])
            project_name = github_details["repo_name"]
            project_description = github_details["description"]

        prompt_feature_extraction = feature_extraction_prompt_template.invoke(
            {
                "project_name": project_name,
                "project_description": project_description,
                "documents": documents,
            }
        )
        return prompt_feature_extraction

    def invoke_llm(self, prompt):
        structured_llm = self.model.with_structured_output(ProjectFeatures)
        return structured_llm.invoke(prompt)
