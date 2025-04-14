
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

## Building the macOS Installer (.dmg)

This section describes how to build a distributable `.dmg` installer for macOS users, which bundles the application and its dependencies (`ghostscript`, `pngquant`).

**Important:** The build process itself requires certain tools to be installed on the **developer's machine**. End-users installing the final `.dmg` will **not** need these tools.

### Build Prerequisites

Ensure the following are installed on your development machine:

1.  **Ghostscript:** Required by PyInstaller to bundle into the app.
    ```bash
    brew install ghostscript
    ```
2.  **pngquant:** Required by PyInstaller to bundle into the app.
    ```bash
    brew install pngquant
    ```
3.  **PyInstaller:** Used to package the Python application.
    ```bash
    pip install pyinstaller
    ```
4.  **create-dmg:** Used to create the final `.dmg` file.
    ```bash
    brew install create-dmg
    ```

### Build Steps

1.  **Navigate to Project Directory:** Open your terminal and change to the project's root directory.

2.  **(Optional) Generate Spec File:** If you don't have `PDFCompressor.spec` or want to regenerate it (this will overwrite existing modifications):
    ```bash
    pyinstaller --name PDFCompressor --windowed --onedir pdf_compressor_gui.py
    ```

3.  **Modify Spec File (`PDFCompressor.spec`):** Ensure the spec file correctly includes the binaries, data files (like the icon), and sets the bundle identifier. Key sections to check/modify:
    *   `Analysis`:
        *   `binaries`: Should include paths to the `gs` and `pngquant` executables found via `brew --prefix ghostscript`/`brew --prefix pngquant`. Example: `[('/opt/homebrew/opt/ghostscript/bin/gs', '.'), ('/opt/homebrew/opt/pngquant/bin/pngquant', '.')]` (Note: The destination '.' might be adjusted by PyInstaller to place them in `Frameworks`).
        *   `datas`: Should include the application icon. Example: `[('icon/Iconfont Graphic.png', '.')]`
    *   `BUNDLE`:
        *   `icon`: Path to the source icon file. Example: `'icon/Iconfont Graphic.png'`
        *   `bundle_identifier`: A unique identifier. Example: `'com.yourdomain.pdfcompressor'`
    *   *(Refer to the existing `PDFCompressor.spec` in the repository for the correct configuration used)*

4.  **Build the `.app` Bundle:** Run PyInstaller using the spec file. This creates the `.app` in the `dist` directory.
    ```bash
    pyinstaller PDFCompressor.spec
    ```
    *Make sure your Python code (`pdf_compressor.py`, `compression_backends.py`) has been modified to correctly locate the bundled `gs` and `pngquant` executables within the `.app` structure (usually in `../Frameworks/` relative to `sys._MEIPASS`).*

5.  **Create the `.dmg` Installer:** Use `create-dmg` to package the `.app` into a distributable disk image.
    ```bash
    create-dmg \
      --volname "PDF Compressor 安装程序" \
      --window-pos 200 120 \
      --window-size 600 400 \
      --icon-size 100 \
      --icon "PDFCompressor.app" 150 190 \
      --hide-extension "PDFCompressor.app" \
      --app-drop-link 450 190 \
      "dist/PDFCompressor_Installer.dmg" \
      "dist/PDFCompressor.app"
    ```

6.  **Distribute:** The resulting `dist/PDFCompressor_Installer.dmg` file can now be distributed to other macOS users.
