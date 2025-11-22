# Unified Analytics Implementation Plan

## Current State vs Target Architecture

### What We Have (Current)

```
L1: raw_events          ✅ Ready
L2: normalized_events   ✅ Ready (code-based)
L3: feature_store       ✅ Ready (code-based)
L4: Analysis Layer      ❌ Missing

Providers:
- Yandex Metrika        ✅ Ready
- Google Analytics 4    ❌ Missing
- Unified Layer         ❌ Missing
```

### Target Architecture (From Research)

```
L1: Raw Data Aggregation (GA4 + Metrika → Supabase)
L2: Normalization (GPT-4 Strict Mode)          ← LLM
L3: Feature Engineering (Claude 3.5 Sonnet)    ← LLM
L4: Analysis & Insights (Perplexity Sonar)     ← LLM NEW!
```

---

## Gap Analysis

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| L1 Raw Storage | ✅ Supabase | ✅ Supabase | None |
| L2 Normalization | Code-based | LLM (GPT-4 Strict) | Optional upgrade |
| L3 Features | Code-based | LLM (Claude) | Optional upgrade |
| L4 Analysis | Missing | LLM (Sonar) | **Need to add** |
| GA4 Provider | Missing | Required | **Need to add** |
| Unified Schema | Missing | Required | **Need to add** |
| Segment Types | 5 types | URGENCY/DECISION/PROBLEM/INFO/BRAND | **Need to update** |

---

## Implementation Plan

### Phase 1: GA4 Provider (Week 1)

**Task 1.1: Create Google Analytics 4 Provider**

```python
# data_intake/providers/google_analytics.py
class GoogleAnalyticsProvider(BaseAnalyticsProvider):
    source_type = SourceType.GOOGLE_ANALYTICS

    async def fetch_visits(self, date_from, date_to, limit=None):
        # Use GA4 Data API
        pass
```

**Files to create:**
- `data_intake/providers/google_analytics.py`
- `credentials/ga4-service-account.json` (user provides)

**Environment variables:**
```env
GOOGLE_ANALYTICS_CREDENTIALS_PATH=credentials/ga4-service-account.json
GOOGLE_ANALYTICS_PROPERTY_ID=your_property_id
```

---

### Phase 2: Unified Metrics Layer (Week 2)

**Task 2.1: Create Unified Schema**

```python
# data_intake/unified/schema.py
class UnifiedMetrics(BaseModel):
    date: date

    # Source data (both)
    ga4_sessions: Optional[int]
    metrika_visits: Optional[int]
    unified_sessions: int  # median/reconciled

    # Traffic breakdown
    traffic_breakdown: dict[str, UnifiedTrafficSource]

    # Engagement metrics (unified)
    sessions: int
    users: int
    pageviews: int
    engagement_rate: float  # 0-1
    bounce_rate: float      # 0-1
    avg_duration: int       # seconds

    # Conversion data
    conversions: int
    conversion_rate: float
    revenue: Optional[float]

    # Hot metrics (from L3)
    hot_score: float        # 0-10
    intent_score: float     # 0-10
    quality_index: float    # 0-1
    segment: str            # URGENCY|DECISION|PROBLEM|INFO|BRAND
```

**Task 2.2: Create Unified Layer Service**

```python
# data_intake/unified/service.py
class UnifiedAnalyticsService:
    async def fetch_unified_data(self, date_from, date_to):
        # 1. Fetch from GA4
        ga4_data = await self.ga4_provider.fetch_visits(...)

        # 2. Fetch from Metrika
        metrika_data = await self.metrika_provider.fetch_visits(...)

        # 3. Normalize & merge
        unified = self._merge_sources(ga4_data, metrika_data)

        return unified
```

---

### Phase 3: Update Segment Classification (Week 2)

**Current segments:**
```python
class SegmentType(str, Enum):
    DOUBTING = "сомневающийся"
    IMPULSIVE = "импульсивный"
    CAUTIOUS = "осторожный"
    METHODICAL = "методичный"
    HOT = "горячий"
```

**New segments (from research):**
```python
class SegmentType(str, Enum):
    # New primary segments
    URGENCY = "urgency"       # conversion_rate > 5% AND time > 3min
    DECISION = "decision"     # actions > 5 AND pages > 4
    PROBLEM = "problem"       # search_queries > 3
    INFO = "info"             # Default
    BRAND = "brand"           # engagement > 0.7 AND duration > 2min

    # Legacy (keep for compatibility)
    HOT = "hot"
```

**Update classification logic in `feature_calculator.py`:**
```python
def _classify_segment(self, event, engagement, intent) -> SegmentType:
    if event.conversion_rate > 0.05 and event.duration > 180:
        return SegmentType.URGENCY
    elif engagement.actions_count > 5 and engagement.pages_visited > 4:
        return SegmentType.DECISION
    elif len(event.search_queries or []) > 3:
        return SegmentType.PROBLEM
    elif engagement.engagement_rate > 0.7 and event.duration > 120:
        return SegmentType.BRAND
    else:
        return SegmentType.INFO
```

---

### Phase 4: L4 Analysis Layer (Week 3)

**Task 4.1: Create Analysis Service**

```python
# data_intake/analysis/service.py
class AnalyticsInsightsService:
    """L4: Analysis & Insights using LLM"""

    async def generate_insights(
        self,
        unified_data: list[UnifiedMetrics],
        historical_days: int = 30
    ) -> AnalysisReport:
        # Option A: Use Perplexity Sonar API
        # Option B: Use Claude API (already have key)
        # Option C: Use OpenAI GPT-4 (already have key)
        pass
```

**Task 4.2: Create Analysis Prompts**

Store prompts from research document:
- `prompts/normalization.txt` (Prompt #1)
- `prompts/feature_engineering.txt` (Prompt #2)
- `prompts/analysis_insights.txt` (Prompt #3)

---

### Phase 5: API Endpoints (Week 3)

**New endpoints:**

```python
# Unified Analytics
GET  /api/analytics/unified/summary
GET  /api/analytics/unified/comparison  # GA4 vs Metrika
GET  /api/analytics/unified/segments
GET  /api/analytics/unified/hot-leads

# Insights (L4)
GET  /api/analytics/insights
POST /api/analytics/insights/generate
GET  /api/analytics/insights/recommendations
```

---

### Phase 6: Frontend Dashboard (Week 4)

**New pages:**
- `/dashboard/analytics/google-analytics` - GA4 reports (already in UI)
- `/dashboard/analytics/unified` - Unified view
- `/dashboard/analytics/insights` - AI-generated insights

---

## Updated Database Schema

```sql
-- New table for unified metrics
CREATE TABLE IF NOT EXISTS unified_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,

    -- Source data
    ga4_sessions INTEGER,
    metrika_visits INTEGER,
    unified_sessions INTEGER NOT NULL,

    -- Traffic breakdown (JSONB)
    traffic_breakdown JSONB,

    -- Unified metrics
    users INTEGER,
    pageviews INTEGER,
    engagement_rate DECIMAL(5,4),
    bounce_rate DECIMAL(5,4),
    avg_duration INTEGER,

    -- Conversions
    conversions INTEGER,
    conversion_rate DECIMAL(5,4),
    revenue DECIMAL(12,2),

    -- Scores
    hot_score DECIMAL(4,2),
    intent_score DECIMAL(4,2),
    quality_index DECIMAL(5,4),
    segment VARCHAR(50),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(date)
);

-- Insights storage
CREATE TABLE IF NOT EXISTS analytics_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,

    -- Analysis results
    executive_summary TEXT,
    key_findings JSONB,
    segment_performance JSONB,
    recommendations JSONB,

    -- Metadata
    model_used VARCHAR(100),
    tokens_used INTEGER,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## Cost Estimation

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| GA4 Data API | Free tier | $0 |
| Metrika API | Free | $0 |
| Supabase | Free tier | $0 |
| OpenAI GPT-4 (L2) | ~100k tokens/day | $200-400 |
| Claude (L3) | ~50k tokens/day | $100-150 |
| **Total** | | **$300-550/month** |

**Free alternative:** Use only code-based normalization (current approach)

---

## Priority Order

```
1. [HIGH] GA4 Provider          ← Enables unified analytics
2. [HIGH] Unified Schema        ← Core for comparison
3. [MED]  Segment Update        ← Better classification
4. [MED]  L4 Analysis Layer     ← AI insights
5. [LOW]  LLM Normalization     ← Optional optimization
```

---

## Quick Wins (Can Do Now)

1. **Update SegmentType enum** - 30 min
2. **Add quality_index to feature_store** - 1 hour
3. **Create GA4 provider skeleton** - 2 hours
4. **Add unified_metrics table** - 30 min

---

## Decision Points

### Q1: Use LLM for normalization (L2)?

**Option A: Keep code-based** (current)
- Pros: Free, fast, deterministic
- Cons: Less flexible

**Option B: Add LLM (GPT-4 Strict)**
- Pros: Better schema compliance, handles edge cases
- Cons: Cost ($200-400/month), latency

**Recommendation:** Keep code-based for now, add LLM as optional enhancement later.

### Q2: Which LLM for L4 Analysis?

**Option A: Claude (already have key)**
- Pros: Low hallucination, good reasoning
- Cost: ~$100-150/month

**Option B: OpenAI GPT-4 (already have key)**
- Pros: Good at structured output
- Cost: ~$200-400/month

**Option C: Perplexity Sonar**
- Pros: Best for data retrieval, citations
- Cons: Need new API key

**Recommendation:** Start with Claude (already integrated), evaluate later.

---

## Next Steps

1. Create GA4 provider
2. Add unified_metrics table to schema
3. Update SegmentType enum
4. Build unified layer service
5. Create frontend page for GA4

---

*Created: 2025-11-22*
*Based on: LLM_Stack_Research_3Prompts_Architecture.md*
