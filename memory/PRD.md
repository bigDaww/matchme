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
- Credit-based economy (Free/Priority tiers) — always integer values
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

## Credit System (Integer-Only)
- Credits are ALWAYS whole integers — never stored or displayed as floats
- `ratings_since_last_credit` counter (0-4) tracks progress toward next credit
- Every 5 ratings: counter resets to 0, +1 credit
- `job_bonus_count` counter (0-4) tracks job completion bonuses
- Every 5 job completions where user was a rater: counter resets to 0, +1 credit
- Frontend uses Math.floor() on all credit displays as safety net

## Credit Costs
- Best Shot: 1 credit
- Profile Analysis: 2 credits

## Background Job Worker
- Runs every 15 minutes via asyncio scheduler
- Weighted score formula: (confident * 0.4) + (approachable * 0.35) + (attractive * 0.25)
- Includes individual ratings with rater_username in results
- Processes jobs when: min_ratings met OR time_cap exceeded

## What's Been Implemented (Apr 2026)

### Backend
- [x] FastAPI with MongoDB Atlas (SSL/TLS)
- [x] JWT authentication + Google OAuth
- [x] Cloudinary photo upload/delete
- [x] Integer-only credit system with counter-based earning
- [x] Job queue (Best Shot, Profile Analysis)
- [x] Rating system with gender matching
- [x] Stripe subscription checkout + webhooks
- [x] Background job worker (15-min cron)
- [x] Tier-based processing logic (Free/Priority/Pro)
- [x] Email notifications via Resend
- [x] Results include individual ratings with rater usernames
- [x] Admin user seeding + manual worker trigger

### Frontend
- [x] Landing page with hero
- [x] Auth (login/signup + Google OAuth) — fixed input padding
- [x] Dashboard with integer credit display
- [x] Results page with reviewer usernames, individual scores, and comments
- [x] Full responsive layout (Mobile/Tablet/Desktop)
- [x] All pages: Pricing, BestShot, ProfileAnalysis, RateOthers, Waiting, etc.

## Prioritized Backlog
### P1 (High Priority)
- [ ] Photo content moderation/filtering

### P2 (Medium Priority)
- [ ] Robust file validation for Cloudinary uploads
- [ ] AI-powered bio rewriter/profile suggestions
- [ ] Profile preview mode
- [ ] Download results as PDF
- [ ] Share results
