REM ======= File: snapgpt/resources/snapgpt_context.bat =======
@echo off
REM This .bat file is invoked by the Windows Explorer context menu.
REM %* are all selected file/folder paths.

echo Creating SnapGPT snapshot for: %*
snapgpt -f %*
IF EXIST working_snapshot.md (
    echo Opening working_snapshot.md in Notepad...
    start notepad.exe working_snapshot.md
) ELSE (
    echo Could not find working_snapshot.md, something went wrong.
)