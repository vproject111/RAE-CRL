@echo off
echo ==========================================
echo RAE-CRL Windows Builder
echo ==========================================

echo 1. Creating Virtual Environment...
python -m venv venv
call venv\Scripts\activate

echo 2. Installing Dependencies...
pip install -r requirements.txt
pip install pyinstaller pywebview

echo 3. Building OneDir Executable...
pyinstaller rae_crl.spec --noconfirm --clean

echo ==========================================
echo BUILD COMPLETE!
echo You can find the app in: dist\RAE-CRL-LabDesk\RAE-CRL-LabDesk.exe
echo ==========================================
pause
