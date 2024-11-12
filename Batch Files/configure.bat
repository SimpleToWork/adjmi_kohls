@echo off

"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" -m pip install virtualenv

cd /d "C:\Users\%USERNAME%\Desktop\New Projects\Adjmi Apparel\adjmi_kohls"
"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python" -m virtualenv venv

cd venv/scripts
call activate.bat

cd /d "C:\Users\%USERNAME%\Desktop\New Projects\Adjmi Apparel\adjmi_kohls"
pip install -r requirements.txt


cmd /k