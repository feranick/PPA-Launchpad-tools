#!/usr/bin/env python3
"""
Launchpad PPA Cleanup Script
Removes old package versions from a PPA, keeping the N most recent.
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone

from launchpadlib.launchpad import Launchpad


def get_ppa(lp, owner, ppa_name):
    """Retrieve the PPA archive object."""
    try:
        person = lp.people[owner]
        ppa = person.getPPAByName(name=ppa_name)
        return ppa
    except Exception as e:
        print(f"Error: Could not find PPA '~{owner}/{ppa_name}': {e}")
        sys.exit(1)


def get_published_sources(ppa, package_name=None, series=None):
    """Get all published source packages, optionally filtered."""
    kwargs = {"status": "Published"}
    if package_name:
        kwargs["source_name"] = package_name
    if series:
        kwargs["distro_series"] = series
    return ppa.getPublishedSources(**kwargs)


def group_by_package_and_series(sources):
    """Group source publications by (package_name, distro_series)."""
    groups = defaultdict(list)
    for src in sources:
        key = (src.source_package_name, src.distro_series_link)
        groups[key].append(src)

    # Sort each group by date_published (newest first)
    for key in groups:
        groups[key].sort(
            key=lambda s: s.date_published or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    return groups


def format_age(date_published):
    """Return a human-readable age string."""
    if not date_published:
        return "unknown age"
    delta = datetime.now(timezone.utc) - date_published
    if delta.days > 365:
        return f"{delta.days // 365}y {(delta.days % 365) // 30}m ago"
    elif delta.days > 30:
        return f"{delta.days // 30}m {delta.days % 30}d ago"
    else:
        return f"{delta.days}d ago"


def display_summary(groups, keep):
    """Show what will be kept and what will be deleted."""
    total_delete = 0
    total_keep = 0

    print("\n" + "=" * 72)
    print(f"{'Package':<30} {'Series':<15} {'Keep':<6} {'Delete':<6}")
    print("=" * 72)

    for (pkg_name, series_link), sources in sorted(groups.items()):
        series_name = series_link.split("/")[-1] if series_link else "unknown"
        n_keep = min(keep, len(sources))
        n_delete = len(sources) - n_keep
        total_keep += n_keep
        total_delete += n_delete

        print(f"{pkg_name:<30} {series_name:<15} {n_keep:<6} {n_delete:<6}")

        # Show details
        for i, src in enumerate(sources):
            age = format_age(src.date_published)
            action = "KEEP  " if i < keep else "DELETE"
            print(f"  [{action}] {src.source_package_version:<25} ({age})")

    print("=" * 72)
    print(f"Total: {total_keep} to keep, {total_delete} to delete")
    print("=" * 72)

    return total_delete


def perform_deletion(groups, keep, dry_run=False):
    """Delete old versions, keeping the newest `keep` per group."""
    deleted = 0
    errors = 0

    for (pkg_name, series_link), sources in sorted(groups.items()):
        to_delete = sources[keep:]  # skip the newest `keep` entries

        for src in to_delete:
            version = src.source_package_version
            if dry_run:
                print(f"  [DRY RUN] Would delete {pkg_name} {version}")
                deleted += 1
            else:
                try:
                    src.requestDeletion(
                        removal_comment=f"Automated cleanup: keeping {keep} newest version(s)"
                    )
                    print(f"  [DELETED] {pkg_name} {version}")
                    deleted += 1
                except Exception as e:
                    print(f"  [ERROR]   {pkg_name} {version}: {e}")
                    errors += 1

    return deleted, errors


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old package versions from a Launchpad PPA.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Preview cleanup, keep 2 newest versions per package/series
  %(prog)s --owner myuser --ppa myppa --keep 2 --dry-run

  # Delete all but the latest version of a specific package
  %(prog)s --owner myuser --ppa myppa --keep 1 --package my-package

  # Actually perform deletion (will prompt for confirmation)
  %(prog)s --owner myuser --ppa myppa --keep 1
        """,
    )
    parser.add_argument("--owner", required=True, help="Launchpad PPA owner username")
    parser.add_argument("--ppa", required=True, help="PPA name")
    parser.add_argument(
        "--keep",
        type=int,
        default=1,
        help="Number of newest versions to keep per package/series (default: 1)",
    )
    parser.add_argument("--package", default=None, help="Filter to a specific package name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    if args.keep < 1:
        print("Error: --keep must be at least 1")
        sys.exit(1)

    # Authenticate with Launchpad
    print("Authenticating with Launchpad...")
    lp = Launchpad.login_with(
        "ppa-cleanup-script",
        "production",
        version="devel",
    )

    # Fetch PPA and packages
    print(f"Fetching packages from ~{args.owner}/{args.ppa}...")
    ppa = get_ppa(lp, args.owner, args.ppa)
    sources = get_published_sources(ppa, package_name=args.package)
    groups = group_by_package_and_series(sources)

    if not groups:
        print("No published packages found matching your criteria.")
        sys.exit(0)

    # Display summary
    total_delete = display_summary(groups, args.keep)

    if total_delete == 0:
        print("\nNothing to delete. All clean!")
        sys.exit(0)

    # Confirm and execute
    if args.dry_run:
        print("\n[DRY RUN MODE]")
        perform_deletion(groups, args.keep, dry_run=True)
        print("\nRe-run without --dry-run to actually delete.")
    else:
        if not args.yes:
            response = input(f"\nProceed with deleting {total_delete} package(s)? [y/N] ")
            if response.lower() not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)

        print("\nDeleting old packages...")
        deleted, errors = perform_deletion(groups, args.keep, dry_run=False)
        print(f"\nDone: {deleted} deleted, {errors} errors.")


if __name__ == "__main__":
    main()
