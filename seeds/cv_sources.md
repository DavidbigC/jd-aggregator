# David's CV sources (devmaster-cv, audited)

<!-- file: README.md -->
# David Chen — Master CV

**GitHub:** [github.com/DavidbigC](https://github.com/DavidbigC)
**Website:** [davidbigc.github.io/Site](https://davidbigc.github.io/Site/)
**X:** [@davidbigcccc](https://x.com/davidbigcccc)
**Dune:** [dune.com/davidbigc](https://dune.com/davidbigc) · [dune.com/dragonborn](https://dune.com/dragonborn)
**Flipside:** [flipsidecrypto.xyz/DavidC/dashboards](https://flipsidecrypto.xyz/DavidC/dashboards)
**AI product repo:** [github.com/DavidbigC/mytradfiagent](https://github.com/DavidbigC/mytradfiagent)

*Last full audit: 2026-10-21 — every GitHub repo, authored PRs, local projects and the private trading workspace.*

---

## How the Work Was Done — read this before generating any CV

My work splits into two eras:

- **2021–2025: hands-on.** I wrote the code, SQL and analysis myself: blockchain data warehouses, Dune / Flipside research and dashboards, DeFi bots and calculators, the Limito CLAMM tool, the Lighter ↔ Bluefin arb with a Go hedge server, indexers, and the dashboards in my analyst roles.
- **2026: AI-directed.** From early 2026 I build by directing AI coding agents (Claude Code and OpenAI Codex). I come up with the ideas, set strategy, requirements and risk limits, approve designs, operate the systems with live capital and judge results; the agents write the code and run most of the measurements I ask for.

**Claim levels used in this repo:**

- **[Mine]** — my own ideas, decisions, domain judgment, operation, or hands-on work (all 2021–2025 work)
- **[Directed]** — I conceived and directed it; AI agents implemented it (2026 technical systems)
- **[AI detail]** — implementation internals recorded for reference; not personal expertise

**Phrasing rules:**

- 2021–2025 work: normal verbs ("built", "wrote", "designed").
- 2026 work: "conceived and directed", "led AI coding agents to build", "specified", "set the strategy / risk limits for", "operated with live capital", "commissioned analysis that showed…". Do not say "implemented / coded / engineered", and do not list 2026 implementation techniques as personal skills.
- Positioning: a hands-on on-chain / DeFi data builder (2021–2025) who became an AI-native builder and operator in 2026 — owning the strategy, the risk and the live operation.

---

## How to Use This Repo (for LLM-assisted CV generation)

This repo is a structured master CV datasource. To generate a tailored CV from a job description:

1. Read **How the Work Was Done** above and apply its claim levels
2. Read `skills.md` for the skills inventory (personal skills first, then technologies used)
3. Read `experience.md` for work history, outcomes, open-source PRs and education
4. Read the project files in `projects/` that are relevant to the role (see Role Index below)
5. Generate a tailored CV in Markdown, ranked: **critical match → nice to have → bonus**
6. Render to PDF using `resume.css`

**Ranking guidance:** For each JD requirement, classify every bullet from this repo as:
- `[CRITICAL]` — direct match to a must-have requirement
- `[NICE]` — relevant but not explicitly required
- `[BONUS]` — impressive differentiator, include if space allows

---

## Short Summary

- 5+ years across crypto, AI, data, analytics, trading systems, and product operations
- Formal training in experimental design, statistical inference, behavioural modelling, and research methods (MSc)
- [Mine] 2021–2025: hands-on on-chain data work — PostgreSQL warehouses for Sui and BNB Chain, Dune / Flipside / Allium research and dashboards, DeFi automation and calculators, a CLAMM limit-order product, cross-venue arb bots
- [Mine] Product and growth analytics in three crypto companies: FLOKI, Dragon Race (#1 dApp on Manta, 1M+ wallets in an opBNB launch week), CARV
- [Mine + Directed] Since Jan 2026, conceived, directed and operated a multi-app cross-venue trading platform as a one-person team with AI coding agents: 1,435 commits, four apps, live capital on five venues (trade.xyz, Omni/Variational, Lighter main, Lighter rh, Perpl)
- [Mine] Run a delta-neutral funding and spread arbitrage desk across Omni, Lighter and trade.xyz; attribution showed ~78% of profit came from funding, which reshaped how I choose and cut pairs
- [Mine] Set the strategy for and ran a market maker on Perpl (Monad) hedged on Lighter that ranked 7th of 71 accounts above $1M volume on spread capture (+3.50 bps), per an on-chain study I commissioned
- [Mine + Directed] Commissioned a ~15-study research library (RWA arbitrage universe, funding mechanisms, oracle risk, 135-symbol funding-harvest screen, oil rolls and backwardation, funding prediction) and traded from it
- [Mine] Run AI agents like an engineering team: brief → spec → plan → build with tests → review → operate; standing operating rules for the agents (ship features inert, never touch live parameters, live data is authoritative)

---

## Domain Capabilities

### On-Chain Research / Crypto Analytics — hands-on [Mine]
- Dune, Allium and Flipside analysis; Dune dashboards (Floki trading bot, Contango, SOFA, CARV node sale)
- Transaction decoding and warehousing for Sui and BNB Chain
- Whale behaviour, TVL, wallet flows, launchpad activity monitoring
- Submitted Dune Spellbook dbt model PRs (Floki bot trades on Solana / Base / Ethereum, Meteora fix) — not merged

### Product Analytics / Growth Analytics — hands-on [Mine]
- KPI dashboards (Tableau, Streamlit), DAU/MAU, campaign performance, protocol interactions
- User behaviour analysis for feature prioritisation, retention, growth, incentive design
- Forecasting, competitor intelligence, protocol scouting

### Trading Strategy & Operation [Mine]
- Funding-rate and spread arbitrage across crypto perps, RWAs and tokenised equities
- Market making on a perp DEX with cross-venue hedging; cross-deployment arbitrage
- Options selling with perp delta hedging; volatility-based advisory
- Risk ownership: limits, arming / derisking decisions, incident follow-through, strategy pivots

### Trading Systems — AI-built under my direction [Directed]
- Funding/spread desk executor and scanners; rwa-auto / omni-auto autonomous engines
- Perpl market maker with percentile tier ladders and cross-venue hedging
- Lighter main ↔ rh arbitrage console with per-coin liquidation guards
- Within-Omni RWA future-vs-swap pair trading; treasury and rebalancer; liquidation-risk stack
- Perpl chain indexer (316.9M actions), real-time L3 order book, Parquet + DuckDB research lake
- Rust signing daemons and a Rust shadow engine (709 µs p50 signal → signed order)

### AI / LLM Systems — AI-built under my direction [Directed]
- mytradfiagent: live AI financial research agent (33+ tools, multi-model debate, A-share data)
- llm-wiki (LLM-maintained knowledge base), ai keyboard (local autocomplete with LoRA fine-tuning), DCs-Transcriber (macOS voice input)

---

## Role Index

### Trading / Quant / Market Making → read these files
- `projects/funding-desk.md` — funding & spread arbitrage desk (core trading business)
- `projects/perpl-mm.md` — Perpl market maker
- `projects/lighter-arb.md` — Lighter main ↔ rh arbitrage
- `projects/research-library.md` — research behind the trading decisions
- `projects/within-omni.md`, `projects/variational-perps.md` — RWA engines
- `projects/har-dashboard.md`, `projects/vol-research.md`, `projects/lighter-hedge.md`, `projects/crypto-options-agg.md` — options and volatility
- `skills.md` → What I Personally Bring; Quant / Trading / Market

### Data Engineering / Blockchain Data → read these files
- `projects/sui-warehouse.md`, `projects/floki-bsc-warehouse.md` (hands-on)
- `projects/perpl-indexer.md` (directed)
- `projects/defi-tools-2024-2025.md` (hands-on)
- `skills.md` → Hands-On Technical Skills

### Product / Growth Analyst → read these files
- `experience.md` → FLOKI, Dragon Race, CARV
- `projects/floki-dashboards.md`

### AI / AI-Native Builder → read these files
- `projects/mytradfiagent.md`, `projects/ai-tools.md`
- `projects/variational-platform.md` (how a one-person team runs AI agents at scale)

### On-Chain Research → read these files
- `projects/sui-warehouse.md`, `projects/floki-bsc-warehouse.md`, `projects/defi-tools-2024-2025.md`
- `experience.md` → FLOKI; open-source PRs

---

## Projects Overview

| File | Project | Era | Type |
|------|---------|-----|------|
| [variational-platform.md](projects/variational-platform.md) | Variational Trading Platform — 2026 overview | 2026 directed | Multi-app trading platform |
| [funding-desk.md](projects/funding-desk.md) | Funding & Spread Arbitrage Desk | 2026 mine + directed | Core trading business |
| [research-library.md](projects/research-library.md) | Cross-Venue Research Library | 2026 mine + directed | ~15 trading studies |
| [perpl-mm.md](projects/perpl-mm.md) | Perpl Market Maker | 2026 mine + directed | Live market making |
| [perpl-indexer.md](projects/perpl-indexer.md) | Perpl On-Chain Indexer & L3 Book | 2026 directed | Blockchain data engineering |
| [lighter-arb.md](projects/lighter-arb.md) | Lighter main ↔ rh Arbitrage | 2026 mine + directed | Live cross-deployment arb |
| [within-omni.md](projects/within-omni.md) | Within-Omni RWA Pair Trading | 2026 directed | Relative value, RWAs |
| [treasury-and-risk.md](projects/treasury-and-risk.md) | Treasury, Rebalancer & Liquidation-Risk Stack | 2026 directed | Capital and risk |
| [rust-shadow-engine.md](projects/rust-shadow-engine.md) | Rust Shadow Engine | 2026 directed | Low-latency port |
| [variational-perps.md](projects/variational-perps.md) | rwa-auto / rwa-maker (trade.xyz ↔ Lighter) | 2026 directed | Autonomous XEMM |
| [har-dashboard.md](projects/har-dashboard.md) | HAR-RV Live Volatility Advisory | 2026 directed | Vol forecasting |
| [vol-research.md](projects/vol-research.md) | Hyperliquid Vol & Options Research | 2026 directed | Backtesting + ML |
| [lighter-hedge.md](projects/lighter-hedge.md) | lighter_hedge | 2026 directed | Rust strangle hedger |
| [crypto-options-agg.md](projects/crypto-options-agg.md) | crypto_options_agg | 2026 directed | Options analytics |
| [mytradfiagent.md](projects/mytradfiagent.md) | mytradfiagent | 2026 directed | Live AI research agent |
| [polymarket.md](projects/polymarket.md) | Polymarket 5-Min Monitor | 2026 directed | Prediction-market research |
| [ai-tools.md](projects/ai-tools.md) | llm-wiki, ai keyboard, DCs-Transcriber, dev tooling | 2026 directed | Personal AI tools |
| [floki-dashboards.md](projects/floki-dashboards.md) | FLOKI product dashboards | 2025 hands-on | Company BI |
| [sui-warehouse.md](projects/sui-warehouse.md) | SUI Transaction Data Warehouse | 2025 hands-on | Blockchain ETL |
| [floki-bsc-warehouse.md](projects/floki-bsc-warehouse.md) | FLOKI BSC Transaction Warehouse | 2025 hands-on | BNB Chain ingestion |
| [clamm-pendle-lfj.md](projects/clamm-pendle-lfj.md) | Limito / Pendle / LFJ | 2024–2025 hands-on | DeFi tooling |
| [defi-tools-2024-2025.md](projects/defi-tools-2024-2025.md) | Other 2024–2025 DeFi tools & research | 2024–2025 hands-on | Bots, indexers, analysis |

---

## Education

**University of Glasgow** — MSc Research Methods of Psychological Science, 2024
- Dissertation: the alleviating effect of cognitive load on cybersickness
- Experimental design, statistical inference, behavioural modelling, research methods

**Denison University** — BSc Psychology & Computer Science, 2021
- Interdisciplinary background useful for analytics, experimentation, AI products, and research

<!-- file: experience.md -->
# Experience

> Claim levels: all company roles and 2021–2025 independent work are [Mine], hands-on. 2026 independent work is AI-built under my direction — see `README.md` → How the Work Was Done.

## FLOKI | Data Analyst | Dec 2024 – Apr 2026

- Dashboard design for product and protocol monitoring
- Tracking for Trading Bot, Floki ID, and TokenFi Launchpad activity
- Owned the product database powering BI and dashboards
- Built predictive analysis and forecasting workflows for trading volume, DAU, and fee trends
- Researched feature viability for FLOKI trading products, including trading terminal functionality
- Analyzed business and product performance to support growth planning, campaign design, and product decision-making
- Helped manage delivery for the trading web terminal from early research through implementation support
- Coordinated development efforts through sprint-style planning and focused working sessions
- Aligned stakeholders and contributors around feature direction and execution priorities
- Competitor analysis: identified gaps and translated findings into recommendations for new features, campaigns, and system improvements
- Market and on-chain intelligence; whale / protocol / token metric monitoring
- Trading bot analytics support: monitoring, behaviour analysis, and product feedback loops
- Database schema collaboration with engineers; event-level data capture planning
- Supported evaluation of campaigns, events, feature changes, and broader product / infrastructure overhauls through data analysis
- Protocol scouting: surfaced early-stage projects for the TokenFi Launchpad pipeline
- Company Streamlit dashboards (102 commits, Apr 2025 → Mar 2026): Trading Bot, Web Bot (web trading terminal), Staking, Locker, UIS board, GenAI NFTs, Smart Contract Auditor; Docker + Helm deployment with semantic-release CI — see `projects/floki-dashboards.md`
- Dune dashboards for the trading bot; Dune Spellbook dbt PRs for Floki bot trades (not merged)
- Airdrop wallet reconciliation across Dune, the internal stake database and the distribution list

## Elfin Metaverse (Dragon Race) | Operation & Data Analyst | May 2024 – Mar 2025

- Product and growth analytics
- On-chain and off-chain user behaviour analysis
- Real-time Tableau dashboards (DAU/MAU, engagement, campaign performance); Streamlit dashboards
- DAU / MAU / campaign / engagement reporting
- Led the data strategy for the opBNB chain launch
- Token / point incentive modelling with Python agent-based simulations
- BattlePass launch support and ownership
- Retention improvement analysis

**Outcomes:**
- Doubled monthly active interactions, making the platform the #1 most-used dApp on Manta Network
- 90% reduction in manual reporting workload
- 1M+ unique active wallets in the first week of the opBNB launch, ranked #3 on opBNB
- 25% next-month retention improvement
- 10,000+ unique participants in BattlePass in under one month

## CARV (GEMI Foundation) | Community Lead & Business Development | May 2022 – Sep 2023

- Incentive structure redesign
- Engagement analytics; community KPI dashboarding
- A/B testing for reward systems
- Churn / sentiment / activity monitoring
- Regional campaign optimization
- CARV node sale dashboard

**Outcomes:**
- 100K+ community (Discord) messages per month, up over 300% year on year
- 200% increase in regional event participation

## Independent On-Chain Market Maker & Arbitrageur | 2021 – Present

Alongside the roles below until April 2026; full-time since May 2026. All venues are on-chain (Lighter, Omni/Variational, trade.xyz on Hyperliquid, Perpl), and the on-chain data work continues. 2021–2025 work is hands-on; from 2026 the strategy, risk and live operation are mine and the systems were built by AI coding agents under my direction. Never describe me as a "trader".

**2021–2025 (hands-on):**

- Blockchain warehousing scripts and transaction decoding (Sui, BNB Chain)
- DeFi automation: LFJ liquidity-book rebalancing, Dolomite, Berachain, Silo and Sui lending/funding bots
- Limito: CLAMM limit-order product (Node.js backend, Next.js frontend, Uniswap hook in Foundry)
- Lighter ↔ Bluefin arbitrage and market making with a Go hedge server; funding monitors across Lighter, EdgeX, Bluefin, Drift, Paradex and Binance
- Notebook-based yield / strategy analysis (Pendle PT, delta-neutral calculators), Dune research and dashboards
- Grid trading and risk-managed execution logic; delta-neutral stablecoin portfolio management

**2026 (AI-built under my direction; strategy, risk and operation mine):**

- Funding & spread arbitrage desk across Omni/Variational, Lighter and trade.xyz — the core trading business
- Perpl market maker hedged on Lighter (ranked 7th of 71 accounts above $1M volume on spread capture)
- Lighter main ↔ rh cross-deployment arbitrage; Within-Omni RWA pair trading; rwa-auto / omni-auto engines
- Treasury, rebalancer and liquidation-risk systems; Perpl chain indexer; Rust daemons and shadow engine
- Options and vol tooling: crypto_options_agg, HAR-RV advisory, Hyperliquid tick backtesting, lighter_hedge
- A ~15-study research library that drove the trading decisions

## AI and Developer Tools (2026 projects, not a job)

- AI-native way of working: I originate and direct, AI agents (Claude Code, Codex) implement
- mytradfiagent (live AI research product), llm-wiki, ai keyboard, DCs-Transcriber, CodexBar HUD, a published Claude Code QA skill

---

## Metrics / Outcomes Bank

Use selectively depending on role:

- 5+ years working across crypto, AI, data, analytics, and market systems
- Built and shipped multiple production systems independently
- Up to 30-turn autonomous reasoning workflows in AI research agent
- Doubled monthly active interactions at Dragon Race
- Reduced reporting workload by 90%
- 1M+ unique active wallets in one week on chain expansion
- Improved next-month retention by 25%
- 10,000+ unique participants in BattlePass launch in under one month
- 100K+ community messages per month at CARV after incentive redesign

Added in the 2026-10 audit (2026 systems; strategy and operation mine, implementation AI-built, most figures measured by the agents on my request):

- ranked 7th of 71 Perpl accounts above $1M volume on spread capture (+3.50 bps), measured from on-chain fills
- Perpl maker went from −3.1 bps to +1.71 bps of the Perpl leg within its first day after a quoting-model change
- taker-open entries: 6.55 net bps per dollar vs 1.76 for maker (3.7×), 52 of 53 positive
- funding & spread desk: ~78% of explained P&L came from funding over a 42-day attribution window (13,114 trades)
- Lighter main ↔ rh arb: 25.8% APR since start (to 2026-10-05), ~80% spread / ~20% funding
- funding regime-following +5–6.5%/yr vs −1.3%/yr static over 161 days, all 24 parameter sets positive out-of-sample
- indexed 8.65M fills + 316.9M actions with zero rate-limit errors; DuckDB/Parquet made wide scans 30–267× faster
- Rust shadow engine: 709 µs p50 signal → signed order vs 123 ms previously
- 1,435 commits and ~83k lines of tests in the trading workspace, run by one person directing AI agents

Use carefully depending on role / audience:

- 100% APR delta-neutral stablecoin strategy claim
- Live capital and live trading performance claims
- Incidents and losses (strong interview material on risk, not CV headlines)
- Ranking claims such as #1 most-used dApp on Manta Network

---

## Education

**University of Glasgow** — MSc Research Methods of Psychological Science, 2024
- Dissertation: the alleviating effect of cognitive load on cybersickness
- Experimental design, statistical inference, behavioural modelling, research methods

**Denison University** — BSc Psychology & Computer Science, 2021
- Psychology and computer science
- Interdisciplinary background useful for analytics, experimentation, AI products, and research

---

## Open-Source Contributions

- duneanalytics/spellbook: #7649 Floki bot trades on Solana, #7650 Floki bot spell, #7658 Floki trades on EVM (Base + Ethereum + Solana dbt models), #8012 Meteora v2 Solana base-trades fix — Feb–Apr 2025, all closed without merge
- DefiLlama/dimension-adapters: #6591 Elfa AI perp trading volume — Apr 2026, closed without merge
- CodexBar fork: floating HUD with token statistics (Mar 2026)
- Say "submitted PRs", not "contributed to" or "merged into"

---

## Notes

- Keep all content factual.
- Prefer concrete systems, tools, tables, workflows, and outcomes.
- Avoid marketing language unless needed in a downstream tailored CV.
- If a skill is not supported by direct work, do not add it.
- Forked repositories are not primary evidence unless authored contributions are verified.
- Where code was vendored or ported (e.g. Lighter's ECgFp5 / Poseidon2 crypto), say so.

<!-- file: skills.md -->
# Skills Inventory

> Apply the claim levels in `README.md` → "How the Work Was Done". Sections marked [Mine] are personal skills. Everything else is technology used in my projects: tools from 2021–2025 work were hands-on; items that appear only in 2026 projects were implemented by AI agents under my direction [Directed] and are not personal expertise.

## What I Personally Bring [Mine]

- Trading strategy and market judgment: cross-venue arbitrage, market making, funding carry and basis trades, options selling and hedging ideas, RWA (commodities, indices) perps, prediction markets — choosing what to trade, where, and when to stop
- Risk ownership: setting position and capital limits, deciding when to arm, derisk, pause or pivot, learning from real losses
- Live operations: running strategies with real capital across several venues, funding and moving capital, monitoring, noticing when numbers look wrong
- Directing AI coding agents (Claude Code, OpenAI Codex): turning an idea into a brief with constraints, steering brainstorm → spec → plan → build, reviewing results, setting standing operating rules, judging output against live evidence
- Product thinking: deciding what a console or tool must show, what ships and what stays inert
- Reading and questioning analysis: asking the next question, rejecting results that conflict with live evidence, turning findings into decisions
- Crypto / DeFi domain breadth: perp DEXs, lending, LPs and CLAMMs, yield tokens, airdrops and points programs, bridges and protocol trust models
- Product and growth analytics: KPI and dashboard design, user behaviour analysis, campaign and incentive design, competitor and on-chain research, stakeholder reporting
- Research training: experimental design and statistical inference (MSc)

## Hands-On Technical Skills (2021–2025 work) [Mine]

- Python for data and automation: pandas, NumPy, Jupyter + ipywidgets, Plotly, Matplotlib, requests / aiohttp / asyncio, SQLAlchemy, Web3.py, Telegram bots
- SQL: Dune (DuneSQL) and dbt-style Spellbook models, Flipside, Allium, PostgreSQL, MySQL, SQLite
- Blockchain data and interaction: JSON-RPC on Sui, BNB Chain, Avalanche, Berachain and Arbitrum; receipt and transfer-log decoding; token metadata enrichment; Uniswap V3 sqrtPriceX96 pricing; Dolomite and Odos integrations; Alchemy, BscScan, Dune Python client, DappRadar API
- Warehousing: PostgreSQL schemas, incremental loads, deduplication and upserts, async batch ingestion with retries
- TypeScript / Node.js: Sui SDK (@mysten/sui), AlphaLend SDK, a Silo vault bot with multi-RPC failover, node-cron, PM2; Next.js + Reown frontend (Limito)
- Go: Lighter order scripts, a TCP hedge server for the Lighter ↔ Bluefin arb, order-book monitors, Paradex WebSocket client
- Solidity with Foundry: Uniswap hook for limit orders (Limito), Dune Sim IDX listener
- Indexing: Envio HyperIndex indexers
- Web apps: Flask + Flask-Login + Gunicorn on Render with Neon Postgres; Flask reporting dashboards
- BI and reporting: Tableau, Streamlit, R / R Markdown with ggplot
- Quantitative DeFi analysis: delta-neutral money-market + perp sizing, LP ratio maths, yield / APY modelling, funding-rate comparison across venues

---

## Languages

- Python
- Rust
- TypeScript
- JavaScript
- SQL
- R
- Go
- Solidity
- Swift (AppKit) — 2026, directed

## Spoken Languages

- English
- Mandarin

## Backend / App

- FastAPI
- APScheduler (background job scheduling)
- Flask
- Express
- Node.js
- Axum
- Podman
- Redis
- containerized local development and testing environments
- Docker-compatible container workflows
- Docker Compose
- REST APIs
- JSON-RPC
- WebSockets
- SSE
- Socket.IO (server and client)
- JWT auth
- SIWE / wallet auth
- auth flows
- admin tooling
- cron / scheduled jobs
- database migrations
- Linux service operations
- Nginx
- Caddy
- gevent (cooperative multitasking, monkey-patching, async workers)
- Unix domain socket IPC
- Python–Rust sidecar process architecture
- hot-reload config systems
- self-healing WebSocket feed infrastructure
- asyncio / FastAPI services, httpx, websockets
- curl_cffi browser-impersonation clients, per-credential session pooling
- HMAC- and Ed25519-signed exchange APIs, JWT cookie auth with token renewal
- Tokio (Rust async), ratatui TUIs; Textual (Python TUI)

## Frontend / UI

- Next.js
- React
- TypeScript frontend apps
- Wagmi
- React Query
- Vite
- HTML / CSS
- Tailwind CSS
- chart-based interfaces
- TradingView Lightweight Charts
- uPlot (high-frequency live charts), React 19, mobile-first operator dashboards
- PyQt6 and AppKit desktop UIs

## Databases / Storage

- PostgreSQL
- SQLite
- MySQL
- MongoDB
- table schema design
- column type decisions
- upserts
- local analytical storage
- event-level storage
- transaction-level storage
- DuckDB over day-partitioned Parquet lakes
- SQLite at scale (18 GB ingest journal, WAL, covering indexes, VACUUM INTO backups)

## Data / Analytics / ETL

- SQLAlchemy
- pandas
- DuckDB (queryable analytical views over Parquet datasets)
- PyArrow / Parquet
- Optuna (Bayesian optimization, TPE and NSGA-II samplers)
- Numba (JIT-compiled numerical simulation)
- dbt exposure through Dune Spellbook model PRs (not merged)
- Envio HyperSync bulk chain-log backfills
- block bootstrap, walk-forward and out-of-sample validation
- Kafka
- forecasting
- trend analysis
- business performance analysis
- experiment analysis
- ETL pipelines
- API-driven ingestion
- async batching
- retry logic
- rate limiting
- deduplication
- backfills
- incremental updates
- schema design
- dashboard data preparation
- product KPI tracking
- user behaviour analysis
- stakeholder-facing analysis

## AI / LLM

- LLM agent architecture
- prompt engineering
- multi-turn reasoning flows
- tool calling systems
- OpenAI-compatible API integration
- hypothesis-driven AI workflows
- AI-assisted research tooling
- multi-model debate (MiniMax, Qwen, judge), Grok, Groq, OpenRouter
- ElevenLabs realtime STT, Whisper STT; Ollama, MLX LoRA fine-tuning
- Claude Code and OpenAI Codex agentic workflows (specs, plans, subagent TDD, memory, skills) [Mine — this is how I work]

## Blockchain / On-Chain Data

- Dune
- Dune Spellbook
- Allium
- Flipside
- Alchemy
- BscScan
- Web3.py
- Sui RPC
- transaction receipt decoding
- token transfer decoding
- event / log decoding
- token metadata enrichment
- wallet flow analysis
- protocol monitoring
- GMX
- Hyperliquid (SDK, order placement, EIP-712 signing, perpetuals API)
- Lighter (main and rh deployments, sub-accounts, positionFunding / fundings APIs, CCTP deposits, fast withdrawals)
- trade.xyz / Hyperliquid HIP-3 (RWA perpetuals)
- Derive
- Paradex
- Polymarket (Gamma REST API, CLOB WebSocket)
- EIP-712 structured data signing
- Schnorr signing over ECgFp5 / Poseidon2 for Lighter — crypto modules vendored from the open-source lighter-rust crate and integrated into my own Rust daemons (2026, directed); the curve arithmetic is not my work
- Omni / Variational (RFQ execution, settlement pools, relayer deposits, risk-limit and swap-financing APIs)
- Perpl on Monad (Ed25519 API auth, contract events, Multicall3 book snapshots, eth_subscribe / eth_getLogs)
- Ondo Perps, RISEx, PopDEX (Morph Tachyon), Kyan, Rysk
- Bluefin (Sui perps), AlphaLend, EdgeX, Paradex, Drift — 2025, hands-on
- Berachain, Dolomite, Odos, Silo (Arbitrum) — 2024–2025, hands-on

## Infrastructure / Reliability / Observability

- AWS Lightsail (VPS provisioning, instance setup, port/firewall configuration)
- AWS EC2 (broader exposure across projects)
- Grafana
- Loki
- Prometheus
- Promtail
- Linux (Ubuntu)
- Redis
- Kafka
- Podman
- Docker Compose
- Nginx
- Caddy
- SSH key-based authentication
- SCP file transfers to remote servers
- remote command execution via SSH heredocs
- Ubuntu server provisioning from scratch
- Python virtualenv setup on remote servers
- systemd service unit authoring
- systemd lifecycle management
- `journalctl` log tailing and filtering
- Gunicorn WSGI server configuration
- Nginx WebSocket reverse proxy config
- server-side `.env` credential management and rotation workflows
- production monitoring
- observability dashboards
- log aggregation
- metrics collection
- reverse proxy setup
- HTTPS / TLS production serving
- public production deployment
- incident investigation
- root cause tracing across logs, databases, and code
- runbook-oriented operational thinking
- SLI / SLO / SLA exposure
- systemd drop-ins and timers, nginx TLS + basic auth for several apps on one box
- git-push deploys to bare repos, deploy backups of server-owned state
- py-spy / perf profiling of live processes; Lightsail burst-credit capacity planning
- Docker + Helm chart + semantic-release CI (company dashboards)
- Telegram bots for signals, liquidation alarms and regime alerts

## Quant / Trading / Market

- statistical arbitrage
- delta-neutral strategies
- funding rate monitoring
- perpetuals
- options analytics
- options Greeks
- volatility analysis
- liquidity modelling
- market microstructure analysis
- trading bots
- grid trading
- risk management
- derivatives product research
- trading parameter analysis
- concentrated liquidity strategies
- market making workflows
- autonomous bilateral market making (XEMM pattern)
- cross-venue order execution (maker on one venue, taker hedge on another)
- short-strangle backtesting with delta-hedging via perpetuals
- multi-objective Bayesian optimization for strategy search (Optuna NSGA-II, Pareto frontier)
- walk-forward validation and holdout backtesting
- fake-breakout / confirmation-gate hedge filtering
- regime detection (efficiency ratio, chop score, trend strength, realized vol)
- realized volatility computation and persistence filtering for entry gating
- microstructure feature engineering (signed trade flow, open pressure, block concentration)
- options APR surface analysis across strikes and DTEs
- HAR-RV model family (HAR-RV, HAR-RV-J, HARQ, HAR-IV): implementation, OLS fitting, crypto-specific calibration
- bipower variation and jump variation decomposition
- variance risk premium (VRP) analysis: IV–RV spread as primary edge signal
- Hidden Markov Models (HMM) for vol regime detection: Gaussian/Student-t HMM, Baum-Welch, Viterbi (researched)
- Markov-switching HAR and regime-switching vol models
- quantile regression for tail breach probability (short-strangle risk)
- realized semivariance (upside/downside vol decomposition)
- XGBoost / gradient-boosted trees for feature-rich vol forecasting
- pure Python OLS implementation: Gauss elimination, partial pivoting, ridge regularization, t-stats, R²
- Random Forest for strategy performance prediction and iterative candidate proposal
- bootstrap / Monte Carlo resampling for strategy risk metric estimation
- regime-adaptive policy switching (best hedge policy selected per regime label)
- GPU-accelerated ML environment setup (XGBoost CUDA, PyTorch CUDA) for large-scale optimization
- adverse-move cancellation logic
- reprice throttle / tick-gate logic
- funding skew adaptive threshold adjustment
- depth-ratio quoting (quoting as fraction of available hedge depth)
- order book depth bucket analysis (1/2/5/10/20 bps cumulative size)
- multi-level risk supervision (global notional cap, per-symbol inventory cap, bilateral net-inventory)
- session-scoped position baseline tracking
- post-fill adverse selection tracking (1s/5s/30s drift)
- funding attribution (proportional split across open fills)
- exponential-weighted statistical signal computation (EW mean, Winsor clipping, halflife)
- Pearson correlation for regime scoring
- live capital deployment and operational trading system management
- funding-carry screening (edge × sign persistence ÷ cost), pair kill lists, clock gating
- Avellaneda–Stoikov-style quoting, exponentially-weighted percentile bands, percentile tier ladders
- spread vs direction P&L decomposition, markouts, slip attribution with edge-matched controls
- regime detection (displacement vs imbalance vs CUSUM comparison), lead-lag estimation
- funding clamps, funding regime following, basis + carry blending
- liquidation-distance guards and chunked de-risking
- RWA perp vs swap relative value; cross-deployment arbitrage

## Visualization / Reporting

- Tableau
- Plotly
- Streamlit
- Chart.js
- Recharts
- Jupyter notebooks
- interactive HTML charts
- uPlot, R Markdown / ggplot, Matplotlib

## Testing / QA

- Playwright
- end-to-end testing
- integration testing
- manual QA
- large pytest suites, mutation testing, fuzzing, golden-vector parity tests (2026, AI-built)

---

## Databases / Warehouses / Pipelines Worked On

- PostgreSQL databases for blockchain transaction warehousing
- PostgreSQL schemas for product / protocol analytics
- SQLite databases for trade logs, balances, P&L, positions, and local app state
- product databases for conversation history, user auth, and app data
- local database-backed tools for portfolio tracking and monitoring

Typical work done:
- schema design, primary keys and deduplication logic, column type selection
- event-level, transaction-level, and metadata tables
- incremental updates, backfills, API polling, WebSocket ingestion
- async batch processing, retry and failure handling
- downstream dashboard / analytics outputs
- local development and test environment setup with containers

---

## Repo-Evidenced Technical Patterns

> **[AI detail]** for 2026 projects: patterns found in the code the agents built under my direction. Use them to describe what systems do, never as personal skills. 2021–2025 patterns (warehouses, decoding, notebooks, Dune workflows) are hands-on.

- PostgreSQL schema design for blockchain transaction warehouses
- SQLite-backed local analytics and execution tools (WAL mode, WITHOUT ROWID + clustered PKs for time-series)
- Podman-based containerized local development environments
- Docker Compose orchestration for multi-service apps
- async ingestion with batching, retry logic, and rate limiting
- JSON-RPC and REST-based blockchain data retrieval
- transaction receipt decoding and transfer log parsing
- token metadata enrichment
- Dune / Flipside / Alchemy-backed data workflows
- notebook-based quantitative research
- Plotly interactive chart generation
- WebSocket-based market data systems with self-healing and rate-limit adaptation
- Socket.IO real-time push from server to browser (trading events, price ticks, session state)
- SSE-based streaming APIs
- Rust API services with Axum
- JWT-based auth flows and SIWE wallet authentication
- PostgreSQL migrations for app services
- Playwright end-to-end testing and Rust integration tests
- Caddy-based reverse proxy and HTTPS serving
- Prometheus / Loki / Promtail / Grafana observability stack
- tracing-based JSON application logging
- backend-as-source-of-truth calculation architecture
- Python–Rust Unix domain socket IPC (newline-delimited JSON protocol, sub-50µs latency)
- Rust Schnorr signing daemon using vendored ECgFp5 + Poseidon2 primitives
- Rust EIP-712 signing daemon with alloy-signer secp256k1 ECDSA and local atomic nonce management
- local nonce cache architecture for blockchain order placement (eliminates per-order HTTP roundtrip)
- gevent cooperative multitasking for concurrent WebSocket + HTTP serving in single-process Flask
- three-tier orchestration hierarchy (Orchestrator → Supervisor → Session) for autonomous trading systems
- hot-reload YAML config with signal overlay and pinning (live parameter changes without process restart)
- multi-level risk supervision: global notional cap, per-symbol inventory cap, bilateral net-inventory monitor
- XEMM cross-exchange market-making: adverse-move cancel, reprice throttle, depth-ratio quoting, funding skew
- consumer-based WebSocket subscription leases (union semantics, add/remove without global resubscribe)
- deferred listener dispatch (release state lock before calling listeners — prevents WS thread blocking)
- exponential-weighted statistical thresholds with Winsor clipping, multiple quantile outputs, halflife fitting
- post-fill adverse selection measurement (1s/5s/30s horizon drift per fill)
- proportional funding attribution across open fills with idempotent upsert
- shadow mode adapter pattern for live production migration (legacy → new data source with disagreement logging)
- real SQLite integration tests with tempfile isolation (not mocked) plus controllable fake clock
- comprehensive fake object injection via dataclass Deps pattern for fast unit tests
- Numba JIT-compiled backtest engines for fast parameter sweep simulation
- multi-objective Bayesian optimization with Optuna NSGA-II (Pareto frontier across Sharpe, return, Calmar)
- walk-forward backtesting with holdout validation
- DuckDB analytical views over multi-gigabyte Parquet (Hyperliquid tick archive, ~18.7M trades)
- fake-breakout confirmation gate pattern for delta-hedge entry filtering (reduces whipsaw crossings 100×)
- regime detection feature computation (efficiency ratio, chop score, trend strength) for adaptive strategy switching
- microstructure feature engineering from tick data (signed trade flow, open pressure, block concentration)
- Random Forest for strategy performance prediction with OOB validation and permutation importance
- bootstrap / Monte Carlo resampling for strategy risk percentile estimation (p5/p95 metrics)
- 4-state regime classification with quantile-fitted thresholds and adaptive hedge policy switching per regime
- GPU-accelerated ML environment (XGBoost CUDA + PyTorch CUDA + Numba) for large-scale optimization runs
- HAR-RV vol forecasting: bipower variation, jump decomposition, VRP analysis, IV–RV spread as edge signal
- XGBoost on rich vol feature sets (lagged RV, DVol, skew, funding, jump indicators) as Tier 3 layer above HAR
- quantile regression and realized semivariance for short-strangle tail breach probability
- Markov-switching HAR and regime-switching vol models with DVol term structure signals

*Forked repos should not be treated as primary evidence unless actual authored work is verified.*
- event-sourced chain indexing (events over calldata), dual-tier proposed / safe chain data
- SQLite ingest journal + Parquet / DuckDB analysis lake, chosen by benchmark
- "ship inert": features deploy disarmed and recording; the operator arms them [Mine — a rule I set]
- pure decision functions that always return a reason, wrapped by thin I/O services
- merged multi-venue order books with venue tags and cap-aware walks
- two-read reconciliation before declaring a position flat; no automatic retry on money-moving calls
- golden-vector parity tests between Python and Rust implementations

<!-- file: projects/ai-tools.md -->
# Personal AI Tools and Developer Tooling (2026)

**My role [Mine]:** my ideas, product decisions and daily use; all AI-built [Directed].

---

## llm-wiki — LLM-maintained knowledge base

**Dates:** 2026-04-24 → 26 (45 commits) · **Stack:** Python, FastAPI, SSE, OpenRouter → MiniMax fallback, fswatch / launchd, Obsidian

- ingest pipeline turns dropped files and repos into linked Obsidian wiki pages; lint and query tools; skips unchanged files
- web app with real-time streaming ingest, chat, graph view, sources browser, GitHub repo import, LLM folder "cleanse"
- 4,535 pages generated from my own repos and notes

## DCs-Transcriber — macOS voice input (public repo, used daily)

**Dates:** 2026-04-14 → 18 · **Stack:** Swift, AppKit, AVAudioEngine, ElevenLabs Scribe v2 realtime, OpenAI-compatible LLM refinement

- hold-a-key dictation from the menu bar: global hotkey, live waveform in a floating panel, realtime transcription, optional LLM clean-up, text injected into the focused app, clipboard fallback, history

## ai keyboard — local AI autocomplete with personal fine-tuning

**Dates:** 2026-02-26 → 27 · **Stack:** Python, pynput, PyQt6, Ollama (qwen2.5:0.5b), MLX LoRA, SQLite

- system-wide suggestion popup with Tab-to-accept; context history feeds an MLX LoRA fine-tuning loop that retrains and exports a personal model to Ollama

## Developer tooling

- **CodexBar fork — floating HUD** with token statistics for Claude Code / Codex usage (Swift)
- **rust-js-qa-skill** — a Claude Code skill for Rust + TypeScript/JavaScript QA
- **mdviewer** — small Node markdown viewer

## Tags

AI-native builder · local LLMs · speech-to-text · knowledge management · macOS apps

<!-- file: projects/clamm-pendle-lfj.md -->
# DeFi Tooling: Limito (CLAMM) / Pendle / LFJ

**My role [Mine]:** all built hands-on (2024–2025) — strategies, code and conclusions are mine.

---

## Limito — CLAMM Limit-Order Tool

**Type:** Concentrated liquidity trading / monitoring product
**Stack:** TypeScript / Node.js, Next.js, Reown (wallet connect), PostgreSQL, Podman-based local containers, Foundry, Uniswap Hook smart contracts

- Limit-maker tooling and position monitoring
- Backend and frontend app flow; database-backed state tracking
- Smart contract-connected workflow; containerized local development with Podman

---

## Pendle PT Trading Tool / Yield Market Analysis

**Type:** Notebook-based DeFi market analysis
**Stack:** Python, pandas, Plotly, Jupyter notebooks, Pendle API

- Market data retrieval; OHLCV and APY history analysis
- PT / YT derived price calculations; EMA-based analysis
- Interactive chart generation; HTML output for review
- APY prediction for PT positions (e.g. sUSDe PT) with yield-curve analysis

---

## LFJ / Trader Joe Liquidity Book Automation

**Type:** DeFi automation and liquidity rebalancing system (AVAX-BTC.b market making and yield farming on LFJ / Trader Joe)
**Stack:** Python, Web3.py, SQLite, Avalanche RPC

- Liquidity add / remove flows; automatic rebalancing
- Active bin monitoring; local position and transaction history tracking
- Direct contract interaction

---

## Tags

DeFi automation · concentrated liquidity · market making · yield analysis · smart contract interaction · notebook research

<!-- file: projects/crypto-options-agg.md -->
# crypto_options_agg

**My role [Mine]:** my idea for a multi-venue options workspace for my own options selling; I chose the venues, views and scanners and published it as a public self-hosted site (repo is private). AI agents wrote the code and ran the Node → Rust migration (Mar 2026) [Directed].

**Type:** Crypto options analytics platform
**Stack:** Node.js, Express, Next.js, TypeScript, JavaScript, Rust, Axum, React, PostgreSQL, SQLite, WebSockets, SSE, REST APIs, Playwright, Docker Compose, Caddy, Prometheus, Loki, Grafana, Wagmi

---

## Built / Implemented

- Live options chain interface; exchange-specific and combined exchange views
- Options analytics for BTC, ETH, and SOL across Bybit, OKX, Deribit, Derive
- Arbitrage and box spread views
- Gamma scanner (straddles + strangles ranked by BE/day)
- Vega scanner (straddles + strangles ranked by BE IV move)
- Multi-leg strategy optimizer
- Position builder and portfolio page
- Analysis page: IV smile + SVI fit, ATM IV term structure, 25Δ skew & butterfly
- Wallet-connected account and portfolio flows
- Auth-protected hub backend with JWT-based sessions
- Live SSE / streaming product flows
- Brand and deployment setup for a public production site

## Data / Infrastructure

- Bybit, OKX, Deribit, and Derive integrations
- Streaming and polling market-data services; backend-side calculation model for shared outputs
- Exchange quote comparison logic; exchange badges with best bid/ask per leg
- Rust backend services for market APIs, streaming, and trading-connected workflows
- PostgreSQL-backed hub service with migrations and encrypted credential storage
- Playwright-based end-to-end testing plus repo-based QA workflows
- Docker Compose / Podman-based local and production orchestration
- Caddy reverse proxy for HTTPS public serving
- Prometheus, Loki, Promtail, and Grafana for metrics, logs, and operational visibility

## Additions (2026-10 audit)

- 250 commits, Mar 6 → Apr 1 2026; Rust (Axum) backend ~25k lines, Next.js frontend ~12.8k, hub backend ~3.3k
- original Node/Express backend migrated to Rust with a parity-verification script
- more venues: Binance options, Kyan, Lighter trading integration
- Polymarket analysis service (implied move distribution by expiry); SVI vol-surface fitting; public vs private run modes

## Tags

derivatives tooling · DEX options familiarity · quant interface · full-stack analytics app · production deployment · product engineering

<!-- file: projects/defi-tools-2024-2025.md -->
# Other 2024–2025 DeFi Tools and Research

**My role [Mine]:** built hands-on — the strategies, research questions, code and conclusions are mine.

---

## Trading and automation

- **Lighter ↔ Bluefin arbitrage / market making** (Jun–Aug 2025): Python Bluefin fill monitor + Go Lighter hedge server over TCP (sub-100 ms), long/short Bluefin market makers, Go order-book monitor, EdgeX analysers
- **Multi-venue funding monitor** (Aug 2025): Lighter / EdgeX / Bluefin / Drift / Paradex / Binance funding APR comparison server with a Telegram bot and API latency tests
- **Lighter ↔ Paradex** (Sep–Nov 2025): Go market lists and Paradex order-book WebSocket for an arb monitor
- **Bluefin + AlphaLend rate bot** (Jun 2025): TypeScript Sui bot logging funding and lending rates every 5 minutes, Telegram alerts, PM2
- **Berachain iBGT / Dolomite monitor** (Jun–Jul 2025): contract reads, Uniswap V3 pricing, LTV and liquidation price, borrow rates, funding comparison, Telegram bot commands
- **Silo vault withdrawal bot** (2025): Node bot polling vault liquidity every 3 s with 6-RPC failover, gas cap, dry-run
- **Price predictor** (2025): Bybit 1-minute data into SQLite with prediction and analysis scripts

## Data and indexing

- **Envio indexers** (2025): HyperIndex configs for BSC IDO contract events
- **Dune Sim IDX — Aave V3 listener** (Jul 2025): Solidity listener on Borrow events with Foundry tests and a Cloudflare Workers + Drizzle API ([repo](https://github.com/DavidbigC/Dune-sim))
- **Portfolio tracker** (Jan 2025): Flask + SQLAlchemy + Flask-Login multi-user position and P&L tracker, SQLite → PostgreSQL (Neon), deployed on Render

## Calculators and analysis

- **DeFi Toolbox** (Dec 2024): money-market + perp delta-neutral sizing and LP split calculators ([repo](https://github.com/DavidbigC/Defi-toolbox))
- **Dolomite tools** (Jul–Oct 2024): ARB STIP delta-neutral farming calculator; collateral auto-trading notebook using Odos swap data
- **BAYC liquidity investigation** (Sep 2024): R Markdown with Dune NFT trade SQL, Blur lending rates, floor and order-book charts ([repo](https://github.com/DavidbigC/BAYC-trading-analysis))
- **Best EVM for GameFi** (Aug 2024): DappRadar API comparison of the top 100 gaming dapps on Base, Arbitrum and Blast ([repo](https://github.com/DavidbigC/Best-Gaming-EVM))
- **Jupiter top traders** (Jul 2024): Dune client analysis ([repo](https://github.com/DavidbigC/Jupiter-best-trader))
- **Dune dashboards and writeups** (2024–2025): Contango $TANGO analysis and trading dashboard, SOFA protocol, CARV node sale, sUSDe PT APY prediction, Dolomite farming writeup

## Tags

DeFi automation · on-chain analytics · Dune · funding monitoring · Go · TypeScript · Python

<!-- file: projects/floki-bsc-warehouse.md -->
# FLOKI BSC Transaction Warehouse

**My role [Mine]:** built hands-on (Feb 2025) — design, code and schema are mine.

**Type:** BNB Chain transaction warehouse and enrichment pipeline
**Stack:** Python, PostgreSQL, SQLAlchemy, pandas, asyncio, aiohttp, Web3.py, Flipside, Dune, Alchemy

---

## Built / Implemented

- Candidate transaction collection from Flipside and Dune
- Transaction receipt retrieval; transfer decoding; buy/sell classification
- Token metadata enrichment; async missing-transaction processing; database sync

## Schema Elements

- Transaction facts; token contract metadata (name, symbol, decimals)
- Denominated amounts; user address; blockchain marker

## Tags

blockchain ETL · product analytics data source · on-chain decoding · BNB Chain · async ingestion · Web3.py

<!-- file: projects/floki-dashboards.md -->
# FLOKI Product Dashboards (company work)

**My role [Mine]:** my work in the FLOKI data-analyst role — I decided what each product dashboard tracks, wrote the dashboards and SQL hands-on through 2025, and shipped them to the team. The Jan–Mar 2026 pages were built in the AI-assisted era.

**Type:** company BI application (private company repository)
**Dates:** 2025-04 → 2026-03 (102 commits by me)
**Stack:** Python, Streamlit (multipage), SQL over the product database (read-only), Docker, Helm, semantic-release CI

---

- product dashboards: Trading Bot (Telegram), Web Bot (web trading terminal), Staking (price fetcher, APR, user analytics, rewards by pool in USD), Locker, UIS board, GenAI NFTs, Smart Contract Auditor
- bot response-time metrics, CSV exports, user-exclusion and app filters in SQL, release versions v0.2 → v0.10.1
- related: Dune dashboards for the trading bot; Dune Spellbook PRs for bot trades; airdrop wallet reconciliation

## Tags

product analytics · BI · Streamlit · company production work

<!-- file: projects/funding-desk.md -->
# Funding & Spread Arbitrage Desk

**My role [Mine]:** my core trading business. I pick which pairs to hold and in which direction, size them, run the manual and automated executors, move capital between venues, and decide what to cut. The attribution analysis below was run by AI agents on my P&L data; the decisions are mine. The tooling is AI-built to my spec [Directed].

**Type:** delta-neutral cross-venue funding-carry and spread arbitrage across crypto perps, RWAs and tokenised equities
**Venues:** Omni / Variational ↔ Lighter ↔ trade.xyz
**Dates:** 2026-01 → ongoing

---

## What the attribution showed (42-day window, May–Jul 2026)

- ~78% of explained P&L came from funding (Lighter 68%, Omni 10%) and ~21% from spread capture; the attribution reconciled to equity change within ~3.5%
- 13,114 trades; spread capture averaged +3.07 bps — the spread is the toll paid to enter funding positions, not the product
- best pairs were high-carry crypto names (NEAR, ZEC, LIT, WLD, FIL, ZRO, ADA) plus CL/WTI; a gold pair was churning large notional for ~0 bps and paying funding both ways → kill list
- spread P&L positive 10–20 UTC, negative 0–5 UTC and on Mondays / Saturdays → clock gating
- basis does not drift into funding settlements — no free "settlement sniping"

## Desk tooling [Directed]

- /trading executor: up to 4 concurrent sessions, parallel legs, hedge venue switchable between Lighter and trade.xyz, WS-verified execution prices, capacity warning before Omni rejects on OI/skew caps
- /arbitrage scanner: funding and spread across 80+ pairs with an RWA tier, settled-funding history, live prices, Telegram alerts
- /historical-data: settled-funding stats via boundary sampling, index-vs-mark premium chart, market-hours filter
- funding ledger: every funding payment backfilled (1,803 Omni + 12,795 Lighter rows), daily sync, daily funding chart; cashflow ledger so deposits never read as profit
- unified three-venue portfolio with net delta per symbol

## Research behind it

- 135-symbol, 6-month spread-vs-funding screen: tier-1 harvest picks paid >20% APR funding difference with ≥80% sign persistence and recovered round-trip cost in <5 days
- carry screen = mean |funding diff| ÷ (1 + entry cost) × sign persistence
- CL ↔ WTI funding regime: +17.5%/yr carry, Lighter ~9 bps structurally rich

## Tags

funding-rate arbitrage · delta-neutral carry · P&L attribution · portfolio management · live capital

<!-- file: projects/har-dashboard.md -->
# HAR-RV Live Volatility Advisory System

**My role [Mine]:** I wanted a live volatility advisor for my options selling; the HAR-RV modelling, regime logic and dashboard were researched and implemented by AI agents (Apr–May 2026) [Directed].

**Type:** Live vol forecasting and options trading advisory platform
**Stack:** Python, FastAPI, APScheduler, DuckDB, TradingView Lightweight Charts (SPA frontend), Deribit API, Hyperliquid API, Binance API

---

## System Overview

- Continuously ingests multi-source market data and runs HAR-RV forecasting every 5 minutes
- Computes Variance Risk Premium (VRP = IV − forecast RV), evaluates regime conditions, and surfaces straddle/strangle trade recommendations via REST API to a live dashboard
- Running in production with APScheduler background jobs for candle ingestion, DVOL, full Deribit options chain snapshots, and derivatives metrics

## HAR-RV Forecasting

- Standard 1-step HAR-RV: `RV_{t+1} = β₀ + β_D × RV_t + β_W × avg(RV_{t-7}) + β_M × avg(RV_{t-30})`
- Monthly component dropped (t-stat ≈ 0 on crypto — crypto-specific calibration decision)
- Horizon-specific OLS fits for h ∈ {7, 14, 30} days; target = mean(RV over window), capturing mean-reversion at longer horizons
- Asset-specific fits on 733 days of BTC/ETH data:
  - BTC: β_D=0.35, β_W=0.44, β_M=0.0
  - ETH: β_D=0.40, β_W=0.29, β_M=0.0
- Pure Python linear algebra: Gauss elimination with partial pivoting + ridge regularization; returns β̂, standard errors, t-stats, R², RMSE
- HAR coefficient research: grid search over β and window-size spaces (~1,800 combinations), ranked by walk-forward Sharpe
- HAR-X funding extension: HAR augmented with Binance/Hyperliquid funding rate and premium features (researched, not yet live)

## Regime Detection

- 4-factor scoring: persistence score (7d mean RV / prior-month RV), spike score (today RV / 7d mean), IV slope (7d/30d tenor ratio), β_w structural break ratio (45d vs 90d window)
- 4 states: NORMAL, SPIKE, REGIME, AMBIGUOUS — each gates/modifies signals differently
- REGIME state: requires 1.5× VRP threshold for SHORT (premium compresses in high-vol regimes)
- SPIKE state: suppresses LONG signals (transient burst expected to mean-revert)
- HMM research documented for future deployment: 3–4 state Gaussian/Student-t HMM, Baum-Welch + Viterbi; `hmmlearn` / `pomegranate` candidates; not yet deployed

## Feature Set

**Realized vol inputs:**
- 1-min returns from Hyperliquid ETH/BTC perps, Deribit perps, Binance spot
- Days with <60 min data excluded (quality gate)
- Daily, 7-day rolling avg, 30-day rolling avg HAR components

**Implied vol inputs:**
- DVOL (Deribit 30-day vol index), ATM IV by tenor (7d/14d/30d expiries from live options chain)
- IV slope (7d/30d ratio), IV z-scores (7d and 30d rolling vs 90-day baseline)

**Derivatives features:**
- Binance USDM: funding rate, open interest, basis, taker buy/sell ratio, global long/short account ratio
- Hyperliquid: funding rate, premium, mark/oracle/mid prices, daily notional volume, impact bid/ask

## Backtesting

- Walk-forward: weekly entry points from (start + 30d) to (now − horizon)
- Separate LONG vs SHORT win rate and avg PnL per horizon
- Advisor auto-selects best horizon {7/14/30} by highest avg PnL on signalled side (≥3 trades minimum)
- 30-minute in-process cache with explicit refresh endpoint

## Frontend

- Single-page app with TradingView Lightweight Charts; auto-refresh every 60s
- Views: advisor ticket (recommendation, strikes, VRP, win rate, Sharpe, per-horizon alternatives table), IV vs RV overlay chart, regime analysis chart with state labels, full backtest trade history

## Data / Infrastructure

- DuckDB local database: 6 tables (candles_1m, dvol_1m, option_chain_snapshots, advice_log, market_features, collector_runs)
- APScheduler jobs: candles (2 min), DVOL (2 min), options chain (1 hr), derivatives features (5 min), strategy advisor (5 min)
- FastAPI backend; all jobs fire synchronously on startup for immediate dashboard population

## Tags

vol forecasting · HAR-RV implementation · VRP-based options signals · regime-aware advisory · live multi-source market data · DuckDB · APScheduler · FastAPI · TradingView

<!-- file: projects/lighter-arb.md -->
# Lighter main ↔ Lighter rh Cross-Deployment Arbitrage (/arb)

**My role [Mine]:** my idea to arbitrage two deployments of the same perp DEX. I fund the sub-accounts, chose symbols, arm and disarm it, set the per-coin derisk behaviour (release only the coin causing the drain, smoothly, at 5%), and asked for multi-account sets to add inventory with risk isolated per pair. My regime-holding idea was tested and shown not to pay, so I kept the high-turnover approach. AI agents built it and ran the analyses [Directed].

**Type:** live taker-taker arbitrage
**Dates:** 2026-08-15 → ongoing
**Stack:** Python asyncio, FastAPI, Rust signing daemon, SQLite, uPlot

---

- own console and isolated sub-accounts; a pure decision function that always reports why it refused; standalone feeds; runtime credential profiles
- symbols BTC, ETH and XAU; regime gating with hysteresis
- per-coin liquidation guard: each pair held ≥5% from its own liquidation price, released in 1% chunks; account-level survival latch
- multi-account "sets" with risk isolated per account pair; Earned & APR ledger with time-weighted capital
- results: 25.8% APR since start (to 2026-10-05); income ~80% spread capture / ~20% funding
- research: 42% of visible edge was lost to slip, 80% of that in the miss / repair path (latency and pick-off ruled out with edge-matched controls); displacement spikes (z ≥ 2) miss 35.6% vs 6.4%; regimes are real but turnover is the P&L, so gating loses money; gold's offset shown to be structural, not edge

## Tags

statistical arbitrage · execution analysis · slippage attribution · liquidation risk · capital accounting

<!-- file: projects/lighter-hedge.md -->
# lighter_hedge — Delta-Hedging Engine for Option Strangles

**My role [Mine]:** my strategy (sell strangles, hedge strike breakouts with perps, filter fake breakouts using my vol research). AI agents wrote the Rust engine and TUI [Directed].

**Type:** Rust trading engine + terminal UI
**Dates:** 2026-03-21 → 22 (26 commits, ~8.8k lines Rust)
**Stack:** Rust, Tokio, ratatui, Lighter WebSocket + REST

---

- opens a perp hedge on Lighter when price breaks a sold strike, scales in by available book liquidity, closes on reversal
- three hedge modes: standard, fake-breakout buffer, preemptive
- wallet-key-only onboarding: discovers accounts, derives and registers an API signing key, cancels stale orders
- live account WebSocket, fill confirmation by transaction hash, closes always IOC
- circuit breakers: max position size, max session loss, no flip-to-opposite, close cooldown
- OKX + Bybit portfolio panel, multi-strategy monitor, hot-reload config, dry-run mode

## Tags

options hedging · Rust · trading tooling

<!-- file: projects/mytradfiagent.md -->
# mytradfiagent

**My role [Mine]:** my product idea (an AI research analyst for A-share and US markets); I chose the features (debate mode, fast mode, voice, sharing), the data sources and model providers, and ran it live as a public product. Built by AI coding agents in Feb 2026 [Directed].

**Type:** AI-powered financial research platform
**Stack:** Async Python, TypeScript, FastAPI-style backend, React / Vite frontend, PostgreSQL, SSE, financial APIs, multiple LLM providers

---

## Built / Implemented

- AI chat product for financial research
- Multi-turn autonomous research loop (up to 30-turn reasoning workflows)
- Hypothesis debate mode with multiple model roles
- Tool-calling system with 30+ financial data tools
- Structured report output
- User auth and conversation storage
- Admin controls; public sharing; voice input support
- Market data ingestion workflows
- Frontend chat interface

## Data / Infrastructure

- PostgreSQL-backed app data; separate market-data database
- OHLCV storage; financial statement ingestion
- Scheduled updates / cron-style jobs; long-running ingestion jobs

## Detail (from the repo README)

- Code: [github.com/DavidbigC/mytradfiagent](https://github.com/DavidbigC/mytradfiagent); 149 commits Feb 16–25 2026; FastAPI + React 19 / Vite, SSE
- 33+ financial data tools called in parallel; three modes: Normal (deep research, up to 30 turns), Debate (MiniMax + Qwen debaters + judge, auto PDF report), Fast (Grok with web search, under 5 s)
- Chinese A-share focus: EastMoney, Shanghai Stock Exchange, TradingView; 5-minute OHLCV for ~5,200 A-shares since 2020 with daily incremental updates; 10 years of quarterly financials incl. DuPont; fund research
- pandas-ta sandbox (40+ indicators); Whisper STT voice input with fuzzy stock-name matching; public share links

## Tags

AI engineer · data engineer · product builder · financial research tooling · LLM agent architecture · tool calling · multi-model orchestration

<!-- file: projects/perpl-indexer.md -->
# Perpl On-Chain Indexer, L3 Order Book and Research Lake

**My role [Mine]:** I wanted to see who else was quoting on Perpl and how my market maker compared, and set the rule that indexing and research run locally, never on the trading server. AI agents designed and built the indexer and ran the analyses [Directed].

**Type:** blockchain data engineering for a perp DEX on Monad
**Dates:** 2026-07 → 2026-08
**Stack:** Python, Envio HyperSync, Monad JSON-RPC (eth_getLogs, eth_subscribe), SQLite, Parquet, DuckDB, Multicall3

---

- decoded an unverified exchange contract from events rather than sequencer calldata (direct user orders bypass the sequencer); reconciled field mappings with the official SDK ABI (191 events)
- full backfill: 94 shards, 8,653,596 fills + 316,851,059 actions, 18 GB, 22,144 requests with zero rate-limit errors
- taker attribution without the expensive per-action event (verified 638/638), making a ~100 GB backfill possible instead of ~1 TB
- storage chosen by benchmark: SQLite ingest journal + day-partitioned Parquet / DuckDB (18 GB → 2.85 GB; a wide scan went 121.6 s → 0.64 s); SQLite kept for narrow indexed lookups
- real-time L3 order book from proposed blocks with a safe-tier journal; validated against the venue's L2 feed; five live-only defects found and fixed
- chain logs lead the venue's own feed by ~390 ms; storm soak: 0 chain drops vs 18 venue drops
- powered the market-maker competitor study and fee / funding forensics

## Tags

blockchain ETL · columnar analytics · L3 order books · Monad · DuckDB / Parquet

<!-- file: projects/perpl-mm.md -->
# Perpl Market Maker (perpl-mm) — maker on Perpl, hedge on Lighter

**My role [Mine]:** my strategy from day one (quote one tick inside when the spread allows, otherwise join; hedge every fill at once; venue incentives as the income thesis). I specified the fair-value anchor, proposed the "EW-80 percentile" band idea, chose symbols, sizes and tiers, armed features one by one, moved it to a Tokyo server, ran it with live capital, and called the pivot to funding holding after the venue's fee change. AI agents built the engine and console and ran the studies [Directed]; internals are [AI detail].

**Type:** live cross-venue market-making engine and operator console
**Dates:** 2026-07-13 → 2026-10 (pivoted to funding holding 2026-10-13)
**Stack:** Python asyncio, FastAPI, WebSockets, Rust signing daemon over a Unix socket, SQLite, uPlot, nginx, systemd, AWS Lightsail Tokyo

---

## Built

- pilot to production in one day; batched hedging, inventory caps, halt-on-hedge-failure, reconciliation, close-only mode
- fair-value quoting off the Lighter book, then an EWMA-recentred fair
- quoting-model upgrade after an Avellaneda–Stoikov review (vol estimator, vol-scaled spread, reservation-price skew, markout guard, ladder), neutral by default
- percentile tier ladder off EW percentile basis bands (entries p60–p99, exits at reversion), multi-half-life bands, touch-anchored and cap-aware merged-book pricing
- taker-open and taker-close paths; regime actor leaning quotes from basis + carry
- multi-symbol runtimes (BTC, ETH, MON); one shared market-data socket under the venue's ~5-WebSocket-per-IP limit
- dual-venue hedging across Lighter main and Lighter rh with a merged venue-tagged book
- operator console: halt vs close-and-stop, live ladders, positions and equity across venues, funding carry panel, per-trade decision log, mobile layout

## Measured

- first day: −3.1 bps → +1.71 bps of the Perpl leg after the fair-value quoting change
- taker-open entries: 6.55 net bps per dollar vs 1.76 for maker (3.7×), 52 of 53 positive
- on-chain competitor study (1.24M fill legs, 71 accounts above $1M): ranked 7th of 71 at +3.50 bps spread capture on the Perpl leg; most was given back on the hedge — the hedge, not the quote, was the leak
- quote freshness: 67 updates/min, 3.3% stale (losing makers left quotes stale ~50% of the time)
- P&L concentrated 13–16 UTC because the venue's own spread widens in US hours; Saturdays ~10× worse
- entry losses are run-over selection, not toxicity; a volatility-ramped size keeps 77% of volume and cuts negative entry edge by ~two-thirds

## Research and operations

- latency: Lighter WS 3.8 ms from Tokyo vs 95 ms from home; Binance leads Lighter by ~200–300 ms
- dedicated instance after measuring the shared box above its sustainable CPU baseline; CPU audits halved engine load
- incidents owned: a sharp BTC spike liquidated the hedge leg, which led to equity-derived caps, liquidation classification and a margin ladder; order-id collisions between two engines; reconnect replays read as new fills

## Tags

market making · cross-venue hedging · percentile bands · latency research · on-chain competitor analysis · live operation

<!-- file: projects/polymarket.md -->
# Polymarket 5-Min Monitor

**My role [Mine]:** my trading hypothesis (late-window probability thresholds) and the entry rules chosen from the backtest; AI agents built the Rust monitor and ran the backtests (Mar 2026) [Directed].

**Type:** Live prediction market trading monitor and backtest research
**Stack:** Rust (Tokio, tokio-tungstenite, sqlx, crossterm), Python, SQLite, Polymarket Gamma REST API, Polymarket CLOB WebSocket

---

## Built / Implemented

- Live Rust TUI monitor subscribing to Polymarket 5-minute BTC/ETH/SOL markets via CLOB WebSocket
- Alert system firing when price crosses probability thresholds (70/80/90%) within configurable final time windows (30–90 seconds)
- SQLite outcome logging for live alerts, markets, and trades
- Python analysis toolkit for EV and win rate binning by probability band and time window
- Backtest research: asset-specific entry rules (BTC: 20–45s remaining, 70–80% probability → ~91% win rate); EV-filtered signal tiers accounting for Polymarket taker fees
- Combined BTC + ETH + SOL backtest: win rate rises toward settlement, from 87.3% (90 s left, >70%, n = 2,474) to 96.8% (30 s left, >90%, n = 1,855)
- Telegram alert integration

## Tags

prediction markets · binary options research · Rust async TUI · CLOB WebSocket · Polymarket

<!-- file: projects/research-library.md -->
# Cross-Venue Research Library (May → Oct 2026)

**My role [Mine]:** I asked the questions and made the trading decisions from the answers; AI agents pulled the data, ran the analysis and wrote the reports [Directed]. Data came from the platform's own snapshot tables (hundreds of thousands of 1-minute rows) plus venue docs and APIs.

---

- **RWA arbitrage findings:** 31 symbols, ~132k snapshots; tiered universe by edge vs round-trip cost, mean reversion and liquidity — gold cleared 2× cost 86% of the time; persistent wide gaps (Korean ADRs, AMD, MU, ORCL) classified as carry, not arbitrage
- **Funding mechanisms, trade.xyz vs Lighter:** formula-level comparison; funding moves with the arb for metals and most equities, against it for WTI/Brent and persistent-gap names
- **Oracle and index risk:** Lighter (Chainlink / Pyth / Stork per asset) vs trade.xyz (in-house relayer, per-update clamp, futures-roll blends); per-asset-class risk map explaining 44–55% funding misalignment on energy
- **HIP-3 landscape and pair map:** Hyperliquid's 9 perp-DEX slots; 28 viable trade.xyz ↔ Lighter RWA pairs; underlying-alignment check (copper futures vs spot flagged)
- **Autonomous MM edge thresholds:** starting thresholds from 154,758 snapshots
- **Taker-only synthesis:** explicit round-trip cost model that showed earlier dashboard $/day figures were too optimistic; universe ranked by envelope ÷ cost (WTI 8.5×, Brent 5.8×, gold 5.6×)
- **WTI playbook:** basis half-life 13.1 min; funding capture lost money at every hold from 2 h to 48 h, so trade the basis; maker / taker / escalating-maker backtests (escalating maker 9.03 bps net per cycle)
- **RWA spread + funding synthesis:** 31 pairs, walk-forward with fees
- **135-symbol funding-harvest screen:** 6 months of crypto data, ranked by funding edge, sign persistence and breakeven days
- **Oil roll weekends:** 248,724 snapshots across three venues; deep negative roll funding fades over the weekend and returns with the roll on trading days
- **Oil perp vs swap:** futures-curve backwardation as the economic explanation; swap financing charged in points, not percent
- **Within-Omni oil basis:** spread decomposed into a perp discount that resets at session reopen plus a 60–94 bps uncompensated index divergence
- **Oracle → basis predictability (Perpl):** no — every reference series lags the book
- **Funding regimes:** 161 days; regime-following +5–6.5%/yr vs −1.3%/yr static, all 24 parameter sets positive out-of-sample
- **Funding prediction validation:** direction right 78% at 6 h on non-overlapping windows; never pool across venue clamp eras
- **Adaptive dead band:** a fixed band armed 41% / 69% / 94% across three clamp eras; a quantile band holds 73–79%
- **Basis + carry blend:** validated on 32.9 days straddling a carry flip (bootstrap P = 100% in both regimes), then run live
- **Funding hold strategy (BTC + ETH):** in backtest won 9 of 9 trades over 62.75 days, +3.44 bps/day net; shipped as a read-only dashboard line by my choice
- **Market-maker studies:** competitor benchmarking from chain data, session profiling, regime detection, Binance → Lighter lead-lag, run-over vs adverse selection (see `perpl-mm.md`)
- **Arb studies:** slip decomposition, spike adverse selection, regime tradeability (see `lighter-arb.md`)
- **Other:** delta-hedged LP simulation, DEX contract review, Omni oil swap structure analysis

## Tags

quantitative research · market microstructure · funding and basis analysis · research-to-decision

<!-- file: projects/rust-shadow-engine.md -->
# Rust Shadow Engine (perpl-shadow)

**My role [Mine]:** my decision to have the market maker rewritten in Rust as a separate, read-only shadow app — partly curiosity, partly to measure what a faster language would buy. I accepted the finding that venue latency, not code speed, is the limit. AI agents wrote all of the Rust [Directed].

**Type:** faithful Rust port of the Python market-making engine, run in shadow
**Dates:** 2026-07-19
**Stack:** Rust, Tokio, WebSockets, SQLite

---

- consumes public market data only, simulates acks at the venue's measured latency, and builds + signs real hedge transactions with a throwaway key that are then dropped — runs beside the live engine with zero credentials and no HTTP client
- parity gate: golden vectors generated from the live Python modules, asserted in Rust to 1e-9
- first 65-minute live session: signal → signed order p50 709 µs / p99 928 µs vs p50 123 ms on the earlier Python-era path

## Tags

Rust · low-latency systems · cross-language parity testing

<!-- file: projects/sui-warehouse.md -->
# SUI Transaction Data Warehouse

**My role [Mine]:** built hands-on (Jan 2025) — design, code and schema are mine.

**Type:** Blockchain transaction ingestion / warehouse pipeline
**Stack:** Python, PostgreSQL, SQLAlchemy, Sui JSON-RPC

---

## Built / Implemented

- Transaction monitor and normalization logic
- Transaction storage flow; object change parsing; event parsing; gas usage extraction
- Checkpoint-based transaction retrieval

## Schema Elements

- transaction digest, sender, timestamp, checkpoint
- transaction type, status, package ID, function, gas used
- created / deleted / modified objects, events JSON

## Tags

analytics engineering · blockchain ETL · warehouse ingestion · Sui · JSON-RPC · PostgreSQL schema design

<!-- file: projects/treasury-and-risk.md -->
# Treasury, Rebalancer and Liquidation-Risk Stack

**My role [Mine]:** I wanted capital to move between venues automatically when one side gets close to liquidation, required liquidation monitoring and de-risking after real drawdowns, set alert behaviour and thresholds, decide when each guard is armed, and mandated that money-moving code never reaches any server or remote. AI agents built and hardened it [Directed].

**Dates:** 2026-05 → 2026-10
**Stack:** Python, web3, Textual TUI, Arbitrum USDC, CCTP, Telegram

---

## Treasury and rebalancer (local only)

- deposit / withdraw primitives for Lighter (fast withdraw, CCTP deposit) and Omni (withdrawal, relayer deposit) — all four legs proven with small real-money round trips
- rebalancer: triggers when any venue's closest position is <10% from liquidation, equalises equity to a 5% band in fixed units, donor keeps a free-margin floor; Textual control-hub TUI
- money safety: dry-run default, max-amount cap, prechecks before submit, no retry on money-moving calls, typed confirmation for live mode; kept off every remote by a pre-push hook; 160 tests

## Liquidation-risk stack

- liquidation alarm bot: all positions on three venues, 5-tier distance ladder with a velocity bump and hysteresis, on a separate Telegram bot from routine alerts
- auto-deleverage design: reduce both legs of a hedged pair until distance is back above 10%
- liquidation guard: % adverse move until liquidation as the operator unit, exposure netted only within an underlying, urgency from position ÷ daily volume; deployed observe-only by my choice
- per-coin guards on the cross-deployment arb; capacity warning before a venue rejects an order on OI / skew caps

## Tags

treasury operations · on-chain transfers · risk management · alerting · production safety

<!-- file: projects/variational-perps.md -->
# Variational Cross-Venue Perpetuals Platform

**My role [Mine]:** my strategy of quoting RWA perps on trade.xyz and hedging on Lighter; I asked for the simpler operator-driven, Hummingbot-style design (pick a coin, set entry, exit and a timer) over auto-calibration, set sizes and limits, and ran it with live capital. AI agents built the engine, daemons and tests (May 2026) [Directed]; the internals below are [AI detail].

> **Scope note:** this file covers the rwa-auto / rwa-maker engine (trade.xyz ↔ Lighter). The same repository grew into a four-app platform — see `variational-platform.md`. trade.xyz (RWA perps), Omni / Variational (omni.variational.io) and Lighter are three different venues.

**Type:** Production autonomous bilateral market-making and cross-exchange arbitrage system
**Stack:** Python, Flask, gevent, Socket.IO, Rust, WebSockets, REST APIs, SQLite (WAL mode), Unix domain sockets, Gunicorn, Nginx, AWS Lightsail

---

## System Architecture

- Three-tier orchestration hierarchy: `Orchestrator → SymbolSupervisor → LegSession → RwaMakerExecutor`
- Orchestrator owns all symbols; hot-reloads YAML config (2s poll) and applies hourly signal overlays without downtime
- SymbolSupervisor manages per-symbol lifecycle with exponential-backoff cooldown ladder (5s → 10s → 20s → 30s → 60s max) and hysteresis re-opening gates to prevent thrashing
- LegSession wraps executor threads; soft shutdown with 8s timeout; terminal event forwarding for error escalation
- Two Rust signing daemons spawned as lazy sidecars, communicated with over Unix domain sockets (newline-delimited JSON, ~40µs IPC)

## Market-Making Engine (XEMM Pattern)

- Cross-exchange market-making: quote limit orders on trade.xyz, hedge fills on Lighter
- Multiple offset strategies: `improve`, `join`, `one_back`, `lighter_anchor`, `xyz_anchor` — configurable per session
- Reprice throttle: only replaces order when age ≥ `reprice_min_age_s` AND price diverges by ≥ `reprice_threshold_ticks`
- Adverse-move cancellation: cancel resting maker order when hedge-side moves against it by `adverse_move_cancel_bps`
- Depth-ratio quoting: limits quote size to a fraction of available Lighter hedge depth at acceptable slippage
- Funding skew: shifts entry threshold by `alpha × funding_diff_bps_per_hr`, capped at configurable max
- Thread-safe fill queue with deduplication across WS retries (fill key = oid:tid:sz:time_ms tuple)
- Periodic reconciliation (30s) against live open_orders to catch orphaned orders after cancel/fill races

## Risk Management

- Multi-level risk supervision: global notional USD cap, per-symbol max inventory cap, bilateral net-inventory check
- Position baseline tracking: caps the *change in position* since supervisor start
- Bilateral net-inventory monitor: quarantines symbols when `xyz_position + lighter_position` breaches tolerance
- Kill-all toggle (force-stops all legs), pause-opening toggle (holds new entries, leaves resting hedges)
- Startup reconciliation: cancels orphaned trade.xyz orders on boot; quarantines imbalanced symbols before first leg
- Oracle staleness gate: refuses to open legs if exchange data is stale beyond threshold

## Statistical Signal Computation

- Hourly signals job computes per-symbol advised thresholds from rolling snapshot history
- Exponential-weighted (EW) threshold with 24h halflife: `μ̂ = Σ(v_i × 2^(−age_i / 24)) / Σ(weights)`
- Winsor clipping at [1%, 99%] before EW calculation to neutralize spike contamination
- Outputs p70/p80/p90 threshold quantiles per direction (buy/sell treated independently)
- Funding halflife fitting: log-linear regression of `log|funding_diff|` vs time; halflife = −log(2)/slope, gated on R² > 0.30
- Pearson correlation between funding differential and basis for regime scoring

## Real-Time Market Data Infrastructure

- MarketDataHub singleton: one TradeXyzFeed + two LighterFeed instances (RWA + crypto split)
- ExchangeFeed base class: consumer-based subscription leases; deferred listener dispatch (lock released before calling listeners)
- Self-healing loop (8s tick): detects stale markets (no update in 45s), resubscribes; adaptive throttle on burst resubs
- LighterFeed inflight management: tracks pending subscribes by channel, TTL-evicts orphaned acks (30s), wire throttle 0.4s between messages
- Reconnect with exponential backoff (2s → 60s max); SSL EOF cooldown 8s post-disconnect
- Push-based price ticking: WS callbacks flag pending updates; flush thread batches Socket.IO events every 50ms

## Rust Signing Daemons

- `lighter-execd`: Schnorr signing over ECgFp5 (GF(p^5), p = 2^64 − 2^32 + 1) and Poseidon2 (Goldilocks field); the crypto modules are vendored from the open-source lighter-rust crate, while the daemon, IPC protocol, nonce cache and order building were built for this project
- `tradexyz-execd`: EIP-712 signing (L1 phantom Agent domain, chainId=1337); action_hash = keccak256(msgpack(action) || nonce), alloy-signer secp256k1 ECDSA
- Both: local nonce cache (AtomicU64 floor) eliminates 10–70ms HTTP roundtrip per order; jittered exponential backoff reconnect
- Per-request latency breakdown: nonce_fetch_ms, sign_ms, total_ms reported to Python caller

## Data Storage (SQLite, WAL Mode)

- 9 tables: `rwa_sessions`, `rwa_fills`, `rwa_market_data`, `rwa_auto_signals`, `rwa_arb_snapshots`, `rwa_depth_snapshots`, `balance_history`, `trade_history`, `daily_arb_pnl`
- Order book depth snapshots at 1/2/5/10/20 bps buckets per venue/side (20 columns per row)
- Funding attribution: proportional split of funding payments across open fills; idempotent via UNIQUE(fill_id, exchange, source_event_id)
- Post-fill adverse selection tracking: 1s/5s/30s horizon drift in bps per fill
- WITHOUT ROWID + clustered PKs on (symbol, timestamp) for fast time-series reads

## Testing

- 87 test files covering all critical paths: orchestration lifecycle, executor order logic, market data feeds, signal computation, funding attribution, Rust daemon IPC
- Fake object injection via dataclass `Deps` pattern (no external I/O in unit tests)
- Real SQLite integration tests (tempfile-isolated per test, not mocked)
- Controllable fake clock for time-based logic tests without actual sleeps
- Monkeypatch-based module-level singleton injection for executor tests
- Data-driven tests: 100+ generated sample rows for percentile and threshold assertions

## Dashboard and Operational UI

- 18 HTML pages served via Flask template routes
- Live Socket.IO events: `rwa_arb_update` (2s cadence), `rwa_price_tick` (50ms cadence), session/fill events
- Background tasks: 2s broadcaster, 60s snapshot scheduler, 15min funding attribution refresh
- In-app docs renderer at `/docs/<page>` with Mermaid diagram support

## Infrastructure

- AWS Lightsail production deployment (ap-northeast-1), systemd service management
- Multi-account credential management (primary + indexed accounts)
- Live capital deployed; real execution risk with fill-on-both-legs requirement

## Tags

autonomous market-making · XEMM · cross-venue delta-neutral execution · RWA perpetuals (trade.xyz / Hyperliquid HIP-3) · zkSync DeFi (Lighter Protocol) · ZK signing integration (vendored Schnorr / Poseidon2 / ECgFp5) · EIP-712 signing · self-healing WebSocket infra · statistical signal computation · risk management systems · Rust + Python IPC · live capital

<!-- file: projects/variational-platform.md -->
# Variational Trading Platform — 2026 Overview

**My role [Mine]:** I decided what to build at every stage, chose venues and strategies, set risk limits and the agents' operating rules, funded and ran the accounts, and judged results by P&L. AI agents (Claude Code, Codex) wrote the code, tests and docs — the repo statistics below measure their output under my direction [Directed].

**Type:** multi-app cross-venue trading platform (market making, arbitrage, funding carry, treasury, risk), run as a one-person team
**Dates:** 2026-01-25 → ongoing
**Stack:** Python (Flask + Socket.IO + gevent; FastAPI + asyncio), Rust (Tokio daemons and a shadow engine), SQLite, DuckDB / Parquet, JavaScript dashboards (uPlot), nginx, systemd, AWS Lightsail (Tokyo)

---

## Scale

- 1,435 commits across 76 branches
- Python: main Flask app ~45.9k lines, market-maker app ~33.6k, scripts ~25.7k, research ~6k; HTML/JS dashboards ~23.6k lines
- Rust: signing daemons ~6.4k lines; shadow engine ~11.5k lines
- Tests: 417 files / ~83k lines; market-maker partition 2,637 tests (~32 s)
- 137 design specs and implementation plans, 2 ADRs, a domain glossary, 13 research write-ups, 8 code-review reports

## Four apps in one repo

| App | What it does | Stack | Runs |
|---|---|---|---|
| main ("variational") | funding/spread desk, rwa-maker / rwa-auto, omni-auto, Within-Omni, liquidation guard, Telegram alerts | Flask, Socket.IO, gevent, SQLite | AWS Lightsail |
| perpl-mm | Perpl market maker, Lighter main ↔ rh arb, funding panels, PopDEX monitor | FastAPI, asyncio, SQLite, uPlot | dedicated AWS Lightsail |
| risex-mm | RISEx ↔ Lighter basis collector, funding dashboard, maker execution | FastAPI, httpx, websockets | not deployed |
| treasury | cross-venue deposits / withdrawals and rebalancer | CLI + Textual TUI, web3 | local only |

## Venues

trade.xyz (HIP-3 RWA perps on Hyperliquid), Omni / Variational (RFQ crypto + commodity perps), Lighter main and Lighter rh (two separate deployments), Perpl (Monad), plus read-only or experimental integrations with Ondo Perps, RISEx, PopDEX, Binance and Hyperliquid.

## Timeline

- **Jan–Feb:** funding-rate scanner Variational ↔ Lighter across 80+ perp pairs, TWAP execution, Telegram alerts
- **May:** rwa-maker and rwa-auto (trade.xyz ↔ Lighter); research pack on Hummingbot XEMM, professional MM firms, open-source arb bots and optimal-MM literature; verified-taker executor; unified portfolio; omni-auto; structured logging; liquidation alarms; full code review
- **Jun:** treasury layer and rebalancer; funding ledger backfill; CL ↔ WTI funding research
- **Jul:** Ondo arb page; Perpl market maker; Rust shadow engine; latency research; chain indexer and L3 book
- **Aug:** Lighter main ↔ rh arb; dual-venue hedging; competitor study; CPU audits; RISEx
- **Sep:** Within-Omni pair trading; liquidation guard; funding-regime research; XAU on the arb; backwardation page
- **Oct:** arb returns ledger and multi-account sets; Perpl pivot from market making to funding holding; PopDEX research and monitor

## Operating rules I set for the agents [Mine]

- ship new features inert (disarmed, recording) and never touch my live parameters
- live trading data on the servers is authoritative and is never overwritten from a laptop
- keep production boxes under 20% CPU (Lightsail burst baseline)
- my observation of a bug is ground truth; report averages over the dashboard window, not medians
- run research locally, never on the trading server

## Other pieces

- **omni-auto:** autonomous taker-taker engine Omni ↔ Lighter with cadence tiers and EW percentile thresholds
- **verified-taker:** quorum-window confirmation, depth verification, simultaneous IOC, residual repair, shadow mode
- **rwa-trading modes:** maker-on-trade.xyz, taker-both, maker-on-Lighter executors
- **Ondo arb page:** Omni ↔ Ondo Perps scanner with hourly funding and symbol aliasing
- **RISEx:** checksummed book collector, BTC basis model, funding dashboard, maker permit signing and an authenticated maker execution daemon
- **PopDEX:** protocol trust-model due diligence; read-only maker / Lighter-hedge spread monitor that paper-hedges every public fill
- **Backwardation page:** oil forward curve and the cost of the next roll
- **Monitoring sidecars:** Binance / Lighter / Perpl touch collector, reorg monitor, competitor reports, memory probe

## Tags

one-person trading platform · AI-directed engineering · multi-venue integration · Python + Rust · production operations · research-driven trading

<!-- file: projects/vol-research.md -->
# Hyperliquid Vol & Options Strategy Research

**My role [Mine]:** my strategy questions (how to hedge a short strangle, when a breakout is fake, which strikes and DTEs to sell) and the decisions taken from the results; the backtests, optimisation and ML were run by AI agents (Apr 2026) [Directed].

**Type:** Quantitative options and volatility research project
**Stack:** Python, Numba, Optuna, DuckDB, PyArrow / Parquet, pandas, NumPy, Streamlit, Matplotlib, Binance Futures API, Hyperliquid tick archive, crypto_options_agg API

---

## Research Conducted

- Short-strangle strategy research with perpetual-futures delta-hedging across 15,000+ parameter combinations (strike distance, DTE, hedge mode, buffer, cooldown, bounce thresholds)
- Directional momentum strategy: 12h return breakout with 6h acceleration filter, realized vol threshold gating, persistence filtering; 89-trade backtest over 13 months, 67.4% win rate, Sharpe 4.58
- Systematic comparison of hedge policies: fake-breakout confirmation vs. preemptive vs. standard immediate — fake mode achieves ~3.66 Sharpe vs. 0.16 for immediate mode
- Regime detection: efficiency ratio, chop score, path length, trend strength used to classify market windows and switch strategy parameters dynamically
- Microstructure feature engineering from Hyperliquid tick data: signed relative trade flow, open pressure, block concentration z-scores (TWAP share, block share over 24h windows)
- Options APR surface analysis: live bid prices across strikes and DTEs from crypto_options_agg; asymmetric strike selection research
- Volatility forecasting research: HAR-RV model family (HAR-RV, HAR-RV-J with bipower variation, HARQ with realized quarticity, HAR-IV with DVol); VRP dynamics and IV–RV spread as primary options edge signal
- Markov-switching HAR and regime-switching vol models; DVol term structure shape, skew steepness, and funding rate divergence as regime transition features
- Tail risk research for short-strangle books: quantile regression for breach probability, realized semivariance (upside/downside decomposition), conditional density forecasting
- XGBoost / gradient-boosted trees on rich vol feature sets (lagged RV, IV level, skew, term structure, funding, jump indicators) as complement to HAR baseline

## Methods and Tooling

- Multi-objective Bayesian optimization (Optuna NSGA-II) — Pareto frontier across Sharpe × net P&L × Calmar; 5,000–20,000 trials per run; v1 TPE sampler, v2 NSGA-II genetic algorithm
- Random Forest (sklearn, 400 estimators, OOB scoring) for strategy performance prediction from 14+ parameter features; permutation importance ranking; multi-round iterative candidate proposal loop
- Regime classification: 4-state labels (volatile whipsaw, breakout trend, quiet chop, quiet drift) fitted with quantile thresholds on realized vol, efficiency ratio, chop score; per-regime policy selection on holdout set
- Bootstrap / Monte Carlo resampling for strategy risk metrics (p5 PnL, p95 drawdown, p5 win rate)
- Hedge policy scoring: 10 variants evaluated via weighted z-score composite (Sharpe + avg net − loss − crossings)
- Numba JIT-compiled simulation engines for sub-millisecond backtest execution
- Walk-forward train/test splits; OOB R² and permutation importance for model evaluation
- DuckDB analytical views over multi-gigabyte Parquet datasets (Hyperliquid S3 tick archives, ~18.7M ETH trades)
- GPU-accelerated ML stack (XGBoost CUDA, PyTorch CUDA, Numba JIT) on remote RTX 3070 via SSH

## Key Findings

- Fake-breakout confirmation filtering (wait for confirmed move beyond buffer for N seconds) reduces crossing frequency 100×+ while preserving profitable trend capture
- Asymmetric strikes outperform symmetric: near-ATM calls collect real premium; far OTM puts near-zero cost due to ETH negative skew
- 7-DTE is the risk-adjusted optimum; shorter DTEs have zero OTM bids, longer DTEs collect less premium per unit of risk
- Cooldown periods of 250–600s between hedge re-entries prevent whipsaw losses
- Bounce gating (4–10 price contests minimum) validates a level as genuinely contested

## Data

- Hyperliquid S3 tick archive: ETH/BTC/SOL, ~9 months, ~18.7M ETH trades
- Binance Futures 1h OHLCV (ETH/BTC perpetuals, back to 2023-01-01) + funding rates

## Tags

quantitative options research · vol strategy backtesting · delta-hedging via perpetuals · Bayesian optimization · regime detection · microstructure analysis · Hyperliquid data · ML strategy search

<!-- file: projects/within-omni.md -->
# Within-Omni — RWA Future vs Swap Pair Trading

**My role [Mine]:** I set the two-rate model (30 s while gathering, 1 s only while trading), ruled that the swap leg goes first with the perp 50–300 ms behind, sized the pairs, and decide when to press Start. My observation that oil pair spreads widened in steps started the basis research. AI agents built the monitor and executor [Directed].

**Type:** monitor and paired executor for economically equivalent instruments on one venue
**Dates:** 2026-09 → 2026-10
**Stack:** Python, Flask, curl_cffi, SQLite

---

- monitors the executable spread between Omni's RWA perpetual futures and their swap twins (gold, silver, US500, WTI, Brent); pairs discovered from venue metadata, declared pairs where naming conventions break
- per-pair cadence cut order-endpoint traffic from 86/min to 8/min; closed-market backoff cut refused probes from 160/hr to ~4/hr
- paired executor: three consecutive threshold confirmations, global execution slot held through repair, swap-first ordering, one-sided fill compensation, two-read reconciliation, force-stop and alert on ambiguity
- positions panel, trade-history integration, EW rails, per-pair health gating; backwardation page with the oil forward curve and the next roll's cost
- oil basis research: the 4-hourly spread widening is the perp's funding; the uncompensated risk is a 60–94 bps index divergence between two Brent series

## Tags

relative value · RWA perps · commodities · execution safety
