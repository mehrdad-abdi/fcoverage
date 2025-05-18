# fcoverage: LLM Testing Assistant to Measure Feature Coverage

An AI-powered assistant to help open-source projects understand and improve their test coverage and quality in relation to their offered features, by analyzing documentation and code.

**Current Status: Proof of Concept (PoC)**
This project is currently in its early Proof of Concept stage, focusing on demonstrating core functionality for Python projects using the pytest testing framework.

## Vision

To provide intelligent, actionable insights that empower developers to build more robust and well-tested software with greater ease. We aim to bridge the gap between project documentation (what features are promised) and test suites (what is actually being verified).

## Core Features (PoC)

1.  **Feature Coverage Reporting:**
    * Analyzes project documentation (README, wikis, etc., as specified by maintainers) to help define a list of user-facing features.
    * Maps existing `pytest` tests to these defined features by analyzing test code and relevant source code.
    * Generates a report detailing which features are covered, by which tests (including the LLM's reasoning), and which features appear to lack test coverage.

2.  **Test Quality Improvement Suggestions:**
    * Analyzes `pytest` test code for potential improvements.
    * Provides suggestions in the report regarding:
        * **Readability:** Clearer variable names, simpler logic.
        * **Brittleness:** Reducing reliance on fragile selectors or hardcoded values, suggesting better mocking.
        * **Focus:** Splitting large tests into smaller, more targeted ones.

## How It Works (PoC Workflow)

1.  **Feature Definition:**
    * Developers specify which project documents (e.g., `README.md`, `docs/foo.txt`) should be used for feature extraction in the configuration file.
    * The tool is started with `feature-extraction` task specified in the command arguments.
    * This task, using an LLM, will propose an initial list of features based on these documents. 
       * If the tool is employed in a GitHub actions, this proposed list can be committed to the main branch, and the file `.fcoverage/feature-list.md` via a Pull Request.
       * If the tool is employed locally, the file is accessible directly. They can include it in the project directory.
    * Developers review, edit, and approve this `feature-list.md` through their standard Git workflow. This file becomes the source of truth for features.

2.  **Source-Code Analysis and Building RAG:**
    * The tool is started with `code-analysis` task specified in the command arguments.
    * The tool iterates over all source code defined in the source folder, parsing it (using Python's `ast`). It then builds function-level chunks and uses an online or offline embedding model.
    * The tool builds a vector database (LangChain's FAISS) using the source code defined in the `source` folder. 
    * The vector database is exported as a GitHub Actions artifact.

3.  **Test Coverage Analysis and Reporting:**
    * The tool is started with `test-analysis` task specified in the command arguments.
    * The tool reads the approved `feature-list.md`, uses the source-code vector database, and iterates over each test in `tests` folder.
    * It parses Python source code and `pytest` test files (using Python's `ast` module and LLM reasoning) to:
        * Map tests to features.
        * Analyze test quality.
    * A comprehensive report, `.fcoverage/report.md`, is generated and committed to a new branch, followed by a Pull Request to the main branch.

## Technology Stack (PoC)

* **Primary Language:** Python 3.x
* **Target Test Framework:** `pytest`
* **Code Parsing:** Python's built-in `ast` module.
* **LLM Orchestration:** LangChain 
* **Vector Store:** FAISS 
* **AI/LLM:** Integration with a Large Language Model that offers a free tier suitable for PoC.

## Getting Started

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/mehrdad-abdi/fcoverage.git
    cd fcoverage
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    pip install -e .
    ```

    (WIP: not pushed to PyPI yet)
    ```bash
    pip install fcoverage
    ```

2.  **Obtain LLM API Key and Configure:**
    * Sign up for an LLM service that provides a free tier (e.g., Google AI Studio for Gemini API key).
    * Generate an API key.
    * For local manual runs, you might set this as an environment variable:
        ```bash
        export GOOGLE_GENAI_API_KEY="YOUR_API_KEY_HERE"
        ```
      Name of the variable is important and differs from service to service. 
      List of supported LLM models can be found here: https://python.langchain.com/docs/integrations/chat/
      You can see which environment variables it needs.
    * For use in GitHub Actions for your project, add this key as a repository secret.

3.  **Prepare the target Repository:**
    * Clone the repository:
    ```bash
    git clone https://github.com/acme/awesome-project.git
    ```
    * Create `.fcoverage` directory, and `.fcoverage/config.yml` file. ([Example file](https://github.com/mehrdad-abdi/fcoverage/blob/main/target-repository-files/config-example.yml))
    * Edit `config.yml`

4.  **Execute the tool:**
    
    Feature extraction:
    ```bash
    fcoverage --project awesome-project --task feature-extraction
    ```
    Read the feature list in `.fcoverage/feature-list.md`

    Code analysis:
    ```bash
    fcoverage --project awesome-project --task code-analysis
    ```
    Verify the RAG files are created in `.fcoverage/rag`

    Test analysis:
    ```bash
    fcoverage --project awesome-project --task test-analysis
    ```
    Verify the report is created in `.fcoverage/report.md`

5. **Customization:**

    If you want to customize the prompts for your project, create the folder `.fcoverage/prompts` add files with the same names as [the default prompt files](https://github.com/mehrdad-abdi/fcoverage/blob/main/src/fcoverage/prompts/).
    

## Configuration

1.  **Specify Documents for Feature Extraction:**
    * Edit or create `.fcoverage/config.yml` to list the paths to documentation files (e.g., `README.md`, `docs/main_guide.md`, URLs to wiki pages) that the tool should use to understand your project's features.

2.  **Customize Prompts (Optional):**
    * The prompts used to interact with the LLM are stored in the `.fcoverage/prompts/` directory.
    * Advanced users can modify these prompts to tailor the analysis to their specific needs. Changes are version-controlled.

3.  **Manage `feature-list.md`:**
    * This file is central to feature coverage. It's expected to be at `.fcoverage/feature-list.md` and managed via Git.

4. **Source folder:** 
    * The folder in the project root (e.g.,`src`) that includes all source files.

5. **Tests folder:** 
    * The folder in the project root (e.g.,`tests`) that includes all test files.

6. **LLM model configuration:**
    * Configurations related to the LLM model. Currently, only online models are supported.

7. **Embedding model configuration:**
    * Configurations related to the embedding model. You can use an offline model by specifying an embedding model from HuggingFace.

## Understanding the Report (`.fcoverage/report.md`)

The generated report will typically contain:
* **Overall Summary:** Statistics on features, tests, coverage, and suggestions.
* **Feature Coverage Analysis:**
    * List of covered features with mapped tests and the LLM's reasoning.
    * List of uncovered features.
* **Test Quality Suggestions:**
    * Suggestions grouped by test file and function.
    * Includes location (file path, line numbers), suggestion type (readability, brittleness, etc.), and the LLM's detailed advice.

## Known Limitations

* **Python/pytest Only:** Currently supports only Python projects tested with `pytest`.
* **API Limits:** Relies on LLM free tiers; if API rate limits are hit, a run might be incomplete (the report will indicate this). The next run will re-analyze from the beginning.
* **No Real-time Feedback:** Analysis is done via manual/scheduled runs, not as real-time feedback on PRs (this is a future goal).
* **LLM Variability:** LLM outputs can sometimes be variable. Prompt engineering and iteration are ongoing.

## Contributing

We welcome contributions! If you're interested in helping improve the LLM Testing Assistant, you can help us by:
* Participating in the pilot program (running the tool on your project)
* Reporting bugs
* Suggesting features
* Setting up a development environment
* Submitting pull requests

Key areas for early contributions could include:
* Refining AST parsing logic.
* Improving prompt templates.
* Expanding test cases for the assistant itself.
* Documentation improvements.

## Roadmap / Future Work

Beyond the Proof of Concept (PoC), we envision:
* Support for other popular languages and testing frameworks.
* Deeper code analysis capabilities.
* Integration with GitHub Actions to provide feedback directly on Pull Requests.
* More sophisticated handling of API rate limits and resumable runs.
* User-configurable suggestion types.

## License

This project is licensed under the MIT License.
