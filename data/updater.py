"""
Scheduled data updater for golf rules and course information.
Runs monthly updates and provides manual update capability.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from data.scrapers.usga_rules_scraper import USGARulesScraper
from data.scrapers.course_scraper import GolfCourseScraper
from data.database import get_db
from rag.retriever import get_retriever


class DataUpdater:
    """
    Manages scheduled and manual updates of golf rules and course data.
    """

    def __init__(self):
        """Initialize the updater."""
        self.db = get_db()
        self.rules_scraper = USGARulesScraper()
        self.course_scraper = GolfCourseScraper()
        self.retriever = get_retriever()
        self.scheduler = BackgroundScheduler(timezone=pytz.UTC)
        self.is_running = False

        logger.info("DataUpdater initialized")

    def start_scheduler(self, cron_schedule: str = "0 2 1 * *"):
        """
        Start the background scheduler.

        Args:
            cron_schedule: Cron expression (default: 2 AM on 1st of each month)
                          Format: "minute hour day month day_of_week"
        """
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        # Schedule rules update
        self.scheduler.add_job(
            func=self.update_rules,
            trigger=CronTrigger.from_crontab(cron_schedule),
            id='update_rules',
            name='Update USGA Rules',
            replace_existing=True
        )

        # Schedule course update
        self.scheduler.add_job(
            func=self.update_courses,
            trigger=CronTrigger.from_crontab(cron_schedule),
            id='update_courses',
            name='Update Golf Courses',
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True
        logger.info(f"Scheduler started with cron: {cron_schedule}")

    def stop_scheduler(self):
        """Stop the background scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")

    def update_rules(self, use_sample: bool = False) -> Dict:
        """
        Update USGA rules data.

        Args:
            use_sample: If True, use sample data instead of scraping

        Returns:
            Dictionary with update status
        """
        logger.info("Starting rules update")
        start_time = datetime.now()

        # Update freshness status to "in_progress"
        self.db.update_data_freshness(
            data_type='rules',
            status='in_progress',
            records_updated=0
        )

        try:
            # Scrape rules
            if use_sample:
                logger.info("Using sample rules data")
                rules = self.rules_scraper.get_sample_rules()
            else:
                logger.info("Scraping USGA rules")
                rules = self.rules_scraper.scrape_all_rules()

            if not rules:
                raise Exception("No rules data retrieved")

            # Store in database
            success_count = 0
            for rule in rules:
                result = self.db.insert_rule(
                    rule_id=rule['rule_id'],
                    section=rule['section'],
                    title=rule['title'],
                    content=rule['content'],
                    effective_date=rule.get('effective_date'),
                    source_url=rule.get('source_url')
                )
                if result:
                    success_count += 1

            logger.info(f"Stored {success_count} rules in database")

            # Update vector database
            logger.info("Updating vector database")
            self.retriever.clear_collection()
            self.retriever.add_documents(rules)

            # Calculate next update (1 month from now)
            next_update = datetime.now() + timedelta(days=30)

            # Update freshness status
            self.db.update_data_freshness(
                data_type='rules',
                status='success',
                records_updated=success_count,
                next_scheduled=next_update
            )

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Rules update completed successfully in {duration:.1f}s")

            return {
                'success': True,
                'records_updated': success_count,
                'duration_seconds': duration,
                'next_update': next_update.isoformat()
            }

        except Exception as e:
            logger.error(f"Rules update failed: {e}")

            # Update freshness with error
            self.db.update_data_freshness(
                data_type='rules',
                status='failed',
                records_updated=0,
                error_message=str(e)
            )

            return {
                'success': False,
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }

    def update_courses(self, use_sample: bool = True) -> Dict:
        """
        Update golf course data.

        Args:
            use_sample: If True, use sample data (recommended for now)

        Returns:
            Dictionary with update status
        """
        logger.info("Starting courses update")
        start_time = datetime.now()

        # Update freshness status
        self.db.update_data_freshness(
            data_type='courses',
            status='in_progress',
            records_updated=0
        )

        try:
            # Get course data
            if use_sample:
                logger.info("Using sample course data")
                courses = self.course_scraper.get_sample_courses()
            else:
                logger.info("Scraping course data")
                courses = self.course_scraper.scrape_all_courses()

            if not courses:
                raise Exception("No course data retrieved")

            # Store in database
            success_count = 0
            for course in courses:
                result = self.db.insert_course(
                    name=course['name'],
                    city=course.get('city'),
                    state=course.get('state'),
                    zip_code=course.get('zip_code'),
                    slope_rating_min=course.get('slope_rating_min'),
                    slope_rating_max=course.get('slope_rating_max'),
                    course_rating_min=course.get('course_rating_min'),
                    course_rating_max=course.get('course_rating_max'),
                    tee_details=course.get('tee_details'),
                    phone=course.get('phone'),
                    website=course.get('website')
                )
                if result:
                    success_count += 1

            logger.info(f"Stored {success_count} courses in database")

            # Calculate next update
            next_update = datetime.now() + timedelta(days=30)

            # Update freshness status
            self.db.update_data_freshness(
                data_type='courses',
                status='success',
                records_updated=success_count,
                next_scheduled=next_update
            )

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Courses update completed successfully in {duration:.1f}s")

            return {
                'success': True,
                'records_updated': success_count,
                'duration_seconds': duration,
                'next_update': next_update.isoformat()
            }

        except Exception as e:
            logger.error(f"Courses update failed: {e}")

            # Update freshness with error
            self.db.update_data_freshness(
                data_type='courses',
                status='failed',
                records_updated=0,
                error_message=str(e)
            )

            return {
                'success': False,
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }

    def update_all(self, use_sample: bool = False) -> Dict:
        """
        Update both rules and courses.

        Args:
            use_sample: If True, use sample data

        Returns:
            Dictionary with combined update status
        """
        logger.info("Starting full data update")

        rules_result = self.update_rules(use_sample=use_sample)
        courses_result = self.update_courses(use_sample=use_sample)

        return {
            'rules': rules_result,
            'courses': courses_result,
            'overall_success': rules_result['success'] and courses_result['success']
        }

    def get_data_freshness_status(self) -> Dict:
        """
        Get current data freshness status with warnings.

        Returns:
            Dictionary with status information
        """
        freshness_data = self.db.get_data_freshness()

        status = {}
        for item in freshness_data:
            data_type = item['data_type']
            last_update = item['last_update']

            # Calculate age in days
            if last_update:
                last_update_dt = datetime.fromisoformat(last_update)
                age_days = (datetime.now() - last_update_dt).days

                # Determine warning level
                if age_days > 60:
                    warning_level = 'red'
                    warning_message = f'Data is {age_days} days old (>60 days)'
                elif age_days > 30:
                    warning_level = 'yellow'
                    warning_message = f'Data is {age_days} days old (>30 days)'
                else:
                    warning_level = 'green'
                    warning_message = f'Data is fresh ({age_days} days old)'
            else:
                age_days = None
                warning_level = 'red'
                warning_message = 'No data available'

            status[data_type] = {
                'last_update': last_update,
                'age_days': age_days,
                'warning_level': warning_level,
                'warning_message': warning_message,
                'update_status': item['update_status'],
                'records_updated': item['records_updated'],
                'next_scheduled_update': item['next_scheduled_update'],
                'error_message': item['error_message']
            }

        return status

    def initialize_data(self, use_sample: bool = True):
        """
        Initialize data on first run.

        Args:
            use_sample: If True, use sample data
        """
        logger.info("Initializing application data")

        # Check if data already exists
        rules = self.db.get_all_rules()
        if rules:
            logger.info(f"Rules already initialized ({len(rules)} rules)")
        else:
            logger.info("No rules found, initializing...")
            self.update_rules(use_sample=use_sample)

        # Check courses
        courses = self.db.search_courses(limit=1)
        if courses:
            logger.info(f"Courses already initialized")
        else:
            logger.info("No courses found, initializing...")
            self.update_courses(use_sample=use_sample)


# Singleton instance
_updater = None


def get_updater() -> DataUpdater:
    """Get or create singleton updater instance."""
    global _updater
    if _updater is None:
        _updater = DataUpdater()
    return _updater


if __name__ == "__main__":
    # Test the updater
    updater = get_updater()

    # Initialize with sample data
    updater.initialize_data(use_sample=True)

    # Check freshness
    status = updater.get_data_freshness_status()
    print("\nData Freshness Status:")
    for data_type, info in status.items():
        print(f"\n{data_type.upper()}:")
        print(f"  Status: {info['warning_level']} - {info['warning_message']}")
        print(f"  Last Update: {info['last_update']}")
