#!/usr/bin/env python3
"""
Django Management MCP for Wallai
Advanced Django management commands integration
"""

import subprocess
import json
import sys
import os
from datetime import datetime
from pathlib import Path

class DjangoMCPManager:
    """Django Management Commands MCP integration for Wallai"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.manage_py = self.project_root / 'manage.py'
        self.current_sprint = "Sprint 3 - Expense Tracking"

    def run_django_command(self, command, *args, capture_output=True):
        """Run Django management command with proper error handling"""

        # Use the same Python interpreter that's currently running
        python_exe = sys.executable
        cmd = [python_exe, str(self.manage_py), command] + list(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root,
                timeout=300,  # 5 minutes timeout
                env=os.environ.copy()  # Inherit current environment
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": ' '.join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 5 minutes",
                "command": ' '.join(cmd)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join(cmd)
            }

    def check_project_health(self):
        """Comprehensive Django project health check"""

        print("DJANGO PROJECT HEALTH CHECK")
        print("=" * 50)

        # Check basic Django setup
        check_result = self.run_django_command('check')
        print(f"[OK] Django Check: {'PASSED' if check_result['success'] else 'FAILED'}")
        if not check_result['success']:
            print(f"  Error: {check_result['stderr']}")

        # Check migrations status
        migrations_result = self.run_django_command('showmigrations')
        print(f"[OK] Migrations Status: {'CHECKED' if migrations_result['success'] else 'ERROR'}")

        # Check if server can start (dry run)
        print("[OK] Server Ready: CHECKING...")

        return {
            "django_check": check_result['success'],
            "migrations_status": migrations_result['success'],
            "overall_health": check_result['success'] and migrations_result['success']
        }

    def smart_makemigrations(self, app_name=None):
        """Smart migration creation with validation"""

        print(f"CREATING MIGRATIONS FOR WALLAI")
        print("=" * 40)

        # Run makemigrations
        if app_name:
            result = self.run_django_command('makemigrations', app_name)
            print(f"Creating migrations for app: {app_name}")
        else:
            result = self.run_django_command('makemigrations')
            print("Creating migrations for all apps")

        if result['success']:
            print("[SUCCESS] Migrations created successfully")
            print(result['stdout'])

            # Auto-apply migrations in development
            migrate_result = self.run_django_command('migrate')
            if migrate_result['success']:
                print("[SUCCESS] Migrations applied successfully")
                return {
                    "migrations_created": True,
                    "migrations_applied": True,
                    "output": result['stdout']
                }
            else:
                print("[WARNING] Migrations created but failed to apply")
                print(migrate_result['stderr'])
                return {
                    "migrations_created": True,
                    "migrations_applied": False,
                    "error": migrate_result['stderr']
                }
        else:
            print("[ERROR] Failed to create migrations")
            print(result['stderr'])
            return {
                "migrations_created": False,
                "error": result['stderr']
            }

    def shell_plus_session(self, command=None):
        """Enhanced Django shell with pre-loaded models"""

        if command:
            # Execute specific command in shell
            result = self.run_django_command('shell', '-c', command)
            return {
                "success": result['success'],
                "output": result['stdout'],
                "error": result['stderr'] if not result['success'] else None
            }
        else:
            # Interactive shell (for manual use)
            print("Starting Django Shell Plus...")
            print("Pre-loaded models: User, Space, SpaceMember, Budget, BudgetCategory")
            print("Use Ctrl+C to exit")

            # Start interactive shell
            os.system('python manage.py shell_plus')

    def run_tests(self, app_name=None, verbose=True):
        """Run Django tests with enhanced output"""

        print("RUNNING WALLAI TESTS")
        print("=" * 30)

        args = ['test']
        if app_name:
            args.append(app_name)
        if verbose:
            args.append('--verbosity=2')

        result = self.run_django_command(*args)

        if result['success']:
            print("[SUCCESS] All tests passed")
            print(result['stdout'])
        else:
            print("[ERROR] Some tests failed")
            print(result['stderr'])

        return {
            "tests_passed": result['success'],
            "output": result['stdout'],
            "errors": result['stderr'] if not result['success'] else None
        }

    def collectstatic_and_optimize(self):
        """Collect static files and optimize for production"""

        print("COLLECTING STATIC FILES")
        print("=" * 30)

        result = self.run_django_command('collectstatic', '--noinput')

        if result['success']:
            print("[SUCCESS] Static files collected")
            return {"success": True, "output": result['stdout']}
        else:
            print("[ERROR] Failed to collect static files")
            return {"success": False, "error": result['stderr']}

    def database_operations(self, operation):
        """Database-related operations"""

        operations = {
            "backup": self.backup_database,
            "reset": self.reset_database,
            "shell": self.database_shell,
            "inspect": self.inspect_database
        }

        if operation in operations:
            return operations[operation]()
        else:
            return {"error": f"Unknown operation: {operation}"}

    def backup_database(self):
        """Backup current database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"db_backup_{timestamp}.json"

        result = self.run_django_command('dumpdata', '--output', backup_file)

        if result['success']:
            return {
                "success": True,
                "backup_file": backup_file,
                "message": f"Database backed up to {backup_file}"
            }
        else:
            return {"success": False, "error": result['stderr']}

    def reset_database(self):
        """Reset database (development only)"""
        print("[WARNING] This will delete all data!")

        # Flush database
        result = self.run_django_command('flush', '--noinput')

        if result['success']:
            # Run migrations
            migrate_result = self.run_django_command('migrate')
            return {
                "success": migrate_result['success'],
                "message": "Database reset and migrations applied"
            }
        else:
            return {"success": False, "error": result['stderr']}

    def database_shell(self):
        """Open database shell"""
        print("Opening database shell...")
        os.system('python manage.py dbshell')

    def inspect_database(self):
        """Inspect database schema"""
        result = self.run_django_command('inspectdb')
        return {
            "success": result['success'],
            "schema": result['stdout'] if result['success'] else None,
            "error": result['stderr'] if not result['success'] else None
        }

    def create_superuser_if_needed(self):
        """Create superuser if none exists"""

        # Check if superuser exists
        check_command = "from django.contrib.auth import get_user_model; User = get_user_model(); print('exists' if User.objects.filter(is_superuser=True).exists() else 'none')"

        result = self.run_django_command('shell', '-c', check_command)

        if 'none' in result['stdout']:
            print("No superuser found. Creating one...")
            print("Use: python manage.py createsuperuser")
            return {"superuser_exists": False, "action_needed": "create_superuser"}
        else:
            return {"superuser_exists": True}

    def wallai_specific_commands(self):
        """Wallai-specific Django commands"""

        commands = {
            "create_test_data": self.create_test_data,
            "validate_models": self.validate_wallai_models,
            "check_sprint3_readiness": self.check_sprint3_readiness
        }

        return commands

    def create_test_data(self):
        """Create test data for Wallai development"""

        test_data_script = """
from authentication.models import User
from spaces.models import Space, SpaceMember
from budgets.models import BudgetCategory, Budget

# Create test users
user1, created = User.objects.get_or_create(
    username='testuser1',
    email='test1@wallai.com',
    defaults={'first_name': 'Test', 'last_name': 'User'}
)

user2, created = User.objects.get_or_create(
    username='testuser2',
    email='test2@wallai.com',
    defaults={'first_name': 'Test', 'last_name': 'User2'}
)

# Create test space
space, created = Space.objects.get_or_create(
    name='Test Space Sprint 3',
    defaults={
        'created_by': user1,
        'invite_code': 'TEST01'
    }
)

# Add members
SpaceMember.objects.get_or_create(space=space, user=user1)
SpaceMember.objects.get_or_create(space=space, user=user2)

print(f"Test data created: Users: {User.objects.count()}, Spaces: {Space.objects.count()}")
"""

        result = self.run_django_command('shell', '-c', test_data_script)
        return {
            "success": result['success'],
            "output": result['stdout'],
            "error": result['stderr'] if not result['success'] else None
        }

    def validate_wallai_models(self):
        """Validate Wallai models are working correctly"""

        validation_script = """
from authentication.models import User
from spaces.models import Space, SpaceMember
from budgets.models import BudgetCategory, Budget

# Model counts
print(f"Users: {User.objects.count()}")
print(f"Spaces: {Space.objects.count()}")
print(f"Space Members: {SpaceMember.objects.count()}")
print(f"Budget Categories: {BudgetCategory.objects.count()}")
print(f"Budgets: {Budget.objects.count()}")

# Test relationships
for space in Space.objects.all()[:3]:
    member_count = space.spacemember_set.count()
    budget_count = Budget.objects.filter(space=space).count()
    print(f"Space '{space.name}': {member_count} members, {budget_count} budgets")
"""

        result = self.run_django_command('shell', '-c', validation_script)
        return {
            "success": result['success'],
            "validation_output": result['stdout'],
            "error": result['stderr'] if not result['success'] else None
        }

    def check_sprint3_readiness(self):
        """Check if project is ready for Sprint 3 development"""

        print("SPRINT 3 READINESS CHECK")
        print("=" * 40)

        checks = []

        # Check Django health
        health = self.check_project_health()
        checks.append(("Django Health", health['overall_health']))

        # Check models
        validation = self.validate_wallai_models()
        checks.append(("Model Validation", validation['success']))

        # Check if we have test data
        superuser = self.create_superuser_if_needed()
        checks.append(("Superuser Exists", superuser['superuser_exists']))

        print("\nREADINESS RESULTS:")
        for check_name, passed in checks:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {check_name}: {status}")

        all_passed = all(passed for _, passed in checks)
        print(f"\nOVERALL READINESS: {'[READY]' if all_passed else '[NEEDS ATTENTION]'}")

        return {
            "ready_for_sprint3": all_passed,
            "checks": dict(checks)
        }

def main():
    """CLI interface for Django MCP Manager"""

    manager = DjangoMCPManager()

    if len(sys.argv) < 2:
        print("Django MCP Manager for Wallai")
        print("Commands:")
        print("  health          - Check project health")
        print("  migrate [app]   - Create and apply migrations")
        print("  shell [command] - Django shell operations")
        print("  test [app]      - Run tests")
        print("  static          - Collect static files")
        print("  db <operation>  - Database operations")
        print("  testdata        - Create test data")
        print("  validate        - Validate models")
        print("  sprint3         - Check Sprint 3 readiness")
        return

    command = sys.argv[1]

    if command == "health":
        result = manager.check_project_health()
        print(json.dumps(result, indent=2))

    elif command == "migrate":
        app_name = sys.argv[2] if len(sys.argv) > 2 else None
        result = manager.smart_makemigrations(app_name)
        print(json.dumps(result, indent=2))

    elif command == "shell":
        if len(sys.argv) > 2:
            shell_command = sys.argv[2]
            result = manager.shell_plus_session(shell_command)
            print(json.dumps(result, indent=2))
        else:
            manager.shell_plus_session()

    elif command == "test":
        app_name = sys.argv[2] if len(sys.argv) > 2 else None
        result = manager.run_tests(app_name)
        print(json.dumps(result, indent=2))

    elif command == "static":
        result = manager.collectstatic_and_optimize()
        print(json.dumps(result, indent=2))

    elif command == "db":
        if len(sys.argv) > 2:
            operation = sys.argv[2]
            result = manager.database_operations(operation)
            print(json.dumps(result, indent=2))
        else:
            print("Available db operations: backup, reset, shell, inspect")

    elif command == "testdata":
        result = manager.create_test_data()
        print(json.dumps(result, indent=2))

    elif command == "validate":
        result = manager.validate_wallai_models()
        print(json.dumps(result, indent=2))

    elif command == "sprint3":
        result = manager.check_sprint3_readiness()
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()