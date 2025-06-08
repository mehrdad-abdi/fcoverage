import json
import os

from fcoverage.models.feature_list import FeatureItem, ProjectFeatureAnalysis
from .base import TasksBase
from langchain_core.prompts import ChatPromptTemplate
from fcoverage.utils.http import get_github_repo_details


class FeatureExtractionTask(TasksBase):
    """
    This class is responsible for extracting features from the documents specified in the configuration.
    It uses the LLMWrapper class to interact with a language model for feature extraction.
    """

    PROMPT_NAME = "feature_extraction.txt"

    def __init__(self, args, config):
        super().__init__(args, config)
        self.documents = []
        self.prompt_template = None
        self.project_name = "not available"
        self.project_description = "not available"

    def prepare(self):
        self.load_llm_model()
        self.load_documents()
        self.load_feature_extraction_prompt()
        if "github" in self.args:
            github_details = get_github_repo_details(self.args["github"])
            self.project_name = github_details["repo_name"]
            self.project_description = github_details["description"]

    def load_documents(self):
        """
        Load documents from the specified directorieis in config.
        """
        docs = self.config["documents"]
        for doc in docs:
            filename = os.path.join(self.args["project"], doc)
            with open(filename, "r") as file:
                content = file.read()
                self.documents.append((doc, content))

    def load_feature_extraction_prompt(self):
        feature_extraction_prompt = self.load_prompt(self.PROMPT_NAME)
        self.prompt_template = ChatPromptTemplate.from_messages(
            messages=[("user", feature_extraction_prompt)]
        )

    def invoke_llm(self):
        documents = "\n\n".join([f"{doc[0]}\n{doc[1]}" for doc in self.documents])
        prompt = self.prompt_template.invoke(
            {
                "project_name": self.project_name,
                "project_description": self.project_description,
                "documents": documents,
            }
        )
        structured_llm = self.model.with_structured_output(ProjectFeatureAnalysis)
        return structured_llm.invoke(prompt)

    def feature_item_to_markdown(self, index: int, feature: FeatureItem):
        is_unique = ""
        critical_to_user_experience = ""
        is_likely_to_change = ""
        if feature.is_unique:
            is_unique = "[**unique** feature compared to similar projects]"
        if feature.critical_to_user_experience:
            critical_to_user_experience = "[**critical** for user experience]"
        if feature.is_likely_to_change:
            is_likely_to_change = "[likely to **evolve** frequently]"
        edge_cases_to_test = ""
        if feature.edge_cases_to_test:
            edge_cases_to_test_items = "\n".join(
                f"- {e}" for e in feature.edge_cases_to_test
            )
            edge_cases_to_test = """#### Edge cases to test:

{edge_cases_to_test_items}   
""".format(
                edge_cases_to_test_items=edge_cases_to_test_items
            )

        return f"""### {index}. {feature.name}

*{feature.description}*

Testing priority for this feature: **{feature.priority}**

{critical_to_user_experience} {is_unique} {is_likely_to_change}

{edge_cases_to_test}
"""

    def features_to_markdown(self, features: ProjectFeatureAnalysis):
        primary_goals = "\n".join(
            f"{idx + 1}. {f}" for idx, f in enumerate(features.main_goals)
        )
        expected_features = "\n".join(
            f"{idx + 1}. {f}" for idx, f in enumerate(features.expected_features)
        )
        similar_projects = "\n".join(
            f"{idx + 1}. {f}" for idx, f in enumerate(features.similar_projects)
        )
        features_list_items = []
        for p in ["High", "Medium", "Low"]:
            # sort High to Low
            features_list_items.extend(
                [
                    self.feature_item_to_markdown(idx + 1, f)
                    for idx, f in enumerate(features.features)
                    if f.priority == p
                ]
            )
        features_list = "\n\n".join(features_list_items)
        edge_case_notes = ""
        if features.edge_case_notes:
            edge_case_notes_items = (
                "\n".join(
                    f"{idx + 1}. {f}" for idx, f in enumerate(features.edge_case_notes)
                )
                if features.edge_case_notes
                else ""
            )

            edge_case_notes = """## Edge case notes

*System-wide or project-level edge cases worth testing.*

{edge_case_notes_items}
""".format(
                edge_case_notes_items=edge_case_notes_items
            )

        return """# Features List

**Project Name:** {project_name}

**Project Description:** {project_description}

## Primary Goals: 

*The main goals or objectives the project is trying to achieve.*

{primary_goals}

### Expected Features (as a User)

*Features that a typical user would expect from the project.*

{expected_features}

### Similar Projects/Products

*Other tools, libraries, or projects that serve a similar purpose.*

{similar_projects}

## Features

{features}

{edge_case_notes}

""".format(
            project_name=features.project_name,
            project_description=features.project_description,
            primary_goals=primary_goals,
            expected_features=expected_features,
            similar_projects=similar_projects,
            features=features_list,
            edge_case_notes=edge_case_notes,
        )

    def write_response_to_file(self, features):
        filename = os.path.join(self.args["project"], self.config["feature-file"])
        filename_json = os.path.join(
            self.args["project"], ".fcoverage", "project-features.json"
        )
        with open(filename_json, "w") as file:
            file.write(json.dumps(features.model_dump(mode="json"), indent=2))
        print(f"Feature extraction results written to {filename_json}")

        with open(filename, "w") as file:
            file.write(self.features_to_markdown(features))
        print(f"Feature extraction results written to {filename}")

    def run(self):
        response = self.invoke_llm()
        self.write_response_to_file(response)
        print("Feature extraction completed successfully.")
        return True
