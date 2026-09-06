#!/bin/bash
export PYTHONIOENCODING=utf-8
cd "$(dirname "$0")"
python ocr_runner.py "F:/philosophy/西方/戈特洛布·弗雷格/算术基础.pdf" "F:/program/Python/DeepPhilosophy/backend/tools/_tmp/mia_batch/suanshu_ocr.txt"
python ocr_runner.py "F:/philosophy/西方/卡尔·波普尔/科学发现的逻辑.pdf" "F:/program/Python/DeepPhilosophy/backend/tools/_tmp/mia_batch/kexue_ocr.txt"
echo "QUEUE2-ALL-DONE"
