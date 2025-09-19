#!/usr/bin/env python
"""
Simple development server starter
"""
import os
import sys
import subprocess
from datetime import datetime


def main():
    """Start the development server with clear messages"""

    print("=" * 80)
    print("                   12mo - Personal Budget Tracker")
    print("=" * 80)
    print(f"Starting Development Server at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    print("Server URLs:")
    print("  * Main:       http://127.0.0.1:8000/")
    print("  * Dashboard:  http://127.0.0.1:8000/dashboard/")
    print("  * Budgets:    http://127.0.0.1:8000/budgets/")
    print("  * Admin:      http://127.0.0.1:8000/admin/")
    print("")
    print("Environment: Development (DEBUG=True)")
    print("Hot Reload: ENABLED - File changes will trigger automatic reload")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print("")

    # Set environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

    # Start the server
    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver'], check=True)
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("Server stopped by user")
        print("=" * 80)
    except Exception as e:
        print(f"Error starting server: {e}")


if __name__ == '__main__':
    main()