@echo off
echo ========================================
echo PHASE 8 - DEPLOIEMENT ET MONITORING
echo ========================================
echo.

echo Activation de l'environnement virtuel...
call venv\Scripts\activate

echo.
echo Lancement des tests de production complets...
python test_production_complete.py

echo.
echo Lancement du deploiement Phase 8...
python run_phase8_deployment.py

echo.
echo Phase 8 terminee !
pause

