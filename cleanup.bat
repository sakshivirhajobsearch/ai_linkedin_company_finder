@echo off
echo ================================
echo   CLEANUP STARTED
echo ================================

:: Remove all __pycache__ folders
echo Removing __pycache__ folders...
for /d /r %%i in (__pycache__) do (
    rd /s /q "%%i"
)

:: Remove .pyc files
echo Removing .pyc files...
del /s /q *.pyc

:: Remove autosave states from root
echo Removing autosave state files...
del /q autosave_state.json
del /q autosave_state.txt

:: Remove generated domain result CSV from root
echo Removing old CSV result files from root...
del /q domain_results.csv
del /q linkedin_results.csv

:: Cleanup temporary LinkedIn session files
echo Removing LinkedIn session files...
del /q "linkedin\__pycache__\*"
del /q "output\linkedin\last_session.csv"

:: Remove temporary output text/csv files
echo Cleaning output folder temporary files...
del /q output\invalid-website.csv
del /q output\invalid-website.txt
del /q output\valid-website.csv
del /q output\valid-website.txt

:: Keep Excel (xlsx) files safe
echo Keeping Excel reports...

echo ================================
echo   CLEANUP FINISHED ✅
echo ================================
pause
