-- MySQL 8 / MariaDB compatible. Run once in the Hostinger database.
-- Stores metadata and derived summaries/metric candidates, never the original PDF.
CREATE TABLE IF NOT EXISTS analysis_reports (
  id VARCHAR(190) NOT NULL PRIMARY KEY, symbol VARCHAR(16) NULL,
  title VARCHAR(500) NOT NULL, publisher VARCHAR(190) NULL, report_date DATE NULL,
  category VARCHAR(80) NOT NULL DEFAULT 'brokerage_research',
  source_name VARCHAR(120) NOT NULL DEFAULT 'Vietstock eDocuments',
  source_url TEXT NOT NULL, access_type VARCHAR(40) NOT NULL DEFAULT 'public_link',
  pdf_pages INT NULL, pdf_bytes BIGINT NULL, pdf_status VARCHAR(40) NOT NULL DEFAULT 'link_only',
  summary TEXT NULL, summary_status VARCHAR(40) NOT NULL DEFAULT 'pending',
  extracted_at DATETIME NULL, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_analysis_symbol_date (symbol, report_date),
  KEY idx_analysis_category_date (category, report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS analysis_report_metrics (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, report_id VARCHAR(190) NOT NULL,
  metric_name VARCHAR(120) NOT NULL, metric_value DECIMAL(24,8) NULL, unit VARCHAR(60) NULL,
  period_label VARCHAR(80) NULL, source_excerpt VARCHAR(500) NULL,
  review_status VARCHAR(30) NOT NULL DEFAULT 'needs_review', created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_report_metric (report_id, metric_name, period_label, metric_value),
  KEY idx_metric_review (review_status, metric_name),
  CONSTRAINT fk_analysis_metric_report FOREIGN KEY (report_id) REFERENCES analysis_reports(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
