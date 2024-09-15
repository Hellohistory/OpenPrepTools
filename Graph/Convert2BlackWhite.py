import json
import logging
import os
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count, Manager

import cv2
import fitz  # PyMuPDF
import numpy as np
from PyQt5 import QtWidgets, QtCore
from fpdf import FPDF
from rich.console import Console
from skimage.filters import threshold_sauvola

CONFIG_FILE = "config.json"  # 持久化配置文件路径

logger = logging.getLogger("PDFProcessor")
logger.setLevel(logging.INFO)

console = Console()


def load_config():
    default_config = {
        "output_folder": "",
        "scale_percent": 75,
        "window_size": 25,
        "k_value": 0.08,
        "skip_pages": ""
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return default_config


def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def extract_images_from_pdf(pdf_path, temp_folder, skip_pages, skipped_pages_folder):
    pdf_document = fitz.open(pdf_path)
    image_counter = 0

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)

        # 如果该页面是跳过的页面，则将其保存为图片或PDF
        if page_num + 1 in skip_pages:
            logger.info(f"跳过第 {page_num + 1} 页，直接保存页面。")
            skipped_page_path = os.path.join(skipped_pages_folder, f"skipped_page_{page_num + 1}.png")
            page_pix = page.get_pixmap()
            page_pix.save(skipped_page_path)
            continue

        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"image_{page_num:04d}_{img_index}.{image_ext}"
            image_path = os.path.join(temp_folder, image_filename)

            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)

            if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
                raise FileNotFoundError(f"图像提取失败或文件为空: {image_path}")

            image_counter += 1

    return image_counter


def process_image_with_progress(image_path, output_folder, scale_percent, window_size, k, progress_counter):
    try:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(f"无法读取图像: {image_path}")

        # 缩放图像
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        threshold_sauvola_val = threshold_sauvola(resized_image, window_size=window_size, k=k)
        binary_image = resized_image > threshold_sauvola_val
        binary_image = binary_image.astype(np.uint8) * 255

        filename = os.path.splitext(os.path.basename(image_path))[0]
        png_output_path = os.path.join(output_folder, f"{filename}.png")

        cv2.imwrite(png_output_path, binary_image, [cv2.IMWRITE_PNG_COMPRESSION, 9])

        # 更新进度计数
        progress_counter.value += 1

    except Exception as e:
        logger.error(f"处理图像时发生错误: {e}")
        raise


def process_images_concurrently(image_files, temp_image_folder, processed_folder, scale_percent, window_size, k):
    with Manager() as manager:
        progress_counter = manager.Value('i', 0)
        total_images = len(image_files)

        if total_images == 0:
            return

        with ProcessPoolExecutor(max_workers=max(1, cpu_count() // 2)) as executor:
            futures = []
            for filename in image_files:
                image_path = os.path.join(temp_image_folder, filename)
                future = executor.submit(process_image_with_progress, image_path, processed_folder,
                                         scale_percent, window_size, k, progress_counter)
                futures.append(future)

            while progress_counter.value < total_images:
                print(f"当前进度: {progress_counter.value}/{total_images}")
                QtCore.QThread.msleep(100)

            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"处理图片时发生错误: {e}")


def create_pdf_from_images(image_folder, skipped_pages_folder, output_pdf_path):
    pdf = FPDF()
    image_files = sorted(
        [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))])
    skipped_page_files = sorted(
        [f for f in os.listdir(skipped_pages_folder) if f.lower().endswith('.png')])

    for skipped_page in skipped_page_files:
        pdf.add_page()
        skipped_page_path = os.path.join(skipped_pages_folder, skipped_page)
        pdf.image(skipped_page_path)

    for filename in image_files:
        image_path = os.path.join(image_folder, filename)
        pdf.add_page()

        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"无法读取图像: {image_path}")
            continue

        img_height, img_width = image.shape[:2]
        pdf_w, pdf_h = pdf.w, pdf.h

        ratio = min(pdf_w / img_width, pdf_h / img_height)
        img_w = img_width * ratio
        img_h = img_height * ratio

        x = (pdf_w - img_w) / 2
        y = (pdf_h - img_h) / 2

        pdf.image(image_path, x, y, img_w, img_h)

    pdf.output(output_pdf_path, "F")


class PDFProcessorThread(QtCore.QThread):
    progress_signal = QtCore.pyqtSignal(int)
    log_signal = QtCore.pyqtSignal(str)

    def __init__(self, pdf_path, output_folder, skip_pages, scale_percent=75, window_size=25, k=0.08):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_folder = output_folder
        self.skip_pages = skip_pages
        self.scale_percent = scale_percent
        self.window_size = window_size
        self.k = k

    def run(self):
        input_pdf_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        output_pdf_path = os.path.join(self.output_folder, f'{input_pdf_name}_processed.pdf')

        self.log_signal.emit(f"开始处理PDF文件: {self.pdf_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_image_folder = os.path.join(temp_dir, 'temp_images')
            processed_folder = os.path.join(temp_dir, 'processed_images')
            skipped_pages_folder = os.path.join(temp_dir, 'skipped_pages')

            os.makedirs(temp_image_folder, exist_ok=True)
            os.makedirs(processed_folder, exist_ok=True)
            os.makedirs(skipped_pages_folder, exist_ok=True)

            self.log_signal.emit("开始提取图片和跳过页面...")

            try:
                image_count = extract_images_from_pdf(self.pdf_path, temp_image_folder, self.skip_pages,
                                                      skipped_pages_folder)
            except Exception as e:
                self.log_signal.emit(f"提取图片时发生错误: {e}")
                return
            self.log_signal.emit(f"提取了 {image_count} 张图片。")

            if image_count == 0:
                self.log_signal.emit("未找到任何图片，处理终止。")
                return

            self.log_signal.emit("开始处理图片...")

            with Manager() as manager:
                progress_counter = manager.Value('i', 0)
                image_files = [f for f in os.listdir(temp_image_folder) if
                               f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
                total_images = len(image_files)

                if total_images == 0:
                    self.log_signal.emit("未找到要处理的图片。")
                    return

                with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
                    futures = []
                    for filename in image_files:
                        image_path = os.path.join(temp_image_folder, filename)
                        future = executor.submit(process_image_with_progress, image_path, processed_folder,
                                                 self.scale_percent, self.window_size, self.k, progress_counter)
                        futures.append(future)

                    while progress_counter.value < total_images:
                        # 实时更新进度条
                        self.progress_signal.emit(int((progress_counter.value / total_images) * 100))
                        self.msleep(100)

                    # 确保所有进程已完成
                    for future in futures:
                        try:
                            future.result()
                        except Exception as e:
                            self.log_signal.emit(f"处理图片时发生错误: {e}")

            self.log_signal.emit("图片处理完成，开始生成PDF...")
            create_pdf_from_images(processed_folder, skipped_pages_folder, output_pdf_path)
            self.log_signal.emit(f"PDF生成完成: {output_pdf_path}")
            self.progress_signal.emit(100)


class PDFProcessorGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('PDF转黑白')
        self.setGeometry(100, 100, 600, 400)

        layout = QtWidgets.QVBoxLayout()

        self.mode_label = QtWidgets.QLabel('请选择处理模式:')
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(['1-单个PDF', '2-多个PDF', '3-文件夹模式'])
        self.mode_combo.currentIndexChanged.connect(self.change_mode)

        self.input_label = QtWidgets.QLabel('输入文件路径:')
        self.input_line_edit = QtWidgets.QLineEdit()
        self.input_button = QtWidgets.QPushButton('浏览')
        self.input_button.clicked.connect(self.browse_input)

        self.output_label = QtWidgets.QLabel('输出文件夹路径:')
        self.output_line_edit = QtWidgets.QLineEdit()
        self.output_button = QtWidgets.QPushButton('浏览')
        self.output_button.clicked.connect(self.browse_output)
        self.output_line_edit.setText(self.config.get("output_folder", ""))

        self.scale_label = QtWidgets.QLabel('缩放比例（默认75）:')
        self.scale_spinbox = QtWidgets.QSpinBox()
        self.scale_spinbox.setRange(1, 100)
        self.scale_spinbox.setValue(self.config.get("scale_percent", 75))

        self.window_size_label = QtWidgets.QLabel('窗口大小（默认25）:')
        self.window_size_spinbox = QtWidgets.QSpinBox()
        self.window_size_spinbox.setRange(1, 100)
        self.window_size_spinbox.setValue(self.config.get("window_size", 25))

        self.k_label = QtWidgets.QLabel('k值（默认0.08）:')
        self.k_double_spinbox = QtWidgets.QDoubleSpinBox()
        self.k_double_spinbox.setRange(0.01, 1.0)
        self.k_double_spinbox.setSingleStep(0.01)
        self.k_double_spinbox.setValue(self.config.get("k_value", 0.08))

        self.skip_pages_label = QtWidgets.QLabel('跳过页码 (例如 1,3,5):')
        self.skip_pages_line_edit = QtWidgets.QLineEdit()
        self.skip_pages_line_edit.setText(self.config.get("skip_pages", ""))

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)

        self.start_button = QtWidgets.QPushButton('开始处理')
        self.start_button.clicked.connect(self.start_processing)

        self.log_text_edit = QtWidgets.QTextEdit()
        self.log_text_edit.setReadOnly(True)

        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.input_line_edit)
        input_layout.addWidget(self.input_button)

        output_layout = QtWidgets.QHBoxLayout()
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(self.output_button)

        parameter_layout = QtWidgets.QGridLayout()
        parameter_layout.addWidget(self.scale_label, 0, 0)
        parameter_layout.addWidget(self.scale_spinbox, 0, 1)
        parameter_layout.addWidget(self.window_size_label, 1, 0)
        parameter_layout.addWidget(self.window_size_spinbox, 1, 1)
        parameter_layout.addWidget(self.k_label, 2, 0)
        parameter_layout.addWidget(self.k_double_spinbox, 2, 1)

        layout.addWidget(self.mode_label)
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.input_label)
        layout.addLayout(input_layout)
        layout.addWidget(self.output_label)
        layout.addLayout(output_layout)
        layout.addLayout(parameter_layout)
        layout.addWidget(self.skip_pages_label)
        layout.addWidget(self.skip_pages_line_edit)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.start_button)
        layout.addWidget(QtWidgets.QLabel('日志输出:'))
        layout.addWidget(self.log_text_edit)

        self.setLayout(layout)

    def change_mode(self):
        mode = self.mode_combo.currentIndex()
        if mode == 0:
            self.input_label.setText('输入PDF文件路径:')
        elif mode == 1:
            self.input_label.setText('输入多个PDF文件路径（逗号分隔）:')
        elif mode == 2:
            self.input_label.setText('输入PDF文件夹路径:')

    def browse_input(self):
        mode = self.mode_combo.currentIndex()
        if mode == 0:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, '选择PDF文件', '', 'PDF Files (*.pdf)')
            if file_path:
                self.input_line_edit.setText(file_path)
        elif mode == 1:
            files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, '选择多个PDF文件', '', 'PDF Files (*.pdf)')
            if files:
                self.input_line_edit.setText(','.join(files))
        elif mode == 2:
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, '选择PDF文件夹')
            if folder:
                self.input_line_edit.setText(folder)

    def browse_output(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, '选择输出文件夹')
        if folder:
            self.output_line_edit.setText(folder)

    def start_processing(self):
        input_path = self.input_line_edit.text()
        output_folder = self.output_line_edit.text()
        scale_percent = self.scale_spinbox.value()
        window_size = self.window_size_spinbox.value()
        k = self.k_double_spinbox.value()

        # 检查输入路径和输出路径
        if not input_path or not output_folder:
            QtWidgets.QMessageBox.warning(self, '警告', '请输入有效的输入路径和输出文件夹。')
            return

        # 检查输出文件夹是否可写
        if not os.access(output_folder, os.W_OK):
            QtWidgets.QMessageBox.warning(self, '警告', '输出文件夹不可写，请选择其他文件夹。')
            return

        skip_pages_input = self.skip_pages_line_edit.text()
        skip_pages = set()
        if skip_pages_input:
            try:
                skip_pages = {int(page.strip()) for page in skip_pages_input.split(',')}
            except ValueError:
                QtWidgets.QMessageBox.warning(self, '警告', '请输入有效的页码，例如: 1,3,5')
                return

        # 更新并保存配置
        self.config.update({
            "output_folder": output_folder,
            "scale_percent": scale_percent,
            "window_size": window_size,
            "k_value": k,
            "skip_pages": skip_pages_input
        })
        save_config(self.config)

        self.thread = PDFProcessorThread(input_path, output_folder, skip_pages, scale_percent, window_size, k)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.log_signal.connect(self.update_log)
        self.thread.finished.connect(lambda: QtWidgets.QMessageBox.information(self, '完成', '处理完成'))
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_text_edit.append(message)
        self.log_text_edit.ensureCursorVisible()


class QtLogHandler(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        QtCore.QMetaObject.invokeMethod(self.text_edit, "append", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, msg))
        self.text_edit.ensureCursorVisible()


def main():
    app = QtWidgets.QApplication(sys.argv)
    gui = PDFProcessorGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
