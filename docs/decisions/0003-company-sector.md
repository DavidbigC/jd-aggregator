# 0003 — Company sector for the crypto filter

**Problem.** The radar is used to find jobs at crypto companies, but about a third of its jobs are at companies that aren't crypto. None of the obvious signals settles it:
- **Crypto aggregators list non-crypto companies.** jobstash lists Fidelity, UniCredit and Optiver; getro VC networks include non-crypto portfolio companies.
- **The research seed list has non-crypto companies too**, such as Carta, Ashby and Virtu.
- **Job text misses crypto-native companies.** Only 63% of jobs at crypto companies use a crypto term, and generic "General Application" posts use none.
- **Softer words point the wrong way.** Words like "protocol" and "network" are used more by cloud and security companies than by small crypto teams.

**Options considered.**
1. Flag a job as crypto if it mentions crypto. This is wrong at company level in both directions.
2. Flag by source: crypto aggregator means crypto. This lets the TradFi and fintech firms listed on jobstash and getro through.
3. Give each company a `sector` from ordered rules (override → crypto_only board → company name → share of crypto jobs → seed board plus evidence → crypto-only boards plus evidence), and review the largest companies by hand into an override file.
4. Classify each company with an LLM. This is more accurate on the long tail, but needs an API key and has a running cost.

**Decision.** Option 3.
- The sector is recomputed after every poll, so new companies get classified without manual work.
- `seeds/company_sectors.csv` holds hand-checked overrides and always wins.
- A toggle on the Companies page appends to that file, so corrections survive a rebuild.
- `companies.sector_source` records which rule fired.

**Consequences.**
- The default jobs view is "Crypto companies only".
- Errors on small, new companies are possible until someone overrides them. The top companies, which hold about 77% of jobs, are hand-checked.
- Banks and brokers with crypto teams (DBS, Robinhood, Fidelity) count as "other" by design.
