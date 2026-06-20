# SmartSort Usage Guide

## 1. First run

Double-click `run.bat` or run:

```bash
python src/smartsort.py --gui
```

If no config exists, SmartSort creates one automatically.

## 2. What the buttons do

- `Load`: load the selected config file
- `Init`: create a default config file if it does not exist
- `Browse`: pick the folder you want to organize
- `Preview`: show what would happen without moving files
- `Run`: move files into their destination folders

## 3. File categories

- Images -> `Pictures`
- Videos -> `Videos`
- Audio -> `Music`
- Documents -> `Documents`
- Archives -> `Archives`
- Everything else -> `Other`

## 4. Recommended workflow

1. Pick a test folder first
2. Run `Preview`
3. Check the destination paths
4. Turn off `Dry run`
5. Run `Sort`

## 5. Troubleshooting

- If the window does not open, make sure Python is installed
- If files do not move, check whether `Dry run` is enabled
- If you picked the wrong folder, move the files back manually
