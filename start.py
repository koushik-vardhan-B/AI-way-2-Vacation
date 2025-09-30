#!/usr/bin/env python3
"""
AI Travel Planner - Startup Script
This script provides different ways to start the application
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import get_settings, validate_environment
from core.logging_config import setup_logging
import logging

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        "fastapi", "uvicorn", "pydantic", "langchain", 
        "langchain-groq", "requests", "python-dotenv"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_environment():
    """Check environment configuration"""
    print("🔍 Checking environment configuration...")
    
    if not os.path.exists(".env"):
        print("⚠️ .env file not found. Copy .env.template to .env and configure your API keys")
        return False
    
    # Validate environment
    is_valid = validate_environment()
    
    if not is_valid:
        print("⚠️ Some environment variables are missing. Check .env.template for guidance")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def start_development():
    """Start the application in development mode"""
    print("🚀 Starting AI Travel Planner in development mode...")
    
    # Setup logging
    setup_logging()
    
    settings = get_settings()
    
    cmd = [
        "uvicorn", "main:app",
        "--host", settings.HOST,
        "--port", str(settings.PORT),
        "--reload",
        "--log-level", "debug" if settings.DEBUG else "info"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down development server...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def start_production():
    """Start the application in production mode"""
    print("🚀 Starting AI Travel Planner in production mode...")
    
    settings = get_settings()
    
    cmd = [
        "gunicorn", "main:app",
        "-w", "4",  # 4 workers
        "-k", "uvicorn.workers.UvicornWorker",
        "--bind", f"{settings.HOST}:{settings.PORT}",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "--log-level", "info"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down production server...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

# def start_docker():
#     """Start using Docker"""
#     print("🐳 Starting AI Travel Planner with Docker...")
    
#     if not os.path.exists("Dockerfile"):
#         print("❌ Dockerfile not found")
#         sys.exit(1)
    
#     try:
#         # Build the image
#         print("🔨 Building Docker image...")
#         subprocess.run(["docker", "build", "-t", "ai-travel-planner", "."], check=True)
        
#         # Run the container
#         print("🚀 Starting Docker container...")
#         subprocess.run([
#             "docker", "run", 
#             "-p", "8000:8000",
#             "--env-file", ".env",
#             "-v", f"{project_root}/output:/app/output",
#             "-v", f"{project_root}/logs:/app/logs",
#             "ai-travel-planner"
#         ], check=True)
        
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Docker command failed: {e}")
#         sys.exit(1)

# def start_docker_compose():
#     """Start using Docker Compose"""
#     print("🐳 Starting AI Travel Planner with Docker Compose...")
    
#     if not os.path.exists("docker-compose.yml"):
#         print("❌ docker-compose.yml not found")
#         sys.exit(1)
    
#     try:
#         subprocess.run(["docker-compose", "up", "--build"], check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Docker Compose failed: {e}")
#         sys.exit(1)

def run_tests():
    """Run the test suite"""
    print("🧪 Running tests...")
    
    try:
        subprocess.run(["python", "-m", "pytest", "tests/", "-v"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Travel Planner Startup Script")
    parser.add_argument(
        "mode", 
        choices=["dev", "prod", "docker", "compose", "test", "check"],
        help="Startup mode"
    )
    parser.add_argument(
        "--skip-checks", 
        action="store_true", 
        help="Skip dependency and environment checks"
    )
    
    args = parser.parse_args()
    
    print("🌍 AI Travel Planner - Startup Script")
    print("=" * 50)
    
    # Run checks unless skipped
    if not args.skip_checks:
        if not check_dependencies():
            sys.exit(1)
        
        if not check_environment() and args.mode not in ["check"]:
            print("💡 Tip: You can still run 'python start.py check' to see what's missing")
            sys.exit(1)
    
    # Execute based on mode
    if args.mode == "dev":
        start_development()
    elif args.mode == "prod":
        start_production()
    # elif args.mode == "docker":
    #     start_docker()
    # elif args.mode == "compose":
    #     start_docker_compose()
    elif args.mode == "test":
        run_tests()
    elif args.mode == "check":
        print("✅ All checks completed!")
    else:
        print(f"❌ Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()