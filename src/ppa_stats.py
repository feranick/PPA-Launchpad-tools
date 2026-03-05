#!/usr/bin/env python3
"""
***********************************************
* Launchpad PPA Statistics Script
* v2026.03.05.1
* Provide usage statistics about individual or all packages in a PPA
***********************************************
"""
print(__doc__)

import argparse
from launchpadlib.launchpad import Launchpad
from collections import defaultdict

#***************************************************
# This is needed for installation through pip
#***************************************************
def ppa_stats():
    main()

def parse_args():
    parser = argparse.ArgumentParser(
        description='Fetch PPA download statistics from Launchpad'
    )
    parser.add_argument(
        '--owner',
        required=True,
        help='Launchpad username (e.g. your-launchpad-username)'
    )
    parser.add_argument(
        '--ppa',
        required=True,
        help='PPA name (e.g. my-ppa)'
    )
    parser.add_argument(
        '--package',
        default=None,
        help='Specific package name to query (default: all packages)'
    )
    parser.add_argument(
        '--status',
        default='Published',
        choices=['Published', 'Superseded', 'Deleted', 'Obsolete', 'Pending'],
        help='Package status filter (default: Published)'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    lp = Launchpad.login_with('ppa-stats', 'production', version='devel')

    owner = lp.people[args.owner]
    ppa = owner.getPPAByName(name=args.ppa)

    if args.package:
        binaries = ppa.getPublishedBinaries(
            status=args.status,
            binary_name=args.package
        )
    else:
        binaries = ppa.getPublishedBinaries(status=args.status)

    package_totals = defaultdict(int)
    package_daily = defaultdict(lambda: defaultdict(int))
    grand_total = 0
    found = False

    for binary in binaries:
        found = True
        name = binary.binary_package_name
        version = binary.binary_package_version
        arch = binary.distro_arch_series_link.split('/')[-1]

        count = binary.getDownloadCount()
        package_totals[name] += count
        grand_total += count

        print(f"Fetching data for {name} {version} ({arch})...")

        daily = binary.getDailyDownloadTotals()
        for date, daily_count in daily.items():
            package_daily[name][date] += daily_count

    if not found:
        if args.package:
            print(f"\nNo {args.status.lower()} binaries found for "
                  f"package '{args.package}' in {args.owner}/{args.ppa}")
        else:
            print(f"\nNo {args.status.lower()} binaries found "
                  f"in {args.owner}/{args.ppa}")
        return

    # --- Summary ---
    print("\n" + "=" * 50)
    print(f"  PPA DOWNLOAD SUMMARY")
    print(f"  Owner: {args.owner} | PPA: {args.ppa}")
    print(f"  Status: {args.status}")
    if args.package:
        print(f"  Package: {args.package}")
    print("=" * 50)

    for name, total in sorted(package_totals.items(), key=lambda x: -x[1]):
        print(f"\n  {name}: {total:,} total downloads")

        if name in package_daily:
            print(f"  {'─' * 30}")
            for date in sorted(package_daily[name].keys()):
                print(f"    {date}: {package_daily[name][date]:,}")

    print(f"\n{'=' * 50}")
    print(f"  Grand total across all packages: {grand_total:,}")
    print(f"{'=' * 50}")

#************************************
# Main initialization routine
#************************************
if __name__ == '__main__':
    main()
