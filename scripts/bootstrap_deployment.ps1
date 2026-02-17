<#
.SYNOPSIS
    Bootstrap AWS Deployment (Pure PowerShell — no bash dependency)
.DESCRIPTION
    Creates prerequisite S3 bucket, uploads nested templates, validates,
    and deploys the CloudFormation master stack.
.EXAMPLE
    .\scripts\bootstrap_deployment.ps1 -Environment development
#>

param (
    [string]$Environment = "development",
    [string]$Region = ""
)

$ErrorActionPreference = "Stop"

# Auto-detect region from AWS CLI config if not provided
if ([string]::IsNullOrEmpty($Region)) {
    $Region = (aws configure get region 2>$null)
    if ([string]::IsNullOrEmpty($Region)) {
        $Region = "ap-south-1"
    }
}

$ProjectName   = "claims-processing"
$StackName     = "$ProjectName-$Environment"
$TemplateBucket = "$ProjectName-templates"
$TemplateFile  = "infrastructure/cloudformation.yaml"
$ParamsFile    = "infrastructure/parameters.json"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Deploying: $StackName" -ForegroundColor Cyan
Write-Host " Region:    $Region" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Verify credentials ──────────────────────────────────────
Write-Host "[1/6] Verifying AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json 2>&1 | ConvertFrom-Json
    Write-Host "  Account : $($identity.Account)" -ForegroundColor Green
    Write-Host "  User    : $($identity.Arn)" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: AWS credentials are invalid or not configured." -ForegroundColor Red
    Write-Host "  Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# ── Step 2: Create template bucket ──────────────────────────────────
Write-Host "[2/6] Ensuring template bucket exists: $TemplateBucket" -ForegroundColor Yellow
$bucketCheck = aws s3api head-bucket --bucket $TemplateBucket 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Bucket already exists." -ForegroundColor Green
} else {
    Write-Host "  Creating bucket..."
    if ($Region -eq "ap-south-1") {
        aws s3api create-bucket --bucket $TemplateBucket --region $Region | Out-Null
    } else {
        aws s3api create-bucket --bucket $TemplateBucket --region $Region `
            --create-bucket-configuration LocationConstraint=$Region | Out-Null
    }
    aws s3api put-bucket-versioning --bucket $TemplateBucket `
        --versioning-configuration Status=Enabled | Out-Null
    Write-Host "  Created bucket." -ForegroundColor Green
}

# ── Step 3: Upload nested templates ─────────────────────────────────
Write-Host "[3/6] Syncing nested templates to S3..." -ForegroundColor Yellow
aws s3 sync infrastructure/templates/ "s3://$TemplateBucket/templates/" --region $Region
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to sync templates." -ForegroundColor Red
    exit 1
}
Write-Host "  Templates uploaded." -ForegroundColor Green

# ── Step 4: Validate master template ────────────────────────────────
Write-Host "[4/6] Validating master template..." -ForegroundColor Yellow
aws cloudformation validate-template --template-body "file://$TemplateFile" --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Template validation failed." -ForegroundColor Red
    exit 1
}
Write-Host "  Template is valid." -ForegroundColor Green

# ── Step 5: Deploy CloudFormation stack ─────────────────────────────
Write-Host "[5/6] Deploying CloudFormation stack: $StackName ..." -ForegroundColor Yellow
Write-Host "       (this may take 10-20 minutes for a fresh stack)" -ForegroundColor DarkGray

# Read parameters.json and convert to Key=Value format
$paramsJson = Get-Content $ParamsFile -Raw | ConvertFrom-Json
$paramOverrides = @()
foreach ($p in $paramsJson.Parameters) {
    $paramOverrides += "$($p.ParameterKey)=$($p.ParameterValue)"
}
Write-Host "  Parameters: $($paramOverrides -join ', ')" -ForegroundColor DarkGray

$deployArgs = @(
    "cloudformation", "deploy",
    "--stack-name", $StackName,
    "--template-file", $TemplateFile,
    "--parameter-overrides"
) + $paramOverrides + @(
    "--capabilities", "CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND",
    "--region", $Region,
    "--tags", "Project=$ProjectName", "Environment=$Environment",
    "--no-fail-on-empty-changeset"
)

& aws @deployArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: Stack deployment failed!" -ForegroundColor Red
    Write-Host "  Check the CloudFormation console for details:" -ForegroundColor Red
    Write-Host "  https://$Region.console.aws.amazon.com/cloudformation/home?region=$Region" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Recent events:" -ForegroundColor Yellow
    aws cloudformation describe-stack-events `
        --stack-name $StackName `
        --region $Region `
        --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[LogicalResourceId,ResourceStatusReason]" `
        --output table 2>$null
    exit 1
}

# ── Step 6: Show outputs ────────────────────────────────────────────
Write-Host "[6/6] Stack outputs:" -ForegroundColor Yellow
aws cloudformation describe-stacks `
    --stack-name $StackName `
    --region $Region `
    --query "Stacks[0].Outputs" `
    --output table

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Initialize the database (see RDS endpoint above)"
Write-Host "  2. Deploy Lambda code:  .\scripts\deploy_lambdas.ps1 -Environment $Environment"
Write-Host ""
