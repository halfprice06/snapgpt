@echo off
if exist "%~1\*" (
    cd /d "%~1"
) else (
    cd /d "%~dp1"
)
python -c "from snapgpt.cli.main import main; main()" -f "%~1"
pause 