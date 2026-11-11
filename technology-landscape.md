# Harness Engineering - Technology Landscape

Harness engineering is the discipline of designing the environments, constraints, and feedback loops around AI coding agents that make them reliable at scale. The formula is: `Agent = Model + Harness`. Harness is everything that isn't the model: the infrastructure that governs how the agent operates, what it can access, and how it self-corrects.

In this article I'm collecting all the technologies I stumbled upon while researching harness engineering. The list is not exhaustive, but it should give you a good starting point to explore the landscape. This aims to be a living document, so I'll keep it updated.

## SDD

### Spec-Driven Development

- [OpenSpec](https://openspec.dev/) - Spec-driven development for AI coding assistants
- [spec-kit](https://github.com/github/spec-kit) - Toolkit to get started with Spec-Driven Development
- [BMAD](https://github.com/bmad-code-org/bmad-method) - Breakthrough Method for Agile AI Driven Development
- [Spec Kitty](https://spec-kitty.ai/) - Spec Kitty is an open-source CLI for turning product intent into a repo-native AI coding workflow:
- [Specula](https://specula.info/) - Specula: An agentic tool for finding deep bugs in system code using TLA+. It uses coding agents to write TLA+ specs of the target system.
- [GSD Core](https://opengsd.net/) - Context-engineering and spec-driven development framework that drives AI coding agents

## Coding Assistants

### Coding assistants usable from a terminal

### General Purpose

- [pi.dev](https://pi.dev/) - Minimal agent harness — adapt to your workflow, not vice versa
- [OpenCode](https://opencode.ai) - OpenCode is an open source agent that helps you write code in your terminal, IDE, or desktop.
- [NanoCoder](https://docs.nanocollective.org/nanocoder) - An open coding agent for your terminal, built by a community collective rather than a company. Bring your own model, keep your code on your machine, and owe nothing to anyone.
- [Qwen Code](https://qwen.ai/qwencode) - An open-source AI agent for the terminal, optimized for Qwen series models
- [DeepSeek Harness](https://deepseek.com/harness/en/) - Open-source agent harness developed by DeepSeek AI
- [jcode](https://jcode.sh/) - The most RAM efficient harness

### Code Review

- [open-code-review](https://open-codereview.ai) - Hybrid-architecture code review tool combining deterministic pipelines with an LLM agent for precise line-level comments and built-in multi-language rulesets

### Local-First

- [Codehamr](https://codehamr.com) - A minimal, local-first coding agent.
- [Atomic Agent](https://atomicagent.io) - A local-first AI agent that runs on your machine, with local or cloud models.

## SDLC Templates or Template Management

### Holding agentic configurations, skills, etc.

- [OpenViking](https://openviking.ai/) - Self-evolving Context Database for AI Agents. Unify Agent Memory, Knowledge RAG and Skills.
- [Mimir](https://mimir.featurefactory.io) - Mimir is a foundation for self-evolving methodologies for well-defined tasks
- [ArcKit](https://arckit.org/) - ArcKit is an enterprise Architecture governance harness that wraps your AI coding assistant
- [Hivemind](https://hivementality.ai/) - Self-hosted multi-agent AI team platform. 40+ built-in tools, 150+ agent templates.
- [OpenHands](https://docs.openhands.dev) - The self-hosted developer control center for coding agents and automations.
- [Fabric](https://danielmiessler.com/) - Open-source framework for augmenting humans with AI; a crowdsourced, modular set of AI prompt skills usable anywhere

## Orchestration

- [Symphony](https://github.com/openai/symphony) - Isolated autonomous implementation runs for teams
- [Conductor](https://github.com/microsoft/conductor) - Multi-agent workflows with GitHub Copilot SDK
- [OpenSquilla](https://github.com/opensquilla/opensquilla) - Token-efficient AI agent with higher intelligence density
- [Fabro](https://docs.fabro.sh/getting-started/introduction) - Version-controlled workflow graphs orchestrating AI agents, commands, and human gates
- [smolagents](https://github.com/huggingface/smolagents) - Barebones library for agents that think in code
- [OpenHive](https://github.com/aden-hive/hive) - Multi-agent harness for production AI workloads
- [bernstein](https://bernstein.run/) - Audit-grade multi-agent orchestration, HMAC-chained audit log
- [T3 Code](https://t3.codes/) - T3 Code is an agent harness control surface.
- [Scion](https://googlecloudplatform.github.io/scion/overview/) - Scion is a container-based orchestration platform for running multiple LLM deep agents concurren
- [AWS AI-DLC](https://awslabs.github.io/aidlc-workflows/) - AI-Driven Life Cycle (AI-DLC) adaptive workflow steering rules for AI coding agents
- [HumanLayer](https://docs.humanlayer.com/) - HumanLayer runs coding agents (Claude Code, Codex, OpenCode, Pi) on your machines and lets your team steer them from one place: tasks, sessions, plans, and reviews, synced between a desktop app, a web app, and a daemon on each host.

## AST and Code Parsers

- [CocoIndex Code](https://cocoindex.io/cocoindex-code/) - AST-based lightweight code search engine CLI; saves 70% tokens
- [CodeGraphContext](https://cgc.codes/) - MCP server indexing local code into a graph database
- [ast-grep](https://ast-grep.github.io/) - CLI tool for code structural search, lint and rewriting in Rust
- [ripwire](https://github.com/redhat-et/ripwire) - The ripgrep of AI context: a zero-dependency C++23 CLI + MCP server for coding agents.
- [Graphify](https://graphify.com/) - Turn code and docs into queryable AI knowledge graphs
- [Understand Anything](https://understand-anything.com/) - Turn any codebase, knowledge base, or docs into an interactive knowledge graph you can explore, search, and ask questions about.

## Sandboxes

- [NVIDIA OpenShell](https://docs.nvidia.com/openshell/about/overview) - Sandboxed agent runtime with hardware-enforced isolation and policy
- [forkd](https://github.com/deeplethe/forkd) - fork() for AI agent microVMs; spawn 100 children in ~100ms
- [OpenSandbox](https://open-sandbox.ai/) - Secure, fast, extensible sandbox runtime for AI agents
- [Daytona](https://www.daytona.io/) - Elastic infrastructure for running AI-generated code; sub-90ms creation
- [E2B](https://docs.e2b.dev) - E2B provides isolated sandboxes that let agents safely execute code, process data, and run tools.
- [Herdr](https://herdr.dev/) - Native app for running coding agents; your agent reshapes the UI, and herdr-core keeps sessions alive when the app is closed

## Working with Skills

### Skill Reference

- [Agent Skills](https://agentskills.io/home) - Standardized open format for extending AI agent capabilities via SKILL.md files

### Skill Syntax Validation

- [skill-validator](https://github.com/agent-ecosystem/skill-validator) - Validates skill content against the Agent Skill specification

### Skill Repositories

- [OSMT](https://github.com/wgu-opensource/osmt) - OSMT is the Open Skills Management Tool
- [SkillHub](https://github.com/iflytek/skillhub) - Self-hosted, open-source agent skill registry for enterprises.

### Skill Dependency Management

- [skills (Vercel Labs)](https://github.com/vercel-labs/skills) - Open agent skills CLI; supports OpenCode, Claude Code, Codex, Cursor and 68+ more
- [Microsoft APM (Agent Package Manager](https://microsoft.github.io/apm/) - An open-source, community-driven dependency manager for AI agents.

### Skill Security Scanners

- [DefenseClaw](https://github.com/cisco-ai-defense/defenseclaw) - Security governance for agentic AI; scan capabilities, inspect traffic, audit evidence
- [SkillSpector](https://github.com/nvidia/skillspector) - Security scanner for AI agent skills; detects vulnerabilities before installation

## Knowledge Base

### LLM Wikis

- [OpenKnowledge](https://openknowledge.ai/) - Beautiful, AI-native markdown IDE and LLM wiki
- [pi-llm-wiki](https://zosmaai.github.io/pi-llm-wiki/) - Self-maintaining, Obsidian-compatible knowledge base for pi

### Open Knowledge Format (OKF)

- [OKF Ecosystem](https://okf.md/tools/) - Open Knowledge Format ecosystem; tools, spec and docs for AI agent knowledge bases
- [okflint](https://github.com/mattdav/okflint) - Deterministic compliance linter for OKF bundles; profile-based rule enforcement
- [okf CLI](https://github.com/superops-team/okf) - CLI for git-based OKF knowledge bases; keeps bundles fresh via git hooks
- [OpenWiki](https://www.langchain.com/blog/introducing-openwiki-an-open-source-agent-for-repo-documentation) - OpenWiki is a CLI that writes and maintains agent documentation for your codebase in OKF compatible format.

### Technology Specifics

- [Context7](https://context7.com/) - Up-to-date documentation for LLMs and AI code editors
- [LangChain docs MCP + skills](https://docs.langchain.com/use-these-docs) - Use LangChain Docs Programmatically with MCP and installed skills
- [NVIDIA Agent Skills](https://github.com/nvidia/skills) - Official NVIDIA-verified skills catalog for CUDA-X, AI Blueprints and platform tools
- [DataHub Skills](https://datahub.com/blog/datahub-open-source-skills-registry/) - Agent skills for working with DataHub

## Token Control

- [rtk](https://www.rtk-ai.app/) - CLI proxy reduces LLM token consumption by 60-90% on common dev commands; single Rust binary
- [ponytail](https://ponytail.dev/) - Makes your AI agent think like the laziest senior dev in the room. The best code is the code you never wrote.
- [Headroom Desktop](https://extraheadroom.com/) - MacOS menu bar app cuts Claude Code and Codex token costs by ~50%
- [Caveman](https://docs.caveman.so/) - An efficiency stack for AI agents - cuts 65% of tokens by talking like caveman

## Observability

- [Langfuse](https://langfuse.com/integrations/native/opentelemetry) - Open source AI observability platform; LLM evals, metrics, tracing, prompt management
- [Phoenix](https://arize.com/docs/phoenix/) - AI observability and evaluation by Arize; traces, evals, datasets
- [Claude Code - OTEL](https://code.claude.com/docs/en/monitoring-usage) - How to enable and configure OpenTelemetry for Claude Code.
- [SigNoz - Coding agent observability](https://signoz.io/blog/claude-code-monitoring-with-opentelemetry/) - ClaudeCode observability with SigNoz and OpenTelemetry
- [agentops](https://github.com/AgentOps-AI/agentops) - Python SDK for AI agent monitoring, LLM cost tracking, benchmarking

## References

### Thoughtworks

- <https://martinfowler.com/articles/harness-engineering.html>
- <https://martinfowler.com/articles/exploring-gen-ai.html>
- <https://martinfowler.com/bliki/FutureOfSoftwareDevelopment.html>

### Whitepapers from Google

- <https://www.kaggle.com/whitepaper-the-new-SDLC-with-vibe-coding>
- <https://www.kaggle.com/whitepaper-agent-skills>
- <https://www.kaggle.com/whitepaper-vibe-coding-agent-security-and-evaluation>
- <https://www.kaggle.com/whitepaper-spec-driven-production-grade-development-in-the-age-of-vibe-coding>
- <https://www.kaggle.com/whitepaper-agent-tools-and-interoperability>
- <https://www.kaggle.com/whitepaper-context-engineering-sessions-and-memory>

### Various

- <https://github.com/ai-boost/awesome-harness-engineering>
- [Introducing the Open Knowledge Format (Google Cloud Blog)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- [How to Build Karpathy's LLM Wiki (Starmorph)](https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide)
- [LLM Wiki (Karpathy Gist)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
