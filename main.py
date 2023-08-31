
import pathlib
import time
import random

import requests
from rich.console import Console

cookie = pathlib.Path("login.txt").read_text()

session = requests.Session()
session.cookies.update({".ROBLOSECURITY": cookie})

console = Console(highlight=False)

def cprint(color: str, content: str) -> None:
    console.print(f"[ [bold {color}]>[/] ] {content}")


def fetch_items() -> None:
    result = {}
    cursor = ""

    while cursor is not None:
        try:
            req = session.get(
                "https://catalog.roblox.com/v2/search/items/details",
                params={
                    "Category": 13,
                    "Subcategory": 37,
                    "MaxPrice": 0,
                    "Limit": 10,
                    "cursor": cursor,
                    "itemType": "Bundle"
                }
            )
            res = req.json()

            if req.status_code == 429:
                cprint("red", "Rate limited. Trying...")
                time.sleep(random.uniform(5, 10))
                continue

            for item in res.get("data", []):
                item_name = item.get("name")
                item_type = item.get("itemType")

                if item_type == "Bundle":
                    result[item_name] = item.get("productId")
                    cprint("blue", f"Bundle found: {item_name}")
                    purchase(item_name, item.get("productId"))
                else:
                    cprint("yellow", f"Not bundle found. Skipping: {item_name}")

            cursor = res.get("nextPageCursor")

        except requests.exceptions.RequestException:
            cprint("red", "Connection lost. Trying...")
            continue

    return result


def purchase(name: str, product_id: int) -> None:
    try:
        req = session.post("https://auth.roblox.com/v2/login")
        csrf_token = req.headers["x-csrf-token"]

        while True:
            req = session.post(
                f"https://economy.roblox.com/v1/purchases/products/{product_id}",
                json={"expectedCurrency": 1, "expectedPrice": 0, "expectedSellerId": 1},
                headers={"X-CSRF-TOKEN": csrf_token},
            )

            if req.status_code == 429:
                cprint("red", "Rate limited. Trying...")
                time.sleep(random.uniform(5, 10))
                continue

            res = req.json()
            if "reason" in res and res.get("reason") == "AlreadyOwned":
                cprint("yellow", f"You already have: {name}.")
                return

            cprint("green", f"Bundle purchased successfully: {name}")
            return

    except requests.exceptions.RequestException:
        cprint("red", "A conexão foi perdida. Reconectando...")
        return


def main() -> None:
    free_items = fetch_items()
    for name, product_id in free_items.items():
        purchase(name, product_id)


main()
