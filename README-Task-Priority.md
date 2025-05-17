# SocialSpark Orchestrator - Development Task Priority

This document outlines the prioritized development tasks for building the SocialSpark Orchestrator, focusing on an MVP (Minimum Viable Product) first, followed by subsequent enhancements.

## Phase 1: MVP - Core Functionality (Highest Priority)

**Goal:** Enable users to connect social accounts, create, schedule, and automatically publish posts to Facebook & Twitter. View basic success/failure.

1.  **Core Agent Framework & A2A Communication Setup:**
    *   [ ] **Task 1.1:** Implement basic A2A server/client libraries (or choose existing ones if available and suitable for A2A compliance). Define core A2A message structures (`AgentCard`, `Task`, `DataPart`, `Artifact`).
    *   [ ] **Task 1.2:** Develop the `Orchestrator UI Agent` (Web App Shell):
        *   User authentication for SocialSpark itself.
        *   Basic dashboard structure.
    *   [ ] **Task 1.3:** Develop the `Content & Scheduling Agent` (CS-Agent) - Skeleton:
        *   Ability to receive and store tasks.
        *   Basic internal scheduler (cron-like).

2.  **Facebook Integration (MVP - Posting Only):**
    *   [ ] **Task 2.1:** `Orchestrator UI Agent`: UI for connecting a Facebook account (OAuth flow initiation).
    *   [ ] **Task 2.2:** Develop `Platform Posting Agent - Facebook` (FB-Agent):
        *   Handle Facebook OAuth2 callback, secure token storage.
        *   Implement A2A endpoint to receive `publish_post` task.
        *   Implement logic to post text & image to Facebook API.
        *   Implement A2A task `post_status_update` (to CS-Agent) and `report_published_post` (to AN-Agent - basic).
    *   [ ] **Task 2.3:** `CS-Agent`:
        *   Logic to send `publish_post` to `FB-Agent` when a Facebook post is due.
        *   Handle `post_status_update` from `FB-Agent`.

3.  **Twitter Integration (MVP - Posting Only):**
    *   [ ] **Task 3.1:** `Orchestrator UI Agent`: UI for connecting a Twitter account.
    *   [ ] **Task 3.2:** Develop `Platform Posting Agent - Twitter` (TW-Agent):
        *   Handle Twitter OAuth, secure token storage.
        *   Implement A2A endpoint for `publish_post`.
        *   Logic to post text & image to Twitter API.
        *   Implement A2A `post_status_update` and `report_published_post`.
    *   [ ] **Task 3.3:** `CS-Agent`: Logic to send `publish_post` to `TW-Agent`. Handle status updates.

4.  **Core Posting Workflow:**
    *   [ ] **Task 4.1:** `Orchestrator UI Agent`:
        *   UI for creating a new post (text input, image upload).
        *   UI for selecting platforms (FB, TW for MVP).
        *   UI for basic date/time scheduling.
        *   Send `process_and_schedule_post` A2A task to `CS-Agent`.
    *   [ ] **Task 4.2:** `CS-Agent`:
        *   Implement `process_and_schedule_post` A2A endpoint.
        *   Basic content adaptation (text length for Twitter).
        *   Store scheduled posts.
        *   Trigger publishing flow at scheduled time.
    *   [ ] **Task 4.3:** `Orchestrator UI Agent`: Display scheduled posts (simple list/calendar). Display basic success/failure status.

5.  **Basic Analytics Agent (MVP - Data Collection Only):**
    *   [ ] **Task 5.1:** Develop `Analytics Agent` (AN-Agent) - Skeleton:
        *   Implement A2A endpoint to receive `report_published_post`.
        *   Store basic post success data (platform, platform_post_id, socialspark_post_id).

## Phase 2: Enhancing Core & Adding Platforms (High Priority)

1.  **Instagram & LinkedIn Integration:**
    *   [ ] **Task 6.1:** `Orchestrator UI Agent`: UI for connecting Instagram & LinkedIn.
    *   [ ] **Task 6.2:** Develop `Platform Posting Agent - Instagram` (IG-Agent): (Similar to FB/TW Agent, specific to IG API for image posts).
    *   [ ] **Task 6.3:** Develop `Platform Posting Agent - LinkedIn` (LI-Agent): (Similar to FB/TW Agent, specific to LI API).
    *   [ ] **Task 6.4:** `CS-Agent`: Integrate IG & LI into scheduling & publishing logic.
    *   [ ] **Task 6.5:** `AN-Agent`: Handle `report_published_post` from IG & LI Agents.

2.  **Basic Analytics Display:**
    *   [ ] **Task 7.1:** `AN-Agent`:
        *   Implement logic to fetch basic engagement (likes, comments/retweets, shares) from FB & TW using stored platform post IDs. (Can initially be direct API calls).
        *   Implement A2A endpoint for `get_post_analytics`.
    *   [ ] **Task 7.2:** `Orchestrator UI Agent`: UI to request and display analytics received from `AN-Agent`.

3.  **Improved Content Processing:**
    *   [ ] **Task 8.1:** `CS-Agent`:
        *   Basic hashtag generation (keyword-based).
        *   Better image handling (e.g., warnings for Instagram aspect ratios).

4.  **User Experience Enhancements:**
    *   [ ] **Task 9.1:** `Orchestrator UI Agent`:
        *   Improved content calendar view.
        *   Post preview per platform.
        *   Error handling and display from platform APIs.

## Phase 3: Advanced Features & A2A Maturity (Medium Priority)

1.  **Advanced Analytics:**
    *   [ ] **Task 10.1:** `AN-Agent`:
        *   More robust analytics fetching for all platforms.
        *   Store historical analytics.
        *   (Optional A2A Enhancement) `Platform Posting Agents` could expose `fetch_platform_analytics` A2A endpoints for `AN-Agent` to call.
    *   [ ] **Task 10.2:** `Orchestrator UI Agent`: More detailed analytics dashboards.

2.  **Content Ingestion/Curation (Introducing New A2A Agent):**
    *   [ ] **Task 11.1:** Design & Develop `Content Ingestion Agent - RSS` (Example):
        *   Monitors RSS feeds.
        *   Sends potential content (as `DataPart`) to `CS-Agent` via an A2A task like `suggest_content_for_scheduling`.
    *   [ ] **Task 11.2:** `CS-Agent`: Handle incoming content suggestions, place them in a draft/review queue for the user.
    *   [ ] **Task 11.3:** `Orchestrator UI Agent`: UI for managing content sources and reviewing suggested content.

3.  **AI Content Assistance (Potential for another A2A Agent):**
    *   [ ] **Task 12.1:** `CS-Agent` or a new `AI Helper Agent`: Integrate with an LLM for:
        *   Post summarization.
        *   Drafting post variations for different platforms.
        *   Improved hashtag suggestions.
    *   [ ] **Task 12.2:** `Orchestrator UI Agent`: UI to trigger and display AI suggestions.

4.  **Full A2A Compliance & Ecosystem Readiness:**
    *   [ ] **Task 13.1:** Rigorous review of all agent interactions against the A2A specification (capability discovery, task management, collaboration patterns, user experience negotiation if applicable).
    *   [ ] **Task 13.2:** Publish `AgentCards` for all SocialSpark agents.
    *   [ ] **Task 13.3:** Documentation for third-party developers wanting to integrate with SocialSpark agents via A2A.

## Phase 4: Ongoing Improvements & Maintenance (Low Priority for initial build, then continuous)

*   [ ] **Task 14.1:** Security hardening and regular updates.
*   [ ] **Task 14.2:** Performance optimization.
*   [ ] **Task 14.3:** Monitoring and alerting for agent health and API issues.
*   [ ] **Task 14.4:** User feedback incorporation and feature requests.
*   [ ] **Task 14.5:** Keeping up with social media platform API changes.

---

This priority list helps focus on delivering value incrementally. Each phase builds upon the last, moving towards a more feature-rich and robust A2A-compliant social media orchestration tool. 