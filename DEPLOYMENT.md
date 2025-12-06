# AI Supply Chain Negotiator - Deployment Guide

## AWS Deployment

### Prerequisites

- AWS Account
- AWS CLI installed and configured
- SAM CLI installed (for Lambda deployment)
- Python 3.10+ (recommended 3.11)

### Backend Deployment (AWS Lambda + API Gateway)

#### Option 1: Using AWS SAM (Recommended)

1. Build the SAM application:
```bash
sam build
```

2. Deploy to AWS:
```bash
sam deploy --guided
```

Follow the prompts to configure:
- Stack Name: negotiator-stack
- AWS Region: us-east-1 (or your preferred region)
- Confirm changes before deploy: Y
- Allow SAM CLI IAM role creation: Y
- Save arguments to configuration file: Y

3. Note the API Gateway endpoint URL from the output.

#### Option 2: Manual Lambda Deployment

1. Create deployment package:
```bash
cd backend
pip install -r requirements.txt -t package/
cp app.py package/
cd package
zip -r ../deployment.zip .
cd ..
```

2. Create Lambda function via AWS Console:
   - Go to AWS Lambda Console
   - Create function
   - Runtime: Python 3.11 (or 3.10+)
   - Architecture: x86_64
   - Upload deployment.zip
   - Set handler to: `app.handler`
   - Increase timeout to 30 seconds
   - Increase memory to 512 MB

3. Create API Gateway:
   - Create new HTTP API or REST API
   - Add routes:
     - GET / → NegotiatorFunction
     - POST /api/sessions/new → NegotiatorFunction
     - POST /api/chat → NegotiatorFunction
     - GET /api/sessions/{session_id} → NegotiatorFunction
   - Enable CORS
   - Deploy API to stage (e.g., 'prod')

### Frontend Deployment (AWS Amplify)

#### Option 1: AWS Amplify Console

1. Push your code to GitHub
2. Go to AWS Amplify Console
3. Click "New app" → "Host web app"
4. Connect your GitHub repository
5. Configure build settings:
   - Build command: (leave empty for static site)
   - Base directory: frontend
   - Publish directory: /
6. Deploy

7. Update frontend/app.js with your API Gateway URL:
```javascript
const API_BASE_URL = 'https://your-api-id.execute-api.region.amazonaws.com/Prod';
```

8. Commit and push the change to trigger redeployment

#### Option 2: AWS S3 + CloudFront

1. Create an S3 bucket:
```bash
aws s3 mb s3://negotiator-frontend
```

2. Configure bucket for static website hosting:
```bash
aws s3 website s3://negotiator-frontend --index-document index.html
```

3. Update frontend/app.js with your API Gateway URL

4. Upload frontend files:
```bash
cd frontend
aws s3 sync . s3://negotiator-frontend --acl public-read
```

5. (Optional) Create CloudFront distribution for HTTPS and caching

### Environment Variables

For production, consider using environment variables for configuration:

**Backend (Lambda):**
- No environment variables needed for basic deployment
- For production with DynamoDB, add:
  - `DYNAMODB_TABLE_NAME`: Name of sessions table

**Frontend:**
- Update `API_BASE_URL` in app.js to point to your API Gateway endpoint

### Database (Optional - Production Enhancement)

For production use, replace in-memory storage with DynamoDB:

1. Create DynamoDB table:
```bash
aws dynamodb create-table \
    --table-name negotiator-sessions \
    --attribute-definitions AttributeName=session_id,AttributeType=S \
    --key-schema AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

2. Update Lambda IAM role to include DynamoDB permissions

3. Modify backend/app.py to use DynamoDB instead of `sessions_db` dict

### Testing Deployment

1. Test the API endpoint:
```bash
curl https://your-api-id.execute-api.region.amazonaws.com/Prod/
```

2. Create a test session:
```bash
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/Prod/api/sessions/new \
  -H "Content-Type: application/json" \
  -d '{"student_id": "TEST123"}'
```

3. Open the Amplify URL in your browser and test the full application

### Monitoring

- CloudWatch Logs: View Lambda function logs
- API Gateway Metrics: Monitor API usage and errors
- X-Ray: Enable for distributed tracing (optional)

### Cost Estimation

Free tier eligible services:
- Lambda: First 1M requests/month free
- API Gateway: First 1M requests/month free
- Amplify: 1000 build minutes/month free
- DynamoDB: 25GB storage + 200M requests/month free

Expected cost for moderate usage (5000 students/month):
- ~$1-5/month

### Security Considerations

1. Enable CORS properly in API Gateway
2. Consider adding API key or authentication for production
3. Use HTTPS only (Amplify and API Gateway provide this)
4. Add rate limiting in API Gateway
5. Implement request validation

### Cleanup

To remove all resources:

```bash
# If using SAM
sam delete

# Or manually delete:
# - Lambda function
# - API Gateway
# - Amplify app
# - S3 bucket
# - DynamoDB table (if created)
```
