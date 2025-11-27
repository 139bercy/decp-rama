cd "%~dp0"
call wsl docker build --pull -t decp-database .
pause