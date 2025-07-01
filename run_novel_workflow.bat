@echo off
echo 🚀 Starting AI Novel Generation Workflow...

REM 设置PYTHONPATH为当前目录
set PYTHONPATH=%cd%
echo ✅ PYTHONPATH set to: %PYTHONPATH%

REM 运行Python脚本
.venv\Scripts\python.exe app\novel_generation\novel_workflow.py

if %ERRORLEVEL% neq 0 (
    echo ❌ Error running workflow
    pause
    exit /b 1
)

echo 🎉 Workflow completed!
pause
