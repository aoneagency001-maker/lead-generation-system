#!/bin/bash

# =============================================================================
# QUICK DEPLOY SCRIPT
# =============================================================================
#
# This is a SIMPLE deployment script that:
# 1. Runs critical tests
# 2. Builds Docker images
# 3. Deploys to production
#
# NO complex CI/CD pipeline - just works!
#
# Usage:
#   ./scripts/quick_deploy.sh
#
# Requirements:
#   - Docker and docker-compose installed
#   - .env.production file exists
#   - Tests pass
#
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

log_info "Starting Quick Deploy..."
echo ""

# Check if running from project root
if [ ! -f "requirements.txt" ]; then
    log_error "Must run from project root directory!"
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    log_error ".env.production file not found!"
    log_info "Copy .env.example to .env.production and configure it"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker is not running! Start Docker first."
    exit 1
fi

log_success "Pre-flight checks passed"
echo ""

# =============================================================================
# STEP 1: RUN CRITICAL TESTS
# =============================================================================

log_info "STEP 1/4: Running critical tests..."

if [ -f "tests/test_critical.py" ]; then
    # Install pytest if not installed
    if ! python -m pytest --version > /dev/null 2>&1; then
        log_warning "pytest not installed, installing..."
        pip install pytest pytest-asyncio -q
    fi
    
    # Run critical tests
    python -m pytest tests/test_critical.py -v --tb=short
    
    if [ $? -ne 0 ]; then
        log_error "Critical tests FAILED! Fix issues before deploying."
        exit 1
    fi
    
    log_success "All critical tests passed"
else
    log_warning "No critical tests found, skipping..."
fi

echo ""

# =============================================================================
# STEP 2: BUILD DOCKER IMAGES
# =============================================================================

log_info "STEP 2/4: Building Docker images..."

# Use production docker-compose
docker-compose -f docker-compose.prod.yml build

if [ $? -ne 0 ]; then
    log_error "Docker build FAILED!"
    exit 1
fi

log_success "Docker images built successfully"
echo ""

# =============================================================================
# STEP 3: STOP OLD CONTAINERS (if running)
# =============================================================================

log_info "STEP 3/4: Stopping old containers..."

docker-compose -f docker-compose.prod.yml down

log_success "Old containers stopped"
echo ""

# =============================================================================
# STEP 4: START NEW CONTAINERS
# =============================================================================

log_info "STEP 4/4: Starting new containers..."

# Start in detached mode
docker-compose -f docker-compose.prod.yml up -d

if [ $? -ne 0 ]; then
    log_error "Failed to start containers!"
    exit 1
fi

# Wait a bit for containers to start
sleep 5

# Check if containers are running
RUNNING=$(docker-compose -f docker-compose.prod.yml ps --services --filter "status=running" | wc -l)
TOTAL=$(docker-compose -f docker-compose.prod.yml ps --services | wc -l)

if [ $RUNNING -eq $TOTAL ]; then
    log_success "All containers started successfully"
else
    log_warning "$RUNNING/$TOTAL containers running"
fi

echo ""

# =============================================================================
# CLEANUP
# =============================================================================

log_info "Cleaning up old Docker images..."

# Remove dangling images
docker image prune -f > /dev/null 2>&1

log_success "Cleanup complete"
echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "DEPLOYMENT COMPLETE! 🚀"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

log_info "Running containers:"
docker-compose -f docker-compose.prod.yml ps

echo ""
log_info "View logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""

log_info "Stop deployment:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""

log_success "Deployment successful! 🎉"

