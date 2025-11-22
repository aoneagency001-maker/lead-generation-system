#!/usr/bin/env python3
"""
LLM Pipeline Full Test Script

Tests all 3 layers:
- L2: GPT-4 Normalization
- L3: Claude Feature Engineering
- L4: Perplexity Analysis

Run: python scripts/test_llm_pipeline.py
"""

import asyncio
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


async def test_l2_normalization():
    """Test L2: GPT-4 Normalization"""
    print("\n" + "="*60)
    print("🔵 L2: Testing GPT-4 Normalization")
    print("="*60)

    from data_intake.llm import NormalizationService

    # Sample raw events (simulating GA4 + Metrika data)
    raw_events = [
        {
            "event_id": "ga4_test_001",
            "source": "google_analytics",
            "session_id": "sess_abc123",
            "occurred_at": datetime.now().isoformat(),
            "url": "https://example.com/pricing",
            "referrer": "https://google.com/search?q=lead+generation",
            "utm_source": "google",
            "utm_medium": "organic",
            "utm_campaign": None,
            "is_new_visitor": True,
            "page_views": 5,
            "active_time_sec": 180,
            "country": "Kazakhstan",
            "city": "Almaty",
            "device_type": "mobile",
        },
        {
            "event_id": "ym_test_002",
            "source": "yandex_metrika",
            "session_id": "sess_xyz789",
            "occurred_at": datetime.now().isoformat(),
            "url": "https://example.com/contacts",
            "referrer": "https://yandex.kz/search/?text=crm+system",
            "utm_source": "yandex",
            "utm_medium": "cpc",
            "utm_campaign": "brand_kz",
            "is_new_visitor": False,
            "page_views": 8,
            "active_time_sec": 320,
            "country": "Kazakhstan",
            "city": "Astana",
            "device_type": "desktop",
        },
    ]

    try:
        normalizer = NormalizationService()
        print(f"✅ NormalizationService initialized")
        print(f"   Model: GPT-4")
        print(f"   Input events: {len(raw_events)}")

        result = await normalizer.normalize_batch(raw_events, batch_size=10)

        print(f"\n📊 L2 Results:")
        print(f"   Normalized events: {len(result.get('normalized_events', []))}")
        print(f"   Tokens input: {result.get('tokens', {}).get('input', 0)}")
        print(f"   Tokens output: {result.get('tokens', {}).get('output', 0)}")

        if result.get('normalized_events'):
            print(f"\n   Sample normalized event:")
            sample = result['normalized_events'][0]
            print(json.dumps(sample, indent=4, ensure_ascii=False, default=str)[:500] + "...")

        return result.get('normalized_events', [])

    except Exception as e:
        print(f"❌ L2 Error: {e}")
        return []


async def test_l3_features(normalized_events=None):
    """Test L3: Claude Feature Engineering"""
    print("\n" + "="*60)
    print("🟣 L3: Testing Claude Feature Engineering")
    print("="*60)

    from data_intake.llm import FeatureService
    from data_intake.models import NormalizedEvent, SourceType

    # Use provided events or create sample
    if not normalized_events:
        normalized_events = [
            NormalizedEvent(
                id="norm_001",
                source=SourceType.GOOGLE_ANALYTICS,
                session_id="sess_abc123",
                user_id="user_001",
                occurred_at=datetime.now(),
                url="https://example.com/pricing",
                landing_page="/pricing",
                utm_source="google",
                utm_medium="organic",
                traffic_source_type="organic",
                device_type="mobile",
                country="Kazakhstan",
                city="Almaty",
                page_views=5,
                raw_visit_duration=180,
                events_count=12,
                is_new_visitor=True,
                is_bounce=False,
            ),
            NormalizedEvent(
                id="norm_002",
                source=SourceType.YANDEX_METRIKA,
                session_id="sess_xyz789",
                user_id="user_002",
                occurred_at=datetime.now(),
                url="https://example.com/contacts",
                landing_page="/contacts",
                utm_source="yandex",
                utm_medium="cpc",
                traffic_source_type="paid",
                device_type="desktop",
                country="Kazakhstan",
                city="Astana",
                page_views=8,
                raw_visit_duration=320,
                events_count=25,
                is_new_visitor=False,
                is_bounce=False,
            ),
        ]
    else:
        # Convert dicts to NormalizedEvent if needed
        events = []
        for e in normalized_events:
            if isinstance(e, dict):
                events.append(NormalizedEvent(
                    id=e.get('id', 'unknown'),
                    source=SourceType(e.get('source', 'google_analytics')),
                    session_id=e.get('session_id'),
                    user_id=e.get('user_id'),
                    occurred_at=datetime.fromisoformat(e['occurred_at']) if e.get('occurred_at') else datetime.now(),
                    url=e.get('url'),
                    landing_page=e.get('landing_page'),
                    utm_source=e.get('utm_source'),
                    utm_medium=e.get('utm_medium'),
                    traffic_source_type=e.get('traffic_source_type'),
                    device_type=e.get('device_type'),
                    country=e.get('country'),
                    city=e.get('city'),
                    page_views=e.get('page_views'),
                    raw_visit_duration=e.get('raw_visit_duration'),
                    events_count=e.get('events_count'),
                    is_new_visitor=e.get('is_new_visitor'),
                    is_bounce=e.get('is_bounce'),
                ))
            else:
                events.append(e)
        normalized_events = events

    try:
        feature_service = FeatureService()
        print(f"✅ FeatureService initialized")
        print(f"   Model: Claude 3.5 Sonnet")
        print(f"   Input events: {len(normalized_events)}")

        result = await feature_service.calculate_features_batch(
            normalized_events=normalized_events,
            batch_size=10
        )

        print(f"\n📊 L3 Results:")
        print(f"   Features calculated: {len(result.get('features', []))}")
        print(f"   Tokens input: {result.get('tokens', {}).get('input', 0)}")
        print(f"   Tokens output: {result.get('tokens', {}).get('output', 0)}")

        summary = result.get('summary', {})
        print(f"\n   Summary:")
        print(f"   - Avg hot_score: {summary.get('avg_hot_score', 0):.1f}")
        print(f"   - Avg intent_score: {summary.get('avg_intent_score', 0):.1f}")
        print(f"   - Segment distribution: {summary.get('segment_distribution', {})}")

        if result.get('features'):
            print(f"\n   Sample feature:")
            sample = result['features'][0]
            print(json.dumps(sample, indent=4, ensure_ascii=False, default=str)[:600] + "...")

        return result.get('features', [])

    except Exception as e:
        print(f"❌ L3 Error: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_l4_analysis(features=None):
    """Test L4: Perplexity Analysis"""
    print("\n" + "="*60)
    print("🟢 L4: Testing Perplexity Analysis")
    print("="*60)

    from data_intake.llm import AnalysisService

    # Sample unified metrics
    unified_metrics = [
        {
            "date": (date.today() - timedelta(days=i)).isoformat(),
            "unified_sessions": 150 + i * 10,
            "unified_users": 120 + i * 8,
            "unified_pageviews": 450 + i * 30,
            "conversions": 5 + i,
            "engagement_rate": 0.65 + i * 0.02,
            "bounce_rate": 0.35 - i * 0.01,
            "avg_hot_score": 6.5 + i * 0.2,
            "avg_intent_score": 5.8 + i * 0.15,
            "dominant_segment": ["DECISION", "URGENCY", "PROBLEM", "INFO", "BRAND"][i % 5],
            "ga4_data_available": True,
            "metrika_data_available": True,
        }
        for i in range(7)
    ]

    # Use provided features or create sample
    if not features:
        features = [
            {
                "session_id": f"sess_{i:03d}",
                "segment_type": ["URGENCY", "DECISION", "PROBLEM", "INFO", "BRAND"][i % 5],
                "hot_score_base": 50 + i * 5,
                "intent_score": 45 + i * 4,
                "engagement_score": 60 + i * 3,
                "decision_stage": ["awareness", "consideration", "evaluation", "purchase_intent"][i % 4],
            }
            for i in range(20)
        ]

    try:
        analyzer = AnalysisService()
        print(f"✅ AnalysisService initialized")

        # Check which model will be used
        import os
        if os.getenv("PERPLEXITY_API_KEY"):
            print(f"   Model: Perplexity Sonar ({os.getenv('PERPLEXITY_MODEL', 'small')})")
        else:
            print(f"   Model: Claude (fallback)")

        print(f"   Unified metrics days: {len(unified_metrics)}")
        print(f"   Feature records: {len(features)}")

        result = await analyzer.generate_insights(
            unified_metrics=unified_metrics,
            feature_store=features,
            date_from=date.today() - timedelta(days=7),
            date_to=date.today(),
            insight_type="weekly",
        )

        print(f"\n📊 L4 Results:")
        print(f"   Model used: {result.get('model_used', 'unknown')}")
        print(f"   Tokens input: {result.get('tokens_input', 0)}")
        print(f"   Tokens output: {result.get('tokens_output', 0)}")

        insights = result.get('insights', {})
        if insights:
            print(f"\n   📝 Executive Summary:")
            print(f"   {insights.get('executive_summary', 'N/A')[:300]}...")

            print(f"\n   🎯 Key Findings: {len(insights.get('key_findings', []))}")
            for i, finding in enumerate(insights.get('key_findings', [])[:3], 1):
                print(f"   {i}. [{finding.get('impact', '?')}] {finding.get('title', 'N/A')}")

            print(f"\n   📈 Segment Performance:")
            for segment, data in insights.get('segment_performance', {}).items():
                if isinstance(data, dict):
                    print(f"   - {segment}: volume={data.get('volume', '?')}, action={data.get('action', 'N/A')[:50]}...")

            print(f"\n   💡 Recommendations:")
            recs = insights.get('recommendations', {})
            for action in recs.get('immediate_actions', [])[:3]:
                if isinstance(action, dict):
                    print(f"   → {action.get('action', 'N/A')[:60]}...")
                else:
                    print(f"   → {str(action)[:60]}...")

        return result

    except Exception as e:
        print(f"❌ L4 Error: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def test_full_pipeline():
    """Test full pipeline L2 → L3 → L4"""
    print("\n" + "="*60)
    print("🚀 FULL PIPELINE TEST: L2 → L3 → L4")
    print("="*60)

    from data_intake.llm import LLMPipeline
    from data_intake.models import VisitEvent, SourceType

    # Create sample raw events
    raw_events = [
        VisitEvent(
            event_id=f"test_{i:03d}",
            source=SourceType.GOOGLE_ANALYTICS if i % 2 == 0 else SourceType.YANDEX_METRIKA,
            session_id=f"sess_{i:03d}",
            occurred_at=datetime.now() - timedelta(hours=i),
            url=f"https://example.com/{['pricing', 'contacts', 'about', 'portfolio', 'faq'][i % 5]}",
            utm_source="google" if i % 2 == 0 else "yandex",
            utm_medium="organic" if i % 3 == 0 else "cpc",
            is_new_visitor=i % 2 == 0,
            page_views=3 + i,
            active_time_sec=60 + i * 30,
            country="Kazakhstan",
            city="Almaty" if i % 2 == 0 else "Astana",
            device_type="mobile" if i % 3 == 0 else "desktop",
        )
        for i in range(5)
    ]

    try:
        pipeline = LLMPipeline()
        print(f"✅ LLMPipeline initialized")
        print(f"   Input events: {len(raw_events)}")

        result = await pipeline.run_full_pipeline(
            raw_events=raw_events,
            date_from=date.today() - timedelta(days=1),
            date_to=date.today(),
            generate_insights=True,
        )

        print(f"\n📊 Pipeline Results:")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Pipeline ID: {result.get('pipeline_id', 'N/A')}")
        print(f"   Total processing time: {result.get('total_processing_time_sec', 0):.2f}s")

        total_tokens = result.get('total_tokens', {})
        print(f"   Total tokens: {total_tokens.get('input', 0) + total_tokens.get('output', 0)}")

        print(f"\n   Layer breakdown:")
        for layer, data in result.get('layers', {}).items():
            print(f"   - {layer}: {data.get('status', '?')}, count={data.get('count', '?')}, time={data.get('processing_time_sec', 0):.2f}s")

        return result

    except Exception as e:
        print(f"❌ Pipeline Error: {e}")
        import traceback
        traceback.print_exc()
        return {}


async def main():
    """Run all tests"""
    print("🧪 LLM PIPELINE TEST SUITE")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check API keys
    print("\n📋 API Keys Status:")
    print(f"   OPENAI_API_KEY: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
    print(f"   ANTHROPIC_API_KEY: {'✅' if os.getenv('ANTHROPIC_API_KEY') else '❌'}")
    print(f"   PERPLEXITY_API_KEY: {'✅' if os.getenv('PERPLEXITY_API_KEY') else '❌'}")

    # Run tests
    print("\n" + "="*60)
    print("Starting individual layer tests...")
    print("="*60)

    # Test each layer
    # normalized = await test_l2_normalization()
    # features = await test_l3_features(normalized)
    # insights = await test_l4_analysis(features)

    # Or test full pipeline
    print("\n🔄 Running full pipeline test...")
    pipeline_result = await test_full_pipeline()

    print("\n" + "="*60)
    print("✅ TEST SUITE COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
