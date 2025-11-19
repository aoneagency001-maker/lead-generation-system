// Enums
export type NicheStatus = 'research' | 'active' | 'paused' | 'completed' | 'rejected';
export type CampaignStatus = 'draft' | 'active' | 'paused' | 'completed' | 'failed';
export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'hot' | 'won' | 'lost' | 'spam';
export type Platform = 'olx' | 'kaspi' | 'telegram' | 'whatsapp';
export type AdStatus = 'draft' | 'published' | 'active' | 'expired' | 'banned' | 'deleted';
export type MessageSender = 'bot' | 'lead' | 'human';
export type MessageType = 'text' | 'image' | 'document' | 'location';

// Database Models
export interface Niche {
  id: string;
  name: string;
  category: string;
  description?: string;
  status: NicheStatus;
  cpl_target?: number;
  roi_target?: number;
  market_size?: number;
  competition_level?: number;
  avg_price?: number;
  seasonality?: Record<string, any>;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface Campaign {
  id: string;
  niche_id: string;
  name: string;
  platform: Platform;
  status: CampaignStatus;
  budget?: number;
  spent?: number;
  start_date?: string;
  end_date?: string;
  config?: Record<string, any>;
  ads_count?: number;
  leads_count?: number;
  conversions_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Ad {
  id: string;
  campaign_id: string;
  platform: Platform;
  external_id?: string;
  url?: string;
  title: string;
  description?: string;
  price?: number;
  images?: string[];
  status: AdStatus;
  views_count?: number;
  clicks_count?: number;
  messages_count?: number;
  published_at?: string;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Lead {
  id: string;
  ad_id?: string;
  name?: string;
  phone?: string;
  email?: string;
  source: Platform;
  platform_user_id?: string;
  status: LeadStatus;
  quality_score?: number;
  budget?: number;
  urgency?: string;
  notes?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  contacted_at?: string;
  qualified_at?: string;
  closed_at?: string;
}

export interface Conversation {
  id: string;
  lead_id: string;
  platform: Platform;
  message: string;
  sender: MessageSender;
  message_type: MessageType;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface MarketResearch {
  id: string;
  niche_id: string;
  platform: Platform;
  data?: Record<string, any>;
  analysis?: Record<string, any>;
  ads_count?: number;
  avg_price?: number;
  min_price?: number;
  max_price?: number;
  competition_score?: number;
  created_at: string;
}

// Analytics & Metrics
export interface CampaignMetrics {
  campaign_id: string;
  total_ads: number;
  total_leads: number;
  total_conversions: number;
  total_spent: number;
  cpl: number; // Cost Per Lead
  cpa: number; // Cost Per Acquisition
  roi: number; // Return on Investment
  conversion_rate: number;
}

export interface NicheMetrics {
  niche_id: string;
  total_campaigns: number;
  total_leads: number;
  avg_cpl: number;
  avg_roi: number;
  success_rate: number;
}

// Dashboard Stats
export interface DashboardStats {
  total_niches: number;
  total_campaigns: number;
  total_leads: number;
  total_conversions: number;
  avg_cpl: number;
  avg_roi: number;
  active_campaigns: number;
  hot_leads: number;
}

// Pipeline Module
export interface PipelineModule {
  id: string;
  name: string;
  type: 'market-research' | 'traffic-generation' | 'lead-qualification' | 'sales-handoff' | 'analytics';
  status: 'idle' | 'running' | 'error' | 'success';
  progress?: number;
  last_run?: string;
  config?: Record<string, any>;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
