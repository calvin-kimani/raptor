"""
Finding management functionality
"""

import json
from pathlib import Path


def new_finding(title=None, severity="MEDIUM", report_formats=None):
    """Create a new finding in JSON format following the schema."""
    findings_dir = Path.cwd() / "audits/findings"
    if not findings_dir.exists():
        print("Error: No findings directory. Run 'raptor init' first.")
        return 1

    schema_path = Path.cwd() / "audits/findings/.templates/finding-schema.json"
    if not schema_path.exists():
        print("Error: Finding schema not found. Run 'raptor init' first.")
        return 1

    if not title:
        title = input("Enter finding title (e.g., 'Attacker will drain funds from stakers'): ").strip()
        if not title:
            print("Error: Title is required")
            return 1

    # Sanitize filename
    filename = title.lower()
    filename = "".join(c if c.isalnum() or c in " -_" else "" for c in filename)
    filename = filename.replace(" ", "-")
    filename = f"{severity.upper()}-{filename}.json"

    output_path = findings_dir / filename
    if output_path.exists():
        response = input(f"File {filename} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            return 1

    # Create finding structure based on schema
    finding = {
        "title": title,
        "severity": severity.upper(),
        "summary": "",
        "root_cause": "",
        "internal_preconditions": [""],
        "external_preconditions": [],
        "attack_path": [""],
        "impact": "",
        "poc": "",
        "mitigation": ""
    }

    # Save finding as JSON
    with open(output_path, 'w') as f:
        json.dump(finding, f, indent=2)

    print(f"\n✓ Created new finding: {filename}")
    print(f"\nEdit your finding at: audits/findings/{filename}")
    print("\nFill in the required fields:")
    print("  • summary: Brief description following the format")
    print("  • root_cause: Fundamental issue in code or design")
    print("  • internal_preconditions: System state requirements")
    print("  • external_preconditions: External protocol conditions")
    print("  • attack_path: Step-by-step exploitation")
    print("  • impact: Quantified losses and affected parties")
    print("  • poc: (Optional) Proof of concept code")
    print("  • mitigation: Recommended fixes")

    # Generate reports if requested
    if report_formats:
        from .report import generate_report
        print(f"\nGenerating reports for formats: {', '.join(report_formats)}")
        # Extract just the finding name without extension
        finding_id = filename.replace('.json', '')
        return generate_report(formats=report_formats, findings=[finding_id])

    return 0
