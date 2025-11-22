#!/usr/bin/env python3
"""Simple LLM test - each layer separately"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload to get fresh values


async def test_openai():
    """Test OpenAI GPT-4 directly"""
    print("\n🔵 Testing OpenAI GPT-4...")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = await client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": "Return JSON only. No markdown."},
            {"role": "user", "content": "Return a simple JSON: {\"status\": \"ok\", \"model\": \"gpt-4\"}"}
        ],
        response_format={"type": "json_object"},
        max_tokens=100,
    )

    content = response.choices[0].message.content
    print(f"   Response: {content}")
    print(f"   Tokens: {response.usage.total_tokens}")
    return json.loads(content)


async def test_anthropic():
    """Test Anthropic Claude directly"""
    print("\n🟣 Testing Anthropic Claude...")

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = await client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Return ONLY this JSON, no other text: {\"status\": \"ok\", \"model\": \"claude\"}"}
        ],
    )

    content = response.content[0].text
    print(f"   Response: {content}")
    print(f"   Tokens in: {response.usage.input_tokens}, out: {response.usage.output_tokens}")
    return json.loads(content)


async def test_perplexity():
    """Test Perplexity Sonar directly"""
    print("\n🟢 Testing Perplexity Sonar...")

    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
                "messages": [
                    {"role": "user", "content": "Return ONLY this JSON, nothing else: {\"status\": \"ok\", \"model\": \"perplexity\"}"}
                ],
                "max_tokens": 100,
            },
            timeout=60.0,
        )

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        print(f"   Response: {content}")
        print(f"   Usage: {data.get('usage', {})}")

        # Try to parse JSON from response
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()

        return json.loads(content.strip())


async def test_l2_normalize():
    """Test L2 normalization with real data"""
    print("\n🔵 Testing L2 Normalization (GPT-4)...")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    sample_event = {
        "id": "test_001",
        "source": "google_analytics",
        "url": "https://example.com/pricing",
        "utm_source": "google",
        "utm_medium": "organic",
        "page_views": 5,
        "active_time_sec": 180,
    }

    prompt = f"""Normalize this raw analytics event into unified format.

Input:
{json.dumps(sample_event, indent=2)}

Return JSON:
{{
  "normalized_events": [
    {{
      "id": "...",
      "source": "google_analytics",
      "session_id": null,
      "url": "...",
      "landing_page": "...",
      "traffic_source_type": "organic|paid|direct|referral|social",
      "page_views": int,
      "visit_duration_sec": int
    }}
  ]
}}"""

    response = await client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": "You normalize analytics events. Return ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        max_tokens=500,
    )

    content = response.choices[0].message.content
    print(f"   Response:\n{content}")
    print(f"   Tokens: {response.usage.total_tokens}")

    return json.loads(content)


async def test_l3_features():
    """Test L3 feature engineering with Claude"""
    print("\n🟣 Testing L3 Feature Engineering (Claude)...")

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    sample_event = {
        "id": "norm_001",
        "source": "google_analytics",
        "url": "https://example.com/pricing",
        "landing_page": "/pricing",
        "traffic_source_type": "organic",
        "page_views": 5,
        "visit_duration_sec": 180,
    }

    prompt = f"""Calculate features for this normalized event.

Input:
{json.dumps(sample_event, indent=2)}

Return JSON with:
- hot_score_base: 0-100 (likelihood to convert)
- intent_score: 0-100 (purchase intent)
- segment_type: URGENCY|DECISION|PROBLEM|INFO|BRAND
- decision_stage: awareness|consideration|evaluation|purchase_intent

Return ONLY valid JSON, no explanation."""

    response = await client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    content = response.content[0].text
    print(f"   Response:\n{content}")
    print(f"   Tokens: in={response.usage.input_tokens}, out={response.usage.output_tokens}")

    # Parse JSON (handle possible markdown)
    if "```" in content:
        content = content.split("```")[1].replace("json", "").strip()

    return json.loads(content.strip())


async def test_l4_insights():
    """Test L4 insights with Perplexity"""
    print("\n🟢 Testing L4 Insights (Perplexity)...")

    import httpx

    sample_data = {
        "period": "last 7 days",
        "total_sessions": 1200,
        "total_users": 950,
        "conversion_rate": 0.035,
        "avg_hot_score": 65,
        "segment_distribution": {
            "URGENCY": 50,
            "DECISION": 200,
            "PROBLEM": 350,
            "INFO": 500,
            "BRAND": 100
        }
    }

    prompt = f"""Analyze this web analytics data and provide insights.

Data:
{json.dumps(sample_data, indent=2)}

Return JSON:
{{
  "summary": "2-3 sentence summary",
  "top_finding": "most important insight",
  "recommendation": "one actionable recommendation"
}}

Return ONLY JSON."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-online"),
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.2,
            },
            timeout=60.0,
        )

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        print(f"   Response:\n{content}")
        print(f"   Usage: {data.get('usage', {})}")

        # Parse JSON
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()

        return json.loads(content.strip())


async def main():
    print("="*60)
    print("🧪 SIMPLE LLM TESTS")
    print("="*60)

    # Basic connectivity tests
    print("\n📋 Basic API Tests:")
    try:
        await test_openai()
        print("   ✅ OpenAI OK")
    except Exception as e:
        print(f"   ❌ OpenAI: {e}")

    try:
        await test_anthropic()
        print("   ✅ Anthropic OK")
    except Exception as e:
        print(f"   ❌ Anthropic: {e}")

    try:
        await test_perplexity()
        print("   ✅ Perplexity OK")
    except Exception as e:
        print(f"   ❌ Perplexity: {e}")

    # Functional tests
    print("\n" + "="*60)
    print("📋 Functional Tests (L2/L3/L4):")
    print("="*60)

    try:
        result = await test_l2_normalize()
        print("   ✅ L2 Normalization OK")
    except Exception as e:
        print(f"   ❌ L2: {e}")

    try:
        result = await test_l3_features()
        print("   ✅ L3 Features OK")
    except Exception as e:
        print(f"   ❌ L3: {e}")

    try:
        result = await test_l4_insights()
        print("   ✅ L4 Insights OK")
    except Exception as e:
        print(f"   ❌ L4: {e}")

    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
