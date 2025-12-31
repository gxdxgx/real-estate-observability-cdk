#!/bin/bash

# Real Estate Observability CDK Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
SKIP_TESTS=false
AUTO_APPROVE=false

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENVIRONMENT    Target environment (dev, staging, prod) [default: dev]"
    echo "  -t, --skip-tests                Skip running tests"
    echo "  -y, --auto-approve              Auto approve CDK deployment"
    echo "  -h, --help                      Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                              # Deploy to dev environment"
    echo "  $0 -e prod                      # Deploy to production"
    echo "  $0 -e staging -t                # Deploy to staging, skip tests"
    echo "  $0 -e prod -y                   # Deploy to prod with auto-approve"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -y|--auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod"
    exit 1
fi

print_info "Starting deployment to $ENVIRONMENT environment"

# Check prerequisites
print_info "Checking prerequisites..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    print_error "AWS CDK is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run 'aws configure' or set environment variables."
    exit 1
fi

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

print_info "AWS Account: $AWS_ACCOUNT"
print_info "AWS Region: $AWS_REGION"

# Set environment variables
export ENVIRONMENT=$ENVIRONMENT
export AWS_REGION=$AWS_REGION

# Load environment-specific variables if they exist
ENV_FILE=".env.${ENVIRONMENT}"
if [[ -f "$ENV_FILE" ]]; then
    print_info "Loading environment variables from $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Run tests (unless skipped)
if [[ "$SKIP_TESTS" != true ]]; then
    print_info "Running tests..."
    
    if [[ -f "tests/requirements.txt" ]]; then
        pip install -r tests/requirements.txt -q
    fi
    
    if command -v pytest &> /dev/null; then
        if ! pytest tests/ -q; then
            print_error "Tests failed. Deployment aborted."
            exit 1
        fi
        print_success "All tests passed"
    else
        print_warning "pytest not found, skipping tests"
    fi
else
    print_warning "Skipping tests (--skip-tests flag used)"
fi

# CDK Bootstrap (if needed)
print_info "Checking CDK bootstrap status..."
cd infrastructure

if ! cdk list --context environment=$ENVIRONMENT &> /dev/null; then
    print_info "Bootstrapping CDK for account $AWS_ACCOUNT in region $AWS_REGION..."
    cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION
    print_success "CDK bootstrap completed"
fi

# CDK Synthesize
print_info "Synthesizing CloudFormation templates..."
if ! cdk synth --context environment=$ENVIRONMENT; then
    print_error "CDK synthesis failed"
    exit 1
fi

# Show diff (for non-prod environments or if auto-approve is not set)
if [[ "$ENVIRONMENT" != "prod" ]] || [[ "$AUTO_APPROVE" != true ]]; then
    print_info "Showing deployment diff..."
    cdk diff --context environment=$ENVIRONMENT || true
fi

# Confirm deployment for production
if [[ "$ENVIRONMENT" == "prod" ]] && [[ "$AUTO_APPROVE" != true ]]; then
    echo ""
    print_warning "You are about to deploy to PRODUCTION environment!"
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
fi

# Deploy
print_info "Deploying stacks to $ENVIRONMENT..."

DEPLOY_ARGS="--context environment=$ENVIRONMENT"
if [[ "$AUTO_APPROVE" == true ]]; then
    DEPLOY_ARGS="$DEPLOY_ARGS --require-approval never"
fi

if cdk deploy --all $DEPLOY_ARGS; then
    print_success "Deployment completed successfully!"
    
    # Show outputs
    print_info "Stack outputs:"
    cdk list --context environment=$ENVIRONMENT | while read -r stack; do
        echo ""
        print_info "Outputs for $stack:"
        aws cloudformation describe-stacks \
            --stack-name "$stack" \
            --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
            --output table 2>/dev/null || true
    done
else
    print_error "Deployment failed!"
    exit 1
fi

cd ..

print_success "🎉 Deployment to $ENVIRONMENT completed successfully!"

# Show next steps
echo ""
print_info "Next steps:"
echo "1. Test your API endpoints"
echo "2. Monitor CloudWatch logs and metrics"
echo "3. Set up monitoring alerts if needed"

if [[ "$ENVIRONMENT" == "dev" ]]; then
    echo "4. Consider deploying to staging when ready"
fi