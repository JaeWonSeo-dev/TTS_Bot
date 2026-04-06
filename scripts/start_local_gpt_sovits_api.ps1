param(
    [string]$RepoDir = "C:\Sjw_dev\Coding\GPT-SoVITS",
    [string]$PythonExe = "python",
    [string]$BindAddress = "127.0.0.1",
    [int]$Port = 9880,
    [string]$ConfigPath = "GPT_SoVITS/configs/tts_infer.yaml"
)

$apiScript = Join-Path $RepoDir "api_v2.py"
if (-not (Test-Path $RepoDir)) {
    Write-Error "GPT-SoVITS repo not found: $RepoDir"
    exit 1
}

if (-not (Test-Path $apiScript)) {
    Write-Error "api_v2.py not found: $apiScript"
    exit 1
}

Write-Host "[INFO] RepoDir     : $RepoDir"
Write-Host "[INFO] PythonExe   : $PythonExe"
Write-Host "[INFO] BindAddress : $BindAddress"
Write-Host "[INFO] Port        : $Port"
Write-Host "[INFO] ConfigPath  : $ConfigPath"
Write-Host "[INFO] Starting GPT-SoVITS api_v2.py ..."

Push-Location $RepoDir
try {
    & $PythonExe $apiScript -a $BindAddress -p $Port -c $ConfigPath
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
