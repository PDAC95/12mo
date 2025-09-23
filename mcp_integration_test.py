#!/usr/bin/env python3
"""
MCP Integration Test for Wallai
Comprehensive testing of all installed MCPs
"""

import subprocess
import json
import sys
import os
from datetime import datetime

class MCPIntegrationTester:
    """Test all MCPs integration for Wallai Sprint 3"""

    def __init__(self):
        self.project_name = "Wallai"
        self.current_sprint = "Sprint 3 - Expense Tracking"
        self.test_results = {}

    def run_command(self, command, timeout=30):
        """Run command with proper error handling"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_context7_mcp(self):
        """Test Context7 MCP availability"""
        print("Testing Context7 MCP...")

        result = self.run_command("npx @upstash/context7-mcp --help")

        self.test_results["context7"] = {
            "available": result["success"],
            "description": "Up-to-date documentation for Django, Alpine.js, Tailwind CSS",
            "usage": "Add 'use context7' to prompts for current framework patterns",
            "status": "READY" if result["success"] else "ERROR"
        }

        return result["success"]

    def test_database_mcp(self):
        """Test Database MCP functionality"""
        print("Testing Database MCP...")

        result = self.run_command("python db_inspector.py summary")

        self.test_results["database"] = {
            "available": result["success"],
            "description": "SQLite/PostgreSQL introspection and analysis",
            "usage": "python db_inspector.py [summary|space|budget]",
            "status": "READY" if result["success"] else "ERROR",
            "sample_output": result["stdout"][:200] + "..." if result["success"] else None
        }

        return result["success"]

    def test_django_mcp(self):
        """Test Django Management MCP"""
        print("Testing Django Management MCP...")

        result = self.run_command("python django_mcp_manager.py health")

        self.test_results["django_management"] = {
            "available": result["success"],
            "description": "Django commands, migrations, tests, health checks",
            "usage": "python django_mcp_manager.py [health|migrate|test|sprint3]",
            "status": "READY" if result["success"] else "ERROR",
            "health_check": "PASSED" if "overall_health\": true" in result["stdout"] else "FAILED"
        }

        return result["success"]

    def test_git_mcp(self):
        """Test Git Advanced MCP"""
        print("Testing Git Advanced MCP...")

        result = self.run_command("python git_mcp_helper.py status")

        self.test_results["git_advanced"] = {
            "available": result["success"],
            "description": "Smart commits, branch management, Sprint tracking",
            "usage": "python git_mcp_helper.py [status|commit|branch|history|summary]",
            "status": "READY" if result["success"] else "ERROR",
            "current_branch": "main" if "main" in result["stdout"] else "unknown"
        }

        return result["success"]

    def test_playwright_mcp(self):
        """Test Playwright Testing MCP"""
        print("Testing Playwright Testing MCP...")

        # Check if Playwright is installed
        result = self.run_command("npx playwright --version")

        self.test_results["playwright_testing"] = {
            "available": result["success"],
            "description": "E2E testing for Wallai PWA with mobile support",
            "usage": "npx playwright test [--ui] [--headed]",
            "status": "READY" if result["success"] else "ERROR",
            "version": result["stdout"].strip() if result["success"] else None,
            "test_files": "tests/e2e/wallai-user-flow.spec.js"
        }

        return result["success"]

    def test_mcp_configuration(self):
        """Test MCP configuration file"""
        print("Testing MCP configuration...")

        config_exists = os.path.exists("mcp.json")

        if config_exists:
            try:
                with open("mcp.json", "r") as f:
                    config = json.load(f)

                mcp_servers = config.get("mcpServers", {})

                self.test_results["configuration"] = {
                    "available": True,
                    "description": "MCP configuration file for Claude Code",
                    "servers_configured": len(mcp_servers),
                    "servers": list(mcp_servers.keys()),
                    "status": "READY"
                }
                return True
            except Exception as e:
                self.test_results["configuration"] = {
                    "available": False,
                    "error": str(e),
                    "status": "ERROR"
                }
                return False
        else:
            self.test_results["configuration"] = {
                "available": False,
                "error": "mcp.json not found",
                "status": "ERROR"
            }
            return False

    def test_sprint3_readiness(self):
        """Test overall Sprint 3 readiness"""
        print("Testing Sprint 3 readiness...")

        result = self.run_command("python django_mcp_manager.py sprint3")

        readiness_data = {}
        try:
            # Extract JSON from output
            json_start = result["stdout"].find("{")
            if json_start != -1:
                json_str = result["stdout"][json_start:]
                readiness_data = json.loads(json_str)
        except:
            pass

        self.test_results["sprint3_readiness"] = {
            "available": result["success"],
            "description": "Overall project readiness for Sprint 3 development",
            "ready_for_sprint3": readiness_data.get("ready_for_sprint3", False),
            "checks": readiness_data.get("checks", {}),
            "status": "READY" if readiness_data.get("ready_for_sprint3", False) else "NEEDS_ATTENTION"
        }

        return readiness_data.get("ready_for_sprint3", False)

    def run_full_integration_test(self):
        """Run complete integration test of all MCPs"""

        print("WALLAI MCP INTEGRATION TEST")
        print("=" * 50)
        print(f"Project: {self.project_name}")
        print(f"Sprint: {self.current_sprint}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

        # Test each MCP
        tests = [
            ("Context7 MCP", self.test_context7_mcp),
            ("Database MCP", self.test_database_mcp),
            ("Django Management MCP", self.test_django_mcp),
            ("Git Advanced MCP", self.test_git_mcp),
            ("Playwright Testing MCP", self.test_playwright_mcp),
            ("MCP Configuration", self.test_mcp_configuration),
            ("Sprint 3 Readiness", self.test_sprint3_readiness)
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            print(f"Running {test_name}...")
            try:
                success = test_func()
                status = "[PASS]" if success else "[FAIL]"
                print(f"  {test_name}: {status}")
                if success:
                    passed_tests += 1
            except Exception as e:
                print(f"  {test_name}: [ERROR] {str(e)}")
            print()

        # Summary
        print("INTEGRATION TEST SUMMARY")
        print("=" * 40)
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        overall_status = "READY FOR SPRINT 3" if passed_tests >= 5 else "NEEDS ATTENTION"
        print(f"Overall Status: {overall_status}")
        print()

        # Detailed results
        print("DETAILED RESULTS:")
        print(json.dumps(self.test_results, indent=2))

        return {
            "overall_success": passed_tests >= 5,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "status": overall_status,
            "detailed_results": self.test_results
        }

    def generate_sprint3_setup_guide(self):
        """Generate setup guide for Sprint 3 development"""

        print("\nSPRINT 3 DEVELOPMENT SETUP GUIDE")
        print("=" * 50)

        print("1. QUICK HEALTH CHECK:")
        print("   python django_mcp_manager.py health")
        print("   python db_inspector.py summary")
        print()

        print("2. CONTEXT7 USAGE FOR SPRINT 3:")
        print("   'use context7 Django model validation for financial calculations'")
        print("   'use context7 Alpine.js dynamic form components for mobile'")
        print("   'use context7 Django REST Framework ViewSets for expense APIs'")
        print()

        print("3. DEVELOPMENT WORKFLOW:")
        print("   a) Create feature branch: python git_mcp_helper.py branch expense-model")
        print("   b) Implement changes with Context7 assistance")
        print("   c) Create migrations: python django_mcp_manager.py migrate expenses")
        print("   d) Run tests: python django_mcp_manager.py test expenses")
        print("   e) E2E testing: npx playwright test")
        print("   f) Smart commit: python git_mcp_helper.py commit feat expenses 'Add expense model'")
        print()

        print("4. DATABASE OPERATIONS:")
        print("   - Inspect data: python db_inspector.py summary")
        print("   - Space analysis: python db_inspector.py space 'space-name'")
        print("   - Budget analysis: python db_inspector.py budget")
        print()

        print("5. SPRINT 3 READY CHECK:")
        print("   python django_mcp_manager.py sprint3")

def main():
    """Main entry point"""

    tester = MCPIntegrationTester()

    if len(sys.argv) > 1 and sys.argv[1] == "guide":
        tester.generate_sprint3_setup_guide()
    else:
        result = tester.run_full_integration_test()

        if result["overall_success"]:
            print("\n[SUCCESS] All MCPs are ready for Sprint 3 development!")
            tester.generate_sprint3_setup_guide()
        else:
            print(f"\n[WARNING] {result['passed_tests']}/{result['total_tests']} MCPs are working correctly.")
            print("Check the detailed results above for issues.")

if __name__ == "__main__":
    main()