import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "collect-financial-reports.py"
SPEC = importlib.util.spec_from_file_location("report_collector", SCRIPT)
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


class CollectorRetryTests(unittest.TestCase):
    def test_needs_review_refreshes_catalog_if_no_saved_candidate_is_pending(self):
        job = {"status": "needs_review"}
        self.assertTrue(collector.catalog_refresh_due(job, now=datetime(2026, 10, 26, tzinfo=timezone.utc)))

    def test_catalog_refresh_is_throttled_for_six_hours(self):
        now = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
        job = {"status": "needs_review", "lastCatalogRefreshAt": (now - timedelta(hours=5)).isoformat()}
        self.assertFalse(collector.catalog_refresh_due(job, now=now))
        job["lastCatalogRefreshAt"] = (now - timedelta(hours=7)).isoformat()
        self.assertTrue(collector.catalog_refresh_due(job, now=now))

    def test_do_not_rescan_while_saved_url_can_be_retried(self):
        job = {"status": "needs_review"}
        self.assertFalse(
            collector.catalog_refresh_due(
                job,
                has_pending_saved_candidates=True,
                now=datetime(2026, 10, 26, tzinfo=timezone.utc),
            )
        )
        self.assertFalse(
            collector.catalog_refresh_due(
                job,
                retryable_failed_urls={"https://static2.vietstock.vn/TPB_report.pdf"},
                now=datetime(2026, 10, 26, tzinfo=timezone.utc),
            )
        )

    def test_failed_urls_reset_after_24_hours_instead_of_being_banned_forever(self):
        url = "https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%201/TPB_report.pdf"
        now = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
        stale_stamp = (now - timedelta(days=2)).isoformat()
        jobs = [{
            "symbol": "TPB",
            "downloadedFiles": [
                {"url": url, "status": "download_error", "attempted_at": stale_stamp},
                {"url": url, "status": "download_error", "attempted_at": stale_stamp},
                {"url": url, "status": "download_error", "attempted_at": stale_stamp},
            ],
        }]
        successful, failures, retryable = collector.failed_url_retry_state(jobs, "TPB", now=now)
        key = collector.retry_url_key(url)
        self.assertNotIn(key, successful)
        self.assertEqual(failures[key]["attempts"], 0)
        self.assertIn(key, retryable)

    def test_stale_queue_urls_are_covered_by_successful_archive_in_another_job(self):
        archived = "https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%203/TCX_Baocaotaichinh_Q3_2026.zip"
        success = {collector.retry_url_key(archived)}
        candidates = [
            {"url": archived},
            {"url": archived + "?ver=changed"},
        ]
        self.assertTrue(collector.all_candidates_already_archived(candidates, success))

    def test_do_not_mark_candidates_archived_when_any_url_is_not_successful(self):
        archived = "https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%203/TCX_Baocaotaichinh_Q3_2026.zip"
        missing = "https://static2.vietstock.vn/data/HOSE/2026/BCTC/VN/QUY%204/TCX_Baocaotaichinh_Q4_2026.zip"
        success = {collector.retry_url_key(archived)}
        self.assertFalse(
            collector.all_candidates_already_archived(
                [{"url": archived}, {"url": missing}],
                success,
            )
        )

    def test_missing_consolidated_zip_counts_as_missing_archive(self):
        item = {
            "period": "2025-Q3",
            "source_url": "https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%203/TPB_Baocaotaichinh_Q3_2025_Hopnhat.zip",
            "source_archive_file": "",
            "report_type": "BCTC hợp nhất TPB 2025-Q3",
        }
        self.assertTrue(collector.item_needs_vietstock_archive("TPB", item))

    def test_recently_exhausted_urls_wait_for_24_hour_reset(self):
        url = "https://static2.vietstock.vn/data/HOSE/2025/BCTC/VN/QUY%201/TPB_report.pdf"
        now = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
        recent_stamp = (now - timedelta(hours=1)).isoformat()
        jobs = [{
            "symbol": "TPB",
            "downloadedFiles": [
                {"url": url, "status": "download_error", "attempted_at": recent_stamp},
                {"url": url, "status": "download_error", "attempted_at": recent_stamp},
                {"url": url, "status": "download_error", "attempted_at": recent_stamp},
            ],
        }]
        _, failures, retryable = collector.failed_url_retry_state(jobs, "TPB", now=now)
        key = collector.retry_url_key(url)
        self.assertEqual(failures[key]["attempts"], 3)
        self.assertNotIn(key, retryable)


if __name__ == "__main__":
    unittest.main()
