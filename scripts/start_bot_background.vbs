Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' scripts 폴더에서 실행하므로 부모 폴더(프로젝트 루트)로 이동
ProjectRoot = FSO.GetParentFolderName(FSO.GetParentFolderName(WScript.ScriptFullName))
WshShell.CurrentDirectory = ProjectRoot

' Python 봇 실행 (창 없이, 로그 남김)
' -u 옵션은 버퍼링 없이 즉시 로그를 기록하게 합니다.
' 절대 경로를 사용하여 서비스 환경에서도 안정적으로 실행되게 합니다.
PyPath = "C:\Users\elecp\AppData\Local\Programs\Python\Python311\python.exe"
WshShell.Run "%comspec% /c """ & PyPath & """ -u main.py >> bot.log 2>&1", 0, False
