/**
 * Google Analytics 4 Types
 * Типы данных для работы с GA4 API
 */

export interface GA4Property {
  id: string;
  name: string;
  property: string; // Формат: "properties/123456789"
}

export interface GA4Summary {
  property_id: string;
  period: {
    date_from: string;
    date_to: string;
    days: number;
  };
  metrics: {
    sessions: number;
    users: number;
    pageviews: number;
    online_users: number;
  };
  top_sources: Array<{
    source: string;
    medium: string;
    campaign: string | null;
    visits: number;
    users: number;
    traffic_type?: string;
    traffic_detail?: string;
    bounce_rate?: number;
    engagement_rate?: number;
  }>;
  traffic_by_type?: {
    [key: string]: {
      visits: number;
      users: number;
      subtypes?: {
        [key: string]: {
          visits: number;
          users: number;
        };
      };
    };
  };
  sync_status: {
    last_sync: string;
    status: string;
  };
}

export interface GA4VisitorsByDate {
  date: string;
  visits: number; // sessions
  users: number; // activeUsers
  pageviews: number; // screenPageViews
  bounce_rate?: number;
  engagement_rate?: number;
}

export interface GA4TrafficSource {
  source: string;
  medium: string;
  campaign: string | null;
  visits: number; // sessions
  users: number; // activeUsers
  bounce_rate: number;
  engagement_rate?: number;
  conversion_rate?: number;
}

export interface GA4Geography {
  country: string;
  city: string;
  region?: string;
  visits: number; // sessions
  users: number; // activeUsers
  bounce_rate?: number;
}

export interface GA4OnlineVisitor {
  country: string;
  device: string; // deviceCategory
  event: string; // eventName
  os?: string; // operatingSystem
  active_users: number; // activeUsers
  event_count: number; // eventCount
}

export interface GA4RecentVisit {
  date: string;
  time?: string;
  country: string;
  city?: string;
  device: string; // deviceCategory
  browser?: string;
  os?: string; // operatingSystem
  landing_page: string; // landingPage
  visits: number; // sessions
  users: number; // activeUsers
  pageviews: number; // screenPageViews
}

export interface GA4SearchQuery {
  query?: string; // eventName в GA4
  event?: string; // eventName
  landing_page?: string;
  count: number; // eventCount
  users: number; // activeUsers
  segment?: string;
}

export interface GA4ReportResponse {
  data: Array<{
    dimensions: string[];
    metrics: number[];
  }>;
  totals: number[];
  row_count: number;
}

export interface GA4RealtimeResponse {
  data: Array<{
    dimensions: string[];
    metrics: number[];
  }>;
  row_count: number;
  note?: string;
}

