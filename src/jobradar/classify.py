import json
import re
from collections import defaultdict

from .normalize import is_web3

ROLES = {
    "engineering": "Engineering", "data": "Data & AI", "research": "Research", "quant-trading": "Quant & Trading",
    "product": "Product", "design": "Design", "security": "Security", "bd-sales": "BD & Sales",
    "marketing-community": "Marketing & Community", "operations": "Operations",
    "compliance-legal-risk": "Compliance, Legal & Risk", "finance": "Finance", "people": "People & Recruiting",
    "support": "Support", "other": "Other",
}
SENIORITY = {
    "intern": "Intern", "junior": "Junior", "mid": "Mid", "senior": "Senior", "lead": "Lead / Staff",
    "head": "Head / Director", "exec": "VP / C-level",
}

# First match wins, so the more specific families come before the generic ones (e.g. "Sales Engineer", "Data Engineer").
_ROLE_RULES = [
    ("support", r"support|customer (service|care|success|experience)|help ?desk|implementation|onboarding|client (success|experience)|customer enablement|professional services|客服|고객|カスタマー|поддержк"),
    ("compliance-legal-risk", r"complian|legal|counsel|lawyer|attorney|paralegal|risk|\baml\b|\bkyc\b|fraud|"
                              r"regulat|financial crime|investigat|\bkyb\b|policy|underwrit|credit|sanction|privacy|surveillance|合规|合規|法务|法務|风控|風控|"
                              r"컴플라이언스|법무|リーガル|コンプライアンス|法務|комплаенс|юрист"),
    ("people", r"recruit|talent|\bhr\b|human resources|people (ops|operations|partner)|\bpeople\b|employee relations|organi[sz]ation development|compensation|薪酬|招聘|人事|人资|"
               r"채용|인사|採用|рекрутер|\bhr-"),
    ("security", r"security|secops|appsec|penetration|pentest|smart contract audit|security audit|red team|安全|"
                 r"보안|セキュリティ|безопасн"),
    ("finance", r"account(ant|ing)|accounts (receivable|payable)|financ(e|ial)|treasur|investor relations|invest|venture|asset management|capital markets|general partner|banking|\btax\b|controller|payroll|\baudit|fp&a|财务|財務|会计|"
                r"會計|재무|회계|経理|бухгалтер|финанс"),
    ("quant-trading", r"quant|trader|trading|market mak|\botc\b|做市|量化|交易员|交易員|トレーダー|트레이더|трейдер"),
    ("design", r"design|\bux\b|\bui\b|illustrat|creative|artist|\b3d\b|设计|設計|디자인|デザイ|дизайн"),
    ("marketing-community", r"marketing|growth|community|content|social media|\bbrand|communications|\bpr\b|\bseo\b|"
                            r"\bkol\b|ambassador|editor|writer|journalist|copywrit|go-to-market|\bgtm\b|\bcrm\b|lifecycle|public relations|government relations|e-commerce|video|producer|paid ads|企劃|企划|主编|运营|運營|市场|市場|마케팅|"
                            r"マーケ|маркет|smm"),
    ("bd-sales", r"business development|\bbdr?\b|\bsdr\b|sales|lead generation|channel|vertrieb|client advisor|account (executive|manager|director)|partnership|"
                 r"institutional|relationship manager|listing|ecosystem|商务|商務|销售|銷售|业务拓展|영업|사업개발|"
                 r"営業|продаж"),
    ("product", r"product|产品|產品|프로덕트|기획|プロダクト|продукт"),
    ("research", r"research|economist|研究|리서치|リサーチ|исследова"),
    ("data", r"\bdata\b|analytic|analyst|\bbi\b|business intelligence|machine learning|\bml\b|\bai\b|\bllm|"
             r"scientist|数据|數據|資料|데이터|データ|аналитик|data-"),
    ("engineering", r"engineer|developer|programmer|technical staff|tech(nical)? lead|\bcto\b|(?-i:\bIT\b)|\bios\b|android|\bhpc\b|\bnoc\b|プログラマ|技術|技术|工程|devops|\bsre\b|architect|front-?end|back-?end|full-?stack|"
                    r"software|solidity|rust|golang|\bqa\b|tester|\btest|工程师|工程師|开发|開發|엔지니어|개발|"
                    r"エンジニア|開発|разработчик|программист|инженер|programista|entwickler|ingénieur|desarrollador"),
    ("operations", r"operation|\bops\b|office|assistant|admin|coordinator|project manager|program manager|"
                   r"chief of staff|strategy|general manager|deputy|procurement|supply chain|buyer|workforce|branch manager|business (manager|lead|partner)|manufactur|technician|operator|electrician|行政|助理|운영|総務|операци"),
]
_ROLE_RE = [(k, re.compile(p, re.I)) for k, p in _ROLE_RULES]

_SENIORITY_RULES = [
    ("intern", r"intern|trainee|apprentice|werkstudent|praktik|stagiaire|实习|實習|인턴|インターン|стаж"),
    ("exec", r"\bvp\b|vice president|\bchief\b|\bc[eotfm]o\b|\bcxo\b|president|co-?founder|managing director|"
             r"总裁|總裁|副总|부사장|執行役員|вице-президент"),
    ("head", r"\bhead\b|director|总监|總監|负责人|負責人|本部長|部長|이사|директор|руководител"),
    ("lead", r"\blead\b|principal|\bstaff\b|tech lead|team lead|主管|组长|組長|リード|리드|팀장|ведущ|тимлид|lider"),
    ("senior", r"senior|\bsr\b|\bsnr\b|資深|资深|高级|高級|シニア|시니어|старш|starszy|\bsenior"),
    ("junior", r"junior|\bjr\b|entry|graduate|new grad|初级|初級|应届|ジュニア|新卒|주니어|신입|младш|młodszy"),
]
_SENIORITY_RE = [(k, re.compile(p, re.I)) for k, p in _SENIORITY_RULES]

# code: (display name, place words). Matched on lowercased text with letter boundaries.
COUNTRIES = {
    "US": ("United States", "united states|usa|u\\.s\\.|us|new york|nyc|san francisco|bay area|silicon valley|"
                            "los angeles|miami|chicago|austin|seattle|boston|denver|atlanta|dallas|houston|"
                            "san jose|palo alto|mountain view|menlo park|washington,? dc|california|texas|florida|"
                            "illinois|massachusetts|new jersey|colorado|nevada|las vegas|美国|美國|纽约|紐約"),
    "GB": ("United Kingdom", "united kingdom|uk|england|scotland|(?<!south )wales|great britain|london|manchester|edinburgh|"
                             "glasgow|bristol|belfast|伦敦|倫敦|英国|英國"),
    "SG": ("Singapore", "singapore|sg|新加坡|싱가포르|シンガポール"),
    "HK": ("Hong Kong", "hong kong|hongkong|hk|香港|홍콩"),
    "CN": ("China", "china|mainland|shanghai|beijing|shenzhen|hangzhou|guangzhou|chengdu|上海|北京|深圳|杭州|广州|"
                    "廣州|成都|中国|中國|大陆"),
    "TW": ("Taiwan", "taiwan|taipei|台北|臺北|台湾|台灣|臺灣|新北|台中|臺中|高雄|新竹"),
    "JP": ("Japan", "japan|tokyo|osaka|fukuoka|日本|东京|東京|大阪|福岡"),
    "KR": ("South Korea", "korea|seoul|busan|韩国|韓國|首尔|首爾|서울|한국|부산"),
    "IN": ("India", "india|bangalore|bengaluru|mumbai|delhi|gurgaon|gurugram|noida|pune|hyderabad|chennai|kolkata"),
    "VN": ("Vietnam", "vietnam|viet nam|hanoi|ho chi minh|越南"),
    "TH": ("Thailand", "thailand|bangkok|泰国|泰國|曼谷"),
    "ID": ("Indonesia", "indonesia|jakarta|bali|印尼|印度尼西亚"),
    "MY": ("Malaysia", "malaysia|kuala lumpur|labuan|马来西亚|馬來西亞|吉隆坡"),
    "PH": ("Philippines", "philippines|manila|makati|taguig|菲律宾|菲律賓"),
    "AU": ("Australia", "australia|sydney|melbourne|brisbane|perth|澳大利亚|澳洲"),
    "NZ": ("New Zealand", "new zealand|auckland|wellington"),
    "AE": ("UAE", "united arab emirates|uae|dubai|abu dhabi|迪拜"),
    "CH": ("Switzerland", "switzerland|zurich|zürich|zug|geneva|lugano|瑞士"),
    "DE": ("Germany", "germany|deutschland|berlin|munich|münchen|frankfurt|hamburg|köln|cologne|德国|德國"),
    "FR": ("France", "france|paris|法国|法國"),
    "NL": ("Netherlands", "netherlands|amsterdam|rotterdam"),
    "IE": ("Ireland", "ireland|dublin"),
    "PT": ("Portugal", "portugal|lisbon|lisboa|porto"),
    "ES": ("Spain", "spain|madrid|barcelona"),
    "IT": ("Italy", "italy|milan|rome"),
    "PL": ("Poland", "poland|polska|warsaw|warszawa|krakow|kraków|wroclaw|wrocław|gdansk|gdańsk|poznan|poznań"),
    "CZ": ("Czechia", "czech|prague"),
    "AT": ("Austria", "austria|vienna|wien"),
    "HU": ("Hungary", "hungary|budapest"),
    "RO": ("Romania", "romania|bucharest"),
    "BG": ("Bulgaria", "bulgaria|sofia"),
    "GR": ("Greece", "greece|athens"),
    "CY": ("Cyprus", "cyprus|limassol|nicosia"),
    "MT": ("Malta", "malta"),
    "GI": ("Gibraltar", "gibraltar"),
    "LU": ("Luxembourg", "luxembourg"),
    "BE": ("Belgium", "belgium|brussels"),
    "SE": ("Sweden", "sweden|stockholm"),
    "DK": ("Denmark", "denmark|copenhagen"),
    "NO": ("Norway", "norway|oslo"),
    "FI": ("Finland", "finland|helsinki"),
    "EE": ("Estonia", "estonia|tallinn"),
    "LT": ("Lithuania", "lithuania|vilnius"),
    "LV": ("Latvia", "latvia|riga"),
    "UA": ("Ukraine", "ukraine|kyiv|kiev|lviv|україна|київ|украина"),
    "RS": ("Serbia", "serbia|belgrade"),
    "TR": ("Turkey", "turkey|türkiye|istanbul|i̇stanbul"),
    "IL": ("Israel", "israel|tel aviv|jerusalem|herzliya"),
    "SA": ("Saudi Arabia", "saudi|riyadh"),
    "QA": ("Qatar", "qatar|doha"),
    "BH": ("Bahrain", "bahrain"),
    "EG": ("Egypt", "egypt|cairo"),
    "PK": ("Pakistan", "pakistan|karachi|lahore|islamabad"),
    "IS": ("Iceland", "iceland|reykjavík|reykjavik"),
    "NG": ("Nigeria", "nigeria|lagos"),
    "KE": ("Kenya", "kenya|nairobi"),
    "ZA": ("South Africa", "south africa|cape town|johannesburg"),
    "RU": ("Russia", "russia|moscow|saint petersburg|россия|москва|санкт-петербург"),
    "BY": ("Belarus", "belarus|minsk|минск"),
    "AM": ("Armenia", "armenia|yerevan|армения"),
    "GE": ("Georgia", "tbilisi"),
    "KZ": ("Kazakhstan", "kazakhstan|almaty|astana|казахстан"),
    "CA": ("Canada", "canada|toronto|vancouver|montreal|calgary|ottawa"),
    "MX": ("Mexico", "mexico|méxico|guadalajara"),
    "BR": ("Brazil", "brazil|brasil|são paulo|sao paulo|rio de janeiro|belo horizonte"),
    "AR": ("Argentina", "argentina|buenos aires|caba"),
    "CO": ("Colombia", "colombia|bogotá|bogota|medellín|medellin"),
    "CL": ("Chile", "chile|santiago"),
    "PE": ("Peru", "peru|perú|lima"),
    "UY": ("Uruguay", "uruguay|montevideo"),
    "BM": ("Bermuda", "bermuda"),
    "KY": ("Cayman Islands", "cayman"),
    "BS": ("Bahamas", "bahamas|nassau"),
}
_COUNTRY_RE = {code: re.compile(r"(?<![a-z])(" + words + r")(?![a-z])") for code, (_, words) in COUNTRIES.items()}
_US_STATES = {"AL", "AZ", "CA", "CO", "CT", "DC", "FL", "GA", "IL", "MA", "MD", "MI", "MN", "NC", "NJ", "NV", "NY",
              "OH", "OR", "PA", "TN", "TX", "UT", "VA", "WA", "WI"}
_ANYWHERE = re.compile(r"anywhere|worldwide|global|earth|international|fully remote|全球|全世界|不限", re.I)
_REGION_WORDS = re.compile(r"europe|emea|\beu\b|apac|asia|americas|latam|north america|\bna\b|mena|africa|"
                           r"european|cet|gmt|utc|time ?zone", re.I)


def classify_job(title: str, locations: list[str], remote: bool) -> dict:
    countries = countries_for(locations)
    return {"role": _first(_ROLE_RE, title) or "other", "seniority": _first(_SENIORITY_RE, title) or "mid",
            "countries": countries, "remote_scope": remote_scope(locations, countries) if remote else None}


def _first(rules, text: str) -> str | None:
    return next((k for k, rx in rules if rx.search(text or "")), None)


def countries_for(locations: list[str]) -> list[str]:
    out = []
    for loc in locations:
        text = loc.lower()
        found = [code for code, rx in _COUNTRY_RE.items() if rx.search(text)]
        if not found and (tail := loc.rsplit(",", 1)[-1].strip()) and re.fullmatch(r"[A-Z]{2}", tail):
            found = ["US"] if tail in _US_STATES and "," in loc else [tail] if tail in COUNTRIES else []
        out += [c for c in found if c not in out]
    return out


def remote_scope(locations: list[str], countries: list[str]) -> str:
    text = " | ".join(locations)
    if _ANYWHERE.search(text):
        return "anywhere"
    return "restricted" if countries or _REGION_WORDS.search(text) else "anywhere"


# Company sector. Rule order and evidence thresholds are explained in docs/decisions/0003-company-sector.md.
_CRYPTO_NAME = re.compile(r"coin|chain|crypto|token|swap|\bdao\b|defi|web3|blockchain|链|鏈|幣|币|블록체인|"
                          r"ブロックチェーン|крипт", re.I)
_WEAK = re.compile(r"\bprotocols?\b|decentrali[sz]|\bnetworks?\b|\btokens?\b|\bwallets?\b|validators?\b|consensus|"
                   r"cryptograph|digital ownership|open networks?|self-custody|\bledger", re.I)
CRYPTO_BOARDS = {"jobstash", "getro", "consider", "web3career", "cryptojobslist", "cryptocurrencyjobs", "web3vacancy",
                 "cryptojobs", "telegram", "rebase", "remote3", "foresight", "learnblockchain"}
REVIEW_MIN_JOBS = 5


def sector_for(name: str, seed: bool, crypto_only: bool, n: int, strong: int, weak: int,
               crypto_board: bool) -> tuple[str, str]:
    if crypto_only:
        return "other", "crypto_only"
    if _CRYPTO_NAME.search(name or ""):
        return "crypto", "name"
    if n and strong / n >= 0.4:
        return "crypto", "share"
    if seed and (n < REVIEW_MIN_JOBS or strong or weak / n >= 0.2):
        return "crypto", "seed"
    if crypto_board and n and strong / n >= 0.2:
        return "crypto", "board"
    return "other", "default"


def company_sectors(conn) -> int:
    stats = defaultdict(lambda: [0, 0, 0])
    for r in conn.execute("SELECT company_id, title, description FROM jobs"):
        text = f"{r['title']} {r['description'] or ''}"
        s = stats[r["company_id"]]
        s[0] += 1
        s[1] += is_web3(text)
        s[2] += len({m.lower() for m in _WEAK.findall(text)}) >= 2
    boards = {r[0]: (r[1], r[2]) for r in conn.execute(
        "SELECT company_id, MAX(NOT crypto_only), MAX(crypto_only) FROM boards GROUP BY company_id")}
    on_crypto_board = {r[0] for r in conn.execute(
        f"SELECT DISTINCT j.company_id FROM sightings s JOIN jobs j ON j.id = s.job_id "
        f"WHERE s.kind IN ({', '.join('?' * len(CRYPTO_BOARDS))})", sorted(CRYPTO_BOARDS))}
    updates = []
    for c in conn.execute("SELECT id, name FROM companies WHERE sector_source IS NOT 'override'").fetchall():
        n, strong, weak = stats[c["id"]]
        seed, crypto_only = boards.get(c["id"], (0, 0))
        updates.append((*sector_for(c["name"], bool(seed), bool(crypto_only), n, strong, weak,
                                    c["id"] in on_crypto_board), c["id"]))
    conn.executemany("UPDATE companies SET sector = ?, sector_source = ? WHERE id = ?", updates)
    conn.commit()
    return len(updates)


def reclassify_jobs(conn) -> int:
    rows = conn.execute("SELECT id, title, locations, remote FROM jobs").fetchall()
    conn.executemany("UPDATE jobs SET role = ?, seniority = ?, countries = ?, remote_scope = ? WHERE id = ?",
                     [(*job_values(r["title"], json.loads(r["locations"]), r["remote"]), r["id"]) for r in rows])
    conn.commit()
    return len(rows)


def job_values(title: str, locations: list[str], remote) -> tuple:
    c = classify_job(title, locations, bool(remote))
    return c["role"], c["seniority"], json.dumps(c["countries"]), c["remote_scope"]
