@echo off
pushd "d:\projects\HALO\legal-hallucination-detector\dashboard-and-eval\lexguard-dashboard"
echo.
echo ========================================
echo   LexGuard Dashboard
echo ========================================
echo.
echo Starting Next.js dev server...
echo Dashboard: http://localhost:3000
echo.
call npm run dev
popd
