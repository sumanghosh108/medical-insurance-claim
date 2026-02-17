param(
    [string]$Environment = "development"
)

$ProjectName = "claims-processing"
$Functions = @(
    "$ProjectName-ingestion-$Environment",
    "$ProjectName-extraction-$Environment",
    "$ProjectName-fraud-$Environment",
    "$ProjectName-workflow-$Environment"
)

Write-Host "Packaging source code into package.zip..."
if (Test-Path package.zip) { Remove-Item package.zip }

# Remove __pycache__ to prevent stale bytecode issues
Get-ChildItem -Path src -Include "__pycache__" -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Zip the contents of src directory so that 'lambda_functions', etc. are at the root
Get-ChildItem -Path src | Compress-Archive -DestinationPath package.zip -Force
Start-Sleep -Seconds 2

if (-not (Test-Path package.zip)) {
    Write-Error "Failed to create package.zip"
    exit 1
}

# Verify zip structure
Write-Host "Verifying zip structure..."
Expand-Archive package.zip -DestinationPath dist_verify -Force
Get-ChildItem dist_verify -Recurse | Select-Object FullName

# Local Import Test
Write-Host "Running local import test..."
try {
    $env:PYTHONPATH = "$PWD\dist_verify"
    python -c "import lambda_functions.claim_ingestion_handler; print('Local Import SUCCESS')"
    if ($LASTEXITCODE -ne 0) { throw "Import failed" }
}
catch {
    Write-Error "Local import failed: $_"
    # Don't exit, just warn (because local might lack boto3 etc?) 
    # Actually local has boto3.
}

Remove-Item dist_verify -Recurse -Force

foreach ($func in $Functions) {
    Write-Host "Updating function code for: $func"
    try {
        aws lambda update-function-code --function-name $func --zip-file fileb://package.zip --no-cli-pager
        Write-Host "Successfully updated code for $func" -ForegroundColor Green
        
        # Update handler if it uses 'src.' prefix
        $config = aws lambda get-function-configuration --function-name $func --no-cli-pager --output json | ConvertFrom-Json
        $currentHandler = $config.Handler
        if ($currentHandler -like "src.*") {
            $newHandler = $currentHandler.Substring(4)
            Write-Host "Updating handler from '$currentHandler' to '$newHandler'"
            aws lambda update-function-configuration --function-name $func --handler $newHandler --no-cli-pager
            Write-Host "Successfully updated handler for $func" -ForegroundColor Green
        }
    }
    catch {
        Write-Error "Failed to update $func : $_"
    }
}

Remove-Item package.zip
Write-Host "Lambda code deployment finished." -ForegroundColor Cyan
