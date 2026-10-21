def gather(items, fn) -> list:
    out, errors = [], []
    for item in items:
        try:
            out += fn(item)
        except Exception as e:
            errors.append(f"{item}: {e!r}")
    if errors and not out:
        raise RuntimeError("; ".join(errors)[:1000])
    return out


def _k(v) -> str:
    return f"{v / 1000:.0f}k" if v >= 1000 else f"{v:g}"


def salary_text(lo, hi, currency=None, period=None) -> str | None:
    if not lo and not hi:
        return None
    rng = _k(lo or hi) if not (lo and hi) or lo == hi else f"{_k(lo)}–{_k(hi)}"
    per = f"/ {period.lower()}" if period and "not_defined" not in period.lower() else None
    return " ".join(x for x in (currency, rng, per) if x)
