$ErrorActionPreference = 'Stop'

$dotnet = Join-Path $env:USERPROFILE '.dotnet\dotnet.exe'
$pattern = Join-Path $env:USERPROFILE '.dotnet\tools\.store\microsoft.powerapps.cli.tool\*\microsoft.powerapps.cli.tool\*\tools\net10.0\any\pac-mcp.dll'
$mcpDll = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName

if (-not (Test-Path $dotnet)) {
    throw 'Missing local .NET 10 at %USERPROFILE%\.dotnet. Install .NET 10 first.'
}

if (-not $mcpDll) {
    throw 'Missing PAC MCP DLL. Install/update Microsoft.PowerApps.CLI.Tool first.'
}

& $dotnet $mcpDll
