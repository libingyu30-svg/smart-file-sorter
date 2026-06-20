@echo off
setlocal
cd /d %~dp0
if not exist config.json python src\smartsort.py --config config.json --init
python src\smartsort.py --config config.json --gui
endlocal
