#!/bin/bash
export PYTHONIOENCODING=utf-8
cd "$(dirname "$0")"
python ocr_runner.py "F:/philosophy/西方/埃德蒙德·胡塞尔/逻辑研究.pdf" "F:/program/Python/DeepPhilosophy/backend/tools/_tmp/mia_batch/luoji_ocr.txt"
python ocr_runner.py "F:/philosophy/西方/约翰·洛克/人类理解论.pdf" "F:/program/Python/DeepPhilosophy/backend/tools/_tmp/mia_batch/renlei_ocr.txt"
echo "QUEUE-ALL-DONE"
