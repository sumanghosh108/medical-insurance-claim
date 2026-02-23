$ErrorActionPreference = "Stop"
$ProjectName = "claims-processing"
$Environment = "development"
$Region = "ap-south-1"

# 1. Get Logged-in Account ID
$Identity = aws sts get-caller-identity --query "Account" --output text
$AccountId = $Identity.Trim()
Write-Host "Account ID: $AccountId"

# 2. Get State Machine ARN again (to be safe)
$stack = aws cloudformation describe-stacks --stack-name "$ProjectName-$Environment" --region $Region --no-cli-pager --output json | ConvertFrom-Json
$arn = $stack.Stacks[0].Outputs | Where-Object { $_.OutputKey -eq 'StateMachineArn' } | Select-Object -ExpandProperty OutputValue

# 3. Construct Correct Variables
$S3_BUCKET = "$ProjectName-documents-$Environment"
$CLAIMS_TABLE = "$ProjectName-metadata-$Environment"
$SNS_TOPIC = "arn:aws:sns:${Region}:${AccountId}:${ProjectName}-alerts-${Environment}"

Write-Host "Constructing Environment Variables..."
Write-Host "S3_BUCKET: $S3_BUCKET"
Write-Host "CLAIMS_TABLE: $CLAIMS_TABLE"
Write-Host "SNS_TOPIC: $SNS_TOPIC"
Write-Host "STATE_MACHINE_ARN: $arn"

$Variables = "Variables={ENVIRONMENT=$Environment,S3_BUCKET=$S3_BUCKET,CLAIMS_TABLE=$CLAIMS_TABLE,SNS_TOPIC=$SNS_TOPIC,DB_TABLE=$CLAIMS_TABLE,STATE_MACHINE_ARN=$arn}"

# 4. Update Function
Write-Host "Restoring Ingestion Function Configuration..."
aws lambda update-function-configuration --function-name "$ProjectName-ingestion-$Environment" --region $Region --environment $Variables --no-cli-pager

Write-Host "Successfully restored Ingestion Function Environment." -ForegroundColor Green
