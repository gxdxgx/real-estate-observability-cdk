#!/bin/bash

# Real Estate Observability Test Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=true
VERBOSE=false

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
    echo "  -t, --type TYPE        Test type (unit, integration, e2e, all) [default: all]"
    echo "  -c, --no-coverage      Skip coverage report"
    echo "  -v, --verbose          Verbose output"
    echo "  -h, --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                     # Run all tests with coverage"
    echo "  $0 -t unit             # Run only unit tests"
    echo "  $0 -t integration -v   # Run integration tests with verbose output"
    echo "  $0 -c                  # Run tests without coverage"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--no-coverage)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
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

# Validate test type
if [[ ! "$TEST_TYPE" =~ ^(unit|integration|e2e|all)$ ]]; then
    print_error "Invalid test type: $TEST_TYPE. Must be one of: unit, integration, e2e, all"
    exit 1
fi

print_info "Running $TEST_TYPE tests..."

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    print_warning "pytest not found. Installing test dependencies..."
    
    if [[ -f "tests/requirements.txt" ]]; then
        pip install -r tests/requirements.txt
    else
        pip install pytest pytest-cov pytest-mock moto
    fi
fi

# Set up test environment
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
export ENVIRONMENT=test
export AWS_DEFAULT_REGION=us-east-1
export LOG_LEVEL=DEBUG

# Build pytest command
PYTEST_ARGS=""

# Test type selection
case $TEST_TYPE in
    unit)
        PYTEST_ARGS="$PYTEST_ARGS tests/unit"
        ;;
    integration)
        PYTEST_ARGS="$PYTEST_ARGS tests/integration"
        ;;
    e2e)
        PYTEST_ARGS="$PYTEST_ARGS tests/e2e"
        ;;
    all)
        PYTEST_ARGS="$PYTEST_ARGS tests/"
        ;;
esac

# Coverage options
if [[ "$COVERAGE" == true ]]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=src --cov-report=term-missing --cov-report=html:htmlcov"
    
    # Set coverage thresholds
    case $TEST_TYPE in
        unit)
            PYTEST_ARGS="$PYTEST_ARGS --cov-fail-under=85"
            ;;
        integration)
            PYTEST_ARGS="$PYTEST_ARGS --cov-fail-under=70"
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS --cov-fail-under=80"
            ;;
    esac
fi

# Verbose output
if [[ "$VERBOSE" == true ]]; then
    PYTEST_ARGS="$PYTEST_ARGS -v -s"
else
    PYTEST_ARGS="$PYTEST_ARGS -q"
fi

# Additional pytest options
PYTEST_ARGS="$PYTEST_ARGS --tb=short --color=yes"

# Run tests
print_info "Executing: pytest $PYTEST_ARGS"

if pytest $PYTEST_ARGS; then
    print_success "All tests passed! ✅"
    
    if [[ "$COVERAGE" == true ]]; then
        print_info "Coverage report generated in htmlcov/ directory"
        
        # Show coverage summary
        if command -v coverage &> /dev/null; then
            echo ""
            print_info "Coverage Summary:"
            coverage report --show-missing
        fi
    fi
    
    exit 0
else
    print_error "Some tests failed! ❌"
    exit 1
fi