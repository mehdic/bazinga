#!/usr/bin/env python3
"""
Tech Debt Management Utility

Manages project technical debt log for tracking issues, shortcuts, and tradeoffs.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class TechDebtManager:
    """Manages technical debt tracking."""

    def __init__(self, bazinga_dir: str = "bazinga"):
        """
        Initialize tech debt manager.

        Args:
            bazinga_dir: Directory containing coordination files
        """
        self.bazinga_dir = Path(bazinga_dir)
        self.debt_file = self.bazinga_dir / "tech_debt.json"
        self._ensure_bazinga_dir()

    def _ensure_bazinga_dir(self):
        """Create coordination directory if it doesn't exist."""
        self.bazinga_dir.mkdir(exist_ok=True)

    def _load_debt(self) -> Dict[str, Any]:
        """Load existing tech debt or create new structure."""
        if self.debt_file.exists():
            try:
                with open(self.debt_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        # Return empty structure
        return {
            "project_tech_debt": [],
            "summary": {
                "total": 0,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "blocking_items": 0,
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
        }

    def _save_debt(self, data: Dict[str, Any]):
        """Save tech debt to file."""
        with open(self.debt_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _generate_id(self, existing_items: List[Dict]) -> str:
        """Generate next tech debt ID."""
        if not existing_items:
            return "TD001"

        # Extract numeric part from existing IDs
        max_num = 0
        for item in existing_items:
            item_id = item.get("id", "TD000")
            try:
                num = int(item_id.replace("TD", ""))
                max_num = max(max_num, num)
            except ValueError:
                continue

        return f"TD{max_num + 1:03d}"

    def _update_summary(self, data: Dict[str, Any]):
        """Update summary statistics."""
        items = data["project_tech_debt"]

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        blocking = 0

        for item in items:
            if item.get("status") == "open":
                severity = item.get("severity", "medium")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

                if item.get("blocks_deployment", False):
                    blocking += 1

        data["summary"] = {
            "total": len([i for i in items if i.get("status") == "open"]),
            "by_severity": severity_counts,
            "blocking_items": blocking,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

    def add_debt(
        self,
        added_by: str,
        severity: str,
        category: str,
        description: str,
        location: str,
        impact: str,
        suggested_fix: str,
        blocks_deployment: bool = False,
        attempts_to_fix: Optional[str] = None
    ) -> str:
        """
        Add a tech debt item.

        Args:
            added_by: Agent name (e.g., "Developer-1", "Tech Lead")
            severity: "critical", "high", "medium", or "low"
            category: Category from CATEGORIES
            description: Clear description of the issue
            location: File and line number
            impact: What could go wrong
            suggested_fix: How to properly fix it
            blocks_deployment: Whether this blocks deployment
            attempts_to_fix: Description of what was tried before logging

        Returns:
            The generated tech debt ID
        """
        data = self._load_debt()

        debt_id = self._generate_id(data["project_tech_debt"])

        item = {
            "id": debt_id,
            "added_by": added_by,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": severity.lower(),
            "category": category,
            "description": description,
            "location": location,
            "impact": impact,
            "suggested_fix": suggested_fix,
            "blocks_deployment": blocks_deployment,
            "status": "open"
        }

        if attempts_to_fix:
            item["attempts_to_fix"] = attempts_to_fix

        data["project_tech_debt"].append(item)
        self._update_summary(data)
        self._save_debt(data)

        return debt_id

    def resolve_debt(self, debt_id: str, resolution_note: str, resolved_by: str):
        """
        Mark a tech debt item as resolved.

        Args:
            debt_id: Tech debt ID (e.g., "TD001")
            resolution_note: How it was resolved
            resolved_by: Agent or person who resolved it
        """
        data = self._load_debt()

        for item in data["project_tech_debt"]:
            if item["id"] == debt_id:
                item["status"] = "resolved"
                item["resolved_at"] = datetime.utcnow().isoformat() + "Z"
                item["resolved_by"] = resolved_by
                item["resolution_note"] = resolution_note
                break

        self._update_summary(data)
        self._save_debt(data)

    def get_blocking_items(self) -> List[Dict[str, Any]]:
        """Get all blocking tech debt items."""
        data = self._load_debt()
        return [
            item for item in data["project_tech_debt"]
            if item.get("status") == "open" and item.get("blocks_deployment", False)
        ]

    def get_items_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get tech debt items by severity level."""
        data = self._load_debt()
        return [
            item for item in data["project_tech_debt"]
            if item.get("status") == "open" and item.get("severity") == severity.lower()
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get tech debt summary."""
        data = self._load_debt()
        return data.get("summary", {})

    def has_blocking_debt(self) -> bool:
        """Check if there are any blocking tech debt items."""
        return len(self.get_blocking_items()) > 0

    def get_all_open_items(self) -> List[Dict[str, Any]]:
        """Get all open tech debt items."""
        data = self._load_debt()
        return [
            item for item in data["project_tech_debt"]
            if item.get("status") == "open"
        ]


# Category definitions
CATEGORIES = {
    "error_handling": "Missing error handling or edge cases",
    "performance": "Known performance bottlenecks",
    "security": "Non-critical security concerns",
    "testing": "Missing or incomplete test coverage",
    "refactoring": "Code needing cleanup/restructuring",
    "documentation": "Missing documentation",
    "scalability": "Won't scale beyond current use",
    "technical_design": "Architectural shortcuts",
    "data_integrity": "Potential data consistency issues",
    "dependencies": "Dependency version or compatibility issues",
    "configuration": "Hardcoded values needing configuration",
    "monitoring": "Missing observability/monitoring"
}

# Severity level guidelines
SEVERITY_GUIDELINES = {
    "critical": "PRODUCTION-BREAKING: Will cause failures in production. Must fix immediately.",
    "high": "USER-FACING: Affects user experience or has security implications. Fix before production.",
    "medium": "INTERNAL QUALITY: Technical quality or performance concern. Fix in next iteration.",
    "low": "NICE-TO-HAVE: Code cleanup or minor improvements. Address when convenient."
}


def main():
    """CLI interface for tech debt management."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tech_debt.py <command> [args]")
        print("\nCommands:")
        print("  list [--severity <level>] - List tech debt items")
        print("  summary - Show tech debt summary")
        print("  blocking - Show blocking items")
        sys.exit(1)

    manager = TechDebtManager()
    command = sys.argv[1]

    if command == "list":
        severity_filter = None
        if "--severity" in sys.argv and len(sys.argv) > sys.argv.index("--severity") + 1:
            severity_filter = sys.argv[sys.argv.index("--severity") + 1]

        items = (
            manager.get_items_by_severity(severity_filter)
            if severity_filter
            else manager.get_all_open_items()
        )

        if not items:
            print("No tech debt items found.")
            return

        print(f"\n📋 Tech Debt Items ({len(items)} total)\n")
        for item in items:
            print(f"[{item['id']}] {item['severity'].upper()}: {item['description']}")
            print(f"  Location: {item['location']}")
            print(f"  Added by: {item['added_by']}")
            if item.get("blocks_deployment"):
                print(f"  ⚠️  BLOCKS DEPLOYMENT")
            print()

    elif command == "summary":
        summary = manager.get_summary()
        print("\n📊 Tech Debt Summary\n")
        print(f"Total open items: {summary.get('total', 0)}")
        print(f"Blocking items: {summary.get('blocking_items', 0)}")
        print("\nBy severity:")
        for severity, count in summary.get("by_severity", {}).items():
            if count > 0:
                print(f"  {severity.upper()}: {count}")

    elif command == "blocking":
        items = manager.get_blocking_items()
        if not items:
            print("✅ No blocking tech debt items.")
            return

        print(f"\n⚠️  Blocking Tech Debt ({len(items)} items)\n")
        for item in items:
            print(f"[{item['id']}] {item['severity'].upper()}: {item['description']}")
            print(f"  Location: {item['location']}")
            print(f"  Impact: {item['impact']}")
            print(f"  Suggested fix: {item['suggested_fix']}")
            print()


if __name__ == "__main__":
    main()
