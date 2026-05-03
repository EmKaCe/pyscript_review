"""IndexedDB persistence layer for review sessions and records.

Provides a dual-mode storage backend:
  - Browser mode: Uses IndexedDB via PyScript's ``js`` module for persistent
    storage in the browser. All operations are async (awaitable).
  - Local fallback: Uses ``collections.OrderedDict`` in-memory store for
    pytest and non-browser environments. All operations are synchronous.

The module auto-detects the runtime environment. When ``indexedDB`` is
available from the ``js`` module, browser mode is used; otherwise, the
in-memory fallback is activated.

This module mirrors the Svelte review app's ``db.ts`` IndexedDB schema:
  - Single object store ``"reviews"`` with ``keyPath: "id"``
  - Index on ``"semester"``, ``"student_id"``, and ``"updated_at"``
  - ``__current__`` sentinel key for crash-recovery auto-save
  - Auto-generated IDs for saved reviews
"""

from __future__ import annotations

import contextlib
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any

from src.models.db import CurrentSessionRecord, DbExport, ReviewRecord
from src.utils.semester import extract_semester

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_NAME = "scipro_reviews"
DB_VERSION = 1
SESSION_STORE = "reviews"
CURRENT_SESSION_KEY = "__current__"
EXPORT_VERSION = 1


# ---------------------------------------------------------------------------
# Abstract storage backend
# ---------------------------------------------------------------------------


class StorageBackend(ABC):
    """Abstract base class for review persistence backends."""

    @abstractmethod
    async def open_db(self) -> None:
        """Open or initialise the storage backend."""

    @abstractmethod
    async def save_current_session(self, data: dict[str, Any]) -> None:
        """Save the current in-progress session (crash recovery).

        Args:
            data: Serialised session state dict.
        """

    @abstractmethod
    async def load_current_session(self) -> dict[str, Any] | None:
        """Load the current in-progress session.

        Returns:
            The serialised session state dict, or ``None`` if not found.
        """

    @abstractmethod
    async def clear_current_session(self) -> None:
        """Delete the current in-progress session."""

    @abstractmethod
    async def save_review(self, record: ReviewRecord) -> str:
        """Save a review record, generating an ID if needed.

        Args:
            record: A ReviewRecord dataclass instance. If ``record.id`` is
                empty, a unique ID will be generated.

        Returns:
            The ID under which the review was stored.
        """

    @abstractmethod
    async def load_review(self, review_id: str) -> ReviewRecord | None:
        """Load a review record by ID.

        Args:
            review_id: The unique identifier of the review.

        Returns:
            The ReviewRecord if found, otherwise ``None``.
        """

    @abstractmethod
    async def delete_review(self, review_id: str) -> bool:
        """Delete a review record by ID.

        Args:
            review_id: The unique identifier of the review.

        Returns:
            ``True`` if the record was deleted, ``False`` if not found.
        """

    @abstractmethod
    async def list_reviews(
        self,
        semester: str | None = None,
    ) -> list[ReviewRecord]:
        """List stored reviews, optionally filtered by semester.

        Results are sorted by ``updated_at`` descending (most recent first).
        The ``__current__`` sentinel record is always excluded.

        Args:
            semester: Optional semester filter (e.g. ``"2026SS"``).

        Returns:
            List of ReviewRecord instances.
        """

    @abstractmethod
    async def list_semesters(self) -> list[str]:
        """List all semesters that have stored reviews.

        The ``"unknown"`` semester is excluded. Results are sorted in
        reverse chronological order.

        Returns:
            List of semester strings.
        """

    @abstractmethod
    async def export_all(self) -> DbExport:
        """Export all reviews as a DbExport-compatible dict.

        Excludes the ``__current__`` sentinel record.

        Returns:
            A DbExport instance with all review records.
        """

    @abstractmethod
    async def import_all(self, data: DbExport) -> dict[str, int]:
        """Import reviews from a DbExport instance.

        Records with the ``__current__`` ID are skipped. Each record is
        written individually; failures are counted as skipped rather
        than aborting the import.

        Args:
            data: DbExport instance with reviews to import.

        Returns:
            Dict with ``"imported"`` and ``"skipped"`` counts.
        """

    @abstractmethod
    async def clear_all_reviews(self) -> None:
        """Delete all review records including the ``__current__`` sentinel."""


# ---------------------------------------------------------------------------
# Helper: generate a unique ID
# ---------------------------------------------------------------------------


def _generate_id() -> str:
    """Generate a unique record ID from timestamp and random suffix.

    Returns:
        A string ID like ``"m1a2b3c"`` suitable for use as an IDB key.
    """
    ts = int(time.time())
    # Use a simple counter for deterministic IDs in local mode.
    # In browser mode, Math.random() provides additional entropy.
    return f"{ts:x}"


# ---------------------------------------------------------------------------
# In-memory (local / test) storage backend
# ---------------------------------------------------------------------------


class MemoryStorage(StorageBackend):
    """In-memory storage backend using OrderedDict for pytest and local dev.

    All operations are **synchronous** — awaiting them simply returns the
    result immediately. This allows test code to use ``await`` for parity
    with the browser backend without requiring an event loop.
    """

    def __init__(self) -> None:
        self._store: OrderedDict[str, CurrentSessionRecord | ReviewRecord] = OrderedDict()
        self._db_open: bool = False

    async def open_db(self) -> None:
        """No-op: in-memory store needs no initialisation."""
        self._db_open = True

    async def save_current_session(self, data: dict[str, Any]) -> None:
        """Save session to the ``__current__`` sentinel key."""
        record = CurrentSessionRecord(data=data)
        self._store[CURRENT_SESSION_KEY] = record

    async def load_current_session(self) -> dict[str, Any] | None:
        """Load the ``__current__`` sentinel record."""
        record = self._store.get(CURRENT_SESSION_KEY)
        if record is None:
            return None
        if isinstance(record, CurrentSessionRecord):
            return record.data
        return None

    async def clear_current_session(self) -> None:
        """Delete the ``__current__`` sentinel record."""
        self._store.pop(CURRENT_SESSION_KEY, None)

    async def save_review(self, record: ReviewRecord) -> str:
        """Save a review, generating an ID if needed."""
        if not record.id:
            object.__setattr__(record, "id", _generate_id())
            object.__setattr__(record, "created_at", _now_iso())
        object.__setattr__(record, "updated_at", _now_iso())
        if not record.semester:
            object.__setattr__(record, "semester", extract_semester(record.student_id))
        self._store[record.id] = record
        self._store.move_to_end(record.id)
        return record.id

    async def load_review(self, review_id: str) -> ReviewRecord | None:
        """Load a review by ID."""
        record = self._store.get(review_id)
        if isinstance(record, ReviewRecord):
            return record
        return None

    async def delete_review(self, review_id: str) -> bool:
        """Delete a review by ID."""
        if review_id in self._store:
            del self._store[review_id]
            return True
        return False

    async def list_reviews(
        self,
        semester: str | None = None,
    ) -> list[ReviewRecord]:
        """List reviews, optionally filtered by semester, sorted newest first."""
        results: list[ReviewRecord] = []
        for record in reversed(self._store.values()):
            if record.id == CURRENT_SESSION_KEY:
                continue
            if semester is not None:
                rec_semester = record.semester or extract_semester(record.student_id)
                if rec_semester != semester:
                    continue
            results.append(record)
        return results

    async def list_semesters(self) -> list[str]:
        """List unique semesters from stored reviews."""
        semesters: set[str] = set()
        for record in self._store.values():
            if record.id == CURRENT_SESSION_KEY:
                continue
            sem = record.semester or extract_semester(record.student_id)
            if sem and sem != "unknown":
                semesters.add(sem)
        return sorted(semesters, reverse=True)

    async def export_all(self) -> DbExport:
        """Export all non-sentinel reviews."""
        records = [r for r in self._store.values() if r.id != CURRENT_SESSION_KEY]
        return DbExport(
            version=EXPORT_VERSION,
            exported_at=_now_iso(),
            reviews=records,
        )

    async def import_all(self, data: DbExport) -> dict[str, int]:
        """Import reviews from a DbExport instance."""
        imported = 0
        skipped = 0
        for record in data.reviews:
            if record.id == CURRENT_SESSION_KEY:
                skipped += 1
                continue
            self._store[record.id] = record
            imported += 1
        return {"imported": imported, "skipped": skipped}

    async def clear_all_reviews(self) -> None:
        """Delete all stored records."""
        self._store.clear()


# ---------------------------------------------------------------------------
# Browser (IndexedDB) storage backend
# ---------------------------------------------------------------------------


class BrowserStorage(StorageBackend):
    """IndexedDB storage backend for PyScript browser environments.

    Uses PyScript's ``js`` module to access the browser's IndexedDB API.
    All operations are async and return Promises that must be awaited.

    Creates a ``create_proxy`` wrapper for all Python callbacks passed to
    raw JS APIs, as required by Pyodide.
    """

    def __init__(self) -> None:
        self._db: Any = None  # IDBDatabase JS proxy

    async def open_db(self) -> None:
        """Open or create the IndexedDB database.

        Creates the ``reviews`` object store with indexes on
        ``semester``, ``student_id``, and ``updated_at`` if it doesn't
        exist yet.
        """
        if self._db is not None:
            return

        try:
            from js import indexedDB  # noqa: F401
            from pyodide.ffi import create_proxy
        except ImportError:
            self._db = None
            return

        proxy_onupgrade = None
        proxy_onsuccess = None
        proxy_onerror = None

        def _on_upgrade_needed(event: Any) -> None:
            db = event.target.result
            if not db.objectStoreNames.contains(SESSION_STORE):
                store = db.createObjectStore(
                    SESSION_STORE,
                    keyPath="id",
                )
                store.createIndex("semester", "semester", unique=False)
                store.createIndex(
                    "student_id",
                    "student_id",
                    unique=False,
                )
                store.createIndex(
                    "updated_at",
                    "updated_at",
                    unique=False,
                )

        def _on_success(event: Any) -> None:
            self._db = event.target.result

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB open failed: {event.target.error}")

        request = indexedDB.open(DB_NAME, DB_VERSION)
        proxy_onupgrade = create_proxy(_on_upgrade_needed)
        proxy_onsuccess = create_proxy(_on_success)
        proxy_onerror = create_proxy(_on_error)

        request.onupgradeneeded = proxy_onupgrade
        request.onsuccess = proxy_onsuccess
        request.onerror = proxy_onerror

        # Wait a tick for async callbacks to fire
        import asyncio

        await asyncio.sleep(0.05)

        # Clean up proxies
        for proxy in (proxy_onupgrade, proxy_onsuccess, proxy_onerror):
            if proxy is not None:
                with contextlib.suppress(Exception):
                    proxy.destroy()

    def _get_store(self, mode: str = "readonly") -> Any:
        """Get an object store from the current database connection.

        Args:
            mode: Transaction mode — ``"readonly"`` or ``"readwrite"``.

        Returns:
            A JS IDBObjectStore proxy.

        Raises:
            RuntimeError: If the database is not open.
        """
        if self._db is None:
            raise RuntimeError("IndexedDB not opened; call open_db() first")
        transaction = self._db.transaction(SESSION_STORE, mode)
        return transaction.objectStore(SESSION_STORE)

    async def save_current_session(self, data: dict[str, Any]) -> None:
        """Save a crash-recovery session under the ``__current__`` key."""
        from pyodide.ffi import create_proxy

        record = CurrentSessionRecord(data=data)
        record_dict = {
            "id": record.id,
            "data": record.data,
        }
        store = self._get_store("readwrite")
        proxy = create_proxy(record_dict)

        def _on_success(event: Any) -> None:
            pass

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB save_current_session failed: {event.target.error}")

        request = store.put(proxy)
        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.02)

        proxy.destroy()
        success_proxy.destroy()
        error_proxy.destroy()

    async def load_current_session(self) -> dict[str, Any] | None:
        """Load the current session data dict from IndexedDB."""
        from pyodide.ffi import create_proxy

        store = self._get_store("readonly")
        result_holder: dict[str, Any] = {"value": None}

        def _on_success(event: Any) -> None:
            row = event.target.result
            if row is not None and row.to_py:
                py_row = row.to_py()
                result_holder["value"] = py_row.get("data")

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB load_current_session failed: {event.target.error}")

        request = store.get(CURRENT_SESSION_KEY)
        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.02)

        success_proxy.destroy()
        error_proxy.destroy()
        return result_holder["value"]

    async def clear_current_session(self) -> None:
        """Delete the current in-progress session from IndexedDB."""
        from pyodide.ffi import create_proxy

        store = self._get_store("readwrite")

        def _on_success(event: Any) -> None:
            pass

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB clear_current_session failed: {event.target.error}")

        request = store.delete(CURRENT_SESSION_KEY)
        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.02)

        success_proxy.destroy()
        error_proxy.destroy()

    async def save_review(self, record: ReviewRecord) -> str:
        """Save a review record to IndexedDB.

        If ``record.id`` is empty, a unique ID is generated.
        """
        from pyodide.ffi import create_proxy

        if not record.id:
            record = ReviewRecord(
                id=_generate_id(),
                student_id=record.student_id,
                assignment_id=record.assignment_id,
                semester=record.semester,
                category_selections=record.category_selections,
                grading_inputs=record.grading_inputs,
                grade_result=record.grade_result,
                generated_text=record.generated_text,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )

        record_dict = {
            "id": record.id,
            "student_id": record.student_id,
            "assignment_id": record.assignment_id,
            "semester": record.semester,
            "category_selections": record.category_selections,
            "grading_inputs": record.grading_inputs,
            "grade_result": record.grade_result,
            "generated_text": record.generated_text,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
        result_holder: dict[str, str] = {"id": record.id}
        store = self._get_store("readwrite")
        proxy = create_proxy(record_dict)

        def _on_success(event: Any) -> None:
            pass

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB save_review failed: {event.target.error}")

        request = store.put(proxy)
        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.02)

        proxy.destroy()
        success_proxy.destroy()
        error_proxy.destroy()
        return result_holder["id"]

    async def load_review(self, review_id: str) -> ReviewRecord | None:
        """Load a review record by ID from IndexedDB."""
        from pyodide.ffi import create_proxy

        store = self._get_store("readonly")
        result_holder: dict[str, Any] = {"value": None}

        def _on_success(event: Any) -> None:
            row = event.target.result
            if row is not None and row.to_py:
                py_row = row.to_py()
                result_holder["value"] = ReviewRecord(
                    id=py_row["id"],
                    student_id=py_row["student_id"],
                    assignment_id=py_row["assignment_id"],
                    semester=py_row["semester"],
                    category_selections=py_row["category_selections"],
                    grading_inputs=py_row["grading_inputs"],
                    grade_result=py_row["grade_result"],
                    generated_text=py_row.get("generated_text", ""),
                    created_at=py_row["created_at"],
                    updated_at=py_row["updated_at"],
                )

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB load_review failed: {event.target.error}")

        request = store.get(review_id)
        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.02)

        success_proxy.destroy()
        error_proxy.destroy()
        return result_holder["value"]

    async def delete_review(self, review_id: str) -> bool:
        """Delete a review record by ID from IndexedDB."""
        from pyodide.ffi import create_proxy

        result_holder: dict[str, bool] = {"deleted": False}
        store = self._get_store("readwrite")

        def _on_success(_event: Any) -> None:
            result_holder["deleted"] = True

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB delete_review failed: {event.target.error}")

        request = store.delete(review_id)
        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.02)

        success_proxy.destroy()
        error_proxy.destroy()
        return result_holder["deleted"]

    async def list_reviews(
        self,
        semester: str | None = None,
    ) -> list[ReviewRecord]:
        """List reviews from IndexedDB, optionally filtered by semester."""
        from pyodide.ffi import create_proxy

        store = self._get_store("readonly")
        results_holder: dict[str, list[ReviewRecord]] = {"value": []}

        if semester is not None:
            key_range = __import__("js").IDBKeyRange.only(semester)
            request = store.index("semester").openCursor(key_range)
        else:
            request = store.index("updated_at").openCursor()

        def _on_success(event: Any) -> None:
            cursor = event.target.result
            if cursor:
                row = cursor.value
                py_row = row.to_py() if hasattr(row, "to_py") else row
                if py_row["id"] != CURRENT_SESSION_KEY:
                    results_holder["value"].append(
                        ReviewRecord(
                            id=py_row["id"],
                            student_id=py_row["student_id"],
                            assignment_id=py_row["assignment_id"],
                            semester=py_row["semester"],
                            category_selections=py_row["category_selections"],
                            grading_inputs=py_row["grading_inputs"],
                            grade_result=py_row["grade_result"],
                            generated_text=py_row.get(
                                "generated_text",
                                "",
                            ),
                            created_at=py_row["created_at"],
                            updated_at=py_row["updated_at"],
                        )
                    )
                getattr(cursor, "continue")()

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB list_reviews failed: {event.target.error}")

        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.05)

        success_proxy.destroy()
        error_proxy.destroy()

        results_holder["value"].sort(
            key=lambda r: r.updated_at,
            reverse=True,
        )
        return results_holder["value"]

    async def list_semesters(self) -> list[str]:
        """List unique semesters from IndexedDB reviews."""
        from pyodide.ffi import create_proxy

        store = self._get_store("readonly")
        semesters_holder: dict[str, set[str]] = {"value": set()}

        request = store.index("semester").openKeyCursor()

        def _on_success(event: Any) -> None:
            cursor = event.target.result
            if cursor:
                sem = str(cursor.key)
                if sem != "unknown":
                    semesters_holder["value"].add(sem)
                getattr(cursor, "continue")()

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB list_semesters failed: {event.target.error}")

        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.05)

        success_proxy.destroy()
        error_proxy.destroy()

        return sorted(semesters_holder["value"], reverse=True)

    async def export_all(self) -> DbExport:
        """Export all reviews from IndexedDB as a DbExport."""
        from pyodide.ffi import create_proxy

        store = self._get_store("readonly")
        reviews_holder: dict[str, list[ReviewRecord]] = {"value": []}

        request = store.openCursor()

        def _on_success(event: Any) -> None:
            cursor = event.target.result
            if cursor:
                row = cursor.value
                py_row = row.to_py() if hasattr(row, "to_py") else row
                if py_row["id"] != CURRENT_SESSION_KEY:
                    reviews_holder["value"].append(
                        ReviewRecord(
                            id=py_row["id"],
                            student_id=py_row["student_id"],
                            assignment_id=py_row["assignment_id"],
                            semester=py_row["semester"],
                            category_selections=py_row["category_selections"],
                            grading_inputs=py_row["grading_inputs"],
                            grade_result=py_row["grade_result"],
                            generated_text=py_row.get(
                                "generated_text",
                                "",
                            ),
                            created_at=py_row["created_at"],
                            updated_at=py_row["updated_at"],
                        )
                    )
                getattr(cursor, "continue")()

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB export_all failed: {event.target.error}")

        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.05)

        success_proxy.destroy()
        error_proxy.destroy()

        return DbExport(
            version=EXPORT_VERSION,
            exported_at=_now_iso(),
            reviews=reviews_holder["value"],
        )

    async def import_all(self, data: DbExport) -> dict[str, int]:
        """Import reviews into IndexedDB from a DbExport."""
        from pyodide.ffi import create_proxy

        reviews = [r for r in data.reviews if r.id != CURRENT_SESSION_KEY]
        if not reviews:
            return {"imported": 0, "skipped": 0}

        store = self._get_store("readwrite")
        imported = 0
        skipped = 0

        for review in reviews:
            record_dict = {
                "id": review.id,
                "student_id": review.student_id,
                "assignment_id": review.assignment_id,
                "semester": review.semester,
                "category_selections": review.category_selections,
                "grading_inputs": review.grading_inputs,
                "grade_result": review.grade_result,
                "generated_text": review.generated_text,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
            }
            proxy = create_proxy(record_dict)
            store.put(proxy)
            # Synchronous put — IDB callbacks aren't awaited per-record
            proxy.destroy()
            imported += 1

        import asyncio

        await asyncio.sleep(0.05)

        return {"imported": imported, "skipped": skipped}

    async def clear_all_reviews(self) -> None:
        """Clear all records from the IndexedDB object store."""
        from pyodide.ffi import create_proxy

        store = self._get_store("readwrite")

        def _on_success(event: Any) -> None:
            pass

        def _on_error(event: Any) -> None:
            raise RuntimeError(f"IndexedDB clear_all_reviews failed: {event.target.error}")

        request = store.clear()
        success_proxy = create_proxy(_on_success)
        error_proxy = create_proxy(_on_error)
        request.onsuccess = success_proxy
        request.onerror = error_proxy

        import asyncio

        await asyncio.sleep(0.02)

        success_proxy.destroy()
        error_proxy.destroy()


# ---------------------------------------------------------------------------
# Helper: ISO timestamp
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Convenience: build a ReviewRecord from session state
# ---------------------------------------------------------------------------


def make_review_record(
    *,
    student_id: str,
    assignment_id: str,
    category_selections: dict[str, Any],
    grading_inputs: dict[str, Any],
    grade_result: dict[str, Any],
    generated_text: str = "",
    existing_id: str = "",
) -> ReviewRecord:
    """Build a ReviewRecord from session data.

    Derives ``semester`` from the student ID and generates timestamps.

    Args:
        student_id: Student identifier (e.g. ``"2026SS_42"``).
        assignment_id: Assignment identifier.
        category_selections: Serialised category selections.
        grading_inputs: Serialised grading inputs.
        grade_result: Serialised grade result.
        generated_text: Generated evaluation text (default empty).
        existing_id: If set, overwrite an existing record with this ID.

    Returns:
        A ReviewRecord ready for ``save_review()``.
    """
    semester = extract_semester(student_id) or "unknown"
    now = _now_iso()
    return ReviewRecord(
        id=existing_id,
        student_id=student_id,
        assignment_id=assignment_id,
        semester=semester,
        category_selections=category_selections,
        grading_inputs=grading_inputs,
        grade_result=grade_result,
        generated_text=generated_text,
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Factory: choose backend based on environment
# ---------------------------------------------------------------------------

_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the appropriate storage backend for the current environment.

    In a PyScript/browser environment, returns a ``BrowserStorage`` instance
    that uses IndexedDB.  In a local/pytest environment, returns a
    ``MemoryStorage`` instance that uses an in-memory OrderedDict.

    Returns:
        A StorageBackend instance (singleton per process).
    """
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    try:
        from js import indexedDB  # noqa: F401

        _storage_instance = BrowserStorage()
    except ImportError:
        _storage_instance = MemoryStorage()

    return _storage_instance


def reset_storage() -> None:
    """Reset the singleton storage instance (useful for testing)."""
    global _storage_instance
    _storage_instance = None
