"""Real-time critical data point monitoring.

Uses PostgreSQL LISTEN/NOTIFY for change detection on critical tables.
Monitors salary spikes, skill shortages, and other critical metrics.
"""

import json
import os
import select
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import psycopg2
import psycopg2.extensions
import structlog

logger = structlog.get_logger()


class CriticalDataMonitor:
    """Monitor critical data points in real-time using PostgreSQL LISTEN/NOTIFY."""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.conn = None
        self.callbacks: Dict[str, Callable] = {}
        self.running = False
        self._thread = None
        
    def connect(self):
        """Establish connection to PostgreSQL."""
        self.conn = psycopg2.connect(self.dsn)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("connected_to_postgres")
        
    def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a PostgreSQL notification channel."""
        self.callbacks[channel] = callback
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute(f"LISTEN {channel};")
            logger.info("subscribed_to_channel", channel=channel)
            
    def start(self):
        """Start listening for notifications in background thread."""
        if self.running:
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("monitor_started")
        
    def stop(self):
        """Stop listening for notifications."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self.conn:
            self.conn.close()
        logger.info("monitor_stopped")
        
    def _listen_loop(self):
        """Main loop for listening to PostgreSQL notifications."""
        while self.running:
            try:
                if self.conn and select.select([self.conn], [], [], 1) == ([], [], []):
                    continue
                elif self.conn:
                    self.conn.poll()
                    while self.conn.notifies:
                        notify = self.conn.notifies.pop(0)
                        channel = notify.channel
                        payload = json.loads(notify.payload) if notify.payload else {}
                        
                        if channel in self.callbacks:
                            try:
                                self.callbacks[channel](payload)
                            except Exception as e:
                                logger.error("callback_error", channel=channel, error=str(e))
            except Exception as e:
                logger.error("listen_loop_error", error=str(e))
                time.sleep(1)
                try:
                    self.connect()
                except Exception:
                    pass


class CriticalDataAnalyzer:
    """Analyze critical data points and generate alerts."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        
    def check_salary_spikes(self, threshold: float = 0.2) -> List[Dict]:
        """Detect salary spikes ( > 20% increase in avg salary)."""
        query = """
        WITH current_avg AS (
            SELECT 
                AVG((salary_min + salary_max) / 2) as avg_salary
            FROM analytics.fact_job_posting
            WHERE posted_date >= CURRENT_DATE - INTERVAL '30 days'
              AND salary_min IS NOT NULL
        ),
        previous_avg AS (
            SELECT 
                AVG((salary_min + salary_max) / 2) as avg_salary
            FROM analytics.fact_job_posting
            WHERE posted_date >= CURRENT_DATE - INTERVAL '60 days'
              AND posted_date < CURRENT_DATE - INTERVAL '30 days'
              AND salary_min IS NOT NULL
        )
        SELECT 
            c.avg_salary as current_avg,
            p.avg_salary as previous_avg,
            ROUND(((c.avg_salary - p.avg_salary) / p.avg_salary * 100)::numeric, 2) as change_pct
        FROM current_avg c, previous_avg p
        WHERE c.avg_salary > p.avg_salary * (1 + %s)
        """
        
        result = self.db_session.execute(query, (threshold,))
        spikes = []
        for row in result:
            spikes.append({
                'type': 'salary_spike',
                'current_avg': float(row[0]),
                'previous_avg': float(row[1]),
                'change_pct': float(row[2]),
                'detected_at': datetime.now().isoformat()
            })
        return spikes
    
    def check_skill_shortages(self, top_n: int = 5) -> List[Dict]:
        """Identify skills with declining supply."""
        query = """
        WITH skill_trends AS (
            SELECT 
                skill AS skill_name,
                COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent,
                COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '90 days' 
                      AND posted_date < CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as previous
            FROM analytics.fact_job_posting,
                 jsonb_array_elements_text(extracted_skills) AS skill
            WHERE extracted_skills IS NOT NULL
              AND is_active = TRUE
            GROUP BY skill
        )
        SELECT 
            skill_name,
            recent,
            previous,
            CASE 
                WHEN previous > 0 THEN ROUND(((recent - previous)::numeric / previous * 100), 1)
                ELSE 0 
            END as change_pct
        FROM skill_trends
        WHERE recent < previous * 0.7
        ORDER BY change_pct ASC
        LIMIT %s
        """
        
        result = self.db_session.execute(query, (top_n,))
        shortages = []
        for row in result:
            shortages.append({
                'type': 'skill_shortage',
                'skill_name': row[0],
                'recent_demand': row[1],
                'previous_demand': row[2],
                'change_pct': float(row[3]),
                'detected_at': datetime.now().isoformat()
            })
        return shortages
    
    def get_critical_metrics(self) -> Dict:
        """Get all critical metrics for real-time dashboard."""
        return {
            'salary_spikes': self.check_salary_spikes(),
            'skill_shortages': self.check_skill_shortages(),
            'timestamp': datetime.now().isoformat()
        }


def setup_realtime_triggers(dsn: str):
    """Set up PostgreSQL triggers for real-time notifications."""
    conn = psycopg2.connect(dsn)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Create notification function
    cursor.execute("""
    CREATE OR REPLACE FUNCTION notify_critical_change()
    RETURNS TRIGGER AS $$
    BEGIN
        PERFORM pg_notify(
            'critical_data_change',
            json_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'timestamp', NOW()
            )::text
        );
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers on key tables
    for table in ['fact_job_posting', 'dim_company', 'dim_location']:
        cursor.execute(f"""
        DROP TRIGGER IF EXISTS trigger_critical_change ON analytics.{table};
        CREATE TRIGGER trigger_critical_change
        AFTER INSERT OR UPDATE OR DELETE ON analytics.{table}
        FOR EACH ROW EXECUTE FUNCTION notify_critical_change();
        """)
    
    conn.close()
    logger.info("realtime_triggers_created")