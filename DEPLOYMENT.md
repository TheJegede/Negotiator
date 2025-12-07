# AWS Deployment Guide

## Prerequisites
- AWS Account
- AWS CLI configured
- Python 3.11
- Node.js (for frontend build if needed)

## Backend Deployment (Lambda + API Gateway)

### Step 1: Prepare Backend Package

```bash
cd backend/app
pip install -r ../requirements.txt -t package/
cp main.py package/
cp -r services package/
```

### Step 2: Create Deployment Package

```bash
cd package
zip -r ../deployment.zip .
cd ..
```

### Step 3: Create Lambda Function

```bash
aws lambda create-function \
  --function-name ai-negotiator-api \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler main.lambda_handler \
  --zip-file fileb://deployment.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables={GOOGLE_API_KEY=your_gemini_api_key}
```

### Step 4: Create API Gateway

1. Go to AWS Console > API Gateway
2. Create new HTTP API
3. Add Lambda integration pointing to `ai-negotiator-api`
4. Configure routes:
   - POST /api/sessions/new
   - POST /api/chat
   - GET /api/sessions/{session_id}
   - POST /api/evaluate
5. Enable CORS
6. Deploy API

### Step 5: Note API Endpoint

Copy the API Gateway invoke URL (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com`)

## Frontend Deployment (Amplify)

### Step 1: Update API Configuration

Edit `frontend/api.js`:

```javascript
const API_BASE_URL = 'https://YOUR_API_GATEWAY_URL';
```

### Step 2: Deploy to Amplify

#### Option A: Console Deployment

1. Go to AWS Amplify Console
2. Click "Host web app"
3. Choose "Deploy without Git provider"
4. Upload frontend folder as ZIP
5. Click Deploy

#### Option B: CLI Deployment

```bash
cd frontend
zip -r frontend.zip .
aws s3 cp frontend.zip s3://your-bucket/
# Use Amplify Console to deploy from S3
```

### Step 3: Configure Custom Domain (Optional)

1. Go to Amplify Console > Domain Management
2. Add custom domain
3. Update DNS records

## Environment Variables

### Lambda Environment Variables

- `GOOGLE_API_KEY`: Your Gemini API key

### Frontend Environment Variables (Build-time)

Update in `frontend/api.js`:
- `API_BASE_URL`: Your API Gateway URL

## Testing

### Test Backend
```bash
curl -X POST https://YOUR_API_GATEWAY_URL/api/sessions/new \
  -H "Content-Type: application/json" \
  -d '{"student_id": "test123"}'
```

### Test Frontend
1. Open Amplify URL in browser
2. Try creating a new chat session
3. Send a test message

## Monitoring

### CloudWatch Logs

- Lambda logs: `/aws/lambda/ai-negotiator-api`
- API Gateway logs: Enable in API Gateway settings

### Metrics to Monitor

- Lambda invocations
- API Gateway requests
- Error rates
- Response times

## Cost Optimization

1. Set Lambda timeout to minimum required (30s recommended)
2. Use Lambda reserved concurrency if needed
3. Monitor API Gateway requests
4. Use Amplify free tier for static hosting

## Troubleshooting

### CORS Issues
- Ensure API Gateway has CORS enabled
- Check `Access-Control-Allow-Origin` headers

### Lambda Timeout
- Increase Lambda timeout if needed
- Optimize code for faster responses

### API Gateway 502 Errors
- Check Lambda function logs
- Verify function is returning proper response format

## Security Best Practices

1. Use API Gateway API keys for production
2. Implement rate limiting
3. Use AWS WAF for DDoS protection
4. Store secrets in AWS Secrets Manager (not environment variables)
5. Enable CloudWatch logging for auditing

## Scaling Considerations

- Lambda auto-scales automatically
- Set reserved concurrency to prevent runaway costs
- Consider DynamoDB for session storage instead of in-memory
- Implement caching with API Gateway or CloudFront

## DynamoDB Integration (Optional)

To use DynamoDB instead of in-memory storage:

1. Create DynamoDB table:
```bash
aws dynamodb create-table \
  --table-name negotiation-sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

2. Update Lambda IAM role with DynamoDB permissions

3. Modify `main.py` to use DynamoDB (code included in comments)
