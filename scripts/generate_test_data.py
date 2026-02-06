import uuid
import random
import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
conn=psycopg2.connect(
    host=os.getenv('DB_HOST','DB_HOST'),
    user=os.getenv('DB_USER','DB_USER'),
    password=os.getenv('DB_PASSWORD','DB_PASSWORD'),
    database=os.getenv('DB_NAME','DB_NAME'),
    port=os.getenv('DB_PORT','DB_PORT')
)

cursor=conn.cursor()

# Generate 100 test claims
print("Generating test clims...")
for i in range(100):
    claim_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())
    hospital_id = str(uuid.uuid4())
    claim_amount = random.uniform(1000, 50000)
    treatment_type = random.choice(['Surgery', 'Consultation', 'ER', 'Lab Work'])
    diagnosis_code = f'ICD10-{random.randint(1, 999):03d}'
    claim_date = datetime.now() - timedelta(days=random.randint(0, 30))
    
    cursor.execute("""
        INSERT INTO claims (
            claim_id, patient_id, hospital_id, claim_amount,
            treatment_type, diagnosis_code, claim_date,
            fraud_score, approval_status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        claim_id, patient_id, hospital_id, claim_amount,
        treatment_type, diagnosis_code, claim_date,
        random.random(), 'pending'
    ))

conn.commit()
cursor.close()
conn.close()
print("Generated 100 test claims")