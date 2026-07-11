$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

function Test-PythonCommand {
  param([string[]]$CommandParts)

  try {
    if ($CommandParts.Count -gt 1) {
      & $CommandParts[0] @($CommandParts[1..($CommandParts.Count - 1)]) -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    } else {
      & $CommandParts[0] -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    }
    return $LASTEXITCODE -eq 0
  } catch {
    return $false
  }
}

function Invoke-Python {
  param(
    [string[]]$CommandParts,
    [string[]]$Arguments
  )

  if ($CommandParts.Count -gt 1) {
    & $CommandParts[0] @($CommandParts[1..($CommandParts.Count - 1)]) @Arguments
  } else {
    & $CommandParts[0] @Arguments
  }
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$venvHealthy = $false
if (Test-Path $venvPython) {
  try {
    & $venvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    $venvHealthy = $LASTEXITCODE -eq 0
  } catch {
    $venvHealthy = $false
  }
}

if (-not $venvHealthy) {
  $pythonCommand = @()
  $candidates = @(
    @("py", "-3.13"),
    @("py", "-3"),
    @("python"),
    @("python3")
  )
  if ($env:USERPROFILE) {
    $bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundledPython) {
      $candidates += ,@($bundledPython)
    }
  }

  foreach ($candidate in $candidates) {
    if (Get-Command $candidate[0] -ErrorAction SilentlyContinue) {
      if (Test-PythonCommand -CommandParts $candidate) {
        $pythonCommand = $candidate
        break
      }
    }
  }

  if ($pythonCommand.Count -eq 0) {
    throw "Python 3.11+ was not found and backend/.venv is not usable. Install Python, then run backend/test_backend.ps1 again."
  }

  if (Test-Path ".venv") {
    Write-Host "Existing .venv is broken. Recreating backend virtual environment..."
    Remove-Item -LiteralPath ".venv" -Recurse -Force
  } else {
    Write-Host "Creating backend virtual environment..."
  }
  Invoke-Python -CommandParts $pythonCommand -Arguments @("-m", "venv", ".venv")
  if ($LASTEXITCODE -ne 0) {
    throw "Python virtual environment creation failed."
  }
}

if (-not (Test-Path $venvPython)) {
  throw "Python virtual environment was not created. Confirm Python is installed and available as py or python."
}

Write-Host "Installing backend test dependencies..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
  throw "pip upgrade failed."
}
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
  throw "Dependency installation failed. Check network access and backend/requirements.txt."
}

& $venvPython -m pytest --version *> $null
if ($LASTEXITCODE -ne 0) {
  throw "pytest is not installed. Run backend/test_backend.ps1 again after confirming pip can install requirements.txt."
}

$testDbPath = Join-Path $PSScriptRoot "test-local.db"
if (Test-Path $testDbPath) {
  Remove-Item -LiteralPath $testDbPath -Force
}
$env:DATABASE_URL = "sqlite:///$($testDbPath.Replace('\', '/'))"
$env:USE_MOCK_AI = "true"
$env:APP_AUTH_SECRET = "test-secret"
$env:INITIAL_ADMIN_EMAIL = "admin@example.com"
$env:INITIAL_ADMIN_PASSWORD = "test-password"
$env:OPENAI_API_KEY = "test-key"
$env:CORS_ORIGINS = "http://localhost:3000"

Write-Host "Running pytest with a test SQLite database..."
& $venvPython -m pytest
if ($LASTEXITCODE -ne 0) {
  throw "pytest failed."
}
