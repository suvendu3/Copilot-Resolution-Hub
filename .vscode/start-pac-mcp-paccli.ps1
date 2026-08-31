$ErrorActionPreference = 'Stop'

$env:DOTNET_ROOT = Join-Path $env:USERPROFILE '.dotnet'
$env:PATH = "$env:DOTNET_ROOT;$env:DOTNET_ROOT\tools;$env:PATH"

$pac = Join-Path $env:USERPROFILE '.dotnet\tools\pac.exe'
if (-not (Test-Path $pac)) {
    throw 'Missing PAC CLI at %USERPROFILE%\.dotnet\tools\pac.exe'
}

& $pac copilot mcp --run
