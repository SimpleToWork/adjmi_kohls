@echo off

pip install virtualenv

cd /d "C:\Users\%USERNAME%\Desktop\New Projects\Nathan's\adjmi_kohls"
python -m virtualenv venv

cd venv/scripts
call activate.bat

cd /d "C:\Users\%USERNAME%\Desktop\New Projects\Nathan's\adjmi_kohls"
pip install -r requirements.txt


cmd /k