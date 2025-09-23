# IDSV Old Exam Question Generator

This project is a tool for generating LaTeX documents from a question bank stored in a CSV file. It allows for filtering questions by subject or chapter, and automatically generates `.tex` files that can be compiled into PDFs.

### Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.x
- A LaTeX distribution (e.g., TeX Live, MiKTeX)
- `pylatexenc` Python library

You can install the required Python library using pip:

```bash
pip install -r requirements.txt
```

### Project Structure

The project is organized as follows:

- `main.py`: The main script to generate LaTeX files.
- `csv_parser.py`: Parses the question bank from a CSV file.
- `generators.py`: Contains different types of question generators.
- `models.py`: Defines the data models for questions and subjects.
- `question_bank/`: Directory containing the question bank CSV files.
- `templates/`: Directory with LaTeX templates.
- `output/`: This is where the generated `.tex` and `.pdf` files will be stored. This directory is not included in the repository but will be created when you run the generator.

### How to Use

1.  **Prepare your question bank**: Create a CSV file with your questions and place it in the `question_bank/` directory. The default file is `2025-08-31.csv`. You can follow the format of the existing file.

2.  **Run the generator**: Execute the `main.py` script to generate the LaTeX files.

    ```bash
    python main.py
    ```

    This will generate a default `output.tex` file in the root directory, which includes all questions from the default CSV file.

3.  **Compile the LaTeX file**: Use a LaTeX compiler (e.g., `pdflatex` with `biber` for bibliography) to create a PDF from the generated `.tex` file. A simple way to do this is:

    ```bash
    pdflatex output.tex
    biber output
    pdflatex output.tex
    pdflatex output.tex
    ```

    This will produce an `output.pdf` file.

### Advanced Usage

You can use command-line arguments to customize the output.

-   **Filter by subject**: Generate a document with questions from a specific subject.

    ```bash
    python main.py --subject HIS
    ```

    This will create `output_his.tex`.

-   **Filter by chapter**: Generate a document with questions from a specific chapter.

    ```bash
    python main.py --chapter 2
    ```

    This will create `output_chapter_2.tex`.

-   **Custom Title**: Specify a custom title for your document.

    ```bash
    python main.py --title "My Custom Title"
    ```

-   **List available subjects**: To see a list of all available subjects you can filter by, run:
    ```bash
    python main.py --list-subjects
    ```

### License

This project is licensed for educational use at Stockholm University DSV. See the `LICENSE.md` file for more details.

### Contributing

External contributions are not accepted for this repository. For any contributions, please contact the course administration at the Department of Computer and Systems Sciences at Stockholm University.
