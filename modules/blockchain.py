import requests, base58, json
import toml

config = toml.load("config.toml")

def build_coingecko_map():
    url = "https://api.coingecko.com/api/v3/coins/list"
    coins = requests.get(url).json()
    return {c["symbol"].upper(): c["id"] for c in coins}

COINGECKO_MAP = build_coingecko_map()

def get_gecko_id(symbol, contract):
    url = f"https://api.coingecko.com/api/v3/coins/tron/contract/{contract}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json().get("id")
    return COINGECKO_MAP.get(symbol.upper(), symbol.lower())

def read_tron(address: str):
    API_KEY = config["apikey"]["trongrid"]
    BASE_URL = "https://api.trongrid.io"
    HEADERS = {
        "Content-Type": "application/json",
        "TRON-PRO-API-KEY": API_KEY, 
    }

    def address_to_parameter(addr: str) -> str:
        raw = base58.b58decode_check(addr).hex()[2:]
        return raw.rjust(64, "0")

    def call_contract(contract: str, func: str, param: str = ""):
        payload = {
            "contract_address": contract,
            "function_selector": func,
            "owner_address": address,
            "visible": True,
        }
        if param:
            payload["parameter"] = param
        r = requests.post(f"{BASE_URL}/wallet/triggerconstantcontract",
                          headers=HEADERS, json=payload).json()
        if "constant_result" in r:
            return int(r["constant_result"][0], 16)
        return None

    assets = []

    acc = requests.post(f"{BASE_URL}/wallet/getaccount",
                        headers=HEADERS,
                        json={"address": address, "visible": True}).json()
    trx_balance = acc.get("balance", 0) / 1_000_000
    if trx_balance > 0:
        assets.append({"name": "tron", "balance": trx_balance})

    resp = requests.get(
        f"{BASE_URL}/v1/accounts/{address}/transactions/trc20",
        headers=HEADERS, params={"limit": 50}
    ).json()

    seen_contracts = set()
    if "data" in resp:
        for tx in resp["data"]:
            seen_contracts.add(tx["token_info"]["address"])

    param = address_to_parameter(address)
    for contract in seen_contracts:
        bal_raw = call_contract(contract, "balanceOf(address)", param)
        if not bal_raw:
            continue

        decimals = call_contract(contract, "decimals()") or 6
        human = bal_raw / (10 ** decimals)
        if human > 0:
            symbol = "UNKNOWN"
            for tx in resp.get("data", []):
                if tx["token_info"]["address"] == contract:
                    symbol = tx["token_info"].get("symbol", "UNKNOWN")
                    break

            gecko_id = get_gecko_id(symbol, contract)
            assets.append({"name": gecko_id, "balance": human})

    return assets

