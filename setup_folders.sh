# #!/bin/bash

# # Create all directories
# mkdir -p infrastructure/{templates,scripts,diagrams}
# mkdir -p lambda_functions/{claim-ingestion-handler,document-extraction-orchestrator,entity-extraction-processor,fraud-detection-inference,workflow-state-manager}
# mkdir -p ml_models/{models,data,notebooks,tests}
# mkdir -p document_processing/tests
# mkdir -p database/{migrations,seeds,views,functions}
# mkdir -p monitoring/{dashboards,alarms,tests}
# mkdir -p tests/{unit,integration,load,smoke,fixtures}
# mkdir -p scripts config docs docker ".github/workflows"

# # Create initial files
# touch README.md .gitignore requirements.txt setup.py .env.example
# touch infrastructure/cloudformation.yaml
# touch lambda_functions/claim-ingestion-handler/lambda_function.py
# touch ml_models/fraud_detection.py
# touch database/schema.sql
# touch docker-compose.yml

# echo "✅ Folder structure created!"
# SETUP
# chmod +x setup_folders.sh