from pathlib import Path
import shutil
from datetime import datetime

CANDIDATE_DIRS = [
    Path(r"C:\Users\PeteMyburgh\OneDrive - Shared Access In-Building\Documents"),
    Path.home() / "Documents",
]

FOLDER_MAP = {
    "Reports": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".ppt", ".pptx"},
    "Python_Scripts": {".py", ".ipynb"},
    "Excel": {".xls", ".xlsx", ".csv"},
    "Screenshots": {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"},
    "Downloads": {".zip", ".rar", ".7z", ".exe", ".msi"},
    "Logs": {".log"},
}

def resolve_target_dir() -> Path:
    for p in CANDIDATE_DIRS:
        if p.exists() and p.is_dir():
            return p
    raise FileNotFoundError("No valid Documents directory found.")

def build_extension_index(folder_map):
    index = {}
    for folder, exts in folder_map.items():
        for ext in exts:
            index[ext.lower()] = folder
    return index

def get_unique_destination(dest_file: Path) -> Path:
    if not dest_file.exists():
        return dest_file
    stem, suffix, parent = dest_file.stem, dest_file.suffix, dest_file.parent
    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def log_line(log_file: Path, msg: str):
    with log_file.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

def organize_documents():
    base_dir = resolve_target_dir()
    log_file = base_dir / "DocumentsSorter.log"
    log_line(log_file, f"\n[{datetime.now()}] Start: {base_dir}")

    ext_index = build_extension_index(FOLDER_MAP)

    for folder in FOLDER_MAP:
        (base_dir / folder).mkdir(parents=True, exist_ok=True)

    moved, skipped = 0, 0
    for item in base_dir.iterdir():
        if not item.is_file():
            continue
        if item.name in {"DocumentsSorter.log", "desktop.ini"}:
            continue

        target_folder_name = ext_index.get(item.suffix.lower())
        if not target_folder_name:
            skipped += 1
            log_line(log_file, f"SKIP {item.name} (unknown extension)")
            continue

        destination = get_unique_destination(base_dir / target_folder_name / item.name)
        shutil.move(str(item), str(destination))
        moved += 1
        log_line(log_file, f"MOVE {item.name} -> {target_folder_name}")

    summary = f"Done. Moved: {moved}, Skipped: {skipped}, Log: {log_file}"
    print(summary)
    log_line(log_file, summary)

if __name__ == "__main__":
    organize_documents()