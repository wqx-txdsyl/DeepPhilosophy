#!/bin/bash
export PYTHONIOENCODING=utf-8
cd "$(dirname "$0")"
python ocr_runner.py "F:/philosophy/西方/威拉德·范·奥曼·蒯因/语词和对象.pdf" "F:/program/Python/DeepPhilosophy/backend/tools/_tmp/mia_batch/yuci_ocr.txt"
python ocr_runner.py "F:/philosophy/西方/安东尼奥·葛兰西/狱中札记.pdf" "F:/program/Python/DeepPhilosophy/backend/tools/_tmp/mia_batch/yuzhongzhaji_ocr.txt"
python ocr_runner.py "F:/philosophy/西方/托马斯·库恩/科学革命的结构.pdf" "F:/program/Python/DeepPhilosophy/backend/tools/_tmp/mia_batch/kexuegeming_ocr.txt"
python ocr_runner.py "F:/philosophy/西方/戈特洛布·弗雷格/算术基础.pdf" "F:/program/Python/DeepPhilosophy/backend/tools/_tmp/mia_batch/suanshu_ocr.txt"
echo "QUEUE3-ALL-DONE"
