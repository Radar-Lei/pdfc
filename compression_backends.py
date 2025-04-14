# -*- coding: utf-8 -*-
"""
包含实际执行文件压缩的后端函数。
"""
import os
import sys
import subprocess
import shutil
import traceback

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

def compress_pdf_backend(input_path, output_path, power, custom_dpi, gs_path, progress_signal):
    """
    使用 Ghostscript 处理 PDF 压缩。

    Args:
        input_path (str): 输入 PDF 文件路径。
        output_path (str): 输出 PDF 文件路径。
        power (int): PDF 压缩级别 (0-5)。
        custom_dpi (int | None): 自定义 DPI 值（如果 power 为 5）。
        gs_path (str): Ghostscript 可执行文件路径。
        progress_signal (pyqtSignal): 用于发送进度更新的信号。

    Returns:
        bool: 成功返回 True，失败返回 False。
    """
    base_name = os.path.basename(input_path)
    progress_signal.emit(f"  压缩 PDF: {base_name} (级别: {power}, DPI: {custom_dpi or '默认'})")

    quality_map = {
        0: "/default", 1: "/prepress", 2: "/printer",
        3: "/ebook", 4: "/screen"
    }

    command = [
        gs_path,
        "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}", input_path,
    ]

    actual_custom_dpi = None
    if power == 5:
        pdf_settings = "/printer" # Default for custom DPI mode
        if isinstance(custom_dpi, int) and custom_dpi > 0:
             actual_custom_dpi = custom_dpi
        else:
             # Keep pdf_settings as /printer if custom_dpi is invalid
             progress_signal.emit(f"  警告 ({base_name}): 无效的自定义 DPI 值 ({custom_dpi})，使用 /printer 默认设置。")
    else:
        pdf_settings = quality_map.get(power, "/default")

    command.insert(3, f"-dPDFSETTINGS={pdf_settings}")

    if actual_custom_dpi:
        # Insert DPI settings after PDFSETTINGS
        command.insert(4, f"-dGrayImageResolution={actual_custom_dpi}")
        command.insert(5, f"-dColorImageResolution={actual_custom_dpi}")
        # Update progress message to show the actual DPI being used
        progress_signal.emit(f"  压缩 PDF: {base_name} (级别: 5, 自定义 DPI: {actual_custom_dpi})")


    try:
        # Use Popen for better error handling and non-blocking potential if needed later
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        stdout, stderr = process.communicate() # Wait for completion

        if process.returncode != 0:
            print(f"--- Ghostscript Error ({base_name}) ---", file=sys.stderr)
            print(f"Return Code: {process.returncode}", file=sys.stderr)
            print(f"Command: {' '.join(command)}", file=sys.stderr) # Log command
            print(f"Stderr:\n{stderr}", file=sys.stderr)
            progress_signal.emit(f"错误: Ghostscript 压缩失败 ({base_name})。详情见终端。")
            # Clean up potentially empty/corrupt output file
            if os.path.exists(output_path):
                try: os.remove(output_path)
                except OSError: pass
            return False

        # Check if output file exists and is not empty
        if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
             print(f"--- Ghostscript Output Error ({base_name}) ---", file=sys.stderr)
             print(f"Command: {' '.join(command)}", file=sys.stderr)
             print(f"Stdout:\n{stdout}", file=sys.stderr)
             print(f"Stderr:\n{stderr}", file=sys.stderr)
             progress_signal.emit(f"错误: Ghostscript 未生成有效输出文件 ({base_name})。详情见终端。")
             if os.path.exists(output_path):
                 try: os.remove(output_path)
                 except OSError: pass
             return False

        # Calculate and report success
        try:
             initial_size = os.path.getsize(input_path)
             final_size = os.path.getsize(output_path)
             ratio = 1 - (final_size / initial_size) if initial_size > 0 else 0
             final_mb = final_size / 1000000
             progress_signal.emit(f"  成功 ({base_name}): {ratio:.0%} 压缩, {final_mb:.3f} MB")
        except Exception as size_err:
             progress_signal.emit(f"  成功 ({base_name}): 但无法计算大小 ({size_err})")

        return True

    except FileNotFoundError:
         error_details = traceback.format_exc()
         print(f"--- Ghostscript Not Found Error --- \n{error_details}", file=sys.stderr)
         progress_signal.emit(f"错误: 未找到 Ghostscript ({gs_path})。请确保已安装。")
         return False
    except Exception as e:
         error_details = traceback.format_exc()
         print(f"--- Ghostscript Execution Error ({base_name}) --- \n{error_details}", file=sys.stderr)
         progress_signal.emit(f"错误: 执行 Ghostscript 时出错 ({base_name}): {e}")
         # Clean up potentially empty/corrupt output file
         if os.path.exists(output_path):
             try: os.remove(output_path)
             except OSError: pass
         return False

def compress_image_backend(input_path, output_path, custom_dpi, png_quality, progress_signal):
    """
    处理图片压缩。使用 pngquant 处理 PNG（带质量），使用 Pillow 处理其他格式（带 DPI）。

    Args:
        input_path (str): 输入图片文件路径。
        output_path (str): 输出图片文件路径。
        custom_dpi (int | None): 目标 DPI（用于非 PNG 图片）。
        png_quality (int | None): PNG 压缩质量 (0-100)。
        progress_signal (pyqtSignal): 用于发送进度更新的信号。

    Returns:
        bool: 成功返回 True，失败返回 False。
    """
    base_name = os.path.basename(input_path)
    file_ext = os.path.splitext(input_path)[1].lower()

    if file_ext == '.png':
        # --- PNG Compression using pngquant ---
        quality_str = f"(质量: {png_quality})" if png_quality is not None else "(默认质量)"
        progress_signal.emit(f"  使用 pngquant 压缩 PNG: {base_name} {quality_str}")
        pngquant_path = "pngquant" # Assume pngquant is in PATH

        command = [
            pngquant_path,
            "--force",        # Overwrite output file if it exists
            "--skip-if-larger", # Don't save if the output is larger
            # "--strip",        # Remove metadata (optional)
        ]

        # Add quality argument if specified
        if png_quality is not None and 0 <= png_quality <= 100:
             # Format as min-max, using 0 as min for broader compatibility
             command.extend(["--quality", f"0-{png_quality}"])

        command.extend([
            "--output", output_path, # Specify output file
            "--",             # End of options marker
            input_path        # Input file
        ])

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
            stdout, stderr = process.communicate()

            # pngquant return codes:
            # 0: success
            # 98: skipped (e.g., --skip-if-larger)
            # 99: quality threshold not met (e.g., --quality)
            # Other non-zero: error

            if process.returncode == 0:
                # Verify output file existence and size
                if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                     print(f"--- pngquant Output Error ({base_name}) ---", file=sys.stderr)
                     print(f"Command: {' '.join(command)}", file=sys.stderr)
                     print(f"Stdout:\n{stdout}", file=sys.stderr)
                     print(f"Stderr:\n{stderr}", file=sys.stderr)
                     progress_signal.emit(f"错误 ({base_name}): pngquant 成功执行但未生成有效文件。")
                     if os.path.exists(output_path):
                         try: os.remove(output_path)
                         except OSError: pass
                     return False
                # Calculate and report success
                try:
                     initial_size = os.path.getsize(input_path)
                     final_size = os.path.getsize(output_path)
                     ratio = 1 - (final_size / initial_size) if initial_size > 0 else 0
                     final_mb = final_size / 1000000
                     progress_signal.emit(f"  成功 ({base_name}): {ratio:.0%} 压缩, {final_mb:.3f} MB")
                except Exception as size_err:
                     progress_signal.emit(f"  成功 ({base_name}): 但无法计算大小 ({size_err})")
                return True
            elif process.returncode == 98:
                progress_signal.emit(f"  跳过 ({base_name}): 压缩后的文件不会更小。将复制原始文件。")
                try:
                    shutil.copy2(input_path, output_path) # Copy original if skipped
                    return True
                except Exception as copy_err:
                    progress_signal.emit(f"错误 ({base_name}): 复制原始 PNG 文件失败: {copy_err}")
                    return False
            else: # Other non-zero return code indicates an error
                print(f"--- pngquant Error ({base_name}) ---", file=sys.stderr)
                print(f"Return Code: {process.returncode}", file=sys.stderr)
                print(f"Command: {' '.join(command)}", file=sys.stderr)
                print(f"Stderr:\n{stderr}", file=sys.stderr)
                progress_signal.emit(f"错误: pngquant 压缩失败 ({base_name})。详情见终端。")
                # Clean up potentially empty/corrupt output file
                if os.path.exists(output_path):
                    try: os.remove(output_path)
                    except OSError: pass
                return False

        except FileNotFoundError:
             error_details = traceback.format_exc()
             print(f"--- pngquant Not Found Error --- \n{error_details}", file=sys.stderr)
             progress_signal.emit(f"错误: 未找到 pngquant。请确保已安装并添加到系统 PATH。")
             return False
        except Exception as e:
             error_details = traceback.format_exc()
             print(f"--- pngquant Execution Error ({base_name}) --- \n{error_details}", file=sys.stderr)
             progress_signal.emit(f"错误: 执行 pngquant 时出错 ({base_name}): {e}")
             # Clean up potentially empty/corrupt output file
             if os.path.exists(output_path):
                 try: os.remove(output_path)
                 except OSError: pass
             return False

    else:
        # --- Non-PNG Image Compression using Pillow ---
        if not PILLOW_AVAILABLE:
            progress_signal.emit(f"错误 ({base_name}): 缺少 Pillow 库。无法处理非 PNG 图片。")
            return False

        # Validate DPI for non-PNG images
        if not isinstance(custom_dpi, int) or custom_dpi <= 0:
             progress_signal.emit(f"错误 ({base_name}): 无效的图片 DPI 值 ({custom_dpi})。需要为非 PNG 图片提供有效的正整数 DPI。")
             return False

        progress_signal.emit(f"  压缩图片 (非 PNG): {base_name} (目标 DPI: {custom_dpi})")

        try:
            img = Image.open(input_path)
            save_kwargs = {'dpi': (custom_dpi, custom_dpi)}
            # Determine Pillow format string from output path extension
            output_ext_upper = os.path.splitext(output_path)[1].upper()[1:]
            pillow_format = {"JPG": "JPEG", "TIF": "TIFF"}.get(output_ext_upper, output_ext_upper)

            # Handle format-specific options
            if pillow_format == 'JPEG':
                save_kwargs['quality'] = 85 # Standard JPEG quality
                save_kwargs['optimize'] = True
                # Convert RGBA or P mode images to RGB for JPEG saving
                if img.mode == 'RGBA' or img.mode == 'P':
                     progress_signal.emit(f"  信息 ({base_name}): 转换为 RGB 以保存为 JPEG。")
                     img = img.convert('RGB')
            elif pillow_format == 'TIFF':
                save_kwargs['compression'] = 'tiff_lzw' # Use LZW compression for TIFF

            # Save the image
            img.save(output_path, format=pillow_format, **save_kwargs)
            img.close()

            # Verify output file existence and size
            if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                 progress_signal.emit(f"错误 ({base_name}): Pillow 保存成功但未生成有效文件。")
                 if os.path.exists(output_path):
                     try: os.remove(output_path)
                     except OSError: pass
                 return False

            # Calculate and report success
            try:
                 initial_size = os.path.getsize(input_path)
                 final_size = os.path.getsize(output_path)
                 ratio = 1 - (final_size / initial_size) if initial_size > 0 else 0
                 final_mb = final_size / 1000000
                 progress_signal.emit(f"  成功 ({base_name}): {ratio:.0%} 压缩, {final_mb:.3f} MB")
            except Exception as size_err:
                 progress_signal.emit(f"  成功 ({base_name}): 但无法计算大小 ({size_err})")

            return True

        except UnidentifiedImageError:
            progress_signal.emit(f"错误 ({base_name}): 无法识别的图片格式。")
            return False
        except FileNotFoundError:
             progress_signal.emit(f"错误 ({base_name}): 输入文件未找到。")
             return False
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"--- Image Processing Error ({base_name}) --- \n{error_details}", file=sys.stderr)
            progress_signal.emit(f"错误 ({base_name}): 处理图片时出错: {e}")
            # Clean up potentially empty/corrupt output file
            if os.path.exists(output_path):
                try: os.remove(output_path)
                except OSError: pass
            return False
