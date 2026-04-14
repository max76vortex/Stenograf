@echo off
REM Пример запуска транскрибации за один месяц.
REM Отредактируй пути RECORDINGS и INBOX под свой компьютер.

set RECORDINGS=D:\1 ЗАПИСИ ГОЛОС\recordings
set INBOX=D:\Obsidian\Audio Brain\00_inbox
set MONTH=2024-03

cd /d "%~dp0"
call .venv\Scripts\activate.bat
python transcribe_to_obsidian.py "%RECORDINGS%\%MONTH%" "%INBOX%" --manifest "%RECORDINGS%\manifest.csv"
pause
