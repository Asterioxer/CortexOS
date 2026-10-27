---
title: "Workout & Health Tracker Full-Stack Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/nextjs
  - cortex/typescript
  - cortex/supabase
  - cortex/health
last_updated: "2026-10-27"
status: "verified"
---

# 🏋️ Workout & Health Tracker Full-Stack Workspace

- **Location**: `C:\Users\soham\Desktop\Workout_tracker`
- **Domain**: Personal Fitness Telemetry, Caloric Intake Tracking & Activity Monitoring
- **Primary Toolchains**: Next.js 15+ (App Router), TypeScript, React, Tailwind CSS, Supabase (PostgreSQL + Auth + RLS)

## 🏗️ Architecture & Tech Stack

```
Workout_tracker/
├── src/
│   └── middleware.ts          # Supabase session validation and protected route redirection
├── supabase/
│   └── schema.sql             # PostgreSQL schema with Row-Level Security (RLS) policies
├── public/                    # Static SVG assets & icons
├── next.config.ts             # Next.js compiler & bundling configuration
├── tsconfig.json              # TypeScript strict configuration
└── package.json               # Dependencies: @supabase/ssr, @supabase/supabase-js, Lucide icons
```

---

## 🗄️ Database Schema & RLS Security (`supabase/schema.sql`)

The backend schema enforces strict multi-tenant Row Level Security (RLS) linked to Supabase Auth (`auth.users`):

1. **`public.users_profile`**:
   - Primary Key: `id` (references `auth.users`).
   - Fields: `height` (cm), `weight` (kg), `age`, `gender` (enum: `male`, `female`, `other`), `activity_level` (enum: `sedentary`, `light`, `moderate`, `active`, `very_active`), `daily_calorie_goal` (default 2,000 kcal).
   - RLS Policy: Users can only select and update their own profile record (`auth.uid() = id`).
2. **`public.food_entries`**:
   - Primary Key: `id` (UUID v4).
   - Fields: `user_id`, `food_name`, `quantity` (grams/servings), `calories`, `date`, `created_at`.
   - RLS Policy: Read, insert, update, and delete scoped strictly to the authenticated `user_id`.
3. **`public.workout_entries`**:
   - Primary Key: `id` (UUID v4).
   - Fields: `user_id`, `workout_type`, `duration_minutes`, `intensity` (`low`, `medium`, `high`), `calories_burned`, `date`.
   - RLS Policy: Authenticated user-scoped data access.

---

## 🔗 Somatosensory & Operator Ergonomics
In CortexOS, this workspace is categorized under [[05_System_State/Operator_Profile_and_Habits|Operator Profile and Habits]]. CortexOS somatosensory monitors can query or log daily active intervals to maintain health awareness alongside system telemetry.

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[05_System_State/Operator_Profile_and_Habits|Operator Profile and Habits]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
- [[05_System_State/Toolchains_and_Compilers|Toolchains and Compilers]]
