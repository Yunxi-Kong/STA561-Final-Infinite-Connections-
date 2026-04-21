@echo off
rem ==================================================================
rem  Infinite Connections — one-click Phase 0 bootstrap
rem
rem  What this does (in order):
rem    1. pip install all upgrade dependencies
rem    2. download NLTK WordNet + CMU Pronouncing Dictionary
rem    3. cache the MiniLM embedding model
rem    4. probe the local Ollama daemon
rem    5. verify API keys from .env
rem    6. build the unified NYT reference corpus (~1400 puzzles)
rem
rem  Just double-click this file. If you prefer, you can also run it
rem  from PowerShell with:  .\RUN_SETUP.bat
rem ==================================================================

setlocal

rem Switch to the folder that this .bat lives in (the project root).
cd /d "%~dp0"

rem Pick a python launcher that actually exists.
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
    echo.
    echo [ERROR] Neither 'py' nor 'python' is on your PATH.
    echo         Install Python 3.10+ from https://www.python.org/downloads/
    echo         and be sure to tick "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   Using python launcher: %PY%
echo   Project root:         %CD%
echo ================================================================
echo.

rem ---- Step A: environment bootstrap --------------------------------
%PY% scripts\setup_env.py
if errorlevel 1 (
    echo.
    echo [WARN] setup_env.py reported a non-zero exit code.
    echo        Scroll up and look for the first red/error line.
    echo        You can still try the next step if only the API-key
    echo        check failed.
    echo.
)

echo.
echo ================================================================
echo   Building the unified NYT reference corpus...
echo ================================================================
echo.

rem ---- Step B: download NYT corpus ----------------------------------
%PY% scripts\download_nyt_corpus.py
if errorlevel 1 (
    echo.
    echo [WARN] download_nyt_corpus.py reported errors. If this is about
    echo        HuggingFace or git, you can retry with a flag, e.g.:
    echo          %PY% scripts\download_nyt_corpus.py --skip-github
    echo.
)

echo.
echo ================================================================
echo   Done. Review the output above for any warnings.
echo   Key artifacts written:
echo     - data\reports\setup_summary.json
echo     - data\history\unified_reference.json
echo     - data\history\unified_summary.json
echo ================================================================
echo.
pause
endlocal
