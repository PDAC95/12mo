import os
import sys
from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.management.base import CommandError
from django.conf import settings
from django.utils import timezone


class Command(RunserverCommand):
    help = 'Enhanced runserver with better startup messages'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--no-banner',
            action='store_true',
            help='Disable the startup banner',
        )

    def handle(self, *args, **options):
        if not options.get('no_banner'):
            self.show_startup_banner(options)

        # Call the original runserver command
        super().handle(*args, **options)

    def show_startup_banner(self, options):
        """Display a nice startup banner with project information"""

        # Get server details
        addrport = options.get('addrport', '127.0.0.1:8000')
        if ':' in addrport:
            addr, port = addrport.rsplit(':', 1)
        else:
            addr, port = '127.0.0.1', addrport

        # Get project info
        project_name = "12mo - Personal Budget Tracker"
        django_version = self.get_django_version()
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Environment info
        debug_mode = getattr(settings, 'DEBUG', False)
        db_engine = settings.DATABASES['default']['ENGINE'].split('.')[-1]

        # Create banner
        banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          {project_name}                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🚀 Starting Development Server...                                           ║
║                                                                              ║
║  📡 Server Information:                                                      ║
║     • URL: http://{addr}:{port}/                                           ║
║     • Admin: http://{addr}:{port}/admin/                                   ║
║     • API: http://{addr}:{port}/api/                                       ║
║                                                                              ║
║  ⚙️  Environment:                                                            ║
║     • Django: {django_version}                                              ║
║     • Python: {python_version}                                              ║
║     • Database: {db_engine.upper()}                                         ║
║     • Debug Mode: {'ON' if debug_mode else 'OFF'}                           ║
║                                                                              ║
║  🔥 Hot Reload: ENABLED                                                      ║
║     Files are being watched for changes...                                  ║
║                                                                              ║
║  📝 Quick Links:                                                             ║
║     • Dashboard: http://{addr}:{port}/dashboard/                           ║
║     • Budgets: http://{addr}:{port}/budgets/                               ║
║     • Spaces: http://{addr}:{port}/spaces/                                 ║
║                                                                              ║
║  💡 Tips:                                                                    ║
║     • Press Ctrl+C to stop the server                                       ║
║     • Changes to Python files trigger auto-reload                           ║
║     • Static files are served automatically                                 ║
║                                                                              ║
║  🕐 Started at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

        self.stdout.write(banner)

        # Show additional debug info if in debug mode
        if debug_mode:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  DEBUG MODE is ON - Remember to turn it OFF in production!"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "✅ Server is ready! Visit the URLs above to start using the application."
            )
        )
        self.stdout.write("")

    def get_django_version(self):
        """Get Django version"""
        try:
            import django
            return django.get_version()
        except ImportError:
            return "Unknown"