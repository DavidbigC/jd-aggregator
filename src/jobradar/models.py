from dataclasses import dataclass, field


@dataclass
class Posting:
    source: str
    source_job_id: str
    company: str
    title: str
    url: str | None = None
    ats_key: str | None = None
    locations: list[str] = field(default_factory=list)
    remote: bool | None = None
    description: str | None = None
    posted_at: str | None = None
    salary: str | None = None
    company_website: str | None = None
    from_ats: bool = False
