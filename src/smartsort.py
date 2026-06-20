from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CONFIG = {
    "source_dir": "./inbox",
    "rules": [
        {"name": "Images", "extensions": [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"], "target_dir": "Pictures"},
        {"name": "Videos", "extensions": [".mp4", ".mov", ".mkv", ".webm", ".avi"], "target_dir": "Videos"},
        {"name": "Audio", "extensions": [".mp3", ".wav", ".flac", ".m4a", ".aac"], "target_dir": "Music"},
        {"name": "Documents", "extensions": [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".md"], "target_dir": "Documents"},
        {"name": "Archives", "extensions": [".zip", ".rar", ".7z", ".tar", ".gz"], "target_dir": "Archives"},
    ],
    "fallback_dir": "Other",
    "group_by_year_month": True,
    "dry_run": False,
    "deduplicate": True,
    "log_file": "smartsort.log",
}

ROOT_BLOCKLIST = {
    "desktop",
}


@dataclass
class Action:
    src: Path
    dst: Path
    reason: str


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    merged = DEFAULT_CONFIG.copy()
    merged.update({k: v for k, v in data.items() if k != "rules"})
    merged["rules"] = data.get("rules", DEFAULT_CONFIG["rules"])
    return merged


def is_blocked_source(source_dir: Path) -> bool:
    name = source_dir.name.lower()
    if name in ROOT_BLOCKLIST:
        return True
    if source_dir == Path.home() / "Desktop":
        return True
    return False


def save_config(config_path: Path, cfg: dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def match_rule(path: Path, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    suffix = path.suffix.lower()
    for rule in rules:
        exts = [e.lower() for e in rule.get("extensions", [])]
        if suffix in exts:
            return rule
    return None


def build_destination(base: Path, rule: dict[str, Any] | None, fallback_dir: str, group_by_year_month: bool, src: Path) -> Path:
    folder = (rule or {}).get("target_dir", fallback_dir)
    target = base / folder
    if group_by_year_month:
        stamp = datetime.fromtimestamp(src.stat().st_mtime)
        target = target / f"{stamp.year:04d}" / f"{stamp.month:02d}"
    return target


def unique_destination(dst: Path) -> Path:
    if not dst.exists():
        return dst
    stem, suffix = dst.stem, dst.suffix
    parent = dst.parent
    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def prepare_actions(source_dir: Path, cfg: dict[str, Any]) -> list[Action]:
    actions: list[Action] = []
    rules = cfg["rules"]
    fallback_dir = cfg["fallback_dir"]
    group_by_year_month = bool(cfg["group_by_year_month"])
    log_name = str(cfg.get("log_file", "smartsort.log"))

    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name.startswith("~") or path.suffix.lower() == ".tmp" or path.name == log_name:
            continue
        rule = match_rule(path, rules)
        dest_dir = build_destination(source_dir, rule, fallback_dir, group_by_year_month, path)
        dst = unique_destination(dest_dir / path.name)
        reason = (rule or {}).get("name", "Fallback")
        actions.append(Action(src=path, dst=dst, reason=reason))
    return actions


def write_log(log_path: Path, lines: Iterable[str]) -> None:
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def handle_actions(actions: list[Action], cfg: dict[str, Any], source_dir: Path) -> tuple[list[str], int]:
    lines = [f"SmartSort report - {datetime.now().isoformat(timespec='seconds')}"]
    lines.append(f"Source: {source_dir}")
    lines.append(f"Dry run: {cfg['dry_run']}")
    lines.append(f"Files found: {len(actions)}")

    moved = 0
    seen_hashes: dict[str, Path] = {}

    for action in actions:
        file_hash = sha256(action.src) if cfg.get("deduplicate") else None
        lines.append(f"[{action.reason}] {action.src} -> {action.dst}")

        if cfg.get("deduplicate") and file_hash in seen_hashes:
            lines.append(f"  duplicate of: {seen_hashes[file_hash]}")
            continue

        if cfg["dry_run"]:
            if file_hash:
                seen_hashes[file_hash] = action.src
            continue

        action.dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(action.src), str(action.dst))
        if file_hash:
            seen_hashes[file_hash] = action.dst
        moved += 1

    lines.append(f"Moved: {moved}")
    return lines, moved


def init_config(config_path: Path) -> None:
    if config_path.exists():
        return
    save_config(config_path, DEFAULT_CONFIG)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SmartSort - organize files into clean folders.")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    parser.add_argument("--source", default=None, help="Override source directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without moving files")
    parser.add_argument("--init", action="store_true", help="Create a default config file and exit")
    parser.add_argument("--gui", action="store_true", help="Launch the graphical interface")
    args = parser.parse_args(argv)

    config_path = Path(args.config).resolve()
    if args.init:
        init_config(config_path)
        print(f"Created config: {config_path}")
        return 0
    if args.gui:
        launch_gui(config_path)
        return 0
    cfg = load_config(config_path)
    if args.source:
        cfg["source_dir"] = args.source
    if args.dry_run:
        cfg["dry_run"] = True

    source_dir = Path(cfg["source_dir"]).expanduser().resolve()
    if is_blocked_source(source_dir):
        raise SystemExit("Refusing to organize Desktop directly. Choose a test folder or set --source to a subfolder.")
    source_dir.mkdir(parents=True, exist_ok=True)
    log_path = source_dir / cfg["log_file"]
    actions = prepare_actions(source_dir, cfg)
    report, _ = handle_actions(actions, cfg, source_dir)
    write_log(log_path, report)

    print("\n".join(report))
    return 0


def launch_gui(config_path: Path) -> None:
    cfg = load_config(config_path)

    root = tk.Tk()
    root.title("SmartSort")
    root.geometry("760x560")
    root.minsize(720, 520)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)

    source_var = tk.StringVar(value=str(cfg.get("source_dir", "./inbox")))
    config_var = tk.StringVar(value=str(config_path))
    dry_var = tk.BooleanVar(value=bool(cfg.get("dry_run", False)))
    group_var = tk.BooleanVar(value=bool(cfg.get("group_by_year_month", True)))
    dedup_var = tk.BooleanVar(value=bool(cfg.get("deduplicate", True)))
    status_var = tk.StringVar(value="Ready")

    def pick_folder() -> None:
        folder = filedialog.askdirectory(title="Select folder to organize", initialdir=source_var.get() or ".")
        if folder:
            source_var.set(folder)

    def load_or_create() -> None:
        current = Path(config_var.get()).expanduser()
        if not current.exists():
            save_config(current, DEFAULT_CONFIG)
        nonlocal cfg
        cfg = load_config(current)
        source_var.set(str(cfg.get("source_dir", "./inbox")))
        dry_var.set(bool(cfg.get("dry_run", False)))
        group_var.set(bool(cfg.get("group_by_year_month", True)))
        dedup_var.set(bool(cfg.get("deduplicate", True)))
        status_var.set(f"Loaded {current}")

    def save_current() -> dict[str, Any]:
        current_cfg = {
            "source_dir": source_var.get().strip(),
            "fallback_dir": cfg.get("fallback_dir", "Other"),
            "group_by_year_month": group_var.get(),
            "dry_run": dry_var.get(),
            "deduplicate": dedup_var.get(),
            "log_file": cfg.get("log_file", "smartsort.log"),
            "rules": cfg.get("rules", DEFAULT_CONFIG["rules"]),
        }
        save_config(Path(config_var.get()).expanduser(), current_cfg)
        return current_cfg

    def preview() -> None:
        try:
            current_cfg = save_current()
            source_dir = Path(current_cfg["source_dir"]).expanduser().resolve()
            if is_blocked_source(source_dir):
                messagebox.showwarning("SmartSort", "Desktop is blocked. Please choose a test folder instead.")
                return
            source_dir.mkdir(parents=True, exist_ok=True)
            actions = prepare_actions(source_dir, current_cfg)
            preview_box.delete("1.0", "end")
            preview_box.insert("end", f"Preview for {source_dir}\n")
            preview_box.insert("end", f"Files found: {len(actions)}\n\n")
            for action in actions[:200]:
                preview_box.insert("end", f"[{action.reason}] {action.src.name} -> {action.dst}\n")
            if len(actions) > 200:
                preview_box.insert("end", f"... and {len(actions) - 200} more\n")
            status_var.set("Preview ready")
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("SmartSort", str(exc))

    def run_sort() -> None:
        try:
            current_cfg = save_current()
            source_dir = Path(current_cfg["source_dir"]).expanduser().resolve()
            if is_blocked_source(source_dir):
                messagebox.showwarning("SmartSort", "Desktop is blocked. Please choose a test folder instead.")
                return
            source_dir.mkdir(parents=True, exist_ok=True)
            actions = prepare_actions(source_dir, current_cfg)
            lines, _ = handle_actions(actions, current_cfg, source_dir)
            write_log(source_dir / current_cfg["log_file"], lines)
            preview_box.delete("1.0", "end")
            preview_box.insert("end", "\n".join(lines))
            status_var.set("Done")
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("SmartSort", str(exc))

    header = ttk.Frame(main)
    header.pack(fill="x")
    ttk.Label(header, text="SmartSort", font=("Segoe UI", 20, "bold")).pack(anchor="w")
    ttk.Label(header, text="Local file organizer with JSON config and one-click sorting").pack(anchor="w", pady=(2, 12))

    form = ttk.Frame(main)
    form.pack(fill="x")
    form.columnconfigure(1, weight=1)

    ttk.Label(form, text="Config").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Entry(form, textvariable=config_var).grid(row=0, column=1, sticky="ew", padx=(8, 8))
    ttk.Button(form, text="Load", command=load_or_create).grid(row=0, column=2, padx=(0, 6))
    ttk.Button(form, text="Init", command=lambda: (init_config(Path(config_var.get()).expanduser()), load_or_create())).grid(row=0, column=3)

    ttk.Label(form, text="Source").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(form, textvariable=source_var).grid(row=1, column=1, sticky="ew", padx=(8, 8))
    ttk.Button(form, text="Browse", command=pick_folder).grid(row=1, column=2, padx=(0, 6))
    ttk.Checkbutton(form, text="Dry run", variable=dry_var).grid(row=1, column=3, sticky="w")

    ttk.Checkbutton(form, text="Group by year/month", variable=group_var).grid(row=2, column=1, sticky="w", pady=(4, 0))
    ttk.Checkbutton(form, text="Deduplicate", variable=dedup_var).grid(row=2, column=2, sticky="w", pady=(4, 0))

    buttons = ttk.Frame(main)
    buttons.pack(fill="x", pady=(12, 8))
    ttk.Button(buttons, text="Preview", command=preview).pack(side="left")
    ttk.Button(buttons, text="Run", command=run_sort).pack(side="left", padx=8)
    ttk.Label(buttons, textvariable=status_var).pack(side="right")

    preview_box = tk.Text(main, height=18, wrap="word")
    preview_box.pack(fill="both", expand=True)

    load_or_create()
    root.mainloop()


if __name__ == "__main__":
    raise SystemExit(main())
