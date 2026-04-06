# MatchMe — Dating Profile Optimizer PRD

## Original Problem Statement
Build a web app called MatchMe — a premium dating profile optimizer. Users upload photos and get feedback from real people to improve their dating profiles on Hinge, Tinder, and Bumble.

## User Personas
1. **Dating App Users** - Singles looking to improve their dating profile photos
2. **Reviewers** - Users who rate others' photos to earn credits
3. **Premium Users** - Users who pay for priority/pro access

## Core Requirements
- Photo upload and storage (Cloudinary)
- Human rating system for photos (Confident/Approachable/Attractive)
- Best Shot analysis (find best first photo, 3-10 photos)
- Profile Analysis (complete profile feedback, 4-6 photos + bio + prompt)
- Credit-based economy (Free/Priority tiers)
- Stripe subscriptions (Priority $9/mo, Pro $25/mo)
- JWT auth + Google OAuth
- Hinge-style mobile-first responsive UI
- Email-only notifications (Resend)

## Services Connected
- **MongoDB Atlas**: Connected (matchme.f5d4nup.mongodb.net)
- **Cloudinary**: Connected (dfhxmvfnk) - Photo uploads working
- **Stripe**: Live keys configured for subscriptions
- **Resend**: Connected for email notifications

## Tier System
| Feature | Free | Priority ($9/mo) | Pro ($25/mo) |
|---------|------|-------------------|--------------|
| Credits | 3 on signup + earn | 12/month | Unlimited (no credits) |
| Min Ratings | 3 | 7 | 10 |
| Time Cap | 24 hours | 4 hours | 4 hours |
| Low Confidence Min | 2 | 4 | 6 |
| Extension | +12 hours | +2 hours | +2 hours |
| Credit Earning | 5 ratings = 1 credit | N/A | N/A |
| Max Daily Credits | 5 | N/A | N/A |

## Credit Costs
- Best Shot: 1 credit
- Profile Analysis: 2 credits

## Background Job Worker
- Runs every 15 minutes via asyncio scheduler
- Weighted score formula: (confident * 0.4) + (approachable * 0.35) + (attractive * 0.25)
- Processes jobs when: min_ratings met OR time_cap exceeded
- Low confidence: processed with fewer ratings after time cap
- Extension: one extension per job before failing
- Failed jobs: refund 1 credit (Free/Priority), no refund (Pro)
- Awards 0.2 credits to raters on job completion (non-Pro only)

## What's Been Implemented (Apr 2026)

### Backend
- [x] FastAPI with MongoDB Atlas (SSL/TLS)
- [x] JWT authentication + Google OAuth
- [x] Cloudinary photo upload/delete
- [x] Credit system (3 free on signup, earn by rating)
- [x] Job queue (Best Shot, Profile Analysis)
- [x] Rating system with gender matching
- [x] Stripe subscription checkout + webhooks
- [x] Background job worker (15-min cron)
- [x] Tier-based processing logic (Free/Priority/Pro)
- [x] Email notifications via Resend (results ready, job failed)
- [x] Admin user seeding + manual worker trigger
- [x] Empty comment validation on rate/submit
- [x] Brute force login protection

### Frontend
- [x] Landing page with hero
- [x] Auth (login/signup + Google OAuth)
- [x] Onboarding (3 questions)
- [x] Dashboard with credits/tier display (no notification toggles)
- [x] Best Shot upload flow (tier-specific delivery time)
- [x] Profile Analysis upload flow (Pro-aware credit display)
- [x] Rate Others interface (Pro users see community help)
- [x] Waiting/Processing page (tier info, extension indicator)
- [x] Results page (ranked photos, comments, tags)
- [x] Pricing page (3 tiers: Free/Priority/Pro)
- [x] Payment success page
- [x] Privacy & Terms pages
- [x] Full responsive layout (Mobile/Tablet/Desktop)

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn UI
- Backend: Python/FastAPI
- Database: MongoDB Atlas
- Storage: Cloudinary
- Payments: Stripe (subscriptions + webhooks)
- Email: Resend
- Auth: JWT + Google OAuth (Emergent)

## Prioritized Backlog
### P0 (Critical)
- None currently

### P1 (High Priority)
- [ ] Photo content moderation/filtering

### P2 (Medium Priority)
- [ ] Robust file validation for Cloudinary uploads
- [ ] AI-powered bio rewriter/profile suggestions
- [ ] Profile preview mode
- [ ] Download results as PDF
- [ ] Share results

## API Endpoints
- POST /api/auth/register, /api/auth/login, /api/auth/logout, /api/auth/refresh
- POST /api/auth/google/session
- POST /api/user/onboarding
- GET /api/auth/me, /api/user/dashboard, /api/user/photos
- POST /api/upload, DELETE /api/photos/{photo_id}
- POST /api/jobs/best-shot, /api/jobs/profile-analysis
- GET /api/jobs, /api/jobs/{job_id}
- GET /api/rate/next, POST /api/rate/submit, POST /api/rate/report
- POST /api/payments/subscribe, GET /api/payments/status/{session_id}
- POST /api/payments/cancel-subscription
- POST /api/webhook/stripe
- POST /api/admin/run-worker
