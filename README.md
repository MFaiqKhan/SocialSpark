# SocialSpark Orchestrator

**SocialSpark Orchestrator** is a social media automation tool designed to help small businesses, marketing teams, and content creators streamline their social media presence across platforms like Facebook, Instagram, Twitter, and LinkedIn.

This project leverages the **Agent2Agent (A2A) protocol**, enabling a modular architecture where specialized AI agents collaborate to manage the entire lifecycle of social media posts – from content creation and adaptation to scheduling, platform-specific posting, and analytics.

## Architecture & Technology

The backend for each specialized agent in the SocialSpark Orchestrator is built using **FastAPI**, a modern, fast (high-performance) web framework for building APIs with Python based on standard Python type hints.

### Why FastAPI?

FastAPI is an excellent choice for this A2A-based system due to:

*   **API-First Design:** Naturally aligns with the A2A protocol where agents communicate via well-defined API contracts (tasks and data parts).
*   **Asynchronous Support (`async`/`await`):** Crucial for handling I/O-bound operations common in social media interactions (e.g., calling external platform APIs, waiting for responses) and for building responsive, scalable agent services. This complements A2A's design for potentially long-running tasks.
*   **Data Validation with Pydantic:** Ensures robust and reliable data exchange between agents, adhering to the defined A2A task payloads and `DataPart` structures.
*   **Automatic API Documentation:** Provides interactive documentation (Swagger UI & ReDoc) out-of-the-box, which is beneficial for inter-agent development, testing, and potentially for exposing `AgentCard` information.
*   **Performance:** High-performance capabilities suitable for a system managing multiple agent interactions and user requests.
*   **Python Ecosystem:** Allows leveraging the vast Python ecosystem for social media API client libraries, AI/ML integrations for advanced features, and more.

Each agent (e.g., `Content & Scheduling Agent`, `Platform Posting Agent - Facebook`) is envisioned as an independent FastAPI service, exposing endpoints that correspond to A2A tasks.

## Detailed Design & Development Plan

For a more in-depth understanding of the system, please refer to:

*   **[Agent Flow Design (README-Flow-Design.md)](README-Flow-Design.md):** Details the flow-to-flow interactions and A2A communication patterns between the various agents.
*   **[Development Task Priority (README-Task-Priority.md)](README-Task-Priority.md):** Outlines the phased development roadmap, starting with a Minimum Viable Product (MVP) and detailing subsequent feature enhancements.

## Getting Started

To get started with SocialSpark Orchestrator development, follow these steps:

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <your-repository-url>
    cd SocialSpark-Orchestrator
    ```

2.  **Create and activate a virtual environment:**

    *   **Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install dependencies:**

    Create a `requirements.txt` file in the root of your project with the following content:

    ```
    fastapi
    uvicorn[standard]
    ```

    Then, install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up MongoDB Atlas:**

    SocialSpark Orchestrator uses MongoDB Cloud (Atlas) for data storage:

    * **Create a MongoDB Atlas account:** Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) and sign up for a free account.
    
    * **Create a new cluster:** Follow the setup wizard to create a new cluster. The free tier is sufficient for development.
    
    * **Configure network access:** In the Network Access tab, add your IP address or use 0.0.0.0/0 for development (not recommended for production).
    
    * **Create a database user:** In the Database Access tab, create a new user with read/write privileges.
    
    * **Get your connection string:** From the Clusters view, click "Connect" on your cluster, then "Connect your application". Copy the connection string, which will look like:
      ```
      mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/?retryWrites=true&w=majority
      ```
      Replace `<username>` and `<password>` with your database user credentials.

    * **Initialize MongoDB collections and indexes:**
        ```bash
        python setup_mongodb.py --mongodb-url "mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/?retryWrites=true&w=majority"
        ```

5.  **Running SocialSpark Orchestrator:**

    ```bash
    # Run with MongoDB Atlas connection
    python main.py --mongodb-url "mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/?retryWrites=true&w=majority"
    
    # Run specific agents
    python main.py --agents content-scheduler --mongodb-url "mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/?retryWrites=true&w=majority"
    ```

6.  **Running a FastAPI Agent Individually:**

    Each agent is an independent FastAPI service. To run an agent (e.g., a hypothetical `main.py` for one of the agents):

    ```python
    # Example main.py for an agent
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    async def root():
        return {"message": "Agent is running"}

    # To run this (save as main.py in an agent's directory):
    # uvicorn main:app --reload --port 8000 
    # (Replace 8000 with the desired port for the agent)
    ```

    You would then navigate to the agent's directory and run:
    ```bash
    uvicorn main:app --reload --port <AGENT_PORT>
    ```
    Replace `<AGENT_PORT>` with the specific port designated for that agent.

    *(Further details on project structure and running multiple agents will be added as development progresses.)*

---

This project aims to build a flexible, scalable, and intelligent social media automation solution by combining the power of the Agent2Agent protocol with the efficiency of FastAPI. 