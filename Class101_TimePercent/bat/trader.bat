@Echo off
@Echo trader Start
set x=0
call "C:\Users\chogd\anaconda3\Scripts\activate.bat" win32
@taskkill /f /im python.exe 2> NUL

:repeat
@tasklist | find "python.exe" /c > NUL

REM goto 문을 통해 1번이나 0번 레이블로 이동한다. 
IF %ErrorLevel%==1 goto 1
IF NOT %ErrorLevel%==1 goto 0

REM 레이블 0
:0
set /a x=%x%+1
echo x : %x%
::echo max : %max%
IF %x%==%max% @taskkill /f /im "python.exe"
goto repeat

REM 레이블 1
:1
set x=0
set max=700

start python "%~dp0/../trader.py"
timeout 5 > NUL
goto repeat
