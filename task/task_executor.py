"""
Task executor.

Translates an IntentResult into a concrete physical action using live world-map data.
All tasks run on daemon threads — never blocks the voice pipeline.

Each dispatched task is:
  - Written to TASK_LOG_PATH (tailed live by the dashboard terminal)
  - Briefly noted in the main terminal (one line)
"""

import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from config import TASK_LOG_PATH
from intent.intent_parser import IntentResult
from vision.world_map import WorldMap

_DIVIDER = "=" * 60


class TaskExecutor:
    """
    Receives IntentResults and dispatches the corresponding action.

    Supported intent types (arm control stubbed — to be wired in Phase 3):
      FIND     -- report object position from world map
      GIVE     -- locate + announce pickup and hand-over sequence
      PICK     -- locate + announce pickup
      PLACE    -- acknowledge placement (target location TBD)
      MOVE_ARM -- acknowledge arm movement request
    """

    def __init__(self, world_map: WorldMap, speak: Callable[[str], None]) -> None:
        self._map      = world_map
        self._speak    = speak
        self._log_path = Path(TASK_LOG_PATH)

        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_path.touch(exist_ok=True)  # must exist before dashboard tails it

        _launch_dashboard(self._log_path)

    def execute_async(self, intent: IntentResult) -> None:
        """Spawn a daemon thread for the task. Returns immediately."""
        threading.Thread(
            target = self._dispatch,
            args   = (intent,),
            name   = f"Task-{intent.intent_type}",
            daemon = True,
        ).start()

    # -- Dispatcher -----------------------------------------------------------

    def _dispatch(self, intent: IntentResult) -> None:
        itype  = intent.intent_type
        target = intent.target_object.lower().strip() or None

        print(f"[Task] -> {itype}  target={target!r}")

        if   itype == "FIND":     self._find(target, intent)
        elif itype == "GIVE":     self._give(target, intent)
        elif itype == "PICK":     self._pick(target, intent)
        elif itype == "PLACE":    self._place(target, intent)
        elif itype == "MOVE_ARM": self._move_arm(intent)
        else:
            print(f"[Task] No handler for intent_type='{itype}'")

    # -- Action handlers ------------------------------------------------------

    def _find(self, label: Optional[str], intent: IntentResult) -> None:
        snapshot = self._map.get_snapshot()

        if not label:
            count = len(snapshot)
            reply = (
                "The desk looks empty to me."
                if count == 0
                else f"I can see {count} object{'s' if count != 1 else ''} on the desk."
            )
            self._speak(reply)
            self._log(intent, action="scene_describe", status="OK", note=reply)
            return

        matches = [o for o in snapshot.values() if o.label == label]
        if not matches:
            reply = f"I don't see any {label} on the desk right now."
        elif len(matches) == 1:
            o     = matches[0]
            cx, cy = int(o.centroid[0]), int(o.centroid[1])
            reply = f"I can see {o.id} at roughly {cx}, {cy} on the camera feed."
        else:
            ids   = ", ".join(o.id for o in matches)
            reply = f"I see {len(matches)} {label}s: {ids}."

        self._speak(reply)
        self._log(intent, action="find_object", status="OK", note=reply)

    def _give(self, label: Optional[str], intent: IntentResult) -> None:
        if not label:
            self._speak("Which object would you like me to give you?")
            self._log(intent, action="hand_over", status="NEED_TARGET")
            return

        matches = self._map.find(label)
        if not matches:
            reply = f"I can't see a {label} on the desk right now."
            self._speak(reply)
            self._log(intent, action="hand_over", status="NOT_FOUND", note=reply)
        else:
            target = matches[0]
            self._speak(f"On it — grabbing the {target.id} for you.")
            self._log(
                intent,
                action = "pick_object -> hand_over -> go_home",
                status = "DISPATCHED  [ARM STUB]",
                note   = f"target_id={target.id}  centroid={target.centroid}",
            )

    def _pick(self, label: Optional[str], intent: IntentResult) -> None:
        if not label:
            self._speak("What would you like me to pick up?")
            self._log(intent, action="pick_object", status="NEED_TARGET")
            return

        matches = self._map.find(label)
        if not matches:
            reply = f"I can't find a {label} on the desk."
            self._speak(reply)
            self._log(intent, action="pick_object", status="NOT_FOUND", note=reply)
        else:
            target = matches[0]
            self._speak(f"Picking up the {target.id}.")
            self._log(
                intent,
                action = "pick_object -> go_home",
                status = "DISPATCHED  [ARM STUB]",
                note   = f"target_id={target.id}  centroid={target.centroid}",
            )

    def _place(self, label: Optional[str], intent: IntentResult) -> None:
        self._speak("Placement tasks will be available once the arm is connected.")
        self._log(intent, action="place_object", status="STUB  [ARM NOT CONNECTED]")

    def _move_arm(self, intent: IntentResult) -> None:
        self._speak("Direct arm movement will be available in a future update.")
        self._log(intent, action="move_to_pose", status="STUB  [ARM NOT CONNECTED]")

    # -- Logging --------------------------------------------------------------

    def _log(
        self,
        intent: IntentResult,
        action: str,
        status: str,
        note:   str = "",
    ) -> None:
        snapshot    = self._map.get_snapshot()
        visible_ids = ", ".join(snapshot.keys()) if snapshot else "--"
        timestamp   = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        target_str  = intent.target_object or "--"

        lines = [
            "",
            _DIVIDER,
            f"  TASK DISPATCHED                      {timestamp}",
            _DIVIDER,
            f"  Intent      : {intent.intent_type}",
            f"  Target      : {target_str}",
            f'  Input       : "{intent.raw_text}"',
            f"  Visible     : {visible_ids}",
            f"  Action      : {action}",
            f"  Status      : {status}",
        ]
        if note:
            lines.append(f"  Note        : {note}")
        lines.append(_DIVIDER)
        lines.append("")

        entry = "\n".join(lines)
        try:
            with open(self._log_path, "a", encoding="utf-8") as fh:
                fh.write(entry)
                fh.flush()
        except OSError as exc:
            print(f"[Task] Log write error: {exc}")


# -- Dashboard terminal -------------------------------------------------------

def _launch_dashboard(log_path: Path) -> None:
    """
    Open a persistent terminal that live-tails the task log.
    Tries Windows Terminal (wt) first; falls back to a new PowerShell window.
    """
    abs_log = str(log_path.resolve())
    ps_cmd  = (
        "$host.UI.RawUI.WindowTitle = 'FRIDAY - Task Dashboard'; "
        "Write-Host ''; "
        "Write-Host '  FRIDAY  |  Task Dashboard' -ForegroundColor Cyan; "
        "Write-Host '  Waiting for tasks...' -ForegroundColor DarkGray; "
        "Write-Host ''; "
        f"Get-Content -Wait '{abs_log}'"
    )

    try:
        if shutil.which("wt"):
            subprocess.Popen(
                ["wt", "--title", "FRIDAY Task Dashboard",
                 "powershell", "-NoExit", "-Command", ps_cmd],
            )
        else:
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        print(f"[Task] Dashboard opened  ->  {abs_log}")
    except Exception as exc:
        print(f"[Task] Could not launch dashboard terminal: {exc}")
