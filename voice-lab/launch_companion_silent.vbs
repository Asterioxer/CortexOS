' Silent Launcher for J.A.R.V.I.S. Arc Reactor Desktop HUD
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\soham\Desktop\voice-lab"
WshShell.Run chr(34) & "C:\Users\soham\Desktop\voice-lab\oi_env\Scripts\python.exe" & chr(34) & " " & chr(34) & "C:\Users\soham\Desktop\voice-lab\launch_jarvis_app.py" & chr(34), 0, False
