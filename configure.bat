@echo off

pip install virtualenv

cd /d "C:\Users\%USERNAME%\Desktop\New Projects\Adjmi Apparel\adjmi_kohls"
python3.12 -m virtualenv venv

cd venv/scripts
call activate.bat

cd /d "C:\Users\%USERNAME%\Desktop\New Projects\Adjmi Apparel\adjmi_kohls"
pip install -r requirements.txt


cmd /k