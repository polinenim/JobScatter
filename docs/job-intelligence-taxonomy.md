# JobScout Job Intelligence Taxonomy

## Purpose

This document defines the approved JobScout architecture decisions for derived Job Intelligence. It is the specification for the future Job Profile contract and deterministic extraction foundation.

These are locked architectural decisions. They must not be changed, extended, or replaced by implementation-specific categories without an explicit architecture decision.

Job Profile is derived intelligence and must remain separate from Canonical Job. Canonical Job is the factual source of truth.

## Controlled Top-Level IT Fields

The controlled top-level taxonomy contains exactly these 15 fields:

1. AI / Machine Learning
2. Software Engineering
3. Data
4. Cloud / DevOps
5. Cybersecurity
6. IT / Systems
7. QA / Testing
8. Networking
9. Embedded / IoT
10. Robotics / Automation
11. Web / Digital Technology
12. Enterprise / Business IT
13. Research / R&D
14. Technical Product / Solutions
15. Other IT / Technology

No additional top-level taxonomy categories may be added.

## Hierarchy

Job Intelligence follows this hierarchy:

**Field -> Role Family -> Specific Role -> Capabilities -> Skills**

Role families and specific roles are not an exhaustive closed list. The system must support real-world and unfamiliar IT/technology job titles and map them to the closest appropriate taxonomy when evidence supports it.

Unknown or ambiguous classifications must remain `Unknown` rather than being invented.

## Role-Family Examples

These are examples within the open role-family taxonomy. They are not a closed list.

### AI / Machine Learning

- AI Engineering
- Machine Learning
- Generative AI
- Deep Learning
- NLP
- Computer Vision
- AI Research
- MLOps/AI Infrastructure
- AI Architecture
- Responsible/Specialized AI

### Software Engineering

- Software Development
- Backend
- Frontend
- Full Stack
- Mobile
- Cloud/Distributed Software
- DevOps/Platform
- Testing/Quality
- Embedded Software
- Game Development
- Security Software
- Architecture
- Specialized Development

## Seniority

Seniority words modify role identity. The extraction foundation must detect seniority words and equivalent senior-role titles, including:

- Senior
- Lead
- Principal
- Staff
- Head
- Director
- Engineering Manager
- Equivalent senior roles

Senior roles are excluded from later recommendations.

## Experience Rules

- No experience or `0` years: highest priority.
- Experience not mentioned: `Unknown` and high-priority potential.
- Experience of `<=1 year`: high priority.
- Experience of `1-2 years`: suitable/lower priority.
- Experience `>2 years REQUIRED`: ineligible.
- Preferred experience is not equivalent to required experience.

## Language Rules

- English only/required: no additional required language.
- Finnish required: `Finnish`.
- Swedish required: `Swedish`.
- Finnish + English: `Finnish`.
- Other required language: that language.
- Unclear language requirement: `Unknown`.
- Never guess a required language.

## Skills and Capabilities

Skills are concrete technologies or tools, such as:

- Python
- SQL
- PyTorch
- Docker
- FastAPI
- Git
- PostgreSQL

Capabilities are broader abilities, such as:

- ML
- Backend development
- Data engineering
- MLOps
- NLP
- Cloud

The extraction foundation must keep skills and capabilities distinct. A concrete technology/tool belongs in skills; a broader ability belongs in capabilities when supported by evidence.

## Other Requirements

Education, workplace/location, opportunity type, and other requirements must remain `Unknown` when evidence is insufficient.

The system must never invent requirements or infer unsupported qualifications.
