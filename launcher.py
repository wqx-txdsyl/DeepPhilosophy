"""
DeepPhilosophy 桌面启动器
双击启动后端服务 + 打开前端界面
"""
import os
import sys
import time
import webbrowser
import subprocess
import threading


def run_backend():
    """启动 Flask/FastAPI 后端"""
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    env = os.environ.copy()
    env["KNOWLEDGE_DIR"] = "F:/philosophy"
    subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=backend_dir,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def run_frontend():
    """启动 Vite 前端预览服务器"""
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
    subprocess.Popen(
        ["node", "./node_modules/vite/bin/vite.js", "preview", "--port", "4173", "--host", "0.0.0.0"],
        cwd=app_dir,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def main():
    print("DeepPhilosophy v1.2 正在启动...")
    print(f"项目目录: {os.path.dirname(os.path.abspath(__file__))}")

    # 启动后端
    print("[1/2] 启动后端 API 服务 (port 8000)...")
    run_backend()
    time.sleep(4)

    # 启动前端
    print("[2/2] 启动前端界面 (port 4173)...")
    run_frontend()
    time.sleep(2)

    # 打开浏览器
    url = "http://localhost:4173"
    print(f"打开浏览器: {url}")
    webbrowser.open(url)

    print("\nDeepPhilosophy 已就绪！")
    print("关闭此窗口将停止服务。")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在关闭...")


if __name__ == "__main__":
    main()
