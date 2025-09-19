#!/usr/bin/env python
"""
Enhanced development server startup script for 12mo Budget Tracker
"""
import os
import sys
import django
from django.utils import timezone


def show_startup_banner():
    """Display a nice startup banner with project information"""

    # Get project info
    project_name = "12mo - Personal Budget Tracker"
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # Server details
    addr, port = '127.0.0.1', '8000'

    # Create banner
    banner = f"""
================================================================================
                          {project_name}
================================================================================
  Starting Development Server...

  Server Information:
     * URL: http://{addr}:{port}/
     * Admin: http://{addr}:{port}/admin/
     * Dashboard: http://{addr}:{port}/dashboard/

  Environment:
     * Python: {python_version}
     * Database: SQLite
     * Debug Mode: ON

  Hot Reload: ENABLED
     Files are being watched for changes...

  Quick Links:
     * Budgets: http://{addr}:{port}/budgets/
     * Spaces: http://{addr}:{port}/spaces/
     * Categories: http://{addr}:{port}/budgets/categories/

  Tips:
     * Press Ctrl+C to stop the server
     * Changes to Python files trigger auto-reload
     * Template changes are detected automatically

  Started at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================
"""

    print(banner)
    print("WARNING: DEBUG MODE is ON - Remember to turn it OFF in production!")
    print("SUCCESS: Server is ready! Visit the URLs above to start using the application.")
    print("")


def main():
    """Start the development server with enhanced features"""

    # Set the settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

    try:
        django.setup()
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Show banner
    show_startup_banner()

    # Import and run the standard runserver
    from django.core.management import execute_from_command_line

    # Set default arguments
    if len(sys.argv) == 1:
        sys.argv = ['start_dev.py', 'runserver']

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()