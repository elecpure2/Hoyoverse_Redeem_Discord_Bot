Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' scripts 폴더에서 실행하므로 부모 폴더(프로젝트 루트)로 이동
ProjectRoot = FSO.GetParentFolderName(FSO.GetParentFolderName(WScript.ScriptFullName))
WshShell.CurrentDirectory = ProjectRoot

' Python 봇 실행 (창 없이)
WshShell.Run "py -3.11 main.py", 0, False
