@Echo off
@Echo collector Start
set x=0
call "C:\Users\chogd\anaconda3\Scripts\activate.bat" win32
@taskkill /f /im python.exe 2> NUL

:repeat
@tasklist | find "python.exe" /c > NUL
IF %ErrorLevel%==1 goto 1
IF NOT %ErrorLevel%==1 goto 0

:0
set /a x=%x%+1
echo x : %x%
::echo max : %max%
IF %x%==%max% @taskkill /f /im "python.exe"
goto repeat

:: 실수로 python 창을 클릭하거나 하면 python 프로그램이 멈춘다. 
:: 이때 언젠가 다시 실행시키기 위해서 x가 max에 도달하면 다시 python 프로그램을 실행한다.
:1
set x=0
:: 너무 많은 시간을 잡아놓으면 사야될때 못사거나 할 수 있기 때문에 max 값을 낮추는게 좋다.
set max=5000

start python "%~dp0/../collector_v3.py"
timeout 5 > NUL
goto repeat
