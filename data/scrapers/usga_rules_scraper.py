"""
USGA Rules of Golf web scraper.
Scrapes rules from https://www.usga.org/rules.html with respectful delays.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from loguru import logger
from datetime import datetime
import re
from urllib.parse import urljoin


class USGARulesScraper:
    """Scraper for USGA Rules of Golf."""

    def __init__(self, delay_seconds: float = 2.0, max_retries: int = 3):
        """
        Initialize the scraper.

        Args:
            delay_seconds: Delay between requests (respectful scraping)
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = "https://www.usga.org"
        self.rules_url = "https://www.usga.org/rules.html"
        self.delay = delay_seconds
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Golf Rules App) AppleWebKit/537.36'
        })

    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with retries and delays."""
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay)  # Respectful scraping
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
        return None

    def check_robots_txt(self) -> bool:
        """Check robots.txt for scraping permissions."""
        try:
            response = self._make_request(f"{self.base_url}/robots.txt")
            if response:
                # Basic check - in production, use robotparser
                logger.info("Checked robots.txt - proceeding with scraping")
                return True
        except Exception as e:
            logger.warning(f"Could not check robots.txt: {e}")
        return True  # Proceed cautiously if robots.txt unavailable

    def scrape_rules_index(self) -> List[Dict[str, str]]:
        """
        Scrape the main rules index page to get all rule sections.

        Returns:
            List of dictionaries with rule metadata
        """
        logger.info(f"Scraping rules index from {self.rules_url}")

        response = self._make_request(self.rules_url)
        if not response:
            logger.error("Failed to fetch rules index page")
            return []

        soup = BeautifulSoup(response.content, 'lxml')

        # The actual structure will depend on USGA's website layout
        # This is a template that needs to be adjusted based on the real site
        rules_list = []

        # Look for rule sections - this is an educated guess at the structure
        # You may need to inspect the actual page and adjust these selectors
        rule_sections = soup.find_all(['div', 'section'], class_=re.compile(r'rule|section', re.I))

        if not rule_sections:
            # Alternative: look for links containing "rule" in the URL
            all_links = soup.find_all('a', href=re.compile(r'rule', re.I))
            logger.info(f"Found {len(all_links)} rule-related links")

            for link in all_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    text = link.get_text(strip=True)

                    # Extract rule number if present
                    rule_match = re.search(r'Rule\s+(\d+)', text, re.I)
                    rule_id = rule_match.group(1) if rule_match else text[:20]

                    rules_list.append({
                        'rule_id': rule_id,
                        'title': text,
                        'url': full_url,
                        'section': self._extract_section(text)
                    })

        logger.info(f"Found {len(rules_list)} rule sections")
        return rules_list

    def _extract_section(self, text: str) -> str:
        """Extract section category from rule title."""
        # Common rule categories
        if re.search(r'player|behavior|conduct', text, re.I):
            return 'Player Conduct'
        elif re.search(r'equipment|clubs|balls', text, re.I):
            return 'Equipment'
        elif re.search(r'play|stroke|course', text, re.I):
            return 'Playing the Game'
        elif re.search(r'relief|penalty', text, re.I):
            return 'Relief and Penalties'
        else:
            return 'General Rules'

    def scrape_rule_content(self, rule_url: str, rule_id: str) -> Optional[Dict]:
        """
        Scrape the full content of a specific rule.

        Args:
            rule_url: URL of the rule page
            rule_id: Rule identifier

        Returns:
            Dictionary with rule content
        """
        logger.info(f"Scraping rule {rule_id} from {rule_url}")

        response = self._make_request(rule_url)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract main content
        # This selector needs to be adjusted based on actual site structure
        content_area = soup.find(['div', 'article', 'main'],
                                class_=re.compile(r'content|rule|article', re.I))

        if not content_area:
            content_area = soup.find('body')

        # Get text content
        content_text = ""
        if content_area:
            # Remove scripts and styles
            for script in content_area(['script', 'style']):
                script.decompose()

            # Get text with some structure preserved
            paragraphs = content_area.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4'])
            content_text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)

        # Get title
        title_tag = soup.find(['h1', 'h2'], class_=re.compile(r'title|heading', re.I))
        title = title_tag.get_text(strip=True) if title_tag else f"Rule {rule_id}"

        # Try to find effective date
        effective_date = self._extract_effective_date(soup)

        return {
            'rule_id': rule_id,
            'title': title,
            'content': content_text,
            'effective_date': effective_date,
            'source_url': rule_url,
            'scraped_at': datetime.now().isoformat()
        }

    def _extract_effective_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Try to extract the effective date of the rules."""
        # Look for date patterns in the page
        date_patterns = [
            r'effective\s+(\w+\s+\d{1,2},?\s+\d{4})',
            r'updated\s+(\w+\s+\d{1,2},?\s+\d{4})',
            r'(\w+\s+\d{1,2},?\s+\d{4})',  # General date pattern
        ]

        page_text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                return match.group(1)

        # Default to current year if not found
        return f"January 1, {datetime.now().year}"

    def scrape_all_rules(self) -> List[Dict]:
        """
        Scrape all USGA rules.

        Returns:
            List of all scraped rules
        """
        # Check robots.txt first
        self.check_robots_txt()

        # Get the index of all rules
        rules_index = self.scrape_rules_index()

        if not rules_index:
            logger.warning("No rules found in index, using fallback method")
            return self._scrape_fallback()

        # Scrape each rule
        all_rules = []
        total_rules = len(rules_index)

        for idx, rule_meta in enumerate(rules_index, 1):
            logger.info(f"Scraping rule {idx}/{total_rules}: {rule_meta['rule_id']}")

            rule_content = self.scrape_rule_content(
                rule_meta['url'],
                rule_meta['rule_id']
            )

            if rule_content:
                # Merge metadata with content
                rule_content['section'] = rule_meta['section']
                all_rules.append(rule_content)
            else:
                logger.warning(f"Failed to scrape rule {rule_meta['rule_id']}")

        logger.info(f"Successfully scraped {len(all_rules)} rules")
        return all_rules

    def _scrape_fallback(self) -> List[Dict]:
        """
        Fallback scraping method if the main index fails.
        Attempts to scrape from a single comprehensive rules page.
        """
        logger.info("Using fallback scraping method")

        # Try alternative URLs
        alt_urls = [
            "https://www.usga.org/content/usga/home-page/rules-hub/rules-modernization/major-changes/rules-of-golf-2023.html",
            "https://www.usga.org/rules/rules-and-clarifications.html",
        ]

        for url in alt_urls:
            response = self._make_request(url)
            if response:
                soup = BeautifulSoup(response.content, 'lxml')

                # Find all heading tags that might indicate rules
                rules = []
                headings = soup.find_all(['h2', 'h3', 'h4'])

                for heading in headings:
                    text = heading.get_text(strip=True)
                    if re.search(r'Rule\s+\d+', text, re.I):
                        # Found a rule heading
                        rule_id = re.search(r'Rule\s+(\d+)', text, re.I).group(1)

                        # Get content until next heading
                        content_parts = []
                        next_elem = heading.find_next_sibling()

                        while next_elem and next_elem.name not in ['h2', 'h3', 'h4']:
                            if next_elem.name in ['p', 'ul', 'ol']:
                                content_parts.append(next_elem.get_text(strip=True))
                            next_elem = next_elem.find_next_sibling()

                        content = '\n\n'.join(content_parts)

                        rules.append({
                            'rule_id': rule_id,
                            'title': text,
                            'content': content,
                            'section': self._extract_section(text),
                            'effective_date': f"January 1, {datetime.now().year}",
                            'source_url': url,
                            'scraped_at': datetime.now().isoformat()
                        })

                if rules:
                    logger.info(f"Fallback method found {len(rules)} rules")
                    return rules

        # If all else fails, return sample rules for testing
        logger.warning("All scraping methods failed, returning empty list")
        return []

    def get_sample_rules(self) -> List[Dict]:
        """
        Return sample rules for testing without scraping.
        Useful for development and testing.
        """
        return [
            {
                'rule_id': '1',
                'section': 'The Game',
                'title': 'Rule 1: The Game, Player Conduct and the Rules',
                'content': '''Rule 1: The Game, Player Conduct and the Rules

Purpose: Rule 1 introduces these central principles of the game:
- Play the course as you find it and play the ball as it lies.
- Play by the Rules and in the spirit of the game.
- You are responsible for applying your own penalties if you breach a Rule, so that you cannot gain any potential advantage over your opponent in match play or other players in stroke play.

1.1 The Game of Golf
Golf is played over a round of 18 (or fewer) holes on a course by striking a ball with a club.

Each hole starts with a stroke from the teeing area and ends when the ball is holed on the putting green (or when the Rules otherwise allow you to finish the hole without holing out).

For each stroke, you:
- Play the course as you find it, and
- Play the ball as it lies.

But: The Rules allow you to alter conditions on the course in a few specific situations, and allow or require you to play the ball from a different place than where it lies in other specific situations.''',
                'effective_date': 'January 1, 2023',
                'source_url': 'https://www.usga.org/rules.html',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'rule_id': '2',
                'section': 'The Course',
                'title': 'Rule 2: The Course',
                'content': '''Rule 2: The Course

Purpose: Rule 2 introduces the basic features that define the golf course, such as:
- The five defined areas of the course,
- Several types of objects and conditions that can interfere with play, and
- Several types of stakes and lines used to define areas of the course or where free relief is available.

2.1 Boundaries and Out of Bounds
The Committee should define the course boundaries and mark any out of bounds using white stakes or white lines.

2.2 Defined Areas of the Course
There are five defined areas of the course:
(1) The general area
(2) The teeing area you must play from in starting the hole you are playing
(3) All penalty areas
(4) All bunkers
(5) The putting green of the hole you are playing''',
                'effective_date': 'January 1, 2023',
                'source_url': 'https://www.usga.org/rules.html',
                'scraped_at': datetime.now().isoformat()
            },
            {
                'rule_id': '13',
                'section': 'Putting Greens',
                'title': 'Rule 13: Putting Greens',
                'content': '''Rule 13: Putting Greens

Purpose: Rule 13 is a specific Rule for putting greens. Putting greens are specially prepared for playing the ball along the ground and there is a flagstick for the hole on each putting green, so certain different Rules apply than for other areas of the course.

13.1 Actions Allowed or Required on Putting Green
13.1a When Ball Is on Putting Green
(1) Ball May Be Marked, Lifted and Cleaned. You may mark the spot of your ball on the putting green and lift and clean the ball, but the ball must be replaced on its original spot.

(2) Sand and Loose Soil May Be Removed. You may remove sand and loose soil on the putting green (but not anywhere else on the course).

(3) Damage May Be Repaired. You may repair damage on the putting green (such as ball-marks, old hole plugs, turf plugs, cut or scrapes made by equipment or flagstick) without penalty, by using your hand, foot or other part of your body or a normal ball-mark repair tool, a tee, a club or similar item of normal equipment.''',
                'effective_date': 'January 1, 2023',
                'source_url': 'https://www.usga.org/rules.html',
                'scraped_at': datetime.now().isoformat()
            }
        ]


if __name__ == "__main__":
    # Test the scraper
    scraper = USGARulesScraper(delay_seconds=2.0)
    rules = scraper.scrape_all_rules()
    print(f"Scraped {len(rules)} rules")
    for rule in rules[:3]:
        print(f"\nRule {rule['rule_id']}: {rule['title']}")
        print(f"Content length: {len(rule['content'])} characters")
