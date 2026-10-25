' Silent Background Ollama Server Launcher
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

ollamaExe = "C:\Users\soham\AppData\Local\Programs\Ollama\ollama.exe"

If fso.FileExists(ollamaExe) Then
    cmd = chr(34) & ollamaExe & chr(34) & " serve"
Else
    cmd = "ollama serve"
End If

WshShell.Run cmd, 0, False
