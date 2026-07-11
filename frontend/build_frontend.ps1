$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

npm.cmd ci
npm.cmd run build
