from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import shutil


def resolve_default_paths() -> tuple[Path, Path]:
    home = Path.home()
    default_desktop = home / "Desktop"
    default_documents = home / "Documents"

    onedrive_roots: list[Path] = []
    for env_var in ("OneDriveCommercial", "OneDriveConsumer", "OneDrive"):
        value = os.environ.get(env_var)
        if value:
            onedrive_roots.append(Path(value))

    for root in onedrive_roots:
        desktop_candidate = root / "Desktop"
        if desktop_candidate.exists() and desktop_candidate.is_dir():
            documents_candidate = root / "Documents"
            if documents_candidate.exists() and documents_candidate.is_dir():
                return desktop_candidate, documents_candidate
            return desktop_candidate, default_documents

    return default_desktop, default_documents


def unique_destination_path(destination: Path) -> Path:
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    counter = 1

    while True:
        candidate = destination.with_name(f"{stem}_{timestamp}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def write_run_log(
    log_dir: Path,
    execute: bool,
    desktop: Path,
    archive_dir: Path,
    item_count: int,
    moved_count: int,
    moved_records: list[tuple[str, str]],
    status: str,
) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"desktop_cleanup_{timestamp}.log"

    lines = [
        f"run_timestamp={datetime.now().isoformat(timespec='seconds')}",
        f"mode={'EXECUTE' if execute else 'DRY_RUN'}",
        f"desktop={desktop}",
        f"archive={archive_dir}",
        f"status={status}",
        f"item_count={item_count}",
        f"moved_count={moved_count}",
        "items:",
    ]

    for source_name, destination_name in moved_records:
        lines.append(f"- {source_name} -> {destination_name}")

    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_path


def move_desktop_files_to_archive(
    desktop: Path,
    documents: Path,
    execute: bool,
    dated_subfolder: bool,
    include_folders: bool,
    skip_confirm: bool,
) -> int:
    if not desktop.exists() or not desktop.is_dir():
        raise FileNotFoundError(f"Desktop folder not found: {desktop}")

    archive_dir = documents / "archive"
    if dated_subfolder:
        archive_dir = archive_dir / datetime.now().strftime("%Y-%m-%d")

    if include_folders:
        items = [item for item in desktop.iterdir() if item.is_file() or item.is_dir()]
    else:
        items = [item for item in desktop.iterdir() if item.is_file()]

    print(f"Desktop:   {desktop}")
    print(f"Archive:   {archive_dir}")
    print(f"Mode:      {'EXECUTE' if execute else 'DRY RUN'}")
    print(f"Item count: {len(items)}")

    moved = 0
    moved_records: list[tuple[str, str]] = []
    status = "completed"

    if not items:
        if include_folders:
            print(f"No files or folders found on Desktop: {desktop}")
        else:
            print(f"No files found on Desktop: {desktop}")
        status = "no-items"

    if items and execute and not skip_confirm:
        print("\nAbout to move items from Desktop to archive.")
        response = input("Type 'yes' to continue: ").strip().lower()
        if response != "yes":
            print("Cancelled. No files were moved.")
            status = "cancelled"

    if items and execute and status != "cancelled":
        archive_dir.mkdir(parents=True, exist_ok=True)

    for source_item in items:
        if status == "cancelled":
            break

        destination_file = unique_destination_path(archive_dir / source_item.name)

        if execute:
            shutil.move(str(source_item), str(destination_file))
            action = "MOVED"
        else:
            action = "WOULD MOVE"

        print(f"{action}: {source_item.name} -> {destination_file.name}")
        moved_records.append((source_item.name, destination_file.name))
        moved += 1

    log_path = write_run_log(
        log_dir=documents / "archive" / "logs",
        execute=execute,
        desktop=desktop,
        archive_dir=archive_dir,
        item_count=len(items),
        moved_count=moved,
        moved_records=moved_records,
        status=status,
    )
    print(f"Log file:  {log_path}")

    return moved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Move files from Desktop to Documents\\archive."
    )
    parser.add_argument(
        "--desktop",
        type=Path,
        default=None,
        help="Desktop folder path (defaults to current user's Desktop).",
    )
    parser.add_argument(
        "--documents",
        type=Path,
        default=None,
        help="Documents folder path (defaults to current user's Documents).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually move files. Without this flag, script runs in dry-run mode.",
    )
    parser.add_argument(
        "--dated-subfolder",
        action="store_true",
        help="Use a dated subfolder in archive, e.g. archive\\2026-03-03.",
    )
    parser.add_argument(
        "--include-folders",
        action="store_true",
        help="Include top-level Desktop folders in the move.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt when using --execute.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    default_desktop, default_documents = resolve_default_paths()
    desktop = (args.desktop or default_desktop).expanduser().resolve()
    documents = (args.documents or default_documents).expanduser().resolve()

    moved = move_desktop_files_to_archive(
        desktop=desktop,
        documents=documents,
        execute=args.execute,
        dated_subfolder=args.dated_subfolder,
        include_folders=args.include_folders,
        skip_confirm=args.yes,
    )

    if args.execute:
        print(f"Done. Moved {moved} file(s).")
    else:
        print(f"Dry run complete. {moved} file(s) would be moved.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
