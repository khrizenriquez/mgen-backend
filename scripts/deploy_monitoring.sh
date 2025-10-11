#!/bin/bash
# Deploy Monitoring Stack Script
# Deploys Prometheus, Grafana, Loki, and Promtail for Donations Guatemala

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="donations-gt-monitoring"
ENVIRONMENT=${1:-"development"}
DOCKER_COMPOSE_FILE="docker-compose.railway.yml"

# Function to print colored output
print_status() {
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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed."
        exit 1
    fi
}

# Function to wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        ((attempt++))
    done

    print_error "$service_name failed to start within expected time"
    return 1
}

# Function to deploy monitoring stack
deploy_monitoring() {
    print_status "🚀 Starting Donations Guatemala Monitoring Stack Deployment"
    print_status "Environment: $ENVIRONMENT"
    echo

    # Check prerequisites
    check_docker
    check_docker_compose

    # Validate environment variables for production
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Validating production environment variables..."

        required_vars=(
            "DATABASE_URL"
            "GRAFANA_ADMIN_USER"
            "GRAFANA_ADMIN_PASSWORD"
        )

        for var in "${required_vars[@]}"; do
            if [ -z "${!var}" ]; then
                print_error "Required environment variable $var is not set"
                print_error "Please set it in your .env file or environment"
                exit 1
            fi
        done

        # Warn about default passwords in development
        if [ "${GRAFANA_ADMIN_USER}" = "admin" ] && [ "$ENVIRONMENT" = "production" ]; then
            print_warning "Using default Grafana admin user 'admin' in production!"
            print_warning "Consider changing GRAFANA_ADMIN_USER in your .env file"
        fi

        print_success "Environment variables validated"
    else
        # Development validation
        print_status "Validating development environment variables..."

        if [ -z "${GRAFANA_ADMIN_USER}" ] || [ -z "${GRAFANA_ADMIN_PASSWORD}" ]; then
            print_warning "Grafana credentials not set. Using defaults for development."
            print_warning "Set GRAFANA_ADMIN_USER and GRAFANA_ADMIN_PASSWORD in your .env file for security."
        fi
    fi

    # Stop existing services if running
    print_status "Stopping any existing monitoring services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans 2>/dev/null || true

    # Start services
    print_status "Starting monitoring services..."
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build
    else
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    fi

    # Wait for services to be ready
    echo
    print_status "Waiting for services to initialize..."

    # Wait for Prometheus
    wait_for_service "Prometheus" "http://localhost:9090/-/healthy"

    # Wait for Grafana
    wait_for_service "Grafana" "http://localhost:3000/api/health"

    # Wait for Loki
    wait_for_service "Loki" "http://localhost:3100/ready"

    echo
    print_success "🎉 All monitoring services are running!"
    echo

    # Display access information
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 DONATIONS GUATEMALA MONITORING               ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║ Service          │ URL                    │ Status          ║"
    echo "╠══════════════════╪════════════════════════╪═════════════════╣"
    echo "║ Grafana          │ http://localhost:3000  │ ✅ Running      ║"
    echo "║ Prometheus       │ http://localhost:9090  │ ✅ Running      ║"
    echo "║ Loki             │ http://localhost:3100  │ ✅ Running      ║"
    echo "║ API Metrics      │ http://localhost:8000/metrics │ -        ║"
    echo "║ Business Metrics │ http://localhost:8000/metrics/business │ - ║"
    echo "╚══════════════════╧════════════════════════╧═════════════════╝"
    echo

    if [ "$ENVIRONMENT" = "development" ]; then
        echo "🔐 Grafana Credentials (Development):"
        echo "   Username: admin"
        echo "   Password: donaciones2024"
        echo
    else
        echo "🔐 Grafana Credentials (Production):"
        echo "   Check your Railway environment variables"
        echo
    fi

    echo "📊 Available Dashboards:"
    echo "   • Donations Guatemala - Overview"
    echo "   • System Metrics"
    echo "   • API Performance"
    echo
    echo "📝 Next Steps:"
    echo "   1. Open Grafana at http://localhost:3000"
    echo "   2. Explore the pre-configured dashboards"
    echo "   3. Check Prometheus metrics at http://localhost:9090"
    echo "   4. View logs in Loki at http://localhost:3100"
    echo

    print_success "Monitoring stack deployment completed successfully! 🎉"
}

# Function to stop monitoring stack
stop_monitoring() {
    print_status "Stopping monitoring services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
    print_success "Monitoring services stopped"
}

# Function to show status
show_status() {
    echo "📊 Monitoring Services Status:"
    echo

    services=("prometheus" "grafana" "loki" "promtail" "api")

    for service in "${services[@]}"; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            echo -e "✅ $service: ${GREEN}Running${NC}"
        else
            echo -e "❌ $service: ${RED}Stopped${NC}"
        fi
    done
}

# Function to show logs
show_logs() {
    local service=${1:-"api"}
    print_status "Showing logs for $service..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f "$service"
}

# Function to restart services
restart_services() {
    print_status "Restarting monitoring services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart
    print_success "Services restarted"
}

# Main script logic
case "${2:-deploy}" in
    "deploy")
        deploy_monitoring
        ;;
    "stop")
        stop_monitoring
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$3"
        ;;
    "restart")
        restart_services
        ;;
    *)
        echo "Usage: $0 [environment] [command]"
        echo
        echo "Environments:"
        echo "  development  - Local development setup"
        echo "  production   - Production deployment"
        echo
        echo "Commands:"
        echo "  deploy       - Deploy monitoring stack (default)"
        echo "  stop         - Stop monitoring services"
        echo "  status       - Show services status"
        echo "  logs [svc]   - Show logs for service (default: api)"
        echo "  restart      - Restart all services"
        echo
        echo "Examples:"
        echo "  $0 development deploy    # Deploy for development"
        echo "  $0 production deploy     # Deploy for production"
        echo "  $0 status                 # Check status"
        echo "  $0 logs grafana          # Show Grafana logs"
        exit 1
        ;;
esac

