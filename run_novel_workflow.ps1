# AI Novel Generation Workflow Runner
# 设置环境变量和运行Python脚本

Write-Host "🚀 Starting AI Novel Generation Workflow..." -ForegroundColor Green

# 设置PYTHONPATH为当前目录
$env:PYTHONPATH = (Get-Location).Path
Write-Host "✅ PYTHONPATH set to: $env:PYTHONPATH" -ForegroundColor Yellow

# 激活虚拟环境并运行脚本
try {
    & .\.venv\Scripts\python.exe app\novel_generation\novel_workflow.py
} catch {
    Write-Host "❌ Error running workflow: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Workflow completed!" -ForegroundColor Green
