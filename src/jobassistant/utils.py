import io

import PyPDF2


def convert_pdf_to_markdown(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
    markdown_content = ""

    for page in pdf_reader.pages:
        text = page.extract_text()
        # Basic formatting: Add two newlines after each page
        markdown_content += text + "\n\n"

    return markdown_content
