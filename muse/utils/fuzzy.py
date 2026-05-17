from rapidfuzz import process, fuzz

def fuzzy_match(query: str, choices: list[str], limit: int = 5, threshold: int = 85):
    """Perform fuzzy matching against a list of choices."""
    results = process.extract(
        query.lower(),
        choices,
        scorer=fuzz.WRatio,
        limit=limit
    )
    return [r for r in results if r[1] >= threshold]
