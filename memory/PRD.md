# MatchMe — Dating Profile Optimizer PRD

## Original Problem Statement
Build a web app called MatchMe — a premium dating profile optimizer. Users upload photos and get feedback from real people to improve their dating profiles on Hinge, Tinder, and Bumble. 

## User Personas
1. **Dating App Users** - Singles looking to improve their dating profile photos
2. **Reviewers** - Users who rate others' photos to earn credits
3. **Premium Users** - Users who pay for priority access

## Core Requirements (Static)
- Photo upload and storage
- Human rating system for photos
- Best Shot analysis (find best first photo)
- Profile Analysis (complete profile feedback)
- Credit-based economy
- Stripe payments (Priority Pass $9, Pro $19/mo)
- JWT auth + Google OAuth
- Hinge-style mobile-first UI

## What's Been Implemented (Jan 2026)

### Responsive Design Update
- [x] Full responsive layout across all screen sizes
- [x] Mobile (under 768px): Full width, bottom navigation, stacked cards
- [x] Tablet (768px-1024px): Max-width 768px centered, single column with padding
- [x] Desktop (1024px+): Max-width 1200px, sidebar navigation, multi-column layouts
- [x] Landing: Full-width hero, 3-column feature cards
- [x] Dashboard: Sidebar on left (240px), main content on right
- [x] Best Shot: 3-column photo grid
- [x] Profile Analysis: 2-column (photos left, prompts right)
- [x] Rate Others: Photo centered with controls on right
- [x] Pricing: 3-column pricing cards

### Backend
- [x] FastAPI with MongoDB
- [x] JWT authentication + Google OAuth
- [x] Emergent Object Storage for photos
- [x] Credit system (3 free on signup)
- [x] Job queue (Best Shot, Profile Analysis)
- [x] Rating system with gender matching
- [x] Stripe payments integration
- [x] Admin user seeding

### Frontend
- [x] Landing page with hero
- [x] Auth (login/signup + Google)
- [x] Onboarding (3 questions)
- [x] Dashboard with credits
- [x] Best Shot upload flow
- [x] Profile Analysis upload flow
- [x] Rate Others interface
- [x] Waiting/Processing page
- [x] Results page
- [x] Pricing page (3 tiers)
- [x] Privacy & Terms pages

## Mocked Features
- SendGrid email notifications (logged to console)
- Job processing (manual trigger via /api/jobs/{id}/process)

## Prioritized Backlog
### P0 (Critical)
- None currently

### P1 (High Priority)
- [ ] Background job processing worker
- [ ] Real email notifications
- [ ] Photo moderation/filtering

### P2 (Medium Priority)
- [ ] Bio rewriter feature
- [ ] Profile preview mode
- [ ] Download results as PDF
- [ ] Share results

## Tech Stack
- Frontend: React + Tailwind
- Backend: Python/FastAPI
- Database: MongoDB
- Storage: Emergent Object Storage
- Payments: Stripe
- Email: SendGrid (mocked)

## Next Tasks
1. Add background job worker for auto-processing
2. Integrate real SendGrid for notifications
3. Add photo content moderation
4. Implement bio rewriter AI feature
