import sys
import os
import subprocess
# Removed traceback import, it's now in the worker
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QCheckBox, QMessageBox, QTextEdit
)
import shutil # Ensure shutil is imported
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator
# Import the worker thread
from compression_worker import CompressionThread, PILLOW_AVAILABLE
# Import UI creation functions
from gui_widgets import (
    create_input_section, create_output_section, create_options_section,
    create_action_button, create_status_section, create_author_label
)
# Import GUI logic functions
import gui_logic

# Try importing Pillow for image processing
try:
    from PIL import Image, UnidentifiedImageError
    # Optimize image saving if possible
    try:
        Image.MAX_IMAGE_PIXELS = None # Disable DecompressionBombError check if needed
    except AttributeError:
        pass # Ignore if the attribute doesn't exist
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    # We'll show a message later if needed

# --- Removed CompressionThread Class Definition ---
# pdf_compressor import and GS_PATH check moved to main_gui


class CompressorGUI(QWidget): # Rename class for generality
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件压缩小助手") # Change window title
        # Increased height further for new elements
        self.setGeometry(200, 200, 600, 500) # x, y, width, height

        # Initialize state variables *before* calling initUI
        self.compression_thread = None
        self.input_mode = 'idle' # 'idle', 'files', 'folder'
        self.files_to_process = []
        self.input_contains_pdf = False
        self.input_contains_image = False
        self.input_contains_png = False # New state variable for PNG detection

        self.initUI() # Now call initUI

    def initUI(self):
        layout = QVBoxLayout(self)

        # --- Input Selection (from gui_widgets) ---
        input_layout, self.input_path_display, self.input_browse_files_btn, self.input_browse_folder_btn = create_input_section(self)
        # Connect signals to gui_logic functions using lambda
        self.input_browse_files_btn.clicked.connect(lambda: gui_logic.browse_input_files(self))
        self.input_browse_folder_btn.clicked.connect(lambda: gui_logic.browse_input_folder(self))
        layout.addLayout(input_layout)

        # --- Output Directory (from gui_widgets) ---
        output_layout, self.output_dir_edit, self.output_browse_dir_btn = create_output_section(self)
        # Connect signal to gui_logic function using lambda
        self.output_browse_dir_btn.clicked.connect(lambda: gui_logic.browse_output_dir(self))
        layout.addLayout(output_layout)

        # --- Options (from gui_widgets) ---
        options_main_layout, self.option_widgets = create_options_section(self)
        # Store individual option widgets for easier access
        self.pdf_compress_label = self.option_widgets["pdf_compress_label"]
        self.pdf_compress_combo = self.option_widgets["pdf_compress_combo"]
        self.pdf_custom_dpi_label = self.option_widgets["pdf_custom_dpi_label"]
        self.pdf_custom_dpi_edit = self.option_widgets["pdf_custom_dpi_edit"]
        self.image_dpi_label = self.option_widgets["image_dpi_label"]
        self.image_dpi_edit = self.option_widgets["image_dpi_edit"]
        self.png_quality_label = self.option_widgets["png_quality_label"]
        self.png_quality_edit = self.option_widgets["png_quality_edit"]
        self.backup_checkbox = self.option_widgets["backup_checkbox"]
        # Connect signals for options
        # Connect signals for options to gui_logic functions
        # Use lambda to pass 'self' (the gui_instance) to the logic function
        self.pdf_compress_combo.currentIndexChanged.connect(
            lambda index: gui_logic.handle_pdf_compression_change(self, index)
        )
        layout.addLayout(options_main_layout)

        # --- Compress Button (from gui_widgets) ---
        self.compress_btn = create_action_button(self)
        self.compress_btn.clicked.connect(lambda: gui_logic.start_compression(self))
        layout.addWidget(self.compress_btn)

        # --- Status Area (from gui_widgets) ---
        status_layout, self.status_text, self.clear_status_btn = create_status_section(self)
        self.clear_status_btn.clicked.connect(lambda: gui_logic.clear_status_text(self))
        layout.addLayout(status_layout)
        layout.addWidget(self.status_text, 1) # Stretch factor

        # --- Drag and Drop ---
        self.setAcceptDrops(True)

        # --- Author Info (from gui_widgets) ---
        author_label = create_author_label(self)
        layout.addWidget(author_label)

        # Initialize UI state by calling the logic function
        gui_logic._update_options_ui(self)

    # --- Methods calling gui_logic functions ---

    # Input Selection Methods are now handled by connecting signals directly in initUI
    # to gui_logic functions (browse_input_files, browse_input_folder, browse_output_dir)

    # Scanning and UI Update Logic is now internal to gui_logic (_scan_and_update_ui, _update_options_ui)
    # We only need to keep the methods called by signals or events

    # --- Event Handlers calling gui_logic ---

    # handle_pdf_compression_change is handled by connecting the signal in initUI

    def dragEnterEvent(self, event):
        """Overrides dragEnterEvent to call the logic function."""
        gui_logic.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """Overrides dropEvent to call the logic function."""
        gui_logic.dropEvent(self, event)

    # start_compression is handled by connecting the signal in initUI

    def update_status(self, message):
        """Slot for progress_signal, calls the logic function."""
        gui_logic.update_status(self, message)

    def compression_finished(self, success, summary_message):
        """Slot for finished_signal, calls the logic function."""
        gui_logic.compression_finished(self, success, summary_message)

    # clear_status_text is handled by connecting the signal in initUI

# --- Main Execution ---
def main_gui():
    app = QApplication(sys.argv)
    # 你可以设置一个样式表，例如 'Fusion'
    # app.setStyle('Fusion')

    # --- Moved Checks Inside main_gui ---
    # 1. 尝试从 pdf_compressor 导入 compress 和 get_ghostscript_path 函数
    try:
        # It's better practice to import the module first, then access attributes
        import pdf_compressor
        # Now check for the specific functions if needed, or just use them later
        # compress_pdf = pdf_compressor.compress
        # get_ghostscript_path = pdf_compressor.get_ghostscript_path
    except ImportError:
        # Pass None as parent since the main window doesn't exist yet
        QMessageBox.critical(None, "Import 错误", "无法导入 'pdf_compressor.py'。\n请确保它与 'pdf_compressor_gui.py' 在同一目录或位于 Python 路径中。")
        sys.exit(1) # Exit after showing the message

    # 2. 检查 Ghostscript 是否安装 (using the imported function)
    try:
        # Use the function imported via pdf_compressor module
        GS_PATH = pdf_compressor.get_ghostscript_path()
        # Optionally store GS_PATH somewhere accessible if needed later,
        # maybe as a global variable or passed to the GUI instance.
        # For now, just checking is enough.
    except FileNotFoundError:
         # Pass None as parent
         QMessageBox.critical(None, "错误", "未找到 Ghostscript 可执行文件。请确保已安装 Ghostscript 并将其添加至系统 PATH。")
         sys.exit(1) # Exit after showing the message
    # --- End Moved Checks ---
    ex = CompressorGUI() # Use updated class name
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main_gui()
