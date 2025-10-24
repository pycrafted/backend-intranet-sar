@echo off
echo ========================================
echo PHASE 7 - TESTS EXHAUSTIFS DU CHATBOT
echo ========================================
echo.

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Validation rapide
echo.
echo 1. VALIDATION RAPIDE DU SYSTÈME
echo ================================
python test_quick_validation.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ VALIDATION RAPIDE ÉCHOUÉE
    echo Veuillez corriger les problèmes avant de continuer
    pause
    exit /b 1
)

echo.
echo ✅ Validation rapide réussie
echo.

REM Demander confirmation pour les tests complets
echo 2. TESTS EXHAUSTIFS
echo ===================
echo.
echo Les tests exhaustifs vont maintenant s'exécuter.
echo Cela peut prendre plusieurs minutes...
echo.
set /p confirm="Voulez-vous continuer ? (o/n): "
if /i "%confirm%" neq "o" (
    echo Tests annulés par l'utilisateur
    pause
    exit /b 0
)

echo.
echo Lancement des tests exhaustifs...
echo.

REM Lancer tous les tests
python run_phase7_all_tests.py

echo.
echo ========================================
echo TESTS TERMINÉS
echo ========================================
echo.
echo Vérifiez les fichiers de résultats :
echo - phase7_overall_results.json
echo - phase7_test_report.md
echo - chatbot_test_results.json
echo - user_scenario_results.json
echo - performance_test_results.json
echo.

pause

