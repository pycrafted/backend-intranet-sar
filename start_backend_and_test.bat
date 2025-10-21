@echo off
echo ========================================
echo DÉMARRAGE BACKEND ET TESTS PHASE 7
echo ========================================
echo.

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dépendances si nécessaire
echo.
echo Vérification des dépendances...
pip install requests==2.31.0

REM Démarrer le backend Django en arrière-plan
echo.
echo Démarrage du backend Django...
echo ATTENTION: Le backend va démarrer sur http://localhost:8000
echo.

REM Démarrer Django en arrière-plan
start "Django Backend" cmd /c "python manage.py runserver 0.0.0.0:8000"

REM Attendre que le backend démarre
echo Attente du démarrage du backend (30 secondes)...
timeout /t 30 /nobreak > nul

REM Tester la connexion au backend
echo.
echo Test de connexion au backend...
python -c "import requests; import time; time.sleep(5); r = requests.get('http://localhost:8000/health/', timeout=10); print('Backend status:', r.status_code)"

REM Lancer les tests
echo.
echo Lancement des tests Phase 7...
python run_phase7_all_tests.py

echo.
echo ========================================
echo TESTS TERMINÉS
echo ========================================
echo.
echo Le backend Django continue de tourner en arrière-plan.
echo Pour l'arrêter, fermez la fenêtre "Django Backend".
echo.

pause
