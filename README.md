# AI Negotiator - AWS Migration Project

## Project Overview

This project is an AI-powered negotiation assistant currently in transition from a Streamlit-based application to a cloud-native AWS architecture. The application facilitates intelligent negotiation scenarios using AI agents.

## Current Architecture

### Technology Stack

**Backend:**
- Python/FastAPI (Target framework)
- AWS Lambda (Serverless computing)

**Frontend:**
- Framework: To be determined (recommendations needed)
- Hosting: AWS Amplify

**Existing Components:**
- `app.py` - Legacy Streamlit application (requires migration)
- `frontend/` - New frontend components (index, script, style files)
- `backend/` - Backend services

## Migration Status

### Completed
- Defined AWS services architecture (Lambda + Amplify)
- Selected backend framework (Python/FastAPI)
- Created initial frontend folder structure

### In Progress
- Analysis of `app.py` for AWS compatibility
- Review of negotiation folder components
- Frontend framework selection

### Pending
- Complete transition from Streamlit to AWS Lambda
- Update all files to align with new architecture
- Implement FastAPI backend
- Develop and integrate chosen frontend framework

## Project Goals

1. **AWS Cloud Migration**: Transition from Streamlit to AWS Lambda and Amplify
2. **Modernize Architecture**: Implement FastAPI backend with modern frontend framework
3. **Serverless Deployment**: Leverage AWS Lambda for scalable, cost-effective compute
4. **Static Hosting**: Use AWS Amplify for frontend hosting and deployment

## Technical Considerations

### AWS Services
- **AWS Lambda**: Serverless backend execution
- **AWS Amplify**: Frontend hosting and CI/CD pipeline

### Backend Framework
- **Python/FastAPI**: RESTful API development with async support

### Frontend Framework
- **Status**: Under evaluation
- **Requirements**: Must integrate seamlessly with AWS Amplify and FastAPI backend

## File Structure

```
negotiation/
├── app.py                    # Legacy Streamlit application
├── main.py                   # Main application entry
├── check_models.py           # Model verification utilities
├── backend/                  # Backend services
├── frontend/                 # Frontend components
│   ├── index.html           # Main HTML file
│   ├── script.js            # JavaScript logic
│   └── style.css            # Styling
├── DEPLOYMENT.md            # Deployment documentation
├── IMPROVEMENTS_SUMMARY.md  # Improvement tracking
├── README_AWS.md            # AWS-specific documentation
└── README.md                # This file
```

## Development Plan

### Phase 1: Analysis
- Analyze `app.py` dependencies and Streamlit-specific code
- Identify components requiring refactoring
- Document API endpoints needed for FastAPI

### Phase 2: Backend Migration
- Implement FastAPI endpoints
- Configure AWS Lambda deployment
- Set up API Gateway integration

### Phase 3: Frontend Development
- Select and implement frontend framework
- Develop UI components
- Integrate with FastAPI backend

### Phase 4: AWS Deployment
- Configure AWS Amplify for frontend
- Deploy Lambda functions
- Set up CI/CD pipeline

## Next Steps

1. Complete analysis of `app.py` for migration requirements
2. Review all files in negotiation folder for AWS compatibility
3. Finalize frontend framework selection
4. Begin FastAPI backend implementation
5. Update all documentation to reflect new architecture

## Lessons Learned

- Framework transitions require comprehensive planning and analysis
- AWS serverless architecture offers scalability benefits
- Careful dependency mapping is critical for successful migration

## Documentation

- `DEPLOYMENT.md` - Deployment procedures and guidelines
- `README_AWS.md` - AWS-specific setup and configuration
- `IMPROVEMENTS_SUMMARY.md` - Ongoing improvements and changes

## Contributing

This project is currently in active migration. Please ensure all changes align with the AWS architecture and FastAPI/modern frontend stack.

## License

[To be determined]
