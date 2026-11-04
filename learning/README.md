# Build an AI Assistant That Can Do Things for You — Study Course

This folder is a step-by-step course for building a personal AI assistant: a program that uses an existing
AI model (like Claude) as its "brain" and connects it to tools such as your tasks, email, calendar, files and the web.

Every section follows the same format: numbered lessons with explanations, code to type out, common mistakes,
exercises, a capstone project that builds on the previous one, a weekly schedule, a checklist, and exercise solutions.

## The sections

| # | Section | What you'll be able to do | Rough time |
|---|---|---|---|
| 1 | [Core Programming](01-core-programming.md) | Write Python, use the terminal and Git, build a CLI Work Organizer | 10–14 weeks |
| 2 | [Working with Data and APIs](02-data-and-apis.md) | Talk to any web API, handle OAuth, pagination, retries and webhooks | 4–6 weeks |
| 3 | [Using AI Models](03-ai-models.md) | Call Claude, write good prompts, give the model tools, build an agent loop | 4–6 weeks |
| 4 | [Memory and Knowledge](04-memory-and-knowledge.md) | Use databases, conversation history, long-term memory, embeddings and RAG | 4–6 weeks |
| 5 | [Integrations](05-integrations.md) | Connect Gmail, Calendar, Slack, the web, files and scheduled jobs | 4–6 weeks |
| 6 | [Interface](06-interface.md) | Talk to your assistant through a Telegram bot, a web app or voice | 3–5 weeks |
| 7 | [Deployment and Operations](07-deployment-and-operations.md) | Run it 24/7 in the cloud with Docker, CI/CD, monitoring and cost control | 3–5 weeks |
| 8 | [Safety and Security](08-safety-and-security.md) | Stop it from doing harmful things: permissions, prompt injection, sandboxing | 2–4 weeks |
| 9 | [Deeper Machine Learning](09-machine-learning.md) *(optional)* | Understand how models work, run open models locally, fine-tune one | 8–12 weeks |

## How the capstones connect

Each section's capstone upgrades the same project, the **Work Organizer**:

1. A command-line task manager that saves to JSON
2. A typed, tested API client library
3. An AI chat agent that manages your tasks through tools
4. The agent gets a database, memory, and answers questions about your documents
5. The agent reads your email and calendar and sends a daily briefing
6. You chat with it on Telegram or in a web page
7. It runs in the cloud around the clock
8. It asks permission before risky actions and resists prompt injection
9. *(optional)* A small model you fine-tuned yourself handles simple requests

## Tips

- Do the sections in order. Section 8 (safety) should be read **before** you give your assistant real write access to email or money.
- Type the code yourself instead of copying it.
- Commit your progress to Git after every lesson.
- When you're stuck for more than 20 minutes, ask for help with the full error message and the smallest code that reproduces it.
