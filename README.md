
# File Compressor

A tool to compress PDF and image files, reducing their file size.

## Installation

### Dependencies

*   **Ghostscript**: Required for PDF processing.
    *   **macOS (using Homebrew):**
        ```bash
        brew install ghostscript
        ```
    *   **Windows:** Download and install from the [official website](https://www.ghostscript.com/).
    *   **(Other Linux distributions might use package managers like apt or yum)**

*   **pngquant**: Used for optimizing PNG images (both standalone and within PDFs).
    *   **macOS (using Homebrew):**
        ```bash
        brew install pngquant
        ```
    *   **(Windows/Linux installation instructions might vary - check pngquant documentation)**

### Python Packages

Install the required Python packages using pip:

```bash
pip install PyQt6 Pillow
```
*Note: Pillow is optional but recommended for image compression features.*

## Usage

1.  Ensure all dependencies (Ghostscript, pngquant, Python packages) are installed.
2.  Navigate to the project directory in your terminal.
3.  Run the GUI application:

    ```bash
    python pdf_compressor_gui.py
    ```
4.  Use the application interface to select input files/folders, choose compression options, and start the process.
