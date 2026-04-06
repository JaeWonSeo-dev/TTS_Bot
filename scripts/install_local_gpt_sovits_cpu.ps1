param(
    [string]$RepoDir = "C:\Sjw_dev\Coding\GPT-SoVITS"
)

$pythonExe = Join-Path $RepoDir ".venv\Scripts\python.exe"
$requirementsPath = Join-Path $RepoDir "requirements.txt"
$extraReqPath = Join-Path $RepoDir "extra-req.txt"
$filteredReqPath = Join-Path $RepoDir "requirements.local-win-cpu.txt"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python venv not found: $pythonExe"
    exit 1
}

$lines = Get-Content $requirementsPath
$filtered = @()
foreach ($line in $lines) {
    $trimmed = $line.Trim()
    if ($trimmed -eq "") { continue }
    if ($trimmed -like "pyopenjtalk*") { continue }
    if ($trimmed -like "jieba_fast*") { continue }
    if ($trimmed -like "opencc*") { continue }
    if ($trimmed -like "onnxruntime-gpu*") { $filtered += "onnxruntime"; continue }
    $filtered += $line
}
$filtered | Set-Content -Encoding UTF8 $filteredReqPath

Write-Host "[INFO] Using filtered requirements: $filteredReqPath"
& $pythonExe -m pip install -r $extraReqPath --no-deps
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $pythonExe -m pip install -r $filteredReqPath
exit $LASTEXITCODE
