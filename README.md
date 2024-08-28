# Jobbing Assistant

Jobbing Assistant is a powerful Streamlit-based web application designed to help job seekers optimize their application process. It leverages AI to evaluate CVs, generate cover letters, and provide tailored edit suggestions based on specific job postings.

## Features

- **CV Evaluation**: Analyze your CV against job requirements and receive a detailed rating.
- **Cover Letter Generation**: Create customized cover letters for specific job applications.
- **CV Edit Suggestions**: Get actionable suggestions to improve your CV for targeted positions.
- **Multiple AI Model Support**: Choose from various AI models for different tasks.
- **Retrieval-Augmented Generation (RAG)**: Optional feature to enhance AI responses with additional context.
- **Job Posting Extraction**: Automatically extract and parse job details from LinkedIn URLs.
- **Company Information**: Integrate relevant company information from Wikipedia.
- **Export Functionality**: Save results as Markdown files for future reference.
- **CV Upload**: Support for uploading CVs in PDF, Markdown, or plain text formats.
- **Website Crawling**: Ability to crawl and analyze job postings from provided URLs.
- **Document Upload for RAG**: Upload various document types to enhance RAG capabilities.
- **Flexible Input**: Choose between entering a Job ID or a URL to crawl for job details.
- **Additional Context**: Provide extra information to guide AI responses.
- **Cache Management**: Clear cache to refresh data and models.

## Requirements

- Python 3.10 or higher
- Conda, Poetry, or pip
- Ollama for local AI model integration

## Installation

You can install Jobbing Assistant using Conda, Poetry, or pip. Choose the method that best suits your workflow.

### Using Conda (Recommended for Conda users)

1. Ensure you have Conda installed. If not, install Miniconda or Anaconda.

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/jobbing-assistant.git
   cd jobbing-assistant
   ```

3. Create a new Conda environment:
   ```
   conda create -n jobbing-assistant python=3.10
   ```

4. Activate the environment:
   ```
   conda activate jobbing-assistant
   ```

5. Install Poetry within the Conda environment:
   ```
   conda install -c conda-forge poetry
   ```

6. Install project dependencies:
   ```
   poetry install
   ```

### Using Poetry (Recommended for non-Conda users)

1. Ensure you have Python 3.10 or higher installed:
   ```
   python --version
   ```
   If not, download and install it from [python.org](https://www.python.org/downloads/).

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/jobbing-assistant.git
   cd jobbing-assistant
   ```

3. Install Poetry:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   
   After installation, make sure Poetry is in your PATH:
   ```
   export PATH="$HOME/.local/bin:$PATH"
   ```
   
   You may want to add this line to your shell configuration file (e.g., `.bashrc`, `.zshrc`) for permanent effect.

4. Configure Poetry to create virtual environments inside the project directory:
   ```
   poetry config virtualenvs.in-project true
   ```

5. Install project dependencies:
   ```
   poetry install
   ```

### Using pip

1. Ensure you have Python 3.10 or higher installed:
   ```
   python --version
   ```
   If not, download and install it from [python.org](https://www.python.org/downloads/).

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/jobbing-assistant.git
   cd jobbing-assistant
   ```

3. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. Install the package and its dependencies:
   ```
   pip install .
   ```

## Development

To set up the development environment:

1. Ensure you've completed the installation steps above.

2. Set up pre-commit hooks:
   ```
   pre-commit install
   ```

3. You can now use the development tools:
   ```
   pytest  # Run tests
   black src tests  # Format code
   isort src tests  # Sort imports
   flake8 src tests  # Lint code
   mypy src  # Type check
   ```

## Usage

### If installed with Conda or Poetry:

1. Activate the environment:
   ```
   conda activate jobbing-assistant  # If using Conda
   # or
   poetry shell  # If using Poetry
   ```

2. Start the Streamlit app:
   ```
   streamlit run src/jobbing_assistant/app.py
   ```

### If installed with pip:

1. Activate the virtual environment:
   ```
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Start the Streamlit app:
   ```
   streamlit run src/jobbing_assistant/app.py
   ```

3. Access the web interface (typically at `http://localhost:8501`).

4. Use the application:
   - Select an AI model from the available options.
   - Upload your CV (PDF, Markdown, or plain text).
   - Choose between entering a Job ID or URL to crawl.
   - (Optional) Enable RAG and upload relevant documents.
   - (Optional) Provide additional context.
   - Select desired action: CV rating, cover letter generation, or CV edit suggestions.

## Configuration

- Adjust settings in `src/jobbing-assistant/config.yaml` to modify application behavior.
- Customize AI behavior by editing prompts in `src/jobbing-assistant/prompts.py`.

## File Structure

- `src/jobbing-assistant/app.py`: Main application logic and Streamlit interface.
- `src/jobbing-assistant/config.py`: Configuration loading and management.
- `src/jobbing-assistant/config.yaml`: Configuration settings for the application.
- `src/jobbing-assistant/prompts.py`: AI task prompts for different functionalities.
- `src/jobbing-assistant/extract.py`: Job posting scraping and processing functions.
- `src/jobbing-assistant/wikipedia.py`: Wikipedia integration for company information.
- `src/jobbing-assistant/utils.py`: Utility functions including PDF to Markdown conversion.
- `src/jobbing-assistant/query_engine.py`: Implementations for different query engines (Plain and RAG).
- `src/jobbing-assistant/crawler/`: Website crawling functionality.

## Advanced Features

### Retrieval-Augmented Generation (RAG)

Enable RAG to incorporate information from uploaded documents into AI responses, providing more context-aware suggestions.

### Website Crawling

Enter a URL to automatically crawl and analyze job postings from specific websites.

### Document Upload for RAG

Upload various document types (PDF, Word, Excel, PowerPoint, etc.) to enhance the RAG system's knowledge base.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the web application framework.
- [Ollama](https://ollama.ai/) for local AI model integration.
- [LlamaIndex](https://www.llamaindex.ai/) for advanced indexing and retrieval.
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for web scraping capabilities.
- [Wikipedia](https://www.wikipedia.org/) for company information.

## Development

To set up the development environment:

### With Poetry:

1. Install development dependencies:
   ```
   poetry install --with dev
   ```

2. Set up pre-commit hooks:
   ```
   poetry run pre-commit install
   ```

### With pip:

1. Ensure you've installed the development dependencies:
   ```
   pip install ".[dev]"
   ```

2. Set up pre-commit hooks:
   ```
   pre-commit install
   ```

### Common development tasks:

3. Run tests:
   ```
   pytest
   ```

4. Format code:
   ```
   black src tests
   isort src tests
   ```

5. Run linters:
   ```
   flake8 src tests
   mypy src
   ```
