import hashlib
from typing import List, Dict, Union

def get_product_id(product:Dict[str, Union[int, str]], tags:List[str]) -> str:
    """
    Produce a unique product ID based on the product's and tags.
    """
    key = "|".join([product[tag] for tag in tags])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()
