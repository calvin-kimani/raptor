"""
Report generation functionality
"""

import json
from pathlib import Path
from .config import load_config, find_template


def generate_report(formats=None, findings=None):
    """Generate audit reports from JSON findings in specified formats."""
    findings_dir = Path.cwd() / "audits/findings"
    reports_dir = Path.cwd() / "audits/reports"

    if not findings_dir.exists():
        print("Error: No findings directory. Run 'raptor init' first.")
        return 1

    reports_dir.mkdir(parents=True, exist_ok=True)

    # Default to sherlock format
    if not formats:
        formats = ["sherlock"]

    # Get all finding JSON files
    all_findings = list(findings_dir.glob("*.json"))

    if not all_findings:
        print("No findings found. Create findings with 'raptor finding --new'")
        return 1

    # Filter findings if specific ones requested
    if findings:
        # findings can be: finding titles, finding filenames, or indexes
        selected_findings = []
        for spec in findings:
            if spec.isdigit():
                # It's an index
                idx = int(spec)
                if 0 <= idx < len(all_findings):
                    selected_findings.append(all_findings[idx])
            else:
                # It's a title or filename
                # Try exact match first
                matched = False
                for f in all_findings:
                    if f.stem == spec or f.name == spec or f.stem == spec.replace('.json', ''):
                        selected_findings.append(f)
                        matched = True
                        break
                if not matched:
                    print(f"Warning: Finding '{spec}' not found, skipping...")

        if not selected_findings:
            print("Error: No valid findings found matching your criteria.")
            return 1

        target_findings = selected_findings
    else:
        target_findings = all_findings

    print(f"\nGenerating reports for {len(target_findings)} finding(s)...")

    # Generate reports for each format
    for fmt in formats:
        fmt = fmt.lower()
        if fmt not in ["sherlock", "code4rena", "codehawks"]:
            print(f"Warning: Unknown format '{fmt}', skipping...")
            continue

        print(f"\nGenerating {fmt} format reports...")

        for finding_path in target_findings:
            try:
                with open(finding_path, 'r') as f:
                    finding_data = json.load(f)

                # Generate markdown based on format
                if fmt == "sherlock":
                    markdown = _generate_sherlock_report(finding_data)
                elif fmt == "code4rena":
                    markdown = _generate_code4rena_report(finding_data)
                elif fmt == "codehawks":
                    markdown = _generate_codehawks_report(finding_data)

                # Save report
                report_filename = f"{finding_path.stem}-{fmt}.md"
                report_path = reports_dir / report_filename

                with open(report_path, 'w') as f:
                    f.write(markdown)

                print(f"  ✓ {report_filename}")

            except json.JSONDecodeError:
                print(f"  ✗ Error reading {finding_path.name}: Invalid JSON")
            except KeyError as e:
                print(f"  ✗ Error processing {finding_path.name}: Missing field {e}")

    print(f"\n✓ Reports generated in audits/reports/")
    return 0


def _generate_sherlock_report(finding):
    """Generate Sherlock format report."""
    markdown = f"""# [{finding['severity']}] {finding['title']}

## Summary
{finding['summary']}

## Root Cause
{finding['root_cause']}

## Internal Pre-conditions
"""
    for i, cond in enumerate(finding['internal_preconditions'], 1):
        if cond.strip():
            markdown += f"{i}. {cond}\n"

    markdown += "\n## External Pre-conditions\n"
    if finding['external_preconditions']:
        for i, cond in enumerate(finding['external_preconditions'], 1):
            if cond.strip():
                markdown += f"{i}. {cond}\n"
    else:
        markdown += "None\n"

    markdown += "\n## Attack Path\n"
    for i, step in enumerate(finding['attack_path'], 1):
        if step.strip():
            markdown += f"{i}. {step}\n"

    markdown += f"""
## Impact
{finding['impact']}
"""

    if finding.get('poc'):
        markdown += f"""
## PoC
{finding['poc']}
"""

    if finding.get('mitigation'):
        markdown += f"""
## Mitigation
{finding['mitigation']}
"""

    return markdown


def _generate_code4rena_report(finding):
    """Generate Code4rena format report."""
    markdown = f"""# {finding['title']}

## Lines of code

<!-- Add relevant GitHub links here -->

## Vulnerability details

**Root Cause**: {finding['root_cause']}

**Pre-conditions**:
"""
    for i, cond in enumerate(finding['internal_preconditions'], 1):
        if cond.strip():
            markdown += f"{i}. {cond}\n"

    markdown += "\n**Attack Path**:\n"
    for i, step in enumerate(finding['attack_path'], 1):
        if step.strip():
            markdown += f"{i}. {step}\n"

    markdown += f"""
## Impact

{finding['impact']}
"""

    if finding.get('poc'):
        markdown += f"""
## Proof of Concept

{finding['poc']}
"""

    markdown += """
## Tools Used

Manual Review, Raptor Framework
"""

    if finding.get('mitigation'):
        markdown += f"""
## Recommended Mitigation Steps

{finding['mitigation']}
"""

    return markdown


def _generate_codehawks_report(finding):
    """Generate CodeHawks format report."""
    markdown = f"""# {finding['title']}

## Severity

{finding['severity']}

## Relevant GitHub Links

<!-- Add relevant GitHub links here -->

## Summary

{finding['summary']}

## Vulnerability Details

**Root Cause**: {finding['root_cause']}

**Internal Pre-conditions**:
"""
    for i, cond in enumerate(finding['internal_preconditions'], 1):
        if cond.strip():
            markdown += f"{i}. {cond}\n"

    if finding['external_preconditions']:
        markdown += "\n**External Pre-conditions**:\n"
        for i, cond in enumerate(finding['external_preconditions'], 1):
            if cond.strip():
                markdown += f"{i}. {cond}\n"

    markdown += "\n**Attack Path**:\n"
    for i, step in enumerate(finding['attack_path'], 1):
        if step.strip():
            markdown += f"{i}. {step}\n"

    markdown += f"""
## Impact

{finding['impact']}

## Tools Used

Manual Review, Raptor Framework
"""

    if finding.get('mitigation'):
        markdown += f"""
## Recommendations

{finding['mitigation']}
"""

    if finding.get('poc'):
        markdown += f"""
## Proof of Concept

{finding['poc']}
"""

    return markdown
