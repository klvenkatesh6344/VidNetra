@echo off
title VidNetra - AI Smart Classroom & Security Platform
color 0b
echo ======================================================================
echo           VIDNETRA - SECURING EVERY LEARNING MOMENT
echo      AI & Computer Vision Classroom Intelligence Platform
echo ======================================================================
echo.

set PY_EXE=C:\Users\kuchi\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PY_EXE%" (
    set PY_EXE=python
)

echo Starting VidNetra Server using %PY_EXE%...
"%PY_EXE%" run.py
pause
