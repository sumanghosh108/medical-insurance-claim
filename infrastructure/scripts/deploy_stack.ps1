param(
    [string]$Environment = "development"
)

$ProjectName = "claims-processing"
$StackName = "${ProjectName}-${Environment}"
$TemplateFile = "cloudformation.yaml"
$ParamsFile = "parameters.json"
$Region = "ap-south-1"

Write-Host "=== Deploying $StackName to $Region ==="

# Upload nested templates to S3
$TemplateBucket = "${ProjectName}-templates"
Write-Host "[1/4] Uploading templates to s3://${TemplateBucket}/"
aws s3 sync templates/ "s3://${TemplateBucket}/templates/" --region $Region

# Validate main template
Write-Host "[2/4] Validating template..."
aws cloudformation validate-template --template-body "file://$TemplateFile" --region $Region

# Parse parameters.json into Key=Value strings
$ParamObj = Get-Content $ParamsFile | ConvertFrom-Json
$OverrideArgs = @()
foreach ($p in $ParamObj.Parameters) {
    if ($p.ParameterValue -ne $null -and $p.ParameterValue -ne "") {
        $OverrideArgs += "$($p.ParameterKey)=$($p.ParameterValue)"
    }
}
$OverrideString = $OverrideArgs -join " "

# Deploy/Update stack
Write-Host "[3/4] Deploying stack with overrides: $OverrideString"
aws cloudformation deploy `
    --stack-name $StackName `
    --template-file $TemplateFile `
    --parameter-overrides $OverrideArgs `
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND `
    --region $Region `
    --tags "Project=$ProjectName" "Environment=$Environment" `
    --no-fail-on-empty-changeset

# Show outputs
Write-Host "[4/4] Stack outputs:"
aws cloudformation describe-stacks `
    --stack-name $StackName `
    --region $Region `
    --query "Stacks[0].Outputs" `
    --output table

Write-Host "=== Deployment complete ==="
