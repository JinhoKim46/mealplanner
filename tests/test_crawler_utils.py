from crawler.shared.utils import get_product_id

def test_get_product_id_stability():
    item = {"title": "Milch", "subtitle": "1L", "unit_price": "0.89"}
    pid1 = get_product_id(item, ["title", "subtitle", "unit_price"])
    pid2 = get_product_id(item, ["title", "subtitle", "unit_price"])
    assert pid1 == pid2
