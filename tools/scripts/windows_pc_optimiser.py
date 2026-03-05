"""
Windows PC Optimisation Script
===============================
Analyses the current system state and prints actionable suggestions to
improve performance and reduce startup lag (e.g. 95% CPU at boot).

Requirements:
    pip install psutil
    Run as a standard user; some checks need Administrator privileges
    and will be skipped gracefully if those privileges are absent.
"""

import sys
import time
import platform
import subprocess
import textwrap
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Guard: only makes sense on Windows
# ---------------------------------------------------------------------------
if platform.system() != "Windows":
    print(
        "⚠  This script is designed for Windows.\n"
        "   On non-Windows systems it will still import psutil checks, but\n"
        "   Windows-specific suggestions will be shown as informational only."
    )

try:
    import psutil
except ImportError:
    print(
        "ERROR: 'psutil' is not installed.\n"
        "       Run:  pip install psutil\n"
        "       then re-run this script."
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 70
SECTION   = "-" * 70

def heading(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def suggestion(icon: str, text: str) -> None:
    wrapped = textwrap.fill(text, width=66, subsequent_indent="       ")
    print(f"  {icon}  {wrapped}")


def info(text: str) -> None:
    wrapped = textwrap.fill(text, width=68, subsequent_indent="     ")
    print(f"  ℹ  {wrapped}")


# ---------------------------------------------------------------------------
# 1.  CPU check
# ---------------------------------------------------------------------------

def check_cpu() -> None:
    heading("CPU USAGE")

    # Per-core and overall usage (1-second sample)
    per_cpu  = psutil.cpu_percent(interval=1, percpu=True)
    overall  = psutil.cpu_percent(interval=0)
    cpu_freq = psutil.cpu_freq()
    core_count = psutil.cpu_count(logical=False)
    logical_count = psutil.cpu_count(logical=True)

    print(f"\n  Overall CPU usage : {overall:.1f} %")
    print(f"  Physical cores    : {core_count}   Logical (threads): {logical_count}")
    if cpu_freq:
        print(f"  Current frequency : {cpu_freq.current:.0f} MHz  "
              f"(max {cpu_freq.max:.0f} MHz)")
    print(f"\n  Per-core usage    : {[f'{p:.0f}%' for p in per_cpu]}")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)

    if overall >= 80:
        suggestion("🔴", "CPU usage is very high. See the 'Top Processes' section below "
                         "and end any task you don't recognise or don't need.")
    elif overall >= 50:
        suggestion("🟡", "CPU usage is moderate. Consider closing background apps you "
                         "are not actively using.")
    else:
        suggestion("🟢", "CPU usage looks healthy right now.")

    suggestion("💡", "If CPU is consistently high right after startup, the most "
                     "common causes are startup programs, antivirus scans, Windows "
                     "Update, and telemetry services — all addressed in the sections "
                     "below.")


# ---------------------------------------------------------------------------
# 2.  Top CPU-consuming processes
# ---------------------------------------------------------------------------

def check_top_processes(top_n: int = 10) -> None:
    heading(f"TOP {top_n} CPU-CONSUMING PROCESSES")

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            p.cpu_percent(interval=None)  # prime the counter
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    time.sleep(1)  # let the counters settle

    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)

    print(f"\n  {'PID':>7}  {'CPU %':>7}  {'RAM %':>7}  Name")
    print(f"  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*30}")
    for proc in procs[:top_n]:
        pid  = proc.get("pid", "?")
        cpu  = proc.get("cpu_percent") or 0
        mem  = proc.get("memory_percent") or 0
        name = proc.get("name", "unknown")
        print(f"  {pid:>7}  {cpu:>6.1f}%  {mem:>6.1f}%  {name}")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)
    suggestion("💡", "Open Task Manager (Ctrl+Shift+Esc) → 'Processes' tab. "
                     "Right-click anything suspicious and choose 'End task' or "
                     "'Search online' to identify it.")
    suggestion("💡", "If 'System', 'svchost.exe', or 'Antimalware Service "
                     "Executable' top the list at startup, see the Windows "
                     "services and antivirus sections further below.")


# ---------------------------------------------------------------------------
# 3.  Memory / RAM
# ---------------------------------------------------------------------------

def check_memory() -> None:
    heading("MEMORY (RAM)")

    vm   = psutil.virtual_memory()
    swap = psutil.swap_memory()

    total_gb = vm.total  / (1024 ** 3)
    used_gb  = vm.used   / (1024 ** 3)
    avail_gb = vm.available / (1024 ** 3)

    print(f"\n  Total RAM  : {total_gb:.1f} GB")
    print(f"  Used       : {used_gb:.1f} GB  ({vm.percent:.1f} %)")
    print(f"  Available  : {avail_gb:.1f} GB")
    print(f"  Page file  : {swap.total/(1024**3):.1f} GB total, "
          f"{swap.used/(1024**3):.1f} GB used")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)

    if vm.percent >= 85:
        suggestion("🔴", "RAM usage is critically high. Windows will be swapping "
                         "to the page file heavily, which causes severe lag.")
        suggestion("💡", "Close applications you are not using, or consider "
                         "upgrading to more RAM.")
    elif vm.percent >= 65:
        suggestion("🟡", "RAM usage is elevated. Close unused browser tabs and "
                         "background apps.")
    else:
        suggestion("🟢", "RAM usage is fine.")

    if total_gb < 8:
        suggestion("🔴", f"You only have {total_gb:.1f} GB of RAM. Windows 10/11 "
                         "runs best with at least 8 GB. Upgrading RAM is the "
                         "single biggest performance improvement for most PCs.")

    suggestion("💡", "Make sure your page file is set to 'Automatically manage': "
                     "System → Advanced → Performance Settings → Advanced → "
                     "Virtual Memory.")


# ---------------------------------------------------------------------------
# 4.  Disk usage & health
# ---------------------------------------------------------------------------

def check_disk() -> None:
    heading("DISK USAGE")

    partitions = psutil.disk_partitions(all=False)
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        total_gb = usage.total / (1024 ** 3)
        used_gb  = usage.used  / (1024 ** 3)
        free_gb  = usage.free  / (1024 ** 3)
        print(f"\n  Drive {part.device}  (fstype: {part.fstype})")
        print(f"    Total : {total_gb:.1f} GB  |  Used : {used_gb:.1f} GB  "
              f"|  Free : {free_gb:.1f} GB  ({usage.percent:.1f} % used)")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)

    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        if usage.percent >= 90:
            suggestion("🔴", f"Drive {part.device} is {usage.percent:.0f} % full. "
                             "Windows needs free space to create temp files and the "
                             "page file. Free up at least 15 % of the drive.")
        elif usage.percent >= 75:
            suggestion("🟡", f"Drive {part.device} is {usage.percent:.0f} % full. "
                             "Consider moving large files to external storage.")

    suggestion("💡", "Run Disk Cleanup (search 'Disk Cleanup' in Start) and tick "
                     "'Temporary files', 'Recycle Bin', and 'Delivery Optimization "
                     "Files' to reclaim space.")
    suggestion("💡", "If you have an HDD (spinning disk), consider upgrading to an "
                     "SSD — this is the single most impactful hardware upgrade for "
                     "boot speed and general responsiveness.")


# ---------------------------------------------------------------------------
# 5.  Startup programs (Windows-only, uses reg query)
# ---------------------------------------------------------------------------

def check_startup_programs() -> None:
    heading("STARTUP PROGRAMS")

    reg_paths = [
        (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",       "Current User"),
        (r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",       "All Users"),
        (r"HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
         "All Users (32-bit)"),
    ]

    all_entries: List[Tuple[str, str, str]] = []

    if platform.system() == "Windows":
        for reg_path, scope in reg_paths:
            try:
                result = subprocess.run(
                    ["reg", "query", reg_path],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line and not line.startswith(reg_path) and "REG_" in line:
                        parts = line.split(None, 2)
                        if len(parts) >= 3:
                            all_entries.append((scope, parts[0], parts[2]))
            except Exception:
                pass

        if all_entries:
            print(f"\n  {'Scope':<18}  {'Name':<35}  Command")
            print(f"  {'-'*18}  {'-'*35}  {'-'*25}")
            for scope, name, cmd in all_entries:
                short_cmd = (cmd[:45] + "…") if len(cmd) > 46 else cmd
                print(f"  {scope:<18}  {name:<35}  {short_cmd}")
        else:
            info("No startup entries found in the registry (or access was denied).")
    else:
        info("Startup program inspection is Windows-only.")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)

    suggestion("💡", "Too many startup programs is the #1 cause of slow boot and "
                     "high CPU usage right after startup.")
    suggestion("💡", "Press Ctrl+Shift+Esc → 'Startup' tab in Task Manager. "
                     "Disable everything you don't need immediately at login "
                     "(e.g. Spotify, Discord, OneDrive, Teams, Zoom, browser "
                     "sync helpers).")
    suggestion("💡", "Only keep security software (antivirus) and essential "
                     "drivers in startup.")


# ---------------------------------------------------------------------------
# 6.  Power plan
# ---------------------------------------------------------------------------

def check_power_plan() -> None:
    heading("POWER PLAN")

    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True, text=True, timeout=5
            )
            print(f"\n  {result.stdout.strip()}")
        except Exception as exc:
            info(f"Could not query power plan: {exc}")
    else:
        info("Power plan inspection is Windows-only.")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)
    suggestion("💡", "Set your power plan to 'Balanced' or 'High Performance': "
                     "Control Panel → Power Options.")
    suggestion("⚠ ", "'Power Saver' mode actively throttles your CPU — this "
                     "alone can cause sustained high CPU % because tasks take "
                     "longer to complete and queue up.")


# ---------------------------------------------------------------------------
# 7.  Windows visual effects
# ---------------------------------------------------------------------------

def suggest_visual_effects() -> None:
    heading("VISUAL EFFECTS & ANIMATIONS")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)
    suggestion("💡", "Disable unnecessary visual effects: right-click 'This PC' → "
                     "Properties → Advanced system settings → Performance → "
                     "Settings → select 'Adjust for best performance' (or "
                     "manually untick animations you don't need).")
    suggestion("💡", "In Settings → Accessibility → Visual effects, turn off "
                     "'Animation effects' and 'Transparency effects'.")


# ---------------------------------------------------------------------------
# 8.  Windows Update & Telemetry
# ---------------------------------------------------------------------------

def suggest_update_and_telemetry() -> None:
    heading("WINDOWS UPDATE & BACKGROUND SERVICES")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)
    suggestion("💡", "Windows Update often runs in the background just after "
                     "startup. Let it finish — rebooting afterward usually "
                     "restores normal CPU usage.")
    suggestion("💡", "Check Settings → Windows Update and install all pending "
                     "updates, then restart.")
    suggestion("💡", "In Services (services.msc) you can set 'SysMain' "
                     "(Superfetch) to 'Manual' or 'Disabled' if you have an SSD "
                     "— on HDDs leave it enabled.")
    suggestion("💡", "Disable Xbox Game Bar / Game DVR if you are not gaming: "
                     "Settings → Gaming → Xbox Game Bar → Off.")
    suggestion("💡", "In Settings → Privacy → Diagnostics & feedback, set "
                     "diagnostic data to 'Required only' to reduce telemetry CPU "
                     "overhead.")


# ---------------------------------------------------------------------------
# 9.  Antivirus
# ---------------------------------------------------------------------------

def suggest_antivirus() -> None:
    heading("ANTIVIRUS / WINDOWS DEFENDER")

    print(f"\n{SECTION}")
    print("  Suggestions")
    print(SECTION)
    suggestion("💡", "'Antimalware Service Executable' (MsMpEng.exe) runs a full "
                     "scan shortly after boot. If it is using >30 % CPU, wait "
                     "10–15 minutes for the scan to complete.")
    suggestion("💡", "Schedule scans for a time you are not using the PC: "
                     "Windows Security → Virus & threat protection → Manage "
                     "settings → Exclusions (add folders you trust) and "
                     "scheduled scans.")
    suggestion("💡", "Make sure you do NOT have two antivirus products installed "
                     "simultaneously — they conflict and both peg the CPU.")


# ---------------------------------------------------------------------------
# 10. Quick-win summary
# ---------------------------------------------------------------------------

def print_summary() -> None:
    heading("QUICK-WIN SUMMARY  (do these first)")

    print("""
  Priority  Action
  --------  ---------------------------------------------------------------
  1 🔴      Disable unnecessary startup programs via Task Manager > Startup
  2 🔴      Let Windows Update finish, then restart
  3 🟡      Set Power Plan to Balanced or High Performance
  4 🟡      End unknown/unneeded processes in Task Manager
  5 🟡      Free up disk space (Disk Cleanup, empty Recycle Bin)
  6 🟢      Disable visual effects and transparency
  7 🟢      Schedule antivirus scans for off-peak hours
  8 🟢      Upgrade to SSD / add more RAM if budget allows
""")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n" + SEPARATOR)
    print("  Windows PC Optimisation Report")
    print(f"  Host: {platform.node()}   OS: {platform.platform()}")
    print(SEPARATOR)

    check_cpu()
    check_top_processes()
    check_memory()
    check_disk()
    check_startup_programs()
    check_power_plan()
    suggest_visual_effects()
    suggest_update_and_telemetry()
    suggest_antivirus()
    print_summary()

    print(SEPARATOR)
    print("  End of report — apply the suggestions above and reboot to test.")
    print(SEPARATOR + "\n")


if __name__ == "__main__":
    main()
