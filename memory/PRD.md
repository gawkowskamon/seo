# SEO Article Writer - Kurdynowski

## Problem Statement
Feature-rich application for writing and managing accounting-related blog articles with SEO optimization, WordPress integration, and AI-powered content tools.

## Stack
FARM (FastAPI, React, MongoDB) with Emergent LLM Key for AI (Gemini + OpenAI)

## Core Features (Implemented)
- Article generation with AI (async, background jobs)
- Visual editor with formatting toolbar + HTML view
- SurferSEO scoring panel (SERP analysis, keyword metrics, NLP terms)
- Auto-optimize with AI (multi-step: plan → sections → FAQ)
- Basic SEO scoring (keyword density, meta, headings, content length)
- AI suggestions for topics
- Meta regeneration (meta title/description, FAQ)
- Image generation (gemini-3.1-flash-image-preview) — single + batch
- PDF/HTML/WordPress export with styled inline CSS
- SEO Report PDF export
- WordPress Preview panel with SEO comparison
- JWT auth, admin role, auto-seeded admin account
- Content Calendar with scheduled WordPress publishing
- AI Chat Assistant, AI Rewriter, Newsletter Generator
- Dark Mode toggle, Keyword Analytics Dashboard
- Article import from URL + WordPress import
- Internal link building, Social Media Scheduling
- Email Notifications, Competition Monitor
- Subscription system (TPay - MOCKED)

## Key Technical Notes
- Auth token stored as `auth_token` in localStorage (AuthContext.js)
- Axios interceptor in App.js reads `auth_token` for global auth
- Auto-optimize uses multi-step LLM calls to avoid JSON truncation
- Visual editor content managed via ref (editorContentRef), not state

## Key Credentials
- Admin: monika.gawkowska@kurdynowski.pl / MonZuz8180!

## Current Status (April 2, 2026)
- All features functional
- Auto-optimize SurferSEO: working end-to-end (optimize → review → apply)
- Auth token key fixed across all components

## Backlog
- [ ] A/B Testing for titles (P2)
- [ ] Real email sending via SendGrid/Resend (P3)
- [ ] Real social media API integration (P3)
