import subprocess
import sys
import time
from pathlib import Path

from . import isolation, protocol

REPO_ROOT = Path(__file__).resolve().parent.parent


class RoomRuntime:
    def __init__(self, workdir, run_id, specimen_path, contract_path):
        self.workdir = Path(workdir)
        self.run_id = run_id
        self.specimen_path = Path(specimen_path)
        self.contract_path = Path(contract_path)
        self.tokens = {room: protocol.new_token() for room in protocol.ROOMS}
        self.room_ids = {room: protocol.new_token() for room in protocol.ROOMS}
        self.rooms_root = self.workdir / "rooms"
        self.isolation = {"mode": "not_applied"}
        self.isolation_release = None
        self.inboxes = {}
        self.outboxes = {}
        self.procs = {}
        self.log_paths = {}

    def room_dir(self, room):
        return self.rooms_root / self.room_ids[room]

    def prepare(self):
        self.rooms_root.mkdir(parents=True, exist_ok=True)
        self.isolation = isolation.apply(self.rooms_root)
        for room in protocol.ROOMS:
            inbox, outbox = protocol.channel_paths(self.room_dir(room))
            self.inboxes[room] = inbox
            self.outboxes[room] = outbox
            dispatch = protocol.make_dispatch(
                run_id=self.run_id,
                specimen_id=self._specimen_id(),
                room=room,
                token=self.tokens[room],
                artifact_ref=str(self.specimen_path),
                context_refs=[str(self.contract_path)],
                issued_at="",
            )
            protocol.write_message(inbox, dispatch)
        return self

    def release(self):
        self.isolation_release = isolation.release(self.rooms_root)
        return self.isolation_release

    def _specimen_id(self):
        import yaml

        doc = yaml.safe_load(Path(self.specimen_path).read_text(encoding="utf-8"))
        return doc["specimen"]["id"]

    def _worker_cmd(self, room):
        return [
            sys.executable,
            "-m",
            "p19_engine.room_worker",
            "--inbox",
            str(self.inboxes[room]),
            "--outbox",
            str(self.outboxes[room]),
            "--room",
            room,
            "--token",
            self.tokens[room],
            "--contract",
            str(self.contract_path),
        ]

    def spawn(self):
        for room in protocol.ROOMS:
            log_path = self.room_dir(room) / "worker.log"
            self.log_paths[room] = log_path
            log_f = log_path.open("w", encoding="utf-8")
            self.procs[room] = subprocess.Popen(
                self._worker_cmd(room),
                cwd=str(REPO_ROOT),
                stdout=log_f,
                stderr=subprocess.STDOUT,
            )
            self.procs[room]._log_file = log_f
        return self

    def collect(self, timeout=20.0):
        reports = {}
        missing = {}
        deadline = time.monotonic() + timeout
        pending = set(protocol.ROOMS)
        while pending and time.monotonic() < deadline:
            for room in list(pending):
                outbox = self.outboxes[room]
                if outbox.is_file():
                    try:
                        msg = protocol.read_message(outbox)
                        protocol.validate_report(
                            msg,
                            expect_room=room,
                            expect_run=self.run_id,
                            expect_token=self.tokens[room],
                        )
                        reports[room] = msg
                        pending.discard(room)
                        continue
                    except protocol.ProtocolError as e:
                        missing[room] = f"invalid report: {e}"
                        pending.discard(room)
                        continue
                proc = self.procs.get(room)
                if proc is not None and proc.poll() is not None and proc.returncode != 0:
                    missing[room] = f"worker exited rc={proc.returncode}"
                    pending.discard(room)
            if pending:
                time.sleep(0.05)
        for room in pending:
            missing[room] = "timeout: no valid report"
        for room in protocol.ROOMS:
            proc = self.procs.get(room)
            if proc is not None and hasattr(proc, "_log_file"):
                try:
                    proc._log_file.close()
                except OSError:
                    pass
        return reports, missing

    def wait_all(self, timeout=20.0):
        deadline = time.monotonic() + timeout
        for room in protocol.ROOMS:
            proc = self.procs.get(room)
            if proc is None:
                continue
            remaining = max(0.0, deadline - time.monotonic())
            try:
                proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
