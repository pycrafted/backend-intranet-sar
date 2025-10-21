@echo off
echo Phase 6 - Test des Optimisations Avancees
echo ==========================================

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Installer les dependances si necessaire
pip install redis==5.0.1 django-redis==5.4.0

REM Executer le test
python test_phase6_simple.py

pause
