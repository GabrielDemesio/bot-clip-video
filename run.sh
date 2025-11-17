#!/bin/bash

# Video Lesson Splitter - Helper Script
# Usage: ./run.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Video Lesson Splitter${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not found. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Build Docker image
build() {
    print_header
    print_info "Building Docker image..."
    docker-compose build
    print_success "Build completed!"
}

# Run the application
run() {
    print_header
    
    # Check if videos_input has any videos
    if [ -z "$(ls -A videos_input 2>/dev/null)" ]; then
        print_warning "No videos found in videos_input/"
        print_info "Please add your videos to the videos_input/ directory"
        exit 1
    fi
    
    print_info "Starting Video Lesson Splitter..."
    docker-compose run --rm video-splitter
}

# Run in background
run_detached() {
    print_header
    print_info "Starting Video Lesson Splitter in background..."
    docker-compose up -d
    print_success "Container started in background"
    print_info "View logs with: ./run.sh logs"
}

# View logs
logs() {
    docker-compose logs -f --tail=100
}

# Stop containers
stop() {
    print_header
    print_info "Stopping containers..."
    docker-compose down
    print_success "Containers stopped"
}

# Clean everything
clean() {
    print_header
    print_warning "This will remove all containers, volumes, and images"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose down -v --rmi all
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Enter container shell
shell() {
    print_header
    print_info "Opening shell in container..."
    docker-compose run --rm video-splitter /bin/bash
}

# Show stats
stats() {
    docker stats video-lesson-splitter
}

# Setup (create directories)
setup() {
    print_header
    print_info "Setting up directories..."
    
    mkdir -p videos_input
    mkdir -p lessons_output
    mkdir -p logs
    
    # Set permissions
    chmod -R 755 videos_input lessons_output logs
    
    print_success "Directories created"
    print_info "Add your videos to: videos_input/"
}

# Show help
show_help() {
    print_header
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build Docker image"
    echo "  run         Run the application (interactive)"
    echo "  detached    Run in background"
    echo "  logs        View logs"
    echo "  stop        Stop containers"
    echo "  clean       Remove all containers, volumes, and images"
    echo "  shell       Open shell in container"
    echo "  stats       Show container resource usage"
    echo "  setup       Create necessary directories"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run.sh build          # Build the image"
    echo "  ./run.sh run            # Run interactively"
    echo "  ./run.sh logs           # View logs"
    echo ""
}

# Main
main() {
    case "${1:-help}" in
        build)
            check_docker
            build
            ;;
        run)
            check_docker
            run
            ;;
        detached|bg)
            check_docker
            run_detached
            ;;
        logs)
            logs
            ;;
        stop)
            stop
            ;;
        clean)
            clean
            ;;
        shell|bash)
            check_docker
            shell
            ;;
        stats)
            stats
            ;;
        setup)
            setup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

