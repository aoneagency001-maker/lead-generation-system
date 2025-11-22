"""
Feature Calculator Service

Computes basic features from normalized events.
This module does NOT perform deep analytics - it only extracts features.

Principles:
- Does NOT make business decisions
- Does NOT determine final hot_score (only base score)
- Does NOT interpret data
- Only computes features based on rules

The "Main Analytics Agent" uses these features for final analysis.
"""

import logging
import re
from datetime import date, datetime
from typing import Any, Optional

from data_intake.models import (
    DecisionStage,
    KeyPagesVisited,
    NormalizedEvent,
    SegmentType,
    SessionFeatures,
    SessionFeaturesCreate,
    SourceType,
    TrafficSourceType,
)

logger = logging.getLogger(__name__)


# Key pages patterns (URL contains these keywords)
KEY_PAGES_PATTERNS = {
    "price": [r"/price", r"/pricing", r"/cena", r"/stoimost", r"/tarif"],
    "guarantee": [r"/guarantee", r"/warranty", r"/garantiya", r"/garantii"],
    "portfolio": [r"/portfolio", r"/works", r"/projects", r"/raboty", r"/proekty"],
    "contacts": [r"/contact", r"/kontakty", r"/svyaz"],
    "about": [r"/about", r"/o-nas", r"/o-kompanii", r"/company"],
    "faq": [r"/faq", r"/voprosy", r"/help"],
    "reviews": [r"/reviews", r"/otzyvy", r"/testimonials"],
}

# Pain point keywords in search queries
PAIN_KEYWORDS = {
    "price_concern": ["дешево", "недорого", "цена", "стоимость", "бюджет", "cheap", "price", "cost"],
    "quality_concern": ["качество", "надежн", "гарантия", "quality", "reliable", "warranty"],
    "urgency": ["срочно", "быстро", "сегодня", "urgent", "fast", "today", "asap"],
    "trust_concern": ["отзывы", "рейтинг", "проверен", "reviews", "rating", "trusted"],
    "comparison": ["лучший", "сравнить", "vs", "или", "best", "compare", "versus"],
}

# AFK threshold in seconds (time gap between hits that indicates idle)
AFK_THRESHOLD_SEC = 60


class FeatureCalculator:
    """
    Calculates features from normalized events.

    This is a "dumb" calculator - it only applies rules, no ML or complex logic.
    """

    def __init__(self, key_pages_patterns: Optional[dict] = None):
        """
        Initialize calculator.

        Args:
            key_pages_patterns: Custom patterns for key pages detection.
                               Uses defaults if not provided.
        """
        self.key_pages_patterns = key_pages_patterns or KEY_PAGES_PATTERNS

    def calculate_features(
        self,
        event: NormalizedEvent,
        user_history: Optional[list[NormalizedEvent]] = None,
    ) -> SessionFeaturesCreate:
        """
        Calculate all features for a normalized event.

        Args:
            event: The normalized event to process
            user_history: Optional list of previous events for this user
                         (for calculating return_flag, visit_frequency, etc.)

        Returns:
            SessionFeaturesCreate with all computed features
        """
        # Calculate individual feature groups
        time_features = self._calculate_time_features(event)
        engagement_features = self._calculate_engagement_features(event, user_history)
        intent_features = self._calculate_intent_features(event)
        bounce_return_features = self._calculate_bounce_return_features(event, user_history)
        search_features = self._calculate_search_features(event)
        scores = self._calculate_base_scores(
            time_features,
            engagement_features,
            intent_features,
            bounce_return_features,
        )
        segmentation = self._calculate_segmentation(
            time_features,
            engagement_features,
            intent_features,
            scores,
        )

        return SessionFeaturesCreate(
            normalized_event_id=event.id,
            source=event.source,
            session_id=event.session_id,
            user_id=event.user_id,
            client_id=event.client_id,
            event_date=event.occurred_at.date() if isinstance(event.occurred_at, datetime) else date.today(),

            # Time features
            active_time_sec=time_features.get("active_time_sec"),
            idle_time_sec=time_features.get("idle_time_sec"),

            # Engagement features
            page_depth=engagement_features.get("page_depth"),
            key_pages_visited=intent_features.get("key_pages_visited"),
            key_pages_count=intent_features.get("key_pages_count"),

            # Bounce/return features
            bounce_flag=bounce_return_features.get("bounce_flag"),
            return_flag=bounce_return_features.get("return_flag"),

            # Scores (BASE only!)
            hot_score_base=scores.get("hot_score_base"),
            engagement_score=scores.get("engagement_score"),
            intent_score=scores.get("intent_score"),

            # Segmentation
            segment_type=segmentation.get("segment_type"),
            decision_stage=segmentation.get("decision_stage"),

            # Technical
            device_type=event.device_type,
            is_mobile=event.device_type in ("mobile", "tablet") if event.device_type else None,
            traffic_source_type=event.traffic_source_type,
        )

    def _calculate_time_features(self, event: NormalizedEvent) -> dict[str, Any]:
        """
        Calculate time-related features.

        TODO: For accurate active_time calculation, we need hit-level data
        with timestamps to detect AFK periods. Currently using raw_visit_duration
        with a simple heuristic.
        """
        raw_duration = event.raw_visit_duration or 0
        active_time = raw_duration
        idle_time = 0

        # If we have raw_hits, calculate active time more accurately
        if event.raw_hits and len(event.raw_hits) > 1:
            active_time, idle_time = self._calculate_active_time_from_hits(event.raw_hits)

        # Simple heuristic: if raw duration > 10 min, assume some AFK
        # TODO: Replace with proper calculation from Logs API
        elif raw_duration > 600:
            # Estimate 20% as AFK for long sessions
            idle_time = int(raw_duration * 0.2)
            active_time = raw_duration - idle_time

        return {
            "active_time_sec": active_time,
            "idle_time_sec": idle_time,
            "time_to_first_action_sec": None,  # Requires hit-level data
        }

    def _calculate_active_time_from_hits(
        self,
        hits: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """
        Calculate active time from hit timestamps.

        Args:
            hits: List of hits with 'timestamp' or 'dateTime' field

        Returns:
            Tuple of (active_time_sec, idle_time_sec)
        """
        if not hits or len(hits) < 2:
            return (0, 0)

        try:
            # Sort hits by timestamp
            sorted_hits = sorted(
                hits,
                key=lambda h: h.get("timestamp") or h.get("dateTime") or ""
            )

            active_time = 0
            idle_time = 0

            for i in range(1, len(sorted_hits)):
                prev_ts = sorted_hits[i - 1].get("timestamp") or sorted_hits[i - 1].get("dateTime")
                curr_ts = sorted_hits[i].get("timestamp") or sorted_hits[i].get("dateTime")

                if prev_ts and curr_ts:
                    # Parse timestamps and calculate diff
                    try:
                        if isinstance(prev_ts, str):
                            prev_dt = datetime.fromisoformat(prev_ts.replace("Z", "+00:00"))
                        else:
                            prev_dt = prev_ts

                        if isinstance(curr_ts, str):
                            curr_dt = datetime.fromisoformat(curr_ts.replace("Z", "+00:00"))
                        else:
                            curr_dt = curr_ts

                        diff_sec = int((curr_dt - prev_dt).total_seconds())

                        if diff_sec > AFK_THRESHOLD_SEC:
                            idle_time += diff_sec - AFK_THRESHOLD_SEC
                            active_time += AFK_THRESHOLD_SEC
                        else:
                            active_time += diff_sec
                    except Exception:
                        continue

            return (active_time, idle_time)

        except Exception as e:
            logger.warning(f"Failed to calculate active time from hits: {e}")
            return (0, 0)

    def _calculate_engagement_features(
        self,
        event: NormalizedEvent,
        user_history: Optional[list[NormalizedEvent]] = None,
    ) -> dict[str, Any]:
        """Calculate engagement-related features."""
        features = {
            "page_depth": event.page_views or 1,
            "scroll_depth_avg": None,  # Requires frontend events
            "clicks_count": None,  # Requires frontend events
        }

        # Calculate frequency features if history available
        if user_history:
            features["total_visits"] = len(user_history) + 1
            features["visit_frequency"] = self._calculate_visit_frequency(user_history)

            if user_history:
                first_visit = min(h.occurred_at for h in user_history)
                last_visit = max(h.occurred_at for h in user_history)

                if isinstance(first_visit, datetime):
                    features["days_since_first_visit"] = (datetime.utcnow() - first_visit).days
                if isinstance(last_visit, datetime):
                    features["days_since_last_visit"] = (datetime.utcnow() - last_visit).days

        return features

    def _calculate_visit_frequency(
        self,
        history: list[NormalizedEvent],
    ) -> Optional[float]:
        """Calculate visits per week based on history."""
        if not history or len(history) < 2:
            return None

        dates = [
            h.occurred_at if isinstance(h.occurred_at, datetime) else datetime.utcnow()
            for h in history
        ]
        min_date = min(dates)
        max_date = max(dates)

        days_span = (max_date - min_date).days
        if days_span < 1:
            return None

        weeks = days_span / 7
        if weeks < 1:
            weeks = 1

        return round(len(history) / weeks, 2)

    def _calculate_intent_features(self, event: NormalizedEvent) -> dict[str, Any]:
        """Calculate intent-related features based on visited pages."""
        key_pages = KeyPagesVisited()
        pages_to_check = []

        # Collect all URLs to check
        if event.url:
            pages_to_check.append(event.url.lower())
        if event.landing_page:
            pages_to_check.append(event.landing_page.lower())
        if event.raw_hits:
            for hit in event.raw_hits:
                url = hit.get("url") or hit.get("pageURL") or ""
                if url:
                    pages_to_check.append(url.lower())

        # Check each key page type
        for page_type, patterns in self.key_pages_patterns.items():
            for url in pages_to_check:
                if any(re.search(pattern, url) for pattern in patterns):
                    setattr(key_pages, page_type, True)
                    break

        # Count key pages visited
        key_pages_count = sum([
            key_pages.price,
            key_pages.guarantee,
            key_pages.portfolio,
            key_pages.contacts,
            key_pages.about,
            key_pages.faq,
            key_pages.reviews,
        ])

        return {
            "key_pages_visited": key_pages.model_dump(),
            "key_pages_count": key_pages_count,
            "form_interactions": None,  # Requires frontend events
            "cta_clicks": None,  # Requires frontend events
        }

    def _calculate_bounce_return_features(
        self,
        event: NormalizedEvent,
        user_history: Optional[list[NormalizedEvent]] = None,
    ) -> dict[str, Any]:
        """Calculate bounce and return features."""
        features = {
            "bounce_flag": event.is_bounce,
            "bounce_reason": None,
            "return_flag": False,
            "return_interval_days": None,
        }

        # Determine bounce reason if bounced
        if event.is_bounce:
            features["bounce_reason"] = self._determine_bounce_reason(event)

        # Check if returning visitor
        if user_history and len(user_history) > 0:
            features["return_flag"] = True

            # Calculate return interval
            last_visit = max(h.occurred_at for h in user_history)
            if isinstance(last_visit, datetime) and isinstance(event.occurred_at, datetime):
                features["return_interval_days"] = (event.occurred_at - last_visit).days

        return features

    def _determine_bounce_reason(self, event: NormalizedEvent) -> Optional[str]:
        """
        Try to determine why user bounced.

        This is a simple heuristic - real analysis needs more data.
        """
        duration = event.raw_visit_duration or 0

        if duration < 5:
            return "immediate_exit"
        elif duration < 15:
            return "quick_scan"
        elif event.is_new_visitor:
            return "first_impression_mismatch"
        else:
            return "unknown"

    def _calculate_search_features(self, event: NormalizedEvent) -> dict[str, Any]:
        """Extract features from search queries."""
        features = {
            "search_pain_points": [],
            "search_intent_category": None,
        }

        search_text = event.search_phrase or event.internal_search_query or ""
        if not search_text:
            return features

        search_lower = search_text.lower()

        # Detect pain points
        pain_points = []
        for pain_type, keywords in PAIN_KEYWORDS.items():
            if any(kw in search_lower for kw in keywords):
                pain_points.append(pain_type)

        features["search_pain_points"] = pain_points

        # Determine primary intent category
        if "price_concern" in pain_points:
            features["search_intent_category"] = "price_sensitive"
        elif "urgency" in pain_points:
            features["search_intent_category"] = "urgent_buyer"
        elif "comparison" in pain_points:
            features["search_intent_category"] = "comparison_shopper"
        elif "trust_concern" in pain_points:
            features["search_intent_category"] = "trust_seeker"

        return features

    def _calculate_base_scores(
        self,
        time_features: dict,
        engagement_features: dict,
        intent_features: dict,
        bounce_return_features: dict,
    ) -> dict[str, int]:
        """
        Calculate BASE scores (not final scores!).

        These are simple rule-based scores.
        Final hot_score is determined by the Analytics Agent.
        """
        # Engagement score (0-100)
        engagement_score = 0

        # Page depth contributes up to 30 points
        page_depth = engagement_features.get("page_depth", 1)
        engagement_score += min(page_depth * 6, 30)

        # Active time contributes up to 40 points
        active_time = time_features.get("active_time_sec", 0)
        if active_time > 180:
            engagement_score += 40
        elif active_time > 60:
            engagement_score += 25
        elif active_time > 30:
            engagement_score += 15

        # Return visitor bonus
        if bounce_return_features.get("return_flag"):
            engagement_score += 20

        # Bounce penalty
        if bounce_return_features.get("bounce_flag"):
            engagement_score = max(engagement_score - 20, 0)

        engagement_score = min(engagement_score, 100)

        # Intent score (0-100)
        intent_score = 0

        # Key pages contribution (up to 70 points)
        key_pages_count = intent_features.get("key_pages_count", 0)
        key_pages = intent_features.get("key_pages_visited", {})

        intent_score += key_pages_count * 10

        # Bonus for high-intent pages
        if key_pages.get("price"):
            intent_score += 15
        if key_pages.get("contacts"):
            intent_score += 15
        if key_pages.get("guarantee"):
            intent_score += 10

        intent_score = min(intent_score, 100)

        # Base hot score (simple average with weights)
        # Note: This is NOT the final hot score!
        hot_score_base = int(engagement_score * 0.4 + intent_score * 0.6)

        return {
            "engagement_score": engagement_score,
            "intent_score": intent_score,
            "hot_score_base": hot_score_base,
        }

    def _calculate_segmentation(
        self,
        time_features: dict,
        engagement_features: dict,
        intent_features: dict,
        scores: dict,
    ) -> dict[str, Any]:
        """
        Determine user segment and decision stage.

        This is a simple rule-based segmentation.
        """
        segment = None
        stage = None

        active_time = time_features.get("active_time_sec", 0)
        page_depth = engagement_features.get("page_depth", 1)
        key_pages = intent_features.get("key_pages_visited", {})
        hot_score = scores.get("hot_score_base", 0)

        # Segment determination
        if hot_score >= 70 and key_pages.get("price"):
            segment = SegmentType.HOT
        elif page_depth >= 5 and active_time > 120:
            segment = SegmentType.METHODICAL
        elif page_depth == 1 and active_time < 30:
            segment = SegmentType.IMPULSIVE
        elif key_pages.get("guarantee") or key_pages.get("reviews"):
            segment = SegmentType.CAUTIOUS
        elif page_depth >= 3 and not key_pages.get("contacts"):
            segment = SegmentType.DOUBTING

        # Decision stage determination
        if key_pages.get("contacts") or key_pages.get("price"):
            stage = DecisionStage.PURCHASE_INTENT
        elif key_pages.get("guarantee") or key_pages.get("reviews"):
            stage = DecisionStage.EVALUATION
        elif page_depth >= 3:
            stage = DecisionStage.CONSIDERATION
        else:
            stage = DecisionStage.AWARENESS

        return {
            "segment_type": segment,
            "decision_stage": stage,
        }


# Default calculator instance
_default_calculator: Optional[FeatureCalculator] = None


def get_feature_calculator() -> FeatureCalculator:
    """Get or create the default feature calculator."""
    global _default_calculator
    if _default_calculator is None:
        _default_calculator = FeatureCalculator()
    return _default_calculator
