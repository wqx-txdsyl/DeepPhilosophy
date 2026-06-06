"""
文档加载模块 —— 支持 PDF / EPUB / TXT 格式
智能判断：文本型PDF直接提取 / 扫描型PDF OCR识别
递归扫描知识库目录，保留哲学家分类元数据
"""
import os
import re
import tempfile
from pathlib import Path
from loguru import logger

from config import KNOWLEDGE_DIR
from modules.ocr_engine import OCREngine


class DocumentLoader:
    """文档加载器：负责从多种格式的文档中提取文本"""

    MIN_TEXT_PER_PAGE = 50  # 判定扫描件的阈值

    def __init__(self, ocr_engine: OCREngine | None = None):
        self.ocr_engine = ocr_engine or OCREngine()

    # ================================================================
    # 文件类型判断
    # ================================================================
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """根据扩展名判断文件类型"""
        ext = Path(file_path).suffix.lower()
        type_map = {
            ".pdf": "pdf",
            ".epub": "epub",
            ".txt": "txt",
            ".md": "txt",
            ".text": "txt",
        }
        return type_map.get(ext, "unknown")

    # ================================================================
    # 主入口：加载任意文件
    # ================================================================
    def load_file(self, file_path: str) -> dict[int, str]:
        """
        根据文件类型自动选择加载策略

        Returns:
            {页码: 文本内容} 字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_type = self.get_file_type(file_path)
        filename = os.path.basename(file_path)
        logger.info(f"加载 [{file_type}] {filename}")

        if file_type == "pdf":
            return self._load_pdf(file_path)
        elif file_type == "epub":
            return self._load_epub(file_path)
        elif file_type == "txt":
            return self._load_txt(file_path)
        else:
            logger.warning(f"不支持的文件类型: {file_path}")
            return {}

    # ================================================================
    # TXT 加载
    # ================================================================
    def _load_txt(self, file_path: str) -> dict[int, str]:
        """加载纯文本文件"""
        encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    text = f.read()
                logger.info(f"TXT 加载完成 (编码: {enc}): {len(text)} 字符")
                return {1: text}
            except UnicodeDecodeError:
                continue
        logger.error(f"无法解码 TXT 文件: {file_path}")
        return {}

    # ================================================================
    # EPUB 加载
    # ================================================================
    def _load_epub(self, file_path: str) -> dict[int, str]:
        """加载 EPUB 电子书"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            import html2text

            book = epub.read_epub(file_path)
            h2t = html2text.HTML2Text()
            h2t.ignore_links = True
            h2t.ignore_images = True
            h2t.body_width = 0  # 不自动换行

            pages = {}
            page_num = 0

            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                try:
                    content = item.get_content()
                    soup = BeautifulSoup(content, "html.parser")

                    # 移除脚本和样式
                    for tag in soup(["script", "style", "nav"]):
                        tag.decompose()

                    # 提取文本
                    html_str = str(soup)
                    text = h2t.handle(html_str)

                    # 清理多余空行
                    text = re.sub(r"\n{3,}", "\n\n", text)
                    text = text.strip()

                    if len(text) > 50:  # 过滤太短的章节
                        page_num += 1
                        pages[page_num] = text
                except Exception as e:
                    logger.debug(f"EPUB 章节解析跳过: {e}")

            logger.info(f"EPUB 加载完成: {page_num} 个章节, {sum(len(t) for t in pages.values())} 字符")
            return pages

        except ImportError:
            logger.error("ebooklib/beautifulsoup4 未安装！请运行: pip install ebooklib beautifulsoup4 html2text")
            return {}
        except Exception as e:
            logger.error(f"EPUB 加载失败 [{file_path}]: {e}")
            return {}

    # ================================================================
    # PDF 加载
    # ================================================================
    def _load_pdf(self, file_path: str) -> dict[int, str]:
        """加载 PDF 文件（自动判断文本型/扫描型）"""
        filename = os.path.basename(file_path)

        # 第一步：pdfplumber 直接提取
        text_pages = self._extract_with_pdfplumber(file_path)

        # 第二步：判断是否需要 OCR
        total_pages = self._get_pdf_page_count(file_path)
        pages_with_text = sum(
            1 for t in text_pages.values()
            if len(t.strip()) >= self.MIN_TEXT_PER_PAGE
        )

        if total_pages > 0 and pages_with_text < total_pages * 0.5:
            logger.info(
                f"  检测到扫描件（有文本页 {pages_with_text}/{total_pages}），"
                f"启动 OCR..."
            )
            ocr_pages = self._extract_with_ocr(file_path)
            for page_num, ocr_text in ocr_pages.items():
                if page_num not in text_pages or \
                   len(text_pages[page_num].strip()) < self.MIN_TEXT_PER_PAGE:
                    text_pages[page_num] = ocr_text

        # 第三步：清理空页
        text_pages = {p: t for p, t in text_pages.items() if len(t.strip()) > 0}
        return text_pages

    def _extract_with_pdfplumber(self, file_path: str) -> dict[int, str]:
        """pdfplumber 文本提取"""
        try:
            import pdfplumber
            pages = {}
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    pages[i] = text
            return pages
        except Exception as e:
            logger.error(f"pdfplumber 提取失败: {e}")
            return {}

    def _extract_with_ocr(self, file_path: str) -> dict[int, str]:
        """OCR 识别（扫描件）"""
        if not self.ocr_engine or not self.ocr_engine.ready:
            logger.warning("OCR 引擎未就绪")
            return {}

        try:
            import fitz
            doc = fitz.open(file_path)
            pages = {}
            for i, page in enumerate(doc, 1):
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(img_bytes)
                    tmp_path = tmp.name
                try:
                    text = self.ocr_engine.extract_text_from_image(tmp_path)
                    pages[i] = text
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            doc.close()
            return pages
        except Exception as e:
            logger.error(f"OCR 提取异常: {e}")
            return {}

    def _get_pdf_page_count(self, file_path: str) -> int:
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages)
        except Exception:
            return 0

    # ================================================================
    # 批量加载：递归扫描知识库
    # ================================================================
    def load_all_from_knowledge_dir(
        self, base_dir: str | None = None,
        file_types: tuple = ("pdf", "epub", "txt"),
    ) -> dict[str, dict[int, str]]:
        """
        递归扫描知识库目录，加载所有支持的文档

        Args:
            base_dir: 知识库根目录，默认从 config 读取
            file_types: 要加载的文件类型

        Returns:
            {相对路径/文件名: {页码: 文本}} 嵌套字典
        """
        base_dir = base_dir or KNOWLEDGE_DIR

        if not os.path.exists(base_dir):
            logger.error(f"知识库目录不存在: {base_dir}")
            return {}

        # 收集所有匹配的文件
        all_files = []
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                ext = Path(f).suffix.lower()
                ftype = {
                    ".pdf": "pdf", ".epub": "epub",
                    ".txt": "txt", ".md": "txt", ".text": "txt",
                }.get(ext, None)
                if ftype in file_types:
                    all_files.append(os.path.join(root, f))

        if not all_files:
            logger.info(f"知识库目录中没有匹配的文件: {base_dir}")
            return {}

        logger.info(f"发现 {len(all_files)} 个文件待加载")

        all_docs = {}
        for i, file_path in enumerate(all_files, 1):
            # 生成可读的相对路径名
            rel_path = os.path.relpath(file_path, base_dir)
            name = rel_path.replace("\\", "/")  # 统一斜杠

            logger.info(f"[{i}/{len(all_files)}] {name}")
            try:
                pages = self.load_file(file_path)
                if pages:
                    all_docs[name] = pages
            except Exception as e:
                logger.error(f"加载失败 [{name}]: {e}")

        total_pages = sum(len(p) for p in all_docs.values())
        logger.info(f"批量加载完成: {len(all_docs)} 个文档, {total_pages} 页/章节")
        return all_docs

    # ================================================================
    # 工具方法
    # ================================================================
    @staticmethod
    def merge_pages_to_text(pages: dict[int, str]) -> str:
        """将分页文本合并为完整文档"""
        merged = []
        for page_num in sorted(pages.keys()):
            merged.append(f"--- 第 {page_num} 页/章节 ---\n{pages[page_num]}")
        return "\n\n".join(merged)

    @staticmethod
    def extract_category(rel_path: str) -> str:
        """从相对路径提取分类（如 '西方/尼采/xxx.pdf' → '西方/尼采'）"""
        parts = rel_path.replace("\\", "/").split("/")
        if len(parts) >= 2:
            return "/".join(parts[:-1])  # 去掉文件名
        return ""
