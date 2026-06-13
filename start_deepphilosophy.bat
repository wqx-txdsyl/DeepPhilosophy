@echo off
chcp 65001 >nul
title DeepPhilosophy - 哲学知识库

echo ========================================
echo   DeepPhilosophy v1.2
echo   哲学爱好者知识库
echo ========================================
echo.

:: Start backend
echo [1/2] 启动后端服务...
start "DeepPhilosophy Backend" /MIN cmd /c "cd /d C:\dp\backend && set KNOWLEDGE_DIR=F:/philosophy && python main.py"

:: Wait for backend
echo 等待后端就绪...
timeout /t 4 /nobreak >nul

:: Start frontend (serve built dist)
echo [2/2] 启动前端界面...
start "DeepPhilosophy Frontend" /MIN cmd /c "cd /d C:\dp\app && node ./node_modules/vite/bin/vite.js preview --port 4173 --host 0.0.0.0"

:: Wait and open browser
timeout /t 2 /nobreak >nul
start "" http://localhost:4173

echo.
echo ✅ DeepPhilosophy 已启动！
echo 浏览器将自动打开 http://localhost:4173
echo.
echo 按任意键关闭此窗口（不影响应用运行）
pause >nul
