from crawler.kaufland import extract_valid_dates

def test_extract_valid_dates():
    text = "Gültig vom 17.04. bis 23.04."
    start, end = extract_valid_dates(text)
    assert start.endswith("-04-17")
    assert end.endswith("-04-23")

