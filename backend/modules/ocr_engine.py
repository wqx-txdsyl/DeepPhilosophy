"""
OCR 引擎模块 —— 基于 PaddleOCR 的文字识别
支持：扫描版PDF、图片中的中文文字提取
"""
import os
from pathlib import Path
from loguru import logger

from config import EXTRACTED_DIR


class OCREngine:
    """OCR 识别引擎，封装 PaddleOCR 的文字识别能力"""

    def __init__(self):
        """
        初始化 PaddleOCR 引擎
        使用 PP-OCRv4 模型，CPU 推理模式
        """
        try:
            from paddleocr import PaddleOCR
            # PaddleOCR 2.x: 使用 PP-OCRv4 中文模型，CPU 推理
            self.ocr = PaddleOCR(
                use_angle_cls=True,   # 启用文本方向分类
                lang="ch",            # 中文识别
                use_gpu=False,        # CPU 推理
                show_log=False,       # 关闭调试日志
            )
            self.ready = True
            logger.info("PaddleOCR 引擎初始化成功 (PP-OCRv4, CPU模式)")
        except ImportError:
            logger.error(
                "PaddleOCR 未安装！请运行: pip install paddlepaddle paddleocr"
            )
            self.ocr = None
            self.ready = False
        except Exception as e:
            logger.error(f"PaddleOCR 初始化失败: {e}")
            self.ocr = None
            self.ready = False

    def extract_text_from_image(self, image_path: str) -> str:
        """
        对单张图片执行 OCR 识别

        Args:
            image_path: 图片文件路径

        Returns:
            识别出的文字文本，每行一个识别结果
        """
        if not self.ready:
            raise RuntimeError("PaddleOCR 引擎未就绪，无法执行识别")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        try:
            result = self.ocr.ocr(image_path)

            if not result or not result[0]:
                logger.warning(f"OCR 未识别到文字: {image_path}")
                return ""

            # 提取所有识别文字，按行拼接
            lines = []
            for line_info in result[0]:
                text = line_info[1][0]  # line_info结构: [[[坐标]], [文字, 置信度]]
                confidence = line_info[1][1]
                if confidence > 0.5:  # 过滤低置信度结果
                    lines.append(text)

            extracted_text = "\n".join(lines)
            logger.info(
                f"OCR 识别完成: {image_path} -> {len(lines)}行文字"
            )
            return extracted_text

        except Exception as e:
            logger.error(f"OCR 识别异常: {image_path}, 错误: {e}")
            return ""

    def extract_text_from_images(self, image_paths: list[str]) -> dict:
        """
        批量 OCR 识别多张图片（对应多页扫描PDF）

        Args:
            image_paths: 图片文件路径列表

        Returns:
            {图片路径: 识别文字} 字典
        """
        results = {}
        total = len(image_paths)
        for i, img_path in enumerate(image_paths, 1):
            logger.info(f"OCR 处理中 [{i}/{total}]: {img_path}")
            text = self.extract_text_from_image(img_path)
            results[img_path] = text
        return results

    def save_extracted_text(
        self, text: str, source_name: str
    ) -> str:
        """
        将 OCR 提取的文本保存为 txt 文件

        Args:
            text: 提取的文字内容
            source_name: 来源文件名（不含扩展名）

        Returns:
            保存的 txt 文件路径
        """
        os.makedirs(EXTRACTED_DIR, exist_ok=True)
        output_path = os.path.join(EXTRACTED_DIR, f"{source_name}.txt")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"文本已保存: {output_path}")
        return output_path
