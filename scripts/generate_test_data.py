import json
import uuid
import random
import base64
import argparse
import time
import boto3
from datetime import datetime, timedelta

# Default function name based on project conventions
DEFAULT_FUNCTION_NAME = "claims-processing-ingestion-development"

def generate_claim(function_name):
    timestamp_now = datetime.utcnow()
    
    # Generate random claim data
    claim_data = {
        "patient_id": str(uuid.uuid4()),
        "hospital_id": str(uuid.uuid4()),
        "claim_amount": round(random.uniform(500.0, 50000.0), 2),
        "treatment_type": random.choice(["Surgery", "Consultation", "Emergency", "Lab Work", "Pharmacy"]),
        "diagnosis_code": f"ICD10-{random.choice(['A', 'B', 'C', 'D'])}{random.randint(10, 99)}",
        "claim_date": (timestamp_now - timedelta(days=random.randint(0, 30))).isoformat(),
        # Simple dummy text document encoded as base64
        "document": base64.b64encode(f"Medical Claim Document\nDate: {timestamp_now}\nType: Test".encode('utf-8')).decode('utf-8'),
        "document_type": "txt"
    }

    # Wrap in API Gateway proxy structure (body field) as expected by handler
    payload = {
        "body": json.dumps(claim_data)
    }

    print(f"Invoking {function_name}...")
    
    try:
        client = boto3.client('lambda', region_name='ap-south-1')
        response = client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        payload_stream = response['Payload']

        if 'FunctionError' in response:
            print(f"[AWS Error] Function Execution Failed: {response['FunctionError']}")
            error_details = json.loads(payload_stream.read().decode('utf-8'))
            print(f"Error Details: {error_details}")
            return
        
        status_code = response['StatusCode']
        response_payload = json.loads(payload_stream.read().decode('utf-8'))
        
        if status_code == 200:
            # Check the application-level status code in the response body
            app_status = response_payload.get('statusCode', 200)
            if app_status in [200, 202]:
                print(f"[Success] Claim submitted. Lambda Response: {response_payload.get('body')}")
            else:
                print(f"[Application Error: {app_status}] {response_payload.get('body')}")
        else:
            print(f"[AWS Error: {status_code}] {response}")

    except Exception as e:
        print(f"[Exception] {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic claims via direct Lambda invocation")
    parser.add_argument("--function", default=DEFAULT_FUNCTION_NAME, help="Lambda Function Name")
    parser.add_argument("--count", type=int, default=5, help="Number of claims to generate")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds")
    
    args = parser.parse_args()

    print(f"Generating {args.count} synthetic claims for: {args.function}")
    print("-" * 60)
    
    for i in range(args.count):
        generate_claim(args.function)
        time.sleep(args.delay)
    
    print("-" * 60)
    print("Data generation complete.")