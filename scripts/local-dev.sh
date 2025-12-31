#!/bin/bash

# Real Estate Observability Local Development Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SERVICE="all"
BUILD_IMAGES=false
DETACHED=false

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
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start                  Start local development environment"
    echo "  stop                   Stop local development environment"
    echo "  restart                Restart local development environment"
    echo "  logs                   Show logs from services"
    echo "  shell                  Open shell in development container"
    echo "  test                   Run tests in container"
    echo ""
    echo "Options:"
    echo "  -s, --service SERVICE  Specific service to operate on [default: all]"
    echo "  -b, --build            Rebuild images before starting"
    echo "  -d, --detached         Run in detached mode"
    echo "  -h, --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start               # Start all services"
    echo "  $0 start -b            # Rebuild and start services"
    echo "  $0 logs -s cdk         # Show logs for CDK service"
    echo "  $0 shell               # Open shell in dev container"
    echo "  $0 test                # Run tests in container"
}

# Parse command line arguments
COMMAND=""
if [[ $# -gt 0 ]] && [[ ! "$1" =~ ^- ]]; then
    COMMAND="$1"
    shift
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -b|--build)
            BUILD_IMAGES=true
            shift
            ;;
        -d|--detached)
            DETACHED=true
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

# Default command is start
if [[ -z "$COMMAND" ]]; then
    COMMAND="start"
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    print_error "Neither docker-compose nor docker compose is available"
    exit 1
fi

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        print_info "Creating .env file from .env.example"
        cp .env.example .env
    else
        print_warning ".env file not found. Creating basic one..."
        cat > .env << EOF
# Local development environment
ENVIRONMENT=dev
AWS_REGION=us-east-1
LOG_LEVEL=DEBUG
DYNAMODB_TABLE_PREFIX=local-real-estate-observability
API_STAGE=local
CORS_ORIGINS=*
ENABLE_XRAY=false
ENABLE_CUSTOM_METRICS=true
EOF
    fi
fi

# Execute commands
case $COMMAND in
    start)
        print_info "Starting local development environment..."
        
        DOCKER_ARGS=""
        if [[ "$BUILD_IMAGES" == true ]]; then
            DOCKER_ARGS="$DOCKER_ARGS --build"
        fi
        
        if [[ "$DETACHED" == true ]]; then
            DOCKER_ARGS="$DOCKER_ARGS -d"
        fi
        
        if [[ "$SERVICE" != "all" ]]; then
            DOCKER_ARGS="$DOCKER_ARGS $SERVICE"
        fi
        
        $COMPOSE_CMD up $DOCKER_ARGS
        
        if [[ "$DETACHED" == true ]]; then
            print_success "Services started in detached mode"
            print_info "Use '$0 logs' to view logs"
            print_info "Use '$0 stop' to stop services"
        fi
        ;;
        
    stop)
        print_info "Stopping local development environment..."
        
        if [[ "$SERVICE" != "all" ]]; then
            $COMPOSE_CMD stop $SERVICE
        else
            $COMPOSE_CMD down
        fi
        
        print_success "Services stopped"
        ;;
        
    restart)
        print_info "Restarting local development environment..."
        
        if [[ "$SERVICE" != "all" ]]; then
            $COMPOSE_CMD restart $SERVICE
        else
            $COMPOSE_CMD restart
        fi
        
        print_success "Services restarted"
        ;;
        
    logs)
        print_info "Showing logs..."
        
        if [[ "$SERVICE" != "all" ]]; then
            $COMPOSE_CMD logs -f $SERVICE
        else
            $COMPOSE_CMD logs -f
        fi
        ;;
        
    shell)
        print_info "Opening shell in development container..."
        
        SERVICE_NAME="cdk"
        if [[ "$SERVICE" != "all" ]]; then
            SERVICE_NAME="$SERVICE"
        fi
        
        $COMPOSE_CMD exec $SERVICE_NAME bash
        ;;
        
    test)
        print_info "Running tests in container..."
        
        $COMPOSE_CMD exec cdk ./scripts/test.sh
        ;;
        
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac