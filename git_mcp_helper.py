#!/usr/bin/env python3
"""
Git Advanced MCP Helper for Wallai
Enhanced Git operations for Sprint development
"""

import subprocess
import json
import sys
from datetime import datetime

class GitMCPHelper:
    """Advanced Git operations helper for Wallai development"""

    def __init__(self):
        self.project_name = "Wallai"
        self.current_sprint = "Sprint 3 - Expense Tracking"

    def get_git_status(self):
        """Get comprehensive Git status"""
        try:
            # Get status
            status_result = subprocess.run(['git', 'status', '--porcelain'],
                                         capture_output=True, text=True)

            # Get branch info
            branch_result = subprocess.run(['git', 'branch', '--show-current'],
                                         capture_output=True, text=True)

            # Get remote status
            remote_result = subprocess.run(['git', 'status', '-b', '--porcelain'],
                                         capture_output=True, text=True)

            return {
                "files_changed": status_result.stdout.strip().split('\n') if status_result.stdout.strip() else [],
                "current_branch": branch_result.stdout.strip(),
                "remote_status": remote_result.stdout.strip(),
                "is_clean": len(status_result.stdout.strip()) == 0
            }
        except Exception as e:
            return {"error": str(e)}

    def smart_commit(self, message_type="feat", scope="", description="", auto_add=True):
        """Create smart commit with Wallai conventions"""

        if auto_add:
            # Add relevant files (exclude node_modules, etc.)
            add_result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
            if add_result.returncode != 0:
                return {"error": f"Git add failed: {add_result.stderr}"}

        # Generate commit message following Wallai pattern
        if scope:
            commit_msg = f"{message_type}({scope}): {description}"
        else:
            commit_msg = f"{message_type}: {description}"

        # Add MCP tracking
        commit_msg += f"\n\n🤖 Generated with Claude Code MCP Enhancement\nSprint: {self.current_sprint}\nTimestamp: {datetime.now().isoformat()}"

        try:
            commit_result = subprocess.run(['git', 'commit', '-m', commit_msg],
                                         capture_output=True, text=True)

            if commit_result.returncode == 0:
                return {
                    "success": True,
                    "message": commit_msg,
                    "output": commit_result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": commit_result.stderr
                }
        except Exception as e:
            return {"error": str(e)}

    def create_feature_branch(self, feature_name):
        """Create and switch to feature branch for Sprint 3"""

        # Sanitize branch name
        branch_name = f"sprint3/{feature_name.lower().replace(' ', '-')}"

        try:
            # Create and checkout branch
            create_result = subprocess.run(['git', 'checkout', '-b', branch_name],
                                         capture_output=True, text=True)

            if create_result.returncode == 0:
                return {
                    "success": True,
                    "branch": branch_name,
                    "output": create_result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": create_result.stderr
                }
        except Exception as e:
            return {"error": str(e)}

    def sync_with_remote(self):
        """Sync current branch with remote"""

        try:
            # Fetch latest
            fetch_result = subprocess.run(['git', 'fetch'], capture_output=True, text=True)

            # Pull changes
            pull_result = subprocess.run(['git', 'pull'], capture_output=True, text=True)

            return {
                "fetch": fetch_result.stdout,
                "pull": pull_result.stdout,
                "success": pull_result.returncode == 0
            }
        except Exception as e:
            return {"error": str(e)}

    def get_commit_history(self, count=10):
        """Get recent commit history with enhanced info"""

        try:
            log_result = subprocess.run([
                'git', 'log', f'--oneline', f'-{count}', '--decorate'
            ], capture_output=True, text=True)

            if log_result.returncode == 0:
                commits = []
                for line in log_result.stdout.strip().split('\n'):
                    if line.strip():
                        commits.append(line.strip())

                return {
                    "success": True,
                    "commits": commits,
                    "total": len(commits)
                }
            else:
                return {"error": log_result.stderr}

        except Exception as e:
            return {"error": str(e)}

    def generate_sprint_summary(self):
        """Generate Sprint 3 progress summary from commits"""

        try:
            # Get commits since last sprint (estimate)
            log_result = subprocess.run([
                'git', 'log', '--oneline', '--since="1 week ago"'
            ], capture_output=True, text=True)

            sprint_commits = log_result.stdout.strip().split('\n') if log_result.stdout.strip() else []

            # Categorize commits
            features = [c for c in sprint_commits if 'feat(' in c or 'feat:' in c]
            fixes = [c for c in sprint_commits if 'fix(' in c or 'fix:' in c]
            docs = [c for c in sprint_commits if 'docs(' in c or 'docs:' in c]
            tests = [c for c in sprint_commits if 'test(' in c or 'test:' in c]

            return {
                "total_commits": len(sprint_commits),
                "features": len(features),
                "fixes": len(fixes),
                "documentation": len(docs),
                "tests": len(tests),
                "recent_features": features[:3],
                "sprint": self.current_sprint
            }

        except Exception as e:
            return {"error": str(e)}

def main():
    """Main CLI interface for Git MCP Helper"""

    helper = GitMCPHelper()

    if len(sys.argv) < 2:
        print("Git MCP Helper for Wallai")
        print("Commands:")
        print("  status     - Get enhanced Git status")
        print("  commit     - Smart commit with Wallai conventions")
        print("  branch     - Create feature branch")
        print("  sync       - Sync with remote")
        print("  history    - Get commit history")
        print("  summary    - Sprint progress summary")
        return

    command = sys.argv[1]

    if command == "status":
        status = helper.get_git_status()
        print(json.dumps(status, indent=2))

    elif command == "commit":
        # Usage: python git_mcp_helper.py commit feat expenses "Add expense model"
        if len(sys.argv) >= 5:
            msg_type = sys.argv[2]
            scope = sys.argv[3]
            description = sys.argv[4]
            result = helper.smart_commit(msg_type, scope, description)
            print(json.dumps(result, indent=2))
        else:
            print("Usage: commit <type> <scope> <description>")

    elif command == "branch":
        if len(sys.argv) >= 3:
            feature_name = sys.argv[2]
            result = helper.create_feature_branch(feature_name)
            print(json.dumps(result, indent=2))
        else:
            print("Usage: branch <feature-name>")

    elif command == "sync":
        result = helper.sync_with_remote()
        print(json.dumps(result, indent=2))

    elif command == "history":
        result = helper.get_commit_history()
        print(json.dumps(result, indent=2))

    elif command == "summary":
        result = helper.generate_sprint_summary()
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()