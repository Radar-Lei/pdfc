import os
import subprocess
import sys # Import sys for stderr output in case of unexpected errors
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

# Import backend compression functions
from compression_backends import compress_pdf_backend, compress_image_backend, PILLOW_AVAILABLE

# Pillow import is now handled in compression_backends.py
# We just import the PILLOW_AVAILABLE flag from there.
# try:
#     from PIL import Image, UnidentifiedImageError
#     # Optimize image saving if possible
#     try:
#         Image.MAX_IMAGE_PIXELS = None # Disable DecompressionBombError check if needed
#     except AttributeError:
#         pass # Ignore if the attribute doesn't exist
# except ImportError:
#     # This case is handled by PILLOW_AVAILABLE flag from backend
#     pass

class CompressionThread(QThread):
    """在单独的线程中运行压缩，调用后端函数执行实际工作"""
    progress_signal = pyqtSignal(str) # For individual file progress/errors
    finished_signal = pyqtSignal(bool, str) # Overall success (bool), summary message (str)

    # Modified __init__ to accept gs_path and png_quality
    def __init__(self, input_files, output_dir, pdf_power, pdf_dpi, image_dpi, png_quality, gs_path):
        super().__init__()
        self.input_files = input_files # List of absolute file paths
        self.output_dir = output_dir
        self.pdf_power = pdf_power # PDF quality index (-1 if not applicable)
        self.pdf_dpi = pdf_dpi     # PDF custom DPI (None if not applicable/set)
        self.image_dpi = image_dpi   # Image DPI (None if not applicable/set, applies to non-PNG)
        self.png_quality = png_quality # PNG quality (0-100, None if not applicable/set)
        self.gs_path = gs_path     # Store Ghostscript path

    def run(self):
        success_count = 0
        error_count = 0
        processed_files = 0
        total_files = len(self.input_files)
        supported_image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']

        self.progress_signal.emit(f"开始处理 {total_files} 个文件...")

        for i, input_path in enumerate(self.input_files):
            processed_files += 1
            base_name = os.path.basename(input_path)
            self.progress_signal.emit(f"({processed_files}/{total_files}) 处理中: {base_name}")

            # Determine file type
            file_ext = os.path.splitext(input_path)[1].lower()
            is_pdf = file_ext == '.pdf'
            is_image = file_ext in supported_image_exts

            if not is_pdf and not is_image:
                self.progress_signal.emit(f"跳过不支持的文件: {base_name}")
                continue # Skip unsupported files silently in batch mode

            # Construct output path
            output_base_name = f"{os.path.splitext(base_name)[0]}_compressed{file_ext}"
            output_path = os.path.join(self.output_dir, output_base_name)

            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            except Exception as e:
                 self.progress_signal.emit(f"错误: 无法创建输出子目录 {os.path.dirname(output_path)} for {base_name}: {e}")
                 error_count += 1
                 continue

            counter = 1
            while os.path.exists(output_path):
                 output_base_name = f"{os.path.splitext(base_name)[0]}_compressed_{counter}{file_ext}"
                 output_path = os.path.join(self.output_dir, output_base_name)
                 counter += 1

            try:
                if is_pdf and self.pdf_power != -1:
                    # Call backend function for PDF compression
                    if compress_pdf_backend(input_path, output_path, self.pdf_power, self.pdf_dpi, self.gs_path, self.progress_signal):
                        success_count += 1
                    else:
                        error_count += 1
                elif is_image:
                    # Call backend function for image compression
                    # Pass both image_dpi (for non-PNG) and png_quality (for PNG)
                    if compress_image_backend(input_path, output_path, self.image_dpi, self.png_quality, self.progress_signal):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    self.progress_signal.emit(f"跳过: {base_name} (无适用压缩设置)")

            except Exception as e:
                error_details = traceback.format_exc()
                print(f"--- Unexpected Error Processing {base_name} --- \n{error_details}", file=sys.stderr)
                self.progress_signal.emit(f"处理 {base_name} 时发生意外错误: {e}")
                error_count += 1

        summary_message = f"处理完成。\n成功: {success_count}\n失败: {error_count}\n总计: {total_files}"
        # Determine overall success based on errors, even if some succeeded
        overall_success = error_count == 0 and success_count > 0 # Or just error_count == 0? Let's keep original logic.
        self.finished_signal.emit(overall_success, summary_message)

    # _compress_pdf and _compress_image methods are removed,
    # their logic is now in compression_backends.py
