REM forfiles : 지정된 조건에 맞는 파일을 찾고, 각 파일에 대해 명령을 실행한다.
REM /P : %~dp0 : 현재 실행 중인 배치 파일의 경로
REM /S : 하위 디렉토리를 포함해서 검색
REM /M : *.log* : 파일 이름이 .log로 끝나는 파일
REM /D -3 : 3일 이상 지난 파일을 찾는다.
REM /C "cmd /c del @file" : 찾은 각 파일에 대해 실행할 명령을 지정한다. @file은 현재 파일의 이름을 나타낸다.
REM timeout : 지정된 시간(초) 동안 대기하고, 사용자 입력을 대기한다.
forfiles /P "%~dp0..\log" /S /M *.log* /D -3 /C "cmd /c del @file"
timeout 5