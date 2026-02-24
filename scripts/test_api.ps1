$ImageBytes = [System.IO.File]::ReadAllBytes("c:\project\tests\fixtures\sample_claim_handwritten.png")
$Base64Doc = [Convert]::ToBase64String($ImageBytes)

$Payload = @{
    body = @{
        patient_id = "pt-test-0001-0001-000000000001"
        hospital_id = "hosp-test-0001-0001-000000000001"
        claim_amount = 5500.00
        treatment_type = "Emergency Room Visit"
        diagnosis_code = "R10.9"
        claim_date = "2025-01-15T08:30:00Z"
        document = $Base64Doc
        document_type = "png"
    }
}

$JsonPayload = $Payload | ConvertTo-Json -Depth 5
Set-Content -Path "c:\project\payload.json" -Value $JsonPayload

Write-Host "Invoking Lambda..."
aws lambda invoke --function-name claims-processing-ingestion-development --cli-binary-format raw-in-base64-out --payload file://c:\project\payload.json --region ap-south-1 response.json
Write-Host "Lambda Response:"
Get-Content response.json
