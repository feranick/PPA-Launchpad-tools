# PPA-Launchpad-tools

## Prerequisites

`pip install launchpadlib keyring`

## ppa_cleanup.py
Clean up old package versions from a Launchpad PPA.

### Preview what would be cleaned up (safe, no changes)
`python ppa_cleanup.py --owner myuser --ppa myppa --keep 1 --dry-run`

### Clean a specific package, keep 2 most recent versions
`python ppa_cleanup.py --owner myuser --ppa myppa --keep 2 --package my-package`

### Full cleanup, skip confirmation prompt
`python ppa_cleanup.py --owner myuser --ppa myppa --keep 1 --yes`

### Help
usage: `ppa_cleanup.py [-h] --owner OWNER --ppa PPA [--keep KEEP] [--package PACKAGE] [--dry-run]
                     [--yes]`

options:
  ```
  -h, --help         show this help message and exit
  --owner OWNER      Launchpad PPA owner username
  --ppa PPA          PPA name
  --keep KEEP        Number of newest versions to keep per package/series (default: 1)
  --package PACKAGE  Filter to a specific package name
  --dry-run          Show what would be deleted without actually deleting
  --yes, -y          Skip confirmation prompt
  ```

### What It Does
* Authenticates with Launchpad (opens browser on first run for OAuth)
* Groups all published packages by name + Ubuntu series
* Sorts each group newest → oldest
* Keeps the N newest versions (per `--keep`)
* Shows a summary table before doing anything
* Asks for confirmation (unless `--yes` or `--dry-run`)
* Deletes old versions via `requestDeletion()`

### Important Notes
* Always start with `--dry-run` to verify what will be removed
* Deleted versions cannot be re-uploaded with the same version number
* Storage quota may take a few hours to update after deletion
* First run will open a browser window for Launchpad authentication; credentials are cached afterward

## ppa_stats.py
Provide usage statistics about individual or all packages in a PPA

### All packages
`python ppa_stats.py --owner your-username --ppa your-ppa-name`

### Specific package
`python ppa_stats.py --owner your-username --ppa your-ppa-name --package my-package`

### Specific package, superseded versions
`python ppa_stats.py --owner your-username --ppa your-ppa-name --package my-package --status Superseded`

### Help
usage: `ppa_stats.py [-h] --owner OWNER --ppa PPA [--package PACKAGE]
                   [--status {Published,Superseded,Deleted,Obsolete,Pending}]`

options:
  ```
  -h, --help            show this help message and exit
  --owner OWNER         Launchpad username (e.g. your-launchpad-username)
  --ppa PPA             PPA name (e.g. my-ppa)
  --package PACKAGE     Specific package name to query (default: all packages)
  --status {Published,Superseded,Deleted,Obsolete,Pending}
                        Package status filter (default: Published)
  ```


