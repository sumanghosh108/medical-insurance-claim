param(
    [string]$Environment = "development"
)

$ProjectName = "claims-processing"
$Region = "ap-south-1"
$AccountId = $(aws sts get-caller-identity --query Account --output text)
$EcrRepoName = "claims-processing-lambda"
$EcrRegistry = "${AccountId}.dkr.ecr.${Region}.amazonaws.com"
$ImageUri = "${EcrRegistry}/${EcrRepoName}:${Environment}"

$ZipFunctions = @(
    "$ProjectName-ingestion-$Environment",
    "$ProjectName-workflow-$Environment"
)

$ImageFunctions = @(
    "$ProjectName-extraction-$Environment-v2",
    "$ProjectName-entity-extraction-$Environment-v2",
    "$ProjectName-fraud-$Environment-v2"
)

# 1. Build and Push Docker Image
Write-Host "=== 1/3 Building and Pushing Docker Image ==="
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $EcrRegistry
if ($LASTEXITCODE -ne 0) { throw "Docker login failed" }

docker build -f docker/Dockerfile.lambda -t $EcrRepoName .
if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }

docker tag "${EcrRepoName}:latest" $ImageUri
docker push $ImageUri
if ($LASTEXITCODE -ne 0) { throw "Docker push failed" }

# 2. Update CloudFormation Parameters JSON
Write-Host "=== 2/3 Updating CloudFormation Parameters ==="
$ParamsFile = "infrastructure/parameters.json"
$Params = Get-Content $ParamsFile | ConvertFrom-Json
$LambdaImageUriParam = $Params.Parameters | Where-Object { $_.ParameterKey -eq "LambdaImageUri" }

if ($LambdaImageUriParam) {
    $LambdaImageUriParam.ParameterValue = $ImageUri
} else {
    $Params.Parameters += @{
        ParameterKey = "LambdaImageUri"
        ParameterValue = $ImageUri
    }
}
$Params | ConvertTo-Json -Depth 5 | Set-Content $ParamsFile
Write-Host "Updated parameters.json with ImageUri: $ImageUri"

# 3. Create lightweight Zip for ingestion and workflow functions
Write-Host "=== 3/3 Packaging lightweight Lambdas ==="
if (Test-Path package.zip) { Remove-Item package.zip }
if (Test-Path dist_temp) { Remove-Item dist_temp -Recurse -Force }
New-Item -ItemType Directory -Path dist_temp -Force

# We don't need heavy ML reqs for ingestion/workflow, just boto3/standard lib
# Copy src contents
Copy-Item -Path "src\*" -Destination dist_temp -Recurse -Force
Get-ChildItem -Path dist_temp -Include "__pycache__" -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Get-ChildItem -Path dist_temp | Compress-Archive -DestinationPath package.zip -Force
Start-Sleep -Seconds 2
Remove-Item dist_temp -Recurse -Force

Write-Host "Uploading package.zip to S3..."
aws s3 cp package.zip s3://$ProjectName-documents-$Environment/lambdas/package.zip --region ap-south-1

foreach ($func in $ZipFunctions) {
    Write-Host "Updating zip code for: $func"
    try {
        aws lambda update-function-code --function-name $func --s3-bucket "$ProjectName-documents-$Environment" --s3-key "lambdas/package.zip" --region ap-south-1 --no-cli-pager
        
        $config = aws lambda get-function-configuration --function-name $func --region ap-south-1 --no-cli-pager --output json | ConvertFrom-Json
        $currentHandler = $config.Handler
        if ($currentHandler -like "src.*") {
            $newHandler = $currentHandler.Substring(4)
            aws lambda update-function-configuration --function-name $func --handler $newHandler --region ap-south-1 --no-cli-pager
        }
    }
    catch {
        Write-Warning "Failed to update $func via AWS CLI (may need CF update first): $_"
    }
}

foreach ($func in $ImageFunctions) {
    Write-Host "Updating image code for: $func"
    try {
        aws lambda update-function-code --function-name $func --image-uri $ImageUri --region ap-south-1 --no-cli-pager
    } catch {
        Write-Warning "Failed to update $func via AWS CLI (may need CF update first to change to Image type): $_"
    }
}

Remove-Item package.zip -ErrorAction SilentlyContinue
Write-Host "Please run ./deploy_stack.sh to update CloudFormation to switch extraction/fraud functions to Image PackageType." -ForegroundColor Cyan

