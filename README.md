# SmartSort

SmartSort is a lightweight local file organizer for messy downloads, project folders, and desktop clutter.

It sorts files by type, groups them by year and month, and gives you both a GUI and a command-line mode.

## What it does

- Sorts files by extension
- Moves pictures, videos, audio, documents, archives, and unknown files into separate folders
- Optionally groups files into `YYYY/MM`
- Supports preview mode before moving anything
- Supports a JSON config file
- Supports a GUI for non-technical users
- Supports a Windows double-click launcher
- Refuses to organize the Desktop directly

## How to use

### GUI mode

```bash
python src/smartsort.py --gui
```

On Windows you can also double-click `run.bat`.

### Command-line mode

```bash
python src/smartsort.py --config config.json
```

### Create a config file

```bash
python src/smartsort.py --config config.json --init
```

### Preview only

```bash
python src/smartsort.py --config config.json --dry-run
```

### Override the source folder

```bash
python src/smartsort.py --config config.json --source "C:/Users/you/Downloads"
```

## Configuration

Copy `config/config.example.json` to `config.json` and edit it.

Important fields:

- `source_dir`: folder to organize
- `fallback_dir`: where uncategorized files go
- `group_by_year_month`: organize into `YYYY/MM`
- `dry_run`: preview without moving
- `deduplicate`: skip repeated files in the same scan
- `log_file`: name of the log file
- `rules`: extension-to-folder mappings

## Safety notes

- Use `--dry-run` first if you are not sure
- The program skips temporary files and its own log file
- Duplicate handling is scan-local and does not delete files
- The tool only moves files; it does not edit file contents
- The Desktop folder itself is blocked on purpose

## Project structure

```text
SmartSort/
  src/smartsort.py
  config/config.example.json
  run.bat
  LICENSE
  README.md
  docs/github-publish.md
  docs/usage.md
```
