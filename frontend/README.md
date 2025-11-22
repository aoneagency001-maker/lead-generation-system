# Lead Generation System - Frontend

Modern, responsive frontend for the Lead Generation System built with Next.js 15, TypeScript, and Tailwind CSS.

## 🚀 Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Visualization**: React Flow (Pipeline), Tremor (Charts)
- **Tables**: TanStack Table
- **Auth**: Supabase Auth
- **API Client**: Custom REST client for FastAPI backend
- **Real-time**: WebSocket client

## 🛠️ Setup

```bash
npm install
npm run dev
```

Open http://localhost:3000

## 📝 Environment Variables

Create `.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8001
```

## 📱 Features

✅ Dashboard with KPI metrics
✅ LEGO Modules pipeline view
✅ Leads management
✅ Niches & Campaigns CRUD
✅ Supabase Auth
✅ Responsive design

🚧 Coming soon:
- React Flow pipeline editor
- TanStack advanced tables
- Analytics charts (Tremor)
- Real-time WebSocket updates
- Landing page

## 📦 Key Dependencies

- next@16.0.3
- react@19.2.0
- tailwindcss@4.0.0
- @supabase/supabase-js
- @xyflow/react
- @tremor/react
- @tanstack/react-table

Part of Lead Generation System v0.1 (Demo MVP)
