"""
L4: Analysis & Insights Service (Perplexity Sonar / Claude fallback)

Generates strategic insights and recommendations from feature data.
Uses Perplexity Sonar for real-time market context, Claude as fallback.

Key outputs:
- Executive summary
- Key findings with citations
- Segment performance analysis
- Actionable recommendations
- Comparative analysis (GA4 vs Metrika)
"""

import json
import logging
from datetime import date, datetime
from typing import Any, Optional

from data_intake.llm.base import BaseLLMService, LLMConfig, LLMProvider

logger = logging.getLogger(__name__)

# System prompt for L4 Analysis (Perplexity Sonar / Claude)
ANALYSIS_SYSTEM_PROMPT = """You are a senior marketing analytics consultant. Your task is to generate actionable business insights from unified analytics data.

INPUT DATA STRUCTURE:
You will receive:
1. unified_metrics: Daily aggregated data from GA4 + Yandex Metrika
2. feature_store: Session-level features with scores and segments
3. date_range: Analysis period

YOUR ANALYSIS MUST INCLUDE:

1. EXECUTIVE SUMMARY (2-3 sentences)
   - Overall performance assessment
   - Key trend direction
   - Most important finding

2. KEY FINDINGS (3-5 findings)
   For each finding:
   - Title: Clear, actionable headline
   - Insight: What the data shows
   - Impact: HIGH / MEDIUM / LOW
   - Data points: Supporting numbers
   - Recommendation: What to do

3. SEGMENT PERFORMANCE
   Analyze each segment:
   - URGENCY: Ready to buy NOW → prioritize immediate follow-up
   - DECISION: Comparing options → provide comparison content
   - PROBLEM: Looking for solution → educational content
   - BRAND: Knows brand → loyalty programs
   - INFO: Just browsing → nurture campaigns

4. COMPARATIVE ANALYSIS (GA4 vs Metrika)
   - Data discrepancies and why they matter
   - Which source is more reliable for each metric
   - Reconciliation recommendations

5. RECOMMENDATIONS
   - immediate_actions: Do this TODAY (3 items max)
   - opportunities: Growth potential areas
   - risks: What to watch out for

CRITICAL RULES:
1. ONLY use data provided - NO assumptions
2. Every insight MUST have supporting data points
3. Be specific with numbers - avoid vague language
4. Recommendations must be actionable and measurable
5. Flag any data quality issues found

OUTPUT SCHEMA:
{
  "executive_summary": "string",
  "key_findings": [
    {
      "title": "string",
      "insight": "string",
      "impact": "HIGH" | "MEDIUM" | "LOW",
      "data_points": {
        "metric_name": value,
        ...
      },
      "recommendation": "string"
    }
  ],
  "segment_performance": {
    "URGENCY": {
      "volume": integer,
      "conversion_rate": float,
      "avg_hot_score": float,
      "trend": "up" | "down" | "stable",
      "action": "string"
    },
    "DECISION": {...},
    "PROBLEM": {...},
    "BRAND": {...},
    "INFO": {...}
  },
  "comparative_analysis": {
    "ga4_advantages": ["string"],
    "metrika_advantages": ["string"],
    "discrepancies": [
      {
        "metric": "string",
        "ga4_value": value,
        "metrika_value": value,
        "difference_pct": float,
        "likely_cause": "string"
      }
    ],
    "reconciliation_notes": "string"
  },
  "recommendations": {
    "immediate_actions": [
      {
        "action": "string",
        "expected_impact": "string",
        "effort": "LOW" | "MEDIUM" | "HIGH"
      }
    ],
    "opportunities": ["string"],
    "risks": ["string"]
  },
  "data_quality": {
    "overall_score": float (0-1),
    "issues": ["string"],
    "coverage": {
      "ga4_days": integer,
      "metrika_days": integer,
      "both_sources_days": integer
    }
  },
  "citations": [
    {
      "claim": "string",
      "source": "string"
    }
  ]
}

Return ONLY valid JSON, no explanations."""


class AnalysisService(BaseLLMService):
    """
    L4 Analysis Service for generating business insights.

    Primary: Perplexity Sonar (real-time context, citations)
    Fallback: Claude 3.5 Sonnet (if Perplexity unavailable)
    """

    def _get_default_config(self) -> LLMConfig:
        """Get default configuration - prefer Perplexity, fallback to Claude."""
        # Try Perplexity first
        import os
        if os.getenv("PERPLEXITY_API_KEY"):
            return self.get_perplexity_config()
        # Fallback to Claude
        return self.get_anthropic_config()

    async def generate_insights(
        self,
        unified_metrics: list[dict[str, Any]],
        feature_store: list[dict[str, Any]],
        date_from: date,
        date_to: date,
        insight_type: str = "daily",
    ) -> dict[str, Any]:
        """
        Generate comprehensive analytics insights.

        Args:
            unified_metrics: List of daily unified metrics
            feature_store: List of session features
            date_from: Analysis start date
            date_to: Analysis end date
            insight_type: 'daily', 'weekly', 'monthly', 'custom'

        Returns:
            Dict with insights, recommendations, and metadata
        """
        logger.info(
            f"Generating {insight_type} insights for period {date_from} to {date_to}"
        )

        # Prepare aggregated data for analysis
        analysis_input = self._prepare_analysis_input(
            unified_metrics=unified_metrics,
            feature_store=feature_store,
            date_from=date_from,
            date_to=date_to,
        )

        user_prompt = f"""Analyze the following unified analytics data and generate strategic insights.

ANALYSIS PERIOD: {date_from} to {date_to}
ANALYSIS TYPE: {insight_type}

INPUT DATA:
{json.dumps(analysis_input, ensure_ascii=False, indent=2)}

Generate comprehensive insights following the output schema."""

        try:
            response = await self.call_llm(
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            content = response.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)

            return {
                "insights": content,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "insight_type": insight_type,
                "model_used": response.get("model"),
                "tokens_input": response.get("tokens_input", 0),
                "tokens_output": response.get("tokens_output", 0),
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return {
                "insights": {},
                "error": str(e),
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "insight_type": insight_type,
                "generated_at": datetime.now().isoformat(),
            }

    def _prepare_analysis_input(
        self,
        unified_metrics: list[dict[str, Any]],
        feature_store: list[dict[str, Any]],
        date_from: date,
        date_to: date,
    ) -> dict[str, Any]:
        """Prepare and aggregate data for LLM analysis."""

        # Aggregate unified metrics
        total_sessions = 0
        total_users = 0
        total_pageviews = 0
        total_conversions = 0
        engagement_rates = []
        bounce_rates = []
        hot_scores = []
        intent_scores = []

        ga4_days = 0
        metrika_days = 0
        both_days = 0

        segment_counts = {
            "URGENCY": 0, "DECISION": 0, "PROBLEM": 0, "INFO": 0, "BRAND": 0
        }

        for metric in unified_metrics:
            total_sessions += metric.get("unified_sessions", 0)
            total_users += metric.get("unified_users", 0)
            total_pageviews += metric.get("unified_pageviews", 0)
            total_conversions += metric.get("conversions", 0)

            if metric.get("engagement_rate"):
                engagement_rates.append(metric["engagement_rate"])
            if metric.get("bounce_rate"):
                bounce_rates.append(metric["bounce_rate"])
            if metric.get("avg_hot_score"):
                hot_scores.append(metric["avg_hot_score"])
            if metric.get("avg_intent_score"):
                intent_scores.append(metric["avg_intent_score"])

            if metric.get("ga4_data_available") and metric.get("metrika_data_available"):
                both_days += 1
            elif metric.get("ga4_data_available"):
                ga4_days += 1
            elif metric.get("metrika_data_available"):
                metrika_days += 1

            segment = metric.get("dominant_segment")
            if segment in segment_counts:
                segment_counts[segment] += 1

        # Aggregate feature store
        for feature in feature_store:
            segment = feature.get("segment_type")
            if segment in segment_counts:
                segment_counts[segment] += 1

        # Calculate averages
        avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
        avg_bounce = sum(bounce_rates) / len(bounce_rates) if bounce_rates else 0
        avg_hot = sum(hot_scores) / len(hot_scores) if hot_scores else 0
        avg_intent = sum(intent_scores) / len(intent_scores) if intent_scores else 0

        return {
            "period": {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "total_days": (date_to - date_from).days + 1,
            },
            "aggregated_metrics": {
                "total_sessions": total_sessions,
                "total_users": total_users,
                "total_pageviews": total_pageviews,
                "total_conversions": total_conversions,
                "conversion_rate": total_conversions / total_sessions if total_sessions > 0 else 0,
                "avg_engagement_rate": round(avg_engagement, 4),
                "avg_bounce_rate": round(avg_bounce, 4),
                "avg_hot_score": round(avg_hot, 2),
                "avg_intent_score": round(avg_intent, 2),
            },
            "segment_distribution": segment_counts,
            "data_coverage": {
                "ga4_only_days": ga4_days,
                "metrika_only_days": metrika_days,
                "both_sources_days": both_days,
                "total_unified_records": len(unified_metrics),
                "total_feature_records": len(feature_store),
            },
            "daily_metrics": unified_metrics[:30],  # Last 30 days detail
            "feature_sample": feature_store[:100],  # Sample of features
        }

    async def generate_realtime_insight(
        self,
        current_metrics: dict[str, Any],
        historical_avg: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate real-time insight comparing current vs historical.

        For live dashboards and alerts.
        """
        user_prompt = f"""Compare current metrics with historical average and identify anomalies.

CURRENT (Last hour):
{json.dumps(current_metrics, indent=2)}

HISTORICAL AVERAGE (Same hour, last 30 days):
{json.dumps(historical_avg, indent=2)}

Identify:
1. Significant deviations (>20% from average)
2. Potential issues requiring attention
3. Positive trends to highlight

Return JSON with: anomalies, alerts, highlights"""

        try:
            response = await self.call_llm(
                system_prompt="You are a real-time analytics monitor. Identify anomalies and trends concisely.",
                user_prompt=user_prompt,
            )

            content = response.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)

            return {
                "realtime_insight": content,
                "generated_at": datetime.now().isoformat(),
                "tokens_input": response.get("tokens_input", 0),
                "tokens_output": response.get("tokens_output", 0),
            }
        except Exception as e:
            logger.error(f"Realtime insight failed: {e}")
            return {"error": str(e)}

    def to_analytics_insight_record(
        self,
        insights_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert insights to analytics_insights table format.

        Args:
            insights_data: Output from generate_insights()

        Returns:
            Dict ready for database insertion
        """
        insights = insights_data.get("insights", {})

        return {
            "date_from": insights_data.get("date_from"),
            "date_to": insights_data.get("date_to"),
            "insight_type": insights_data.get("insight_type", "custom"),
            "executive_summary": insights.get("executive_summary"),
            "key_findings": json.dumps(insights.get("key_findings", [])),
            "comparative_analysis": json.dumps(insights.get("comparative_analysis", {})),
            "segment_performance": json.dumps(insights.get("segment_performance", {})),
            "recommendations": json.dumps(insights.get("recommendations", {})),
            "citations": json.dumps(insights.get("citations", [])),
            "model_used": insights_data.get("model_used"),
            "tokens_input": insights_data.get("tokens_input"),
            "tokens_output": insights_data.get("tokens_output"),
            "confidence_score": insights.get("data_quality", {}).get("overall_score"),
            "status": "completed" if insights else "failed",
            "error_message": insights_data.get("error"),
            "generated_at": insights_data.get("generated_at"),
        }
