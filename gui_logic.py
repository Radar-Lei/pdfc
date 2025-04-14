# -*- coding: utf-8 -*-
"""
包含 CompressorGUI 的事件处理和逻辑函数。
"""
import os
import sys
import subprocess
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import Qt

# 导入工作线程，因为 start_compression 需要它
from compression_worker import CompressionThread

# 导入 Pillow 检查变量，虽然 Pillow 本身不在此处使用
# 但 _scan_and_update_ui 可能需要根据 PILLOW_AVAILABLE 调整行为（如果需要）
# from compression_worker import PILLOW_AVAILABLE # 或者从主 GUI 传入

# 尝试导入 GS_PATH，或者从主 GUI 传入
try:
    from pdf_compressor import get_ghostscript_path
    GS_PATH = get_ghostscript_path()
except (ImportError, FileNotFoundError):
    GS_PATH = None # 在 start_compression 中处理

# --- Input/Output Handling ---

def browse_input_files(gui_instance):
    """处理“选择文件”按钮点击，更新 GUI 状态。"""
    file_filter = "Supported Files (*.pdf *.jpg *.jpeg *.png *.bmp *.gif *.tiff);;All Files (*)"
    file_paths, _ = QFileDialog.getOpenFileNames(gui_instance, "选择一个或多个文件", "", file_filter)
    if file_paths:
        gui_instance.input_mode = 'files'
        gui_instance.files_to_process = file_paths
        gui_instance.input_path_display.setText(f"已选择 {len(file_paths)} 个文件")
        _scan_and_update_ui(gui_instance) # Scan selected files and update options

def browse_input_folder(gui_instance):
    """处理“选择文件夹”按钮点击，更新 GUI 状态。"""
    folder_path = QFileDialog.getExistingDirectory(gui_instance, "选择文件夹")
    if folder_path:
        gui_instance.input_mode = 'folder'
        gui_instance.files_to_process = [folder_path] # Store folder path in list
        gui_instance.input_path_display.setText(folder_path)
        _scan_and_update_ui(gui_instance) # Scan folder and update options

def browse_output_dir(gui_instance):
    """处理输出目录“浏览”按钮点击。"""
    dir_path = QFileDialog.getExistingDirectory(gui_instance, "选择输出文件夹",
                                                gui_instance.output_dir_edit.text() or os.path.expanduser("~"))
    if dir_path:
        gui_instance.output_dir_edit.setText(dir_path)

# --- Scanning and UI Update ---

def _scan_and_update_ui(gui_instance):
    """扫描当前输入（文件或文件夹）并相应地更新 UI。"""
    gui_instance.input_contains_pdf = False
    gui_instance.input_contains_image = False
    gui_instance.input_contains_png = False # Reset PNG flag
    files_found = []
    status_messages = []

    if gui_instance.input_mode == 'files':
        files_to_scan = gui_instance.files_to_process
        status_messages.append(f"扫描 {len(files_to_scan)} 个选定文件...")
    elif gui_instance.input_mode == 'folder':
        folder_path = gui_instance.files_to_process[0]
        files_to_scan = []
        status_messages.append(f"扫描文件夹: {folder_path}...")
        try:
            for root, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    # 检查扩展名以初步过滤
                    ext = os.path.splitext(filename)[1].lower()
                    supported_exts = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
                    if ext in supported_exts:
                        files_to_scan.append(os.path.join(root, filename))
        except Exception as e:
            QMessageBox.warning(gui_instance, "扫描错误", f"扫描文件夹时出错: {e}")
            gui_instance.input_mode = 'idle'
            gui_instance.input_path_display.clear()
            _update_options_ui(gui_instance) # Reset UI
            return
    else: # idle
        _update_options_ui(gui_instance)
        return

    supported_image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff']
    for f_path in files_to_scan:
        ext = os.path.splitext(f_path)[1].lower()
        if ext == '.pdf':
            gui_instance.input_contains_pdf = True
            files_found.append(f_path)
        elif ext in supported_image_exts:
            gui_instance.input_contains_image = True
            files_found.append(f_path)
            if ext == '.png': # Specifically check for PNG
                gui_instance.input_contains_png = True

    if not files_found:
         status_messages.append("未找到支持的 PDF 或图片文件。")
         QMessageBox.information(gui_instance, "扫描结果", "\n".join(status_messages))
         gui_instance.input_mode = 'idle' # Reset mode if nothing found
         # Optionally clear input display: gui_instance.input_path_display.clear()
    else:
         pdf_count = sum(1 for f in files_found if f.lower().endswith('.pdf'))
         img_count = len(files_found) - pdf_count
         png_count = sum(1 for f in files_found if f.lower().endswith('.png'))

         type_str = []
         if pdf_count > 0: type_str.append(f"{pdf_count} PDF")
         if img_count > 0: type_str.append(f"{img_count} 图片" + (f" ({png_count} PNG)" if png_count > 0 else ""))

         status_messages.append(f"找到 {len(files_found)} 个支持的文件 ({', '.join(type_str)})。")
         # Update the list of files to be actually processed
         gui_instance.files_to_process = files_found

    # Update status bar (optional, maybe remove if too verbose)
    # gui_instance.status_text.append("\n".join(status_messages))

    # Update the options UI based on scan results
    _update_options_ui(gui_instance)

def _update_options_ui(gui_instance):
    """根据扫描结果显示/隐藏选项。"""
    # PDF Options
    gui_instance.pdf_compress_label.setVisible(gui_instance.input_contains_pdf)
    gui_instance.pdf_compress_combo.setVisible(gui_instance.input_contains_pdf)
    show_pdf_dpi = gui_instance.input_contains_pdf and gui_instance.pdf_compress_combo.currentIndex() == 5
    gui_instance.pdf_custom_dpi_label.setVisible(show_pdf_dpi)
    gui_instance.pdf_custom_dpi_edit.setVisible(show_pdf_dpi)

    # Image Options (DPI for non-PNG)
    gui_instance.image_dpi_label.setVisible(gui_instance.input_contains_image)
    gui_instance.image_dpi_edit.setVisible(gui_instance.input_contains_image)

    # PNG Quality Options
    gui_instance.png_quality_label.setVisible(gui_instance.input_contains_png)
    gui_instance.png_quality_edit.setVisible(gui_instance.input_contains_png)

    # Backup checkbox
    is_single_file_input = gui_instance.input_mode == 'files' and len(gui_instance.files_to_process) == 1
    # Keep disabled as output dir is always required now
    gui_instance.backup_checkbox.setEnabled(False)

    # Adjust placeholder text
    if gui_instance.input_contains_pdf and gui_instance.input_contains_image:
        gui_instance.pdf_custom_dpi_edit.setPlaceholderText("输入 PDF DPI")
        gui_instance.image_dpi_edit.setPlaceholderText("输入图片 DPI")
    elif gui_instance.input_contains_pdf:
         gui_instance.pdf_custom_dpi_edit.setPlaceholderText("输入 DPI (例如 150)")
    elif gui_instance.input_contains_image:
         gui_instance.image_dpi_edit.setPlaceholderText("输入 DPI (JPG/BMP/GIF/TIFF)")

# --- Event Handlers ---

def handle_pdf_compression_change(gui_instance, index):
    """处理 PDF 压缩级别下拉框变化，显示/隐藏自定义 DPI 输入。"""
    show_pdf_dpi = gui_instance.input_contains_pdf and index == 5
    gui_instance.pdf_custom_dpi_label.setVisible(show_pdf_dpi)
    gui_instance.pdf_custom_dpi_edit.setVisible(show_pdf_dpi)

def clear_status_text(gui_instance):
    """清除状态文本区域的内容。"""
    gui_instance.status_text.clear()

# --- Drag and Drop ---

def dragEnterEvent(gui_instance, event):
    """处理拖入事件，接受包含 URL 的拖放。"""
    if event.mimeData().hasUrls():
        event.acceptProposedAction()

def dropEvent(gui_instance, event):
    """处理放下事件，获取文件/文件夹路径并更新 UI。"""
    urls = event.mimeData().urls()
    paths = [url.toLocalFile() for url in urls if url.isLocalFile()]

    if not paths:
        return

    # Filter out unsupported files immediately during drop? Maybe not, scan later.
    # paths = [p for p in paths if os.path.isdir(p) or os.path.splitext(p)[1].lower() in supported_exts]

    if len(paths) == 1 and os.path.isdir(paths[0]):
        # Single folder dropped
        gui_instance.input_mode = 'folder'
        gui_instance.files_to_process = paths # Store folder path
        gui_instance.input_path_display.setText(paths[0])
        _scan_and_update_ui(gui_instance)
    elif paths:
        # One or more files dropped (or maybe a mix, handle as files)
        # Filter out directories if multiple items are dropped
        files_only = [p for p in paths if os.path.isfile(p)]
        if not files_only:
             QMessageBox.warning(gui_instance, "拖放无效", "请拖放文件或单个文件夹。")
             return

        gui_instance.input_mode = 'files'
        gui_instance.files_to_process = files_only # Store list of files
        gui_instance.input_path_display.setText(f"已拖放 {len(files_only)} 个文件") # Update display
        _scan_and_update_ui(gui_instance) # Scan and update

# --- Compression Logic ---

def start_compression(gui_instance):
    """验证输入和选项，启动压缩线程。"""
    if GS_PATH is None:
         QMessageBox.critical(gui_instance, "错误", "未找到 Ghostscript 可执行文件。请确保已安装 Ghostscript 并将其添加至系统 PATH。")
         return

    # Validate input mode and files
    if gui_instance.input_mode == 'idle' or not gui_instance.files_to_process:
        QMessageBox.warning(gui_instance, "警告", "请先选择要压缩的文件或文件夹。")
        return

    # Validate output directory
    output_dir = gui_instance.output_dir_edit.text().strip()
    if not output_dir:
        QMessageBox.warning(gui_instance, "警告", "请选择一个输出文件夹。")
        return
    if not os.path.isdir(output_dir):
         # Try to create it? Or just warn? Let's warn for now.
         reply = QMessageBox.question(gui_instance, "确认", f"输出文件夹 '{output_dir}' 不存在。是否要创建它？",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
         if reply == QMessageBox.StandardButton.Yes:
             try:
                 os.makedirs(output_dir, exist_ok=True)
                 gui_instance.status_text.append(f"已创建输出文件夹: {output_dir}")
             except Exception as e:
                 QMessageBox.critical(gui_instance, "错误", f"无法创建输出文件夹: {e}")
                 return
         else:
             return # User chose not to create

    # Gather options
    pdf_power = -1
    pdf_custom_dpi = None
    image_custom_dpi = None
    png_quality = None

    if gui_instance.input_contains_pdf:
        pdf_power = gui_instance.pdf_compress_combo.currentIndex()
        if pdf_power == 5: # Custom PDF DPI
            pdf_dpi_str = gui_instance.pdf_custom_dpi_edit.text().strip()
            if not pdf_dpi_str:
                QMessageBox.warning(gui_instance, "警告", "请输入 PDF 的自定义 DPI 值。")
                return
            try:
                pdf_custom_dpi = int(pdf_dpi_str)
                if pdf_custom_dpi <= 0: raise ValueError("DPI 必须是正数")
            except ValueError:
                QMessageBox.warning(gui_instance, "警告", "无效的 PDF DPI 值。请输入一个正整数。")
                return

    if gui_instance.input_contains_image:
        img_dpi_str = gui_instance.image_dpi_edit.text().strip()
        # Only require DPI if non-PNG images are present
        contains_non_png = any(not f.lower().endswith('.png') for f in gui_instance.files_to_process if os.path.splitext(f)[1].lower() in ['.jpg', '.jpeg', '.bmp', '.gif', '.tiff'])
        if contains_non_png:
            if not img_dpi_str:
                 QMessageBox.warning(gui_instance, "警告", "请输入非 PNG 图片的 DPI 值。")
                 return
            try:
                 image_custom_dpi = int(img_dpi_str)
                 if image_custom_dpi <= 0: raise ValueError("DPI 必须是正数")
            except ValueError:
                 QMessageBox.warning(gui_instance, "警告", "无效的图片 DPI 值。请输入一个正整数。")
                 return
        elif img_dpi_str: # User entered DPI but only PNGs are present
             try: # Still validate if entered
                 image_custom_dpi = int(img_dpi_str)
                 if image_custom_dpi <= 0: raise ValueError("DPI 必须是正数")
                 # Inform user it won't be used for PNGs
                 gui_instance.status_text.append("提示: 输入的图片 DPI 值将不会应用于 PNG 文件。")
             except ValueError:
                 QMessageBox.warning(gui_instance, "警告", "无效的图片 DPI 值。请输入一个正整数。")
                 return


    if gui_instance.input_contains_png:
        png_quality_str = gui_instance.png_quality_edit.text().strip()
        if png_quality_str: # Only validate if user entered something
             try:
                 png_quality = int(png_quality_str)
                 if not (0 <= png_quality <= 100): raise ValueError("质量必须在 0-100 之间")
             except ValueError:
                  QMessageBox.warning(gui_instance, "警告", "无效的 PNG 质量值。请输入 0 到 100 之间的整数。")
                  return
        # If empty, png_quality remains None (worker uses default)

    # Disable button, clear status
    gui_instance.compress_btn.setEnabled(False)
    gui_instance.compress_btn.setText("压缩中...")
    # gui_instance.status_text.clear() # Keep previous messages? Maybe clear is better.
    gui_instance.status_text.append("-" * 20)
    gui_instance.status_text.append(f"准备压缩 {len(gui_instance.files_to_process)} 个文件到: {output_dir}")

    # Launch Thread
    gui_instance.compression_thread = CompressionThread(
        input_files=gui_instance.files_to_process,
        output_dir=output_dir,
        pdf_power=pdf_power,
        pdf_dpi=pdf_custom_dpi,
        image_dpi=image_custom_dpi, # Pass potentially validated DPI even if only PNGs
        png_quality=png_quality,
        gs_path=GS_PATH # Pass the validated Ghostscript path
    )
    # Connect signals in the main GUI class after creating the thread instance
    gui_instance.compression_thread.progress_signal.connect(gui_instance.update_status)
    gui_instance.compression_thread.finished_signal.connect(gui_instance.compression_finished)
    gui_instance.compression_thread.start()

def update_status(gui_instance, message):
    """将消息附加到状态文本区域并滚动到底部。"""
    gui_instance.status_text.append(message)
    gui_instance.status_text.ensureCursorVisible() # Scroll to bottom

def compression_finished(gui_instance, success, summary_message):
    """处理压缩线程完成信号。"""
    gui_instance.status_text.append("-" * 20) # Separator
    gui_instance.status_text.append(summary_message) # Show summary message from thread
    gui_instance.status_text.ensureCursorVisible()
    gui_instance.compress_btn.setEnabled(True)
    gui_instance.compress_btn.setText("开始压缩")

    # Show final message box
    if success:
        QMessageBox.information(gui_instance, "成功", summary_message)
        # Optional: Open output directory
        # try_open_directory(gui_instance.output_dir_edit.text())
    else:
        QMessageBox.critical(gui_instance, "失败或有错误", summary_message)

    gui_instance.compression_thread = None # Clean up thread reference

# --- Utility (Optional) ---
def try_open_directory(dir_path):
    """尝试在文件浏览器中打开目录。"""
    if not dir_path or not os.path.isdir(dir_path):
        return
    try:
        if sys.platform == "win32":
            os.startfile(dir_path)
        elif sys.platform == "darwin": # macOS
            subprocess.call(["open", dir_path])
        else: # linux variants
            subprocess.call(["xdg-open", dir_path])
    except Exception as e:
        print(f"无法打开输出目录 '{dir_path}': {e}")
        # Optionally show message to user via status bar if gui_instance is passed
