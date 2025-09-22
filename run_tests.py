#!/usr/bin/env python
"""
Wallai Test Runner - Execute Playwright E2E tests
"""
import os
import sys
import subprocess
import time
import signal
import django
from django.core.management import execute_from_command_line

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

def start_django_server(port=8001):
    """Start Django development server for testing"""
    print(f"Starting Django server on port {port}...")

    # Start server in background
    server_process = subprocess.Popen([
        sys.executable, 'manage.py', 'runserver', f'localhost:{port}', '--noreload'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)

    return server_process

def run_playwright_tests(test_pattern=None, headed=False, mobile_only=False):
    """Run Playwright tests with specified options"""
    print("Running Playwright E2E tests...")

    cmd = ['python', '-m', 'pytest', 'tests/', '-v']

    # Add browser options
    if headed:
        cmd.extend(['--headed'])
    else:
        cmd.extend(['--browser', 'chromium'])

    # Add test pattern filter
    if test_pattern:
        cmd.extend(['-k', test_pattern])

    # Mobile only tests
    if mobile_only:
        cmd.extend(['-m', 'mobile'])

    # Add output options
    cmd.extend(['--tb=short', '--strict-markers'])

    print(f"Running command: {' '.join(cmd)}")

    # Run tests
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("Test Results:")
    print("=" * 50)
    print(result.stdout)

    if result.stderr:
        print("Errors:")
        print(result.stderr)

    return result.returncode == 0

def main():
    """Main test runner function"""
    import argparse

    parser = argparse.ArgumentParser(description='Wallai E2E Test Runner')
    parser.add_argument('--headed', action='store_true',
                       help='Run tests in headed mode (visible browser)')
    parser.add_argument('--mobile', action='store_true',
                       help='Run only mobile tests')
    parser.add_argument('--auth', action='store_true',
                       help='Run only authentication tests')
    parser.add_argument('--spaces', action='store_true',
                       help='Run only spaces tests')
    parser.add_argument('--budgets', action='store_true',
                       help='Run only budget tests')
    parser.add_argument('--pattern', type=str,
                       help='Run tests matching pattern')
    parser.add_argument('--port', type=int, default=8001,
                       help='Django server port (default: 8001)')

    args = parser.parse_args()

    # Build test pattern
    test_pattern = args.pattern
    if args.auth:
        test_pattern = 'auth'
    elif args.spaces:
        test_pattern = 'spaces'
    elif args.budgets:
        test_pattern = 'budgets'

    server_process = None

    try:
        # Start Django server
        server_process = start_django_server(args.port)

        # Run tests
        success = run_playwright_tests(
            test_pattern=test_pattern,
            headed=args.headed,
            mobile_only=args.mobile
        )

        if success:
            print("All tests passed!")
            return 0
        else:
            print("Some tests failed!")
            return 1

    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1

    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

    finally:
        # Cleanup: stop Django server
        if server_process:
            print("Stopping Django server...")
            server_process.terminate()
            server_process.wait()

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)