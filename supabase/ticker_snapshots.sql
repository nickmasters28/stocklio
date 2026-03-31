-- Run this once in the Supabase SQL editor to create the ticker snapshots table.
-- This table stores daily pre-computed indicator snapshots for public ticker pages.

create table if not exists ticker_snapshots (
  ticker          text        primary key,
  company_name    text        not null default '',
  sector          text        not null default '',
  exchange        text        not null default '',
  market_cap      numeric     not null default 0,
  price           numeric     not null default 0,
  change_pct      numeric     not null default 0,
  change_amt      numeric     not null default 0,
  ai_score_label  text        not null default 'Neutral',  -- Bullish | Neutral | Bearish
  ai_score_value  numeric     not null default 0,          -- -1.0 to +1.0
  rsi_value       numeric     not null default 50,
  rsi_label       text        not null default 'Neutral',
  macd_label      text        not null default 'Neutral',
  bb_label        text        not null default 'Mid-Band',
  on_demand       boolean     not null default false,      -- true = generated on request, not batch
  updated_at      timestamptz not null default now()
);

-- Index for sorting/filtering by update time and sector
create index if not exists ticker_snapshots_updated_at on ticker_snapshots (updated_at desc);
create index if not exists ticker_snapshots_sector     on ticker_snapshots (sector);
create index if not exists ticker_snapshots_ai_score   on ticker_snapshots (ai_score_label);
