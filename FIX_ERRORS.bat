@echo off
echo Running migrations...
C:\Python314\python.exe manage.py makemigrations home
C:\Python314\python.exe manage.py migrate
echo Done! You can close this window now.
pause
