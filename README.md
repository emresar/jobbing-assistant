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

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/jobbing-assistant.git
   cd jobbing-assistant
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure Ollama is installed and running on your local machine.

4. Place your CV in Markdown format as `cv.md` in the root directory.

## Usage

1. Start the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Access the web interface (typically at `http://localhost:8501`).

3. Use the application:
   - Select an AI model from the available options.
   - Enter a LinkedIn Job ID.
   - (Optional) Provide additional context.
   - Choose between CV rating, cover letter generation, or CV edit suggestions.
   - Enable RAG and upload relevant documents if desired.

## Configuration

- Adjust `NUM_PREDICT_LEN` and `NUM_CTX` in `app.py` to modify token prediction and context window size.
- Customize AI behavior by editing prompts in `prompts.py`.

## File Structure

- `app.py`: Main application logic and Streamlit interface.
- `prompts.py`: AI task prompts for different functionalities.
- `extract.py`: Job posting scraping and processing functions.
- `wikipedia.py`: Wikipedia integration for company information.
- `cv.md`: User's CV in Markdown format (to be added by the user).

## Advanced Features

### Retrieval-Augmented Generation (RAG)

Enable RAG to incorporate information from uploaded documents into AI responses, providing more context-aware suggestions.

### Command-line Arguments

Customize the application behavior using command-line arguments:
```
python app.py --model llama3.1:latest --num_predict 12000 --num_ctx 116000
```

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