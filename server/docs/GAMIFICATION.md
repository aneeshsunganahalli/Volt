# Volt Gamification Specification

This document proposes a pragmatic gamification system for Volt that rewards healthy money habits, increases engagement, and creates clear, motivating feedback loops without encouraging risky behavior.

## Objectives
- Increase weekly active days by making small actions feel rewarding
- Improve data quality (categorized transactions, on-time goal updates)
- Encourage consistent habits (daily check-ins, no-spend days, budget adherence)
- Celebrate meaningful milestones (goal completion, savings streaks)

## Core Mechanics
- Points (XP): Earned for positive financial actions; drive Levels
- Levels: Long-term progression; unlocks badges and cosmetics
- Streaks: Consecutive-day behaviors (check-ins, logging, no-spend)
- Badges: One-time or tiered achievements (Bronze/Silver/Gold)
- Challenges: Weekly curated tasks with bonus XP
- Leaderboards (optional): Opt-in friend groups; never public by default

## Domain Events → Rewards
Emit an internal event for each user action (server-side hooks). Values below are suggested defaults; tune via config/experiments.

- TRANSACTION_IMPORTED: +2 XP (cap 100 XP/day)
- TRANSACTION_CATEGORIZED: +5 XP (first-time manual categorize)
- GOAL_CREATED: +10 XP
- GOAL_MILESTONE_REACHED (e.g., +10%, +25%, +50%, +75%): +15/25/40/60 XP
- GOAL_COMPLETED: +150 XP + badge
- DAILY_CHECKIN (opened app + viewed dashboard): +3 XP
- NO_SPEND_DAY: +15 XP (if no discretionary category spend)
- BUDGET_UNDER_TARGET (weekly): +30 XP
- SPENDING_REVIEW_COMPLETED (weekly digest flow): +10 XP

Rate limits and anti-gaming rules apply (see Fair Play below).

## Streaks
- Check-in Streak: +1 per day with dashboard view (resets after 1 day gap)
- Categorization Streak: +1 for each day with >=1 manual categorizations
- No-Spend Streak: +1 for consecutive no-spend-days (discretionary-only)

Streak bonuses: +5 XP per 3-day multiple, +20 XP on 7, +50 XP on 30.

## Levels
- Level curve: XP required grows gently to sustain multi-month retention
  - L1: 0
  - L2: 100
  - L3: 220
  - L4: 360
  - L5: 520
  - After L5: next_level_xp = current_level_xp + 200 + (level-5)*20
- Level-ups trigger celebratory UI and optional confetti; never block flows

## Badges (examples)
- First Steps: First transaction categorized
- Consistency Bronze/Silver/Gold: 7/30/100-day check-in streak
- Saver Bronze/Silver/Gold: Save 1k/5k/10k toward goals
- Categorizer: Categorize 50/200/1000 transactions
- Goal Crusher: Complete 1/3/10 goals
- No-Spend Ninja: 7-day no-spend streak

## Weekly Challenges (rotating)
- “Categorize 10 transactions” (+50 XP)
- “Review weekly spending” (+30 XP)
- “Add 2 goal deposits” (+40 XP)

## Fair Play & Guardrails
- Daily XP cap per category: prevent farming (e.g., categorize XP capped at 100/day)
- Cooldowns: repeated edits don’t re-award XP for the same transaction
- Server-side validation: compute streaks and check-ins based on server time
- Privacy: leaderboards are opt-in, limited to user-created groups

---

# Server Design

## Data Model (proposed tables)
- gamification_events: id, user_id, type, metadata(JSON), created_at
- user_points: user_id (PK), xp_total, level, updated_at
- user_streaks: id, user_id, streak_type, count, last_date
- achievements: id, code, name, tier, criteria(JSON)
- user_achievements: id, user_id, achievement_id, earned_at
- leaderboards (optional v2): id, name, owner_user_id
- leaderboard_members (optional v2): leaderboard_id, user_id, joined_at

Alembic migrations will create indices on (user_id, type, created_at) and enforce foreign keys.

## Event Types (enum)
- TRANSACTION_IMPORTED
- TRANSACTION_CATEGORIZED
- GOAL_CREATED
- GOAL_MILESTONE_REACHED
- GOAL_COMPLETED
- DAILY_CHECKIN
- NO_SPEND_DAY
- BUDGET_UNDER_TARGET
- SPENDING_REVIEW_COMPLETED

## Integration Hooks (where to emit events)
- transactions_router / transaction_worker: when import/create/categorize
- goal_service: on create, deposit/milestone detection, completion
- user_router/dashboard: mark DAILY_CHECKIN on dashboard view
- statistics/budget weekly job: evaluate BUDGET_UNDER_TARGET

## Services
- GamificationService
  - award_event(user_id, event_type, metadata)
  - recalc_level(user_id): returns (new_level, xp_total)
  - evaluate_achievements(user_id, recent_event)
  - update_streak(user_id, streak_type, event_date)
  - get_profile(user_id): points, level, streaks, badges
- LeaderboardService (v2)
  - create_board, join_board, get_board, get_rankings

## API Endpoints (FastAPI)
- GET /me/gamification/profile
  - Returns: { xpTotal, level, nextLevelXp, streaks[], badges[] }
- GET /me/gamification/feed (optional)
  - Returns recent earned events
- GET /gamification/leaderboards/{id} (v2, opt-in)
  - Returns top N and user’s rank

Schemas defined under `server/app/schemas/gamification_schema.py`.

## Migration Plan
1. Create core tables (events, points, streaks, achievements, user_achievements)
2. Backfill: derive initial achievements and XP from history (optional)
3. Add background job to compute weekly budgets and events
4. Add indices and constraints; verify performance with tests

---

# Mobile App Design (Flutter)

## Surfaces
- Dashboard Header: Level chip + XP progress bar
- Streak Widget: shows current streaks and next bonus
- Trophy Case: badges with locked/earned states
- Goal Celebration: confetti + share sheet on completion
- Challenges: weekly card with progress and claim flow
- Leaderboards (v2): friends-only, opt-in, small groups

## UX Principles
- Supportive tone; no shaming for misses
- Private by default; no public ranks
- Tiny nudges: snackbars, tasteful confetti, haptics

## API Integration
- GET profile on app open and dashboard view
- Cache profile locally; refresh on reward-worthy actions
- Show toasts when XP is earned; update header progress

---

# Analytics & Experiments
- Event logs: reward_granted, level_up, badge_earned, streak_update
- KPIs: WAU/DAU, 7-day retention, categorized_tx count, goal updates
- A/B: XP values, daily caps, presence of challenges, level curve tuning
- Feature flags: GAMIFICATION_ENABLED, LEADERBOARD_ENABLED

---

# Rollout Plan
1. Phase 1 (Silent): compute XP and streaks server-side; no UI
2. Phase 2 (Soft Launch): add profile header + streak widget (A/B 50%)
3. Phase 3: add badges + goal celebration; tune XP
4. Phase 4: introduce weekly challenges
5. Phase 5: opt-in leaderboards

---

# Open Questions
- Should “no-spend” exclude essential categories only? (recommended)
- Budget sources: monthly budget model vs inferred baseline?
- Social graph source for leaderboards (contacts vs usernames)?

---

# Next Steps
- Implement `GamificationService` and event enums under `app/services`
- Add `gamification_schema.py` with profile response models
- Wire hooks in transactions and goals service flows
- Create Alembic migration for new tables
- Ship Phase 1 in shadow mode behind `GAMIFICATION_ENABLED`
