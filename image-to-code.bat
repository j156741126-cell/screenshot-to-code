@echo off
REM 多模型协作流水线：千问 VL + DeepSeek 推理 + 代码生成
REM 用法: image-to-code <图片路径> [需求描述]

if "%~1"=="" (
    echo 用法: image-to-code ^<图片路径^> [需求描述]
    echo 示例: image-to-code ui.png "根据设计稿生成React组件"
    exit /b 1
)

cd /d %~dp0
python orchestrator.py %*
