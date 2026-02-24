import boto3
import json
import base64
import time

lambda_client = boto3.client('lambda', region_name='ap-south-1')
sfn_client = boto3.client('stepfunctions', region_name='ap-south-1')

# Tiny valid 1x1 PNG
b64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

payload = {
    "body": {
        "patient_id": "pt-test-0001",
        "hospital_id": "hosp-test-0001",
        "claim_amount": 5500.0,
        "treatment_type": "Emergency Room Visit",
        "diagnosis_code": "R10.9",
        "claim_date": "2025-01-15T08:30:00Z",
        "document": b64_image,
        "document_type": "png"
    }
}

print("Invoking Lambda...")
response = lambda_client.invoke(
    FunctionName='claims-processing-ingestion-development',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

response_payload = json.loads(response['Payload'].read())
print(f"Lambda Response Payload: {json.dumps(response_payload, indent=2)}")

if response_payload.get('statusCode') == 202:
    body = json.loads(response_payload['body'])
    execution_arn = body.get('execution_arn')
    print(f"Workflow triggered: {execution_arn}")
    
    # Poll step functions
    print("Polling Step Functions execution...")
    while True:
        sfn_res = sfn_client.describe_execution(executionArn=execution_arn)
        status = sfn_res['status']
        print(f"Status: {status}")
        if status in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
            if status == 'FAILED':
                history = sfn_client.get_execution_history(executionArn=execution_arn, reverseOrder=True)
                for event in history['events']:
                    if event.get('type') == 'ExecutionFailed':
                        print("Failed Event:", json.dumps(event, indent=2))
                        break
            break
        time.sleep(3)
