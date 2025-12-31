#!/bin/bash

# LocalStackへのローカルデプロイスクリプト
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"

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
    echo "  -h, --help                      Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                              # Deploy to LocalStack (dev)"
    echo "  $0 -e dev                      # Deploy to LocalStack (dev)"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
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

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if LocalStack is running
if ! docker ps | grep -q real-estate-localstack; then
    print_warning "LocalStack container is not running. Starting it..."
    docker-compose up -d localstack
    
    # Wait for LocalStack to be ready
    print_info "Waiting for LocalStack to be ready..."
    sleep 10
    
    # Check LocalStack health
    if ! curl -f http://localhost:4566/health &> /dev/null; then
        print_error "LocalStack is not healthy. Please check the logs: docker-compose logs localstack"
        exit 1
    fi
fi

print_info "Deploying to LocalStack ($ENVIRONMENT environment)"

# Set LocalStack environment variables
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_REGION=us-east-1

# Check if we're in a container or on host
if [ -f /.dockerenv ]; then
    # Inside container - use service name
    export AWS_ENDPOINT_URL=http://localstack:4566
    CDK_CMD="cdk"
else
    # On host - use localhost
    export AWS_ENDPOINT_URL=http://localhost:4566
    CDK_CMD="docker-compose exec -T cdk cdk"
fi

# CDK Bootstrap (if needed)
print_info "Bootstrapping CDK for LocalStack..."
if [ -f /.dockerenv ]; then
    # Inside container
    cd infrastructure
    AWS_ENDPOINT_URL=http://localstack:4566 \
    cdk bootstrap aws://000000000000/us-east-1 \
        --endpoint-url=http://localstack:4566 \
        --profile default || print_warning "Bootstrap may have already been done"
    cd ..
else
    # On host
    docker-compose exec -T cdk bash -c "
        export AWS_ENDPOINT_URL=http://localstack:4566
        export AWS_ACCESS_KEY_ID=test
        export AWS_SECRET_ACCESS_KEY=test
        export AWS_DEFAULT_REGION=us-east-1
        cd infrastructure
        cdk bootstrap aws://000000000000/us-east-1 \
            --endpoint-url=http://localstack:4566 \
            --profile default || true
    "
fi

# CDK Synthesize
print_info "Synthesizing CloudFormation templates..."
if [ -f /.dockerenv ]; then
    cd infrastructure
    AWS_ENDPOINT_URL=http://localstack:4566 \
    cdk synth --context environment=$ENVIRONMENT || {
        print_error "CDK synthesis failed"
        exit 1
    }
    cd ..
else
    docker-compose exec -T cdk bash -c "
        export AWS_ENDPOINT_URL=http://localstack:4566
        export AWS_ACCESS_KEY_ID=test
        export AWS_SECRET_ACCESS_KEY=test
        export AWS_DEFAULT_REGION=us-east-1
        cd infrastructure
        cdk synth --context environment=$ENVIRONMENT
    " || {
        print_error "CDK synthesis failed"
        exit 1
    }
fi

# Deploy
print_info "Deploying stacks to LocalStack..."

if [ -f /.dockerenv ]; then
    # Inside container
    cd infrastructure
    AWS_ENDPOINT_URL=http://localstack:4566 \
    AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1 \
    cdk deploy --all \
        --context environment=$ENVIRONMENT \
        --require-approval never \
        --endpoint-url=http://localstack:4566 || {
        print_error "Deployment failed!"
        exit 1
    }
    cd ..
else
    # On host
    docker-compose exec -T cdk bash -c "
        export AWS_ENDPOINT_URL=http://localstack:4566
        export AWS_ACCESS_KEY_ID=test
        export AWS_SECRET_ACCESS_KEY=test
        export AWS_DEFAULT_REGION=us-east-1
        cd infrastructure
        cdk deploy --all \
            --context environment=$ENVIRONMENT \
            --require-approval never \
            --endpoint-url=http://localstack:4566
    " || {
        print_error "Deployment failed!"
        exit 1
    }
fi

print_success "🎉 Deployment to LocalStack completed successfully!"

# Show LocalStack endpoints
echo ""
print_info "LocalStack Endpoints:"
echo "  - API Gateway: http://localhost:4566/restapis"
echo "  - DynamoDB: http://localhost:4566/dynamodb"
echo "  - Lambda: http://localhost:4566/lambda"
echo "  - CloudWatch: http://localhost:4566/cloudwatch"

# Show how to test
echo ""
print_info "To test your API:"
echo "  1. Get the API Gateway endpoint:"
echo "     aws --endpoint-url=http://localhost:4566 apigateway get-rest-apis"
echo ""
echo "  2. Test the health endpoint:"
echo "     curl http://localhost:4566/restapis/<api-id>/local/_user_request_/health"

