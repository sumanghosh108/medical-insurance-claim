$ErrorActionPreference = "Stop"
$ProjectName = "claims-processing"
$Environment = "development"
$Region = "ap-south-1"

# 1. Get State Machine ARN
Write-Host "Fetching State Machine ARN..."
$stack = aws cloudformation describe-stacks --stack-name "$ProjectName-$Environment" --region $Region --no-cli-pager --output json | ConvertFrom-Json
$arn = $stack.Stacks[0].Outputs | Where-Object { $_.OutputKey -eq 'StateMachineArn' } | Select-Object -ExpandProperty OutputValue

if (-not $arn) {
    Write-Error "State Machine ARN not found in stack outputs."
    exit 1
}
Write-Host "State Machine ARN: $arn"

# 2. Get Current Function Configuration
$FunctionName = "$ProjectName-ingestion-$Environment"
Write-Host "Fetching configuration for $FunctionName..."
$config = aws lambda get-function-configuration --function-name $FunctionName --region $Region --no-cli-pager --output json | ConvertFrom-Json
$newEnv = @{}
if ($envVars -is [System.Collections.IDictionary]) {
     $newEnv = $envVars
} elseif ($envVars -is [PSCustomObject]) {
     $envVars.PSObject.Properties | ForEach-Object {
         $newEnv[$_.Name] = $_.Value
     }
}

$newEnv['STATE_MACHINE_ARN'] = $arn

$envString = "Variables={"
foreach ($key in $newEnv.Keys) {
     $val = $newEnv[$key]
     $envString += "$key=$val,"
}
$envString = $envString.TrimEnd(",") + "}"

# 4. Update Function
Write-Host "Updating function configuration..."
aws lambda update-function-configuration --function-name $FunctionName --region $Region --environment $envString --no-cli-pager

Write-Host "Successfully linked Ingestion Function to Step Functions Workflow." -ForegroundColor Green
