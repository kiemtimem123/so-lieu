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
