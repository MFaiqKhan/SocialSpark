# SocialSpark Orchestrator - Agent Flow Design

This document outlines the primary operational flows and inter-agent communication within the SocialSpark Orchestrator system, which leverages the Agent2Agent (A2A) protocol.

## Core Agents Involved:

*   **`Orchestrator UI Agent` (UI-GW)**: User-facing gateway.
*   **`Content & Scheduling Agent` (CS-Agent)**: Handles content processing, adaptation, and scheduling.
*   **`Platform Posting Agent - Facebook` (FB-Agent)**: Posts to Facebook.
*   **`Platform Posting Agent - Instagram` (IG-Agent)**: Posts to Instagram.
*   **`Platform Posting Agent - Twitter` (TW-Agent)**: Posts to Twitter (X).
*   **`Platform Posting Agent - LinkedIn` (LI-Agent)**: Posts to LinkedIn.
*   **`Analytics Agent` (AN-Agent)**: Fetches and provides basic post analytics.

*(Each agent would expose its capabilities via an A2A AgentCard as per the A2A specification).*

## Key Operational Flows:

### Flow 1: User Creates & Schedules a New Post

1.  **User Action (via `UI-GW`):**
    *   Inputs post details (text, media).
    *   Selects target platforms (e.g., Facebook, Twitter).
    *   Sets schedule (date/time).
    *   Submits for scheduling.
2.  **`UI-GW` -> `CS-Agent`:**
    *   **A2A Task:** `process_and_schedule_post`
    *   **Payload (`DataPart`):**
        ```json
        {
          "user_id": "user123",
          "raw_text": "Exciting news from SocialSpark!",
          "image_data": "base64_encoded_image_or_url", // Or a reference
          "target_platforms": ["facebook", "twitter"],
          "schedule_time": "2025-12-01T10:00:00Z",
          "social_media_credentials": { // Or references to stored credentials
              "facebook_token": "user_fb_token_abc",
              "twitter_token": "user_tw_token_xyz"
          }
        }
        ```
    *   **Expected `CS-Agent` Action:** Process content for each platform, store it, and schedule it.
    *   **`CS-Agent` Response (to `UI-GW`):** Task acknowledgement (success/failure).
3.  **`UI-GW`:** Updates display to reflect the scheduled post.

### Flow 2: System Publishes a Scheduled Post

1.  **`CS-Agent` (Internal Trigger: Scheduled time reached):**
    *   Identifies a post due for publishing.
    *   Retrieves platform-adapted content and user credentials for each target platform.
2.  **`CS-Agent` -> `FB-Agent` (if Facebook is a target):**
    *   **A2A Task:** `publish_post`
    *   **Payload (`DataPart`):**
        ```json
        {
          "user_id": "user123",
          "platform_specific_content": {
            "text": "Adapted text for Facebook.",
            "image_reference": "path_or_id_to_image"
          },
          "facebook_token": "user_fb_token_abc",
          "socialspark_post_id": "internal_post_id_123" // For tracking
        }
        ```
3.  **`FB-Agent`:**
    *   Receives task.
    *   Uses Facebook API to publish.
    *   **`FB-Agent` -> `CS-Agent`:**
        *   **A2A Task:** `post_status_update`
        *   **Payload (`DataPart`):**
            ```json
            {
              "socialspark_post_id": "internal_post_id_123",
              "platform": "facebook",
              "status": "success", // or "failure"
              "platform_post_id": "facebook_post_id_789", // If successful
              "error_message": null // Or error details
            }
            ```
    *   **`FB-Agent` -> `AN-Agent`:**
        *   **A2A Task:** `report_published_post`
        *   **Payload (`DataPart`):**
            ```json
            {
              "socialspark_post_id": "internal_post_id_123",
              "user_id": "user123",
              "platform": "facebook",
              "platform_post_id": "facebook_post_id_789",
              "publish_time": "2025-12-01T10:00:05Z"
            }
            ```
4.  *(Repeat steps 2 & 3 for `TW-Agent`, `IG-Agent`, `LI-Agent` if they are targets, with their respective platform-specific payloads).*
5.  **`CS-Agent`:** Updates internal status of the SocialSpark post based on `post_status_update` from each platform agent.
6.  **`AN-Agent`:** Stores information from `report_published_post` for later analytics retrieval.

### Flow 3: User Views Basic Post Analytics

1.  **User Action (via `UI-GW`):** Requests analytics for a previously published SocialSpark post.
2.  **`UI-GW` -> `AN-Agent`:**
    *   **A2A Task:** `get_post_analytics`
    *   **Payload (`DataPart`):**
        ```json
        {
          "socialspark_post_id": "internal_post_id_123",
          "user_id": "user123"
        }
        ```
3.  **`AN-Agent`:**
    *   Receives task.
    *   Retrieves stored `platform_post_id`(s) for the given `socialspark_post_id`.
    *   **If analytics need fetching/refreshing:**
        *   For each platform:
            *   (Option A) `AN-Agent` directly calls the social media platform's API using the `platform_post_id`.
            *   (Option B - More A2A pure) `AN-Agent` -> `<Platform>-Agent` (e.g., `FB-Agent`):
                *   **A2A Task:** `fetch_platform_analytics`
                *   **Payload (`DataPart`):** `{ "platform_post_id": "facebook_post_id_789", "facebook_token": "..." }`
                *   `<Platform>-Agent` responds with analytics data.
    *   Aggregates basic metrics (likes, comments, shares, etc.).
    *   **`AN-Agent` -> `UI-GW`:**
        *   **A2A Task Response (to `get_post_analytics`):**
        *   **Payload (`DataPart`):**
            ```json
            {
              "socialspark_post_id": "internal_post_id_123",
              "analytics_data": {
                "facebook": { "likes": 10, "comments": 2, "shares": 1 },
                "twitter": { "likes": 25, "retweets": 5 }
              }
            }
            ```
4.  **`UI-GW`:** Displays analytics to the user.

### Flow 4: User Connects a New Social Media Account

1.  **User Action (via `UI-GW`):** Initiates adding a new social account (e.g., Facebook).
2.  **`UI-GW` -> (Respective `Platform Posting Agent`, e.g., `FB-Agent`):**
    *   This flow is highly dependent on the OAuth 2.0 specifics for each platform.
    *   The `UI-GW` will likely redirect the user to the platform's authorization server.
    *   The `Platform Posting Agent` might provide the initial OAuth URL parameters.
    *   After user authorization on the platform, the platform redirects back to a pre-configured URI, likely handled by the `Platform Posting Agent` or `UI-GW`.
3.  **(Respective `Platform Posting Agent`):**
    *   Securely receives and stores the access token (and refresh token, if applicable) for the user.
    *   **A2A Interaction (to `UI-GW` or a `User Profile Agent` if one exists):**
        *   Task: `confirm_social_account_link`
        *   Payload: `{ "user_id": "user123", "platform": "facebook", "status": "success", "account_name": "User's FB Page Name" }`
4.  **`UI-GW`:** Updates interface to show the connected account.

---

This flow design emphasizes clear task definitions and data exchange between agents, adhering to A2A principles. Each A2A task implies a request-response pattern, potentially over HTTP with JSON-RPC, and could involve Server-Sent Events (SSE) for longer-running tasks if needed, as per the A2A specification. 