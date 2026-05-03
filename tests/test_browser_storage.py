"""Tests for the browser storage module — MemoryStorage backend.

All tests use MemoryStorage (the in-memory fallback) which operates
synchronously, so async/await is used with pytest-asyncio for parity
with the browser backend API.
"""

from __future__ import annotations

import time

import pytest
from src.browser.storage import (
    CURRENT_SESSION_KEY,
    EXPORT_VERSION,
    MemoryStorage,
    StorageBackend,
    _generate_id,
    _now_iso,
    get_storage,
    make_review_record,
    reset_storage,
)
from src.models.db import DbExport, ReviewRecord

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def storage() -> MemoryStorage:
    """Provide a fresh MemoryStorage instance for each test."""
    s = MemoryStorage()
    return s


@pytest.fixture
async def opened_storage() -> MemoryStorage:
    """Provide a MemoryStorage instance after open_db()."""
    s = MemoryStorage()
    await s.open_db()
    return s


def _make_review(
    *,
    review_id: str = "rev_001",
    student_id: str = "2026SS_42",
    assignment_id: str = "hw01",
    semester: str = "2026SS",
    updated_at: str = "2026-01-15T12:00:00Z",
    created_at: str = "2026-01-15T10:00:00Z",
) -> ReviewRecord:
    """Build a ReviewRecord with sensible defaults for tests."""
    return ReviewRecord(
        id=review_id,
        student_id=student_id,
        assignment_id=assignment_id,
        semester=semester,
        category_selections={"code_quality": {"checked": ["a"]}},
        grading_inputs={"code_quality_design": 5.0},
        grade_result={"percentage": 83.33, "grade": 2.0},
        generated_text="Good work.",
        created_at=created_at,
        updated_at=updated_at,
    )


# ---------------------------------------------------------------------------
# MemoryStorage.open_db
# ---------------------------------------------------------------------------


class TestOpenDb:
    """Tests for MemoryStorage.open_db."""

    async def test_open_db_sets_flag(self, storage: MemoryStorage) -> None:
        await storage.open_db()
        assert storage._db_open is True

    async def test_open_db_idempotent(self, storage: MemoryStorage) -> None:
        await storage.open_db()
        await storage.open_db()  # second call should not raise


# ---------------------------------------------------------------------------
# Current session (crash recovery)
# ---------------------------------------------------------------------------


class TestCurrentSession:
    """Tests for save/load/clear_current_session."""

    async def test_save_and_load_current_session(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        data = {"student_id": "2026SS_42", "assignment_id": "hw01"}
        await opened_storage.save_current_session(data)
        result = await opened_storage.load_current_session()
        assert result == data

    async def test_load_current_session_returns_none_when_empty(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        result = await opened_storage.load_current_session()
        assert result is None

    async def test_save_overwrites_previous_session(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_current_session({"mode": "first"})
        await opened_storage.save_current_session({"mode": "second"})
        result = await opened_storage.load_current_session()
        assert result == {"mode": "second"}

    async def test_clear_current_session(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_current_session({"mode": "teacher"})
        await opened_storage.clear_current_session()
        result = await opened_storage.load_current_session()
        assert result is None

    async def test_clear_current_session_noop_when_empty(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.clear_current_session()  # should not raise


# ---------------------------------------------------------------------------
# Review CRUD
# ---------------------------------------------------------------------------


class TestSaveReview:
    """Tests for save_review."""

    async def test_save_review_returns_id(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        record = _make_review()
        result_id = await opened_storage.save_review(record)
        assert result_id == "rev_001"

    async def test_save_review_generates_id_when_empty(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        record = _make_review(review_id="")
        result_id = await opened_storage.save_review(record)
        assert result_id  # non-empty
        assert len(result_id) > 0

    async def test_save_review_stores_all_fields(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        record = _make_review()
        await opened_storage.save_review(record)
        loaded = await opened_storage.load_review("rev_001")
        assert loaded is not None
        assert loaded.student_id == "2026SS_42"
        assert loaded.assignment_id == "hw01"
        assert loaded.semester == "2026SS"
        assert loaded.grade_result["grade"] == 2.0

    async def test_save_review_overwrite_existing(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        record1 = _make_review(review_id="rev_001", student_id="A")
        await opened_storage.save_review(record1)
        record2 = _make_review(review_id="rev_001", student_id="B")
        await opened_storage.save_review(record2)
        loaded = await opened_storage.load_review("rev_001")
        assert loaded is not None
        assert loaded.student_id == "B"


class TestLoadReview:
    """Tests for load_review."""

    async def test_load_review_returns_none_when_not_found(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        result = await opened_storage.load_review("nonexistent")
        assert result is None

    async def test_load_review_returns_review(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        record = _make_review()
        await opened_storage.save_review(record)
        loaded = await opened_storage.load_review("rev_001")
        assert loaded is not None
        assert loaded.id == "rev_001"

    async def test_load_review_preserves_generated_text(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        record = _make_review()
        record = ReviewRecord(
            id="rev_g",
            student_id="2026SS_42",
            assignment_id="hw01",
            semester="2026SS",
            category_selections={},
            grading_inputs={},
            grade_result={},
            generated_text="Excellent submission.",
            created_at="2026-01-15T10:00:00Z",
            updated_at="2026-01-15T12:00:00Z",
        )
        await opened_storage.save_review(record)
        loaded = await opened_storage.load_review("rev_g")
        assert loaded is not None
        assert loaded.generated_text == "Excellent submission."


class TestDeleteReview:
    """Tests for delete_review."""

    async def test_delete_existing_review(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        record = _make_review()
        await opened_storage.save_review(record)
        result = await opened_storage.delete_review("rev_001")
        assert result is True
        loaded = await opened_storage.load_review("rev_001")
        assert loaded is None

    async def test_delete_nonexistent_review(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        result = await opened_storage.delete_review("nonexistent")
        assert result is False


# ---------------------------------------------------------------------------
# list_reviews
# ---------------------------------------------------------------------------


class TestListReviews:
    """Tests for list_reviews."""

    async def test_list_reviews_empty(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        result = await opened_storage.list_reviews()
        assert result == []

    async def test_list_reviews_returns_all(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_review(
            _make_review(review_id="r1", updated_at="2026-01-10T10:00:00Z"),
        )
        await opened_storage.save_review(
            _make_review(review_id="r2", updated_at="2026-01-15T10:00:00Z"),
        )
        result = await opened_storage.list_reviews()
        assert len(result) == 2

    async def test_list_reviews_sorted_by_updated_at_desc(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_review(
            _make_review(review_id="older", updated_at="2026-01-10T10:00:00Z"),
        )
        await opened_storage.save_review(
            _make_review(review_id="newer", updated_at="2026-01-15T10:00:00Z"),
        )
        result = await opened_storage.list_reviews()
        assert result[0].id == "newer"
        assert result[1].id == "older"

    async def test_list_reviews_excludes_current_session(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_current_session({"mode": "teacher"})
        await opened_storage.save_review(_make_review())
        result = await opened_storage.list_reviews()
        assert len(result) == 1
        assert result[0].id != CURRENT_SESSION_KEY

    async def test_list_reviews_filter_by_semester(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_review(
            _make_review(review_id="r1", semester="2026SS"),
        )
        await opened_storage.save_review(
            _make_review(
                review_id="r2",
                student_id="2025WS_99",
                semester="2025WS",
            ),
        )
        result = await opened_storage.list_reviews(semester="2026SS")
        assert len(result) == 1
        assert result[0].semester == "2026SS"

    async def test_list_reviews_semester_filter_returns_empty(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_review(
            _make_review(semester="2026SS"),
        )
        result = await opened_storage.list_reviews(semester="2025WS")
        assert result == []


# ---------------------------------------------------------------------------
# list_semesters
# ---------------------------------------------------------------------------


class TestListSemesters:
    """Tests for list_semesters."""

    async def test_list_semesters_empty(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        result = await opened_storage.list_semesters()
        assert result == []

    async def test_list_semesters_returns_unique(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_review(
            _make_review(review_id="r1", semester="2026SS"),
        )
        await opened_storage.save_review(
            _make_review(review_id="r2", semester="2026SS"),
        )
        await opened_storage.save_review(
            _make_review(review_id="r3", semester="2025WS"),
        )
        result = await opened_storage.list_semesters()
        assert result == ["2026SS", "2025WS"]

    async def test_list_semesters_excludes_unknown(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_review(
            _make_review(review_id="r1", semester="unknown"),
        )
        await opened_storage.save_review(
            _make_review(review_id="r2", semester="2026SS"),
        )
        result = await opened_storage.list_semesters()
        assert "unknown" not in result
        assert "2026SS" in result

    async def test_list_semesters_excludes_current_session(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_current_session({"mode": "teacher"})
        await opened_storage.save_review(
            _make_review(semester="2026SS"),
        )
        result = await opened_storage.list_semesters()
        assert result == ["2026SS"]


# ---------------------------------------------------------------------------
# export_all / import_all
# ---------------------------------------------------------------------------


class TestExportAll:
    """Tests for export_all."""

    async def test_export_all_returns_db_export(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        review = _make_review()
        await opened_storage.save_review(review)
        export = await opened_storage.export_all()
        assert isinstance(export, DbExport)
        assert export.version == EXPORT_VERSION
        assert len(export.reviews) == 1
        assert export.reviews[0].id == "rev_001"

    async def test_export_all_excludes_current_session(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_current_session({"mode": "teacher"})
        await opened_storage.save_review(_make_review())
        export = await opened_storage.export_all()
        assert len(export.reviews) == 1

    async def test_export_all_has_timestamp(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        export = await opened_storage.export_all()
        assert export.exported_at  # non-empty ISO string


class TestImportAll:
    """Tests for import_all."""

    async def test_import_all_adds_reviews(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        review = _make_review(review_id="imported_1")
        data = DbExport(
            version=EXPORT_VERSION,
            exported_at=_now_iso(),
            reviews=[review],
        )
        result = await opened_storage.import_all(data)
        assert result["imported"] == 1
        assert result["skipped"] == 0

    async def test_import_all_skips_current_session_key(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        review = _make_review(review_id="valid_1")
        data = DbExport(
            version=EXPORT_VERSION,
            exported_at=_now_iso(),
            reviews=[
                ReviewRecord(
                    id=CURRENT_SESSION_KEY,
                    student_id="2026SS_42",
                    assignment_id="hw01",
                    semester="2026SS",
                    category_selections={},
                    grading_inputs={},
                    grade_result={},
                    generated_text="",
                    created_at="2026-01-15T10:00:00Z",
                    updated_at="2026-01-15T12:00:00Z",
                ),
                review,
            ],
        )
        result = await opened_storage.import_all(data)
        assert result["imported"] == 1
        assert result["skipped"] == 1

    async def test_import_all_empty_reviews(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        data = DbExport(
            version=EXPORT_VERSION,
            exported_at=_now_iso(),
            reviews=[],
        )
        result = await opened_storage.import_all(data)
        assert result["imported"] == 0
        assert result["skipped"] == 0

    async def test_import_all_replaces_existing(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        original = _make_review(review_id="rev_001", student_id="OLD")
        await opened_storage.save_review(original)
        updated = _make_review(review_id="rev_001", student_id="NEW")
        data = DbExport(
            version=EXPORT_VERSION,
            exported_at=_now_iso(),
            reviews=[updated],
        )
        await opened_storage.import_all(data)
        loaded = await opened_storage.load_review("rev_001")
        assert loaded is not None
        assert loaded.student_id == "NEW"


# ---------------------------------------------------------------------------
# clear_all_reviews
# ---------------------------------------------------------------------------


class TestClearAllReviews:
    """Tests for clear_all_reviews."""

    async def test_clear_all_removes_everything(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.save_current_session({"mode": "teacher"})
        await opened_storage.save_review(_make_review())
        await opened_storage.clear_all_reviews()
        result = await opened_storage.load_current_session()
        assert result is None
        reviews = await opened_storage.list_reviews()
        assert reviews == []

    async def test_clear_all_on_empty_store(
        self,
        opened_storage: MemoryStorage,
    ) -> None:
        await opened_storage.clear_all_reviews()  # should not raise


# ---------------------------------------------------------------------------
# Utils: make_review_record
# ---------------------------------------------------------------------------


class TestMakeReviewRecord:
    """Tests for the make_review_record helper."""

    def test_make_review_record_derives_semester(self) -> None:
        record = make_review_record(
            student_id="42SS25",
            assignment_id="hw01",
            category_selections={"code": {"checked": ["a"]}},
            grading_inputs={"dim1": 5.0},
            grade_result={"grade": 2.0},
        )
        assert record.semester == "SS25"

    def test_make_review_record_unknown_semester(self) -> None:
        record = make_review_record(
            student_id="plain_id",
            assignment_id="hw01",
            category_selections={},
            grading_inputs={},
            grade_result={},
        )
        assert record.semester == "unknown"

    def test_make_review_record_with_existing_id(self) -> None:
        record = make_review_record(
            student_id="2026SS_42",
            assignment_id="hw01",
            category_selections={},
            grading_inputs={},
            grade_result={},
            existing_id="rev_999",
        )
        assert record.id == "rev_999"

    def test_make_review_record_empty_id_by_default(self) -> None:
        record = make_review_record(
            student_id="2026SS_42",
            assignment_id="hw01",
            category_selections={},
            grading_inputs={},
            grade_result={},
        )
        assert record.id == ""

    def test_make_review_record_sets_timestamps(self) -> None:
        record = make_review_record(
            student_id="2026SS_42",
            assignment_id="hw01",
            category_selections={},
            grading_inputs={},
            grade_result={},
        )
        assert record.created_at
        assert record.updated_at


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


class TestUtilities:
    """Tests for utility functions."""

    def test_generate_id_non_empty(self) -> None:
        id_val = _generate_id()
        assert id_val
        assert isinstance(id_val, str)

    def test_now_iso_returns_iso_format(self) -> None:
        now = _now_iso()
        assert "T" in now  # ISO 8601 format contains T

    def test_generate_id_unique(self) -> None:
        ids = set()
        for _ in range(10):
            ids.add(_generate_id())
            time.sleep(0.001)
        assert all(len(id_val) > 0 for id_val in ids)


# ---------------------------------------------------------------------------
# get_storage / reset_storage
# ---------------------------------------------------------------------------


class TestGetStorage:
    """Tests for get_storage and reset_storage."""

    def setup_method(self) -> None:
        reset_storage()

    def teardown_method(self) -> None:
        reset_storage()

    def test_get_storage_returns_memory_in_non_browser(self) -> None:
        storage = get_storage()
        assert isinstance(storage, MemoryStorage)

    def test_get_storage_returns_singleton(self) -> None:
        storage1 = get_storage()
        storage2 = get_storage()
        assert storage1 is storage2

    def test_reset_storage_creates_new_instance(self) -> None:
        storage1 = get_storage()
        reset_storage()
        storage2 = get_storage()
        assert storage1 is not storage2


# ---------------------------------------------------------------------------
# StorageBackend ABC
# ---------------------------------------------------------------------------


class TestStorageBackendABC:
    """Verify StorageBackend cannot be instantiated directly."""

    def test_abstract_methods_enforced(self) -> None:
        with pytest.raises(TypeError):
            StorageBackend()  # type: ignore[abstract]
