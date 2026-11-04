@echo off
setlocal EnableDelayedExpansion
rem Opens Mintline in its own Chrome app window. Falls back to your default browser.
set "APP=%~dp0index.html"
set "URL=file:///!APP:\=/!"
set "URL=!URL: =%%20!"

set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

if defined CHROME (
  start "" "!CHROME!" --app="!URL!"
) else (
  start "" "%APP%"
)
endlocal
