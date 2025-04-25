from bs4 import BeautifulSoup
from crawler.kaufland import extract_price_block

def test_price_block_parser():
    html = """
    <div class="k-price-tag">
        <div class="k-price-tag__price">0.99</div>
        <div class="k-price-tag__old-price">1.49</div>
        <div class="k-price-tag__discount">-33%</div>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = extract_price_block(soup)
    assert result["price"] == "0.99"
    assert result["discount"] == "-33%"
