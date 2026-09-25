import threading
import time
import uuid
from datetime import datetime


class ExecutionTracker:
    """
    Tracks the lifecycle of one Agentic AI workflow.

    Responsibilities:
    - Track request ID
    - Track current workflow stage
    - Measure stage duration
    - Measure total workflow duration
    - Record failures
    - Record timeouts
    - Provide terminal diagnostics
    """

    def __init__(self, question: str):

        self.request_id = (
            datetime.now().strftime("%Y%m%d-%H%M%S")
            + "-"
            + uuid.uuid4().hex[:6]
        )

        self.question = question

        self.workflow_start = time.perf_counter()

        self.current_stage = "INITIALIZING"

        self.stage_start = time.perf_counter()

        # IMPORTANT:
        # This attribute must always exist.
        self.status = "RUNNING"

        self.error = None

        self._lock = threading.RLock()

        print()
        print("=" * 65)
        print("AGENTIC AI EXECUTION TRACKER")
        print("=" * 65)

        print(
            f"Request ID : {self.request_id}"
        )

        print(
            f"Question   : {self.question}"
        )

        print(
            f"Started    : "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        print(
            f"Status     : {self.status}"
        )

        print("=" * 65)

    # ========================================================
    # START STAGE
    # ========================================================

    def start_stage(self, stage_name: str):

        with self._lock:

            if self.current_stage not in (
                "INITIALIZING",
                "COMPLETED",
                "FAILED",
                "TIMEOUT",
                "IDLE",
            ):

                self.end_stage()

            self.current_stage = stage_name

            self.stage_start = time.perf_counter()

            elapsed = (
                time.perf_counter()
                - self.workflow_start
            )

            print()
            print(
                f"[START] {stage_name}"
            )

            print(
                f"        Request : {self.request_id}"
            )

            print(
                f"        Elapsed : {elapsed:.2f}s"
            )

    # ========================================================
    # END STAGE
    # ========================================================

    def end_stage(self, status="COMPLETED"):

        with self._lock:

            duration = (
                time.perf_counter()
                - self.stage_start
            )

            elapsed = (
                time.perf_counter()
                - self.workflow_start
            )

            print(
                f"[{status}] "
                f"{self.current_stage} "
                f"— {duration:.2f}s "
                f"(total {elapsed:.2f}s)"
            )

            self.current_stage = "IDLE"

            self.stage_start = time.perf_counter()

    # ========================================================
    # FAILURE
    # ========================================================

    def fail(self, error):

        with self._lock:

            duration = (
                time.perf_counter()
                - self.stage_start
            )

            elapsed = (
                time.perf_counter()
                - self.workflow_start
            )

            self.status = "FAILED"

            self.error = str(error)

            print()
            print(
                "[FAILED]"
            )

            print(
                f"Stage    : {self.current_stage}"
            )

            print(
                f"Duration : {duration:.2f}s"
            )

            print(
                f"Total    : {elapsed:.2f}s"
            )

            print(
                f"Error    : {self.error}"
            )

    # ========================================================
    # TIMEOUT
    # ========================================================

    def timeout(self):

        with self._lock:

            duration = (
                time.perf_counter()
                - self.stage_start
            )

            elapsed = (
                time.perf_counter()
                - self.workflow_start
            )

            self.status = "TIMEOUT"

            print()
            print(
                "[TIMEOUT]"
            )

            print(
                f"Stage    : {self.current_stage}"
            )

            print(
                f"Duration : {duration:.2f}s"
            )

            print(
                f"Total    : {elapsed:.2f}s"
            )

    # ========================================================
    # COMPLETE
    # ========================================================

    def complete(self):

        with self._lock:

            duration = (
                time.perf_counter()
                - self.workflow_start
            )

            self.status = "COMPLETED"

            self.current_stage = "COMPLETED"

            print()
            print("=" * 65)

            print(
                "[WORKFLOW COMPLETED]"
            )

            print(
                f"Request ID : {self.request_id}"
            )

            print(
                f"Total Time : {duration:.2f}s"
            )

            print(
                "=" * 65
            )

    # ========================================================
    # STATUS
    # ========================================================

    def get_status(self):

        with self._lock:

            stage_duration = (
                time.perf_counter()
                - self.stage_start
            )

            total_duration = (
                time.perf_counter()
                - self.workflow_start
            )

            return {
                "request_id": self.request_id,
                "question": self.question,
                "status": self.status,
                "current_stage": self.current_stage,
                "stage_duration_seconds": round(
                    stage_duration,
                    2,
                ),
                "total_duration_seconds": round(
                    total_duration,
                    2,
                ),
                "error": self.error,
            }