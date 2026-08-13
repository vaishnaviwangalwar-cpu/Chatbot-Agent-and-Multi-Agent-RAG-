## Deployment

### Deploy to Cloud Run
* Docker Basics: writing a production Dockerfile, minimizing image size, `.dockerignore`
* Building and running the image locally to confirm parity with local dev
* Cloud Run: serverless container hosting, scale-to-zero, why it fits this workload
* Artifact Registry: pushing the built image
* Environment Variables & Secrets: wiring the LLM API key through Secret Manager instead of hardcoding it
* Public API Deployment: getting a live URL and testing it externally

**Build**
* Write and test a Dockerfile for the FastAPI app locally
* Push the image to Artifact Registry
* Deploy to Cloud Run with the LLM API key sourced from Secret Manager
* Hit the live public URL from outside the local network and confirm chat, document upload, and (infra permitting) voice all work end-to-end

---

## Bonus Topics (If Time Permits)
* CI/CD: GitHub Actions or Cloud Build auto-deploy on push
* Autoscaling & Load Testing: tuning min/max instances and concurrency, simulating concurrent users
* Cloud Monitoring & Logging: dashboards, latency/error alerts
* Cost Optimization: model tier selection (lighter vs. stronger model tradeoffs), token usage tracking, caching repeated queries
* Agent Development Kit (ADK): a framework alternative to the manually-built agent loop taught in Module 5

---

## Closing Discussion Topics
* Small Language Models (SLMs): when a smaller/lighter model is the better choice over a large one
* Evaluation: how to systematically measure whether an AI application is actually working (golden datasets, LLM-as-judge, human review)
* Hallucination: why it happens, and mitigation strategies beyond grounding (RAG)
* Cost & Caching: token cost management, response caching, prompt caching
* AI & Infra Security: prompt injection, data leakage, securing API keys and internal tools exposed to agents
* Scaling & Optimization: handling concurrent load, reducing latency, batching, model routing (lighter model for simple tasks, stronger model for complex ones)
* Emerging AI Landscape: what's changing fast in the space and how to keep pace with it

## Trending in AI Right Now
* Agentic AI & Multi-Agent Systems: the shift from chat-based AI to AI that autonomously plans and executes multi-step tasks — directly what Projects 2 and 4 teach
* Reasoning Models: models that "think" through extended intermediate steps before answering, improving performance on hard multi-step problems
* Physical AI & World Models: AI moving into robotics and real-world physical environments, not just digital tasks
* Context Engineering: the emerging discipline beyond prompt engineering — deciding what information (memory, retrieved data, tool outputs) to feed a model and when
* Computer Use / Browser Agents: models that can operate a computer or browser directly (clicking, filling forms, navigating apps) rather than only calling defined tools
* Open-Source & Small Reasoning Models: smaller, efficient, multimodal models that can be fine-tuned for specific domains — an alternative to always reaching for the largest model
* AI Governance & Regulation: growing enforcement around data provenance, explainability, and auditability of AI systems
* AI Infrastructure ("AI Factories"): the buildout of specialized, high-capacity infrastructure to support large-scale AI deployment and reasoning workloads
