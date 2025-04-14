# -*- coding: utf-8 -*-
"""
包含创建 CompressorGUI 各个 UI 部分的函数。
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QTextEdit
)
from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import Qt

def create_input_section(parent_widget):
    """创建文件/文件夹输入部分 UI"""
    layout = QHBoxLayout()
    input_label = QLabel("输入:", parent_widget)
    input_path_display = QLineEdit(parent_widget)
    input_path_display.setPlaceholderText("选择文件、文件夹或拖放...")
    input_browse_files_btn = QPushButton("选择文件...", parent_widget)
    input_browse_folder_btn = QPushButton("选择文件夹...", parent_widget)

    layout.addWidget(input_label)
    layout.addWidget(input_path_display, 1) # Give it stretch factor
    layout.addWidget(input_browse_files_btn)
    layout.addWidget(input_browse_folder_btn)

    # 返回包含控件的布局和控件本身的引用，以便主类可以连接信号
    return layout, input_path_display, input_browse_files_btn, input_browse_folder_btn

def create_output_section(parent_widget):
    """创建输出文件夹选择部分 UI"""
    layout = QHBoxLayout()
    output_dir_label = QLabel("输出到文件夹:", parent_widget)
    output_dir_edit = QLineEdit(parent_widget)
    output_dir_edit.setPlaceholderText("选择压缩文件保存的位置")
    output_browse_dir_btn = QPushButton("浏览...", parent_widget)

    layout.addWidget(output_dir_label)
    layout.addWidget(output_dir_edit)
    layout.addWidget(output_browse_dir_btn)

    # 返回布局和控件引用
    return layout, output_dir_edit, output_browse_dir_btn

def create_options_section(parent_widget):
    """创建压缩选项部分 UI"""
    options_main_layout = QVBoxLayout()
    options_main_layout.setSpacing(5)

    # --- PDF Options ---
    pdf_options_layout = QHBoxLayout()
    pdf_compress_label = QLabel("PDF 压缩级别:", parent_widget)
    pdf_compress_combo = QComboBox(parent_widget)
    pdf_compress_combo.addItems([
        "0: 默认 (类似 /screen)",
        "1: 印前 (高质量, 300dpi)",
        "2: 打印机 (高质量, 300dpi)",
        "3: 电子书 (低质量, 150dpi)",
        "4: 屏幕 (仅屏幕查看, 72dpi)",
        "5: 自定义 DPI..."
    ])
    pdf_compress_combo.setCurrentIndex(2) # 默认级别 2

    pdf_custom_dpi_label = QLabel("PDF 自定义 DPI:", parent_widget)
    pdf_custom_dpi_edit = QLineEdit(parent_widget)
    pdf_custom_dpi_edit.setPlaceholderText("输入 PDF DPI")
    pdf_custom_dpi_edit.setValidator(QIntValidator(1, 9999, parent_widget))
    pdf_custom_dpi_edit.setFixedWidth(100)
    pdf_custom_dpi_label.setVisible(False)
    pdf_custom_dpi_edit.setVisible(False)

    pdf_options_layout.addWidget(pdf_compress_label)
    pdf_options_layout.addWidget(pdf_compress_combo, 1)
    pdf_options_layout.addWidget(pdf_custom_dpi_label)
    pdf_options_layout.addWidget(pdf_custom_dpi_edit)
    pdf_options_layout.addStretch()
    options_main_layout.addLayout(pdf_options_layout)

    # --- Image Options (Non-PNG DPI) ---
    image_options_layout = QHBoxLayout()
    image_dpi_label = QLabel("图片 DPI (非 PNG):", parent_widget)
    image_dpi_edit = QLineEdit(parent_widget)
    image_dpi_edit.setPlaceholderText("输入 DPI (JPG/BMP/GIF/TIFF)")
    image_dpi_edit.setValidator(QIntValidator(1, 9999, parent_widget))
    image_dpi_edit.setFixedWidth(150)

    image_options_layout.addWidget(image_dpi_label)
    image_options_layout.addWidget(image_dpi_edit)
    image_options_layout.addStretch()
    options_main_layout.addLayout(image_options_layout)

    # --- PNG Quality Options ---
    png_options_layout = QHBoxLayout()
    png_quality_label = QLabel("PNG 质量 (0-100):", parent_widget)
    png_quality_edit = QLineEdit(parent_widget)
    png_quality_edit.setPlaceholderText("默认 (推荐 70-95)")
    png_quality_edit.setValidator(QIntValidator(0, 100, parent_widget))
    png_quality_edit.setFixedWidth(150)

    png_options_layout.addWidget(png_quality_label)
    png_options_layout.addWidget(png_quality_edit)
    png_options_layout.addStretch()
    options_main_layout.addLayout(png_options_layout)

    # --- Backup Checkbox ---
    backup_layout = QHBoxLayout()
    backup_checkbox = QCheckBox("覆盖时备份原文件 (仅限单文件输入)", parent_widget)
    backup_checkbox.setToolTip("仅当输入为单个文件且未指定输出文件夹时生效")
    backup_checkbox.setEnabled(False)
    backup_layout.addWidget(backup_checkbox)
    backup_layout.addStretch()
    options_main_layout.addLayout(backup_layout)

    # Initially hide all options
    pdf_compress_label.setVisible(False)
    pdf_compress_combo.setVisible(False)
    image_dpi_label.setVisible(False)
    image_dpi_edit.setVisible(False)
    png_quality_label.setVisible(False)
    png_quality_edit.setVisible(False)

    # 返回主布局和所有需要引用的控件
    return options_main_layout, {
        "pdf_compress_label": pdf_compress_label,
        "pdf_compress_combo": pdf_compress_combo,
        "pdf_custom_dpi_label": pdf_custom_dpi_label,
        "pdf_custom_dpi_edit": pdf_custom_dpi_edit,
        "image_dpi_label": image_dpi_label,
        "image_dpi_edit": image_dpi_edit,
        "png_quality_label": png_quality_label,
        "png_quality_edit": png_quality_edit,
        "backup_checkbox": backup_checkbox
    }

def create_action_button(parent_widget):
    """创建开始压缩按钮"""
    compress_btn = QPushButton("开始压缩", parent_widget)
    compress_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; font-size: 16px; }")
    return compress_btn

def create_status_section(parent_widget):
    """创建状态显示区域"""
    status_layout = QHBoxLayout()
    status_label = QLabel("状态:", parent_widget)
    clear_status_btn = QPushButton("清除状态", parent_widget)
    status_layout.addWidget(status_label)
    status_layout.addStretch()
    status_layout.addWidget(clear_status_btn)

    status_text = QTextEdit(parent_widget)
    status_text.setReadOnly(True)
    status_text.setPlaceholderText("压缩状态和结果将显示在这里...")

    # 返回包含标签和按钮的布局，以及文本区域和清除按钮的引用
    return status_layout, status_text, clear_status_btn

def create_author_label(parent_widget):
    """创建作者信息标签"""
    author_label = QLabel("Author: Lei Da | Contact: greatradar@gmail.com", parent_widget)
    author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    author_label.setStyleSheet("QLabel { color: grey; margin-top: 10px; }")
    return author_label
