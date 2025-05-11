# fcoverage: LLM Testing Assistant

An AI-powered assistant to help open-source projects understand and improve their test coverage and quality by analyzing documentation and code.

**Current Status: Proof of Concept (PoC)**
This project is currently in its early Proof of Concept stage, focusing on demonstrating core functionality for Python projects using the pytest testing framework.

## Vision

To provide intelligent, actionable insights that empower developers to build more robust and well-tested software with greater ease. We aim to bridge the gap between project documentation (what features are promised) and test suites (what is actually being verified).

## Core Features (PoC)

1.  **Feature Coverage Reporting:**
    * Analyzes project documentation (README, wikis, etc., as specified by maintainers) to help define a list of user-facing features.
    * Maps existing `pytest` tests to these defined features by analyzing test code and relevant source code.
    * Generates a report (`.fcoverage/report.md`) detailing which features are covered, by which tests (including the LLM's reasoning), and which features appear to lack test coverage.

2.  **Test Quality Improvement Suggestions:**
    * Analyzes `pytest` test code for potential improvements.
    * Provides suggestions in the `report.md` regarding:
        * **Readability:** Clearer variable names, simpler logic.
        * **Brittleness:** Reducing reliance on fragile selectors or hardcoded values, suggesting better mocking.
        * **Focus:** Splitting large tests into smaller, more targeted ones.

## How It Works (PoC Workflow)

1.  **Feature Definition (`feature-list.md`):**
    * Developers specify which project documents (e.g., `README.md`, `docs/`) should be used for feature extraction in the configuration file (`.fcoverage/config.yml`).
    * The tool, using an LLM, can propose an initial list of features based on these documents. This proposed list is typically committed to the main branch.file `.fcoverage/feature-list.md` via a Pull Request.
    * Developers review, edit, and approve this `feature-list.md` through their standard Git workflow. This file becomes the source of truth for features.

2.  **Analysis & Reporting (`report.md`):**
    * Triggered manually or via a scheduled job (e.g., weekly GitHub Action).
    * The tool reads the approved `feature-list.md`.
    * It parses Python source code and `pytest` test files (using Python's `ast` module and LLM reasoning) to:
        * Map tests to features.
        * Analyze test quality.
    * A comprehensive report, `.fcoverage/report.md`, is generated and committed to a new branch, followed by a Pull Request to the main branch.

## Technology Stack (PoC)

* **Primary Language:** Python 3.x
* **Target Test Framework:** `pytest`
* **Code Parsing:** Python's built-in `ast` module.
* **AI/LLM:** Integration with a Large Language Model that offers a free tier suitable for PoC (In the POC, we use Google's Gemini).
* **Prompt Management:** LLM Prompts are stored as editable text files in `.fcoverage/prompts/`.

## Getting Started (PoC Guide)

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/mehrdad-abdi/fcoverage.git](https://github.com/mehrdad-abdi/fcoverage.git)
    ```

2.  **Obtain LLM API Key and Configure:**
    * Sign up for an LLM service that provides a free tier (e.g., Google AI Studio for Gemini API key).
    * Generate an API key.
    * For local manual runs, you might set this as an environment variable:
        ```bash
        export LLM_API_KEY="YOUR_API_KEY_HERE"
        ```
    * For use in GitHub Actions for your project, add this key as a repository secret (e.g., named `LLM_API_KEY`).

3.  **Prepare the target Repository:**
    * Clone the repository:
    ```bash
    git clone [https://github.com/acme/awsome-project.git](https://github.com/acme/awsome-project.git)
    ```
    * Create `.fcoverage` directory:
    ```bash
    cp -r fcoverage/target-repository-files awsome-project/.fcoverage
    cp -r fcoverage/prompts awsome-project/.fcoverage/prompts
    cd awsome-project/.fcoverage
    mv config.yml.example config.yml 
    ```
    * Edit `config.yml`

4.  **Set up Python Environment:**
    * You need to do it only first time:
    ```bash
    # in the "fcoverage" directory
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

5.  **Execute the tool:**
    ```bash
    # in the "fcoverage" directory
    python main.py --project ../awsome-project
    ```

## Configuration

1.  **Specify Documents for Feature Extraction:**
    * Edit or create `.fcoverage/config.yml` to list the paths to documentation files (e.g., `README.md`, `docs/main_guide.md`, URLs to wiki pages) that the tool should use to understand your project's features.

2.  **Customize Prompts (Optional):**
    * The prompts used to interact with the LLM are stored in the `.fcoverage/prompts/` directory.
    * Advanced users can modify these prompts to tailor the analysis to their specific needs. Changes are version-controlled.

3.  **Manage `feature-list.md`:**
    * This file is central to feature coverage. It's expected to be at `.fcoverage/feature-list.md` and managed via Git.

## Usage (PoC CLI - Tentative Commands)

*(Note: CLI commands are illustrative for the PoC)*

1.  **Propose/Update Feature List:**
    * (After configuring documents in `config.yml`)
    * ```bash
        python main.py generate-features
        ```
    * This command will analyze the specified documents, create a new branch (e.g., `testing-assistant/update-features`), commit a proposed `feature-list.md`, and guide you to create a PR. Maintainers review and merge this PR.

2.  **Run Analysis and Generate Report:**
    * ```bash
        python main.py run-report
        ```
    * This command performs the full analysis (feature mapping, quality suggestions), creates a new branch (e.g., `testing-assistant/report-YYYY-MM-DD`), commits/updates `.fcoverage/report.md`, and guides you to create a PR to merge the report into your main branch.

## Understanding the Report (`.fcoverage/report.md`)

The generated report will typically contain:
* **Overall Summary:** Statistics on features, tests, coverage, and suggestions.
* **Feature Coverage Analysis:**
    * List of covered features with mapped tests and the LLM's reasoning.
    * List of uncovered features.
* **Test Quality Suggestions:**
    * Suggestions grouped by test file and function.
    * Includes location (file path, line numbers), suggestion type (readability, brittleness, etc.), and the LLM's detailed advice.

## Limitations (PoC)

* **Python/pytest Only:** Currently supports only Python projects tested with `pytest`.
* **API Limits:** Relies on LLM free tiers; if API rate limits are hit, a run might be incomplete (the report will indicate this). The next run will re-analyze from the beginning.
* **No Real-time Feedback:** Analysis is done via manual/scheduled runs, not as real-time feedback on PRs (this is a future goal).
* **LLM Variability:** LLM outputs can sometimes be variable. Prompt engineering and iteration are ongoing.

## Contributing

We welcome contributions! If you're interested in helping improve the LLM Testing Assistant, please see our `CONTRIBUTING.md` file (to be created) for guidelines on:
* Reporting bugs
* Suggesting features
* Setting up a development environment
* Submitting pull requests

Key areas for early contributions could include:
* Refining AST parsing logic.
* Improving prompt templates in `.fcoverage/prompts/`.
* Expanding test cases for the assistant itself.
* Documentation improvements.

## Roadmap / Future Work

Beyond the PoC, we envision:
* Support for other popular languages and testing frameworks.
* Deeper code analysis capabilities.
* Integration with GitHub Actions to provide feedback directly on Pull Requests.
* Caching mechanisms to optimize performance and API usage.
* More sophisticated handling of API rate limits and resumable runs.
* User-configurable suggestion types.

## License

This project is licensed under the MIT License.
