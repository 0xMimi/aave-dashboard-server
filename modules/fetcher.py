import numpy as np
import requests

from modules.query import queries
from modules.providers import providers


def to_readable(value, decimals) -> float:
    return float(value) / 10 ** int(decimals)


def get_user_reserve_data():
    return


def get_aave_data(address, version, market):
    params = {"id": address.lower()}
    response = requests.post(
        f"https://api.thegraph.com/subgraphs/name/messari/aave-{version}-{market}",
        json={"query": queries[version], "variables": params},
    )
    data = response.json()
    if "errors" in data:
        return {"data": {"account": None}}
    return data["data"]["account"]


def get_activity(event_groups):
    activity = []
    event_types = ["deposit", "borrow", "repay", "withdraw", "liquidation"]
    for i, events in enumerate(event_groups):
        activity_type = event_types[i]
        for event in events:
            asset = event["asset"]
            name = asset["name"]
            symbol = asset["symbol"]
            decimals = asset["decimals"]
            amount_raw = event["amount"]
            amount = to_readable(amount_raw, decimals)

            data = {
                "timestamp": event["timestamp"],
                "txhash": event["hash"],
                "action": activity_type,
                "name": name,
                "symbol": symbol,
                "amount": amount,
                "value": float(event["amountUSD"]),
            }
            activity.append(data)

    activity.sort(key=lambda x: x["timestamp"], reverse=True)

    return activity


def get_lend_positions(lend_positions):
    positions = []

    total_balance = 0
    apys = []
    weights = []

    for position in lend_positions:
        market = position["market"]
        token = market["inputToken"]
        price = market["inputTokenPriceUSD"]
        name = token["name"]
        symbol = token["symbol"]
        decimals = token["decimals"]

        apy = float(
            [rate["rate"] for rate in market["rates"] if rate["side"] == "LENDER"][0]
        )

        amount_raw = position["balance"]
        amount = to_readable(amount_raw, decimals)
        value = amount * float(price)

        lend = {
            "name": name,
            "symbol": symbol,
            "amount": amount,
            "value": value,
            "apy": apy,
            "is_collateral": position["isCollateral"],
        }

        total_balance += value
        apys.append(apy)
        weights.append(value)
        positions.append(lend)

    if len(apys) == 0:
        average_apy = 0
    else:
        average_apy = np.average(apys, weights=weights)
    data = {
        "balance": total_balance,
        "apy": average_apy,
        "positions": positions,
    }

    return data


def get_borrow_positions(borrow_positions, address, version, blockchain):
    positions = []

    total_balance = 0
    apys = []
    weights = []

    for position in borrow_positions:
        market = position["market"]
        token = market["inputToken"]
        price = market["inputTokenPriceUSD"]
        name = token["name"]
        symbol = token["symbol"]
        decimals = token["decimals"]

        rates = [rate for rate in market["rates"] if rate["side"] == "BORROWER"]
        if version == "v2":
            token_address = token["id"]
            variable_debt = providers[version][blockchain].get_user_reserve_data(
                token_address, address
            )[2]
            balances = (0, variable_debt)
        elif version == "v3":
            balances = (
                position["_stableDebtBalance"],
                position["_variableDebtBalance"],
            )

        modes = ("STABLE", "VARIABLE")

        for i in range(2):
            if int(balances[i]) == 0:
                continue
            mode = modes[i]
            amount_raw = balances[i]
            amount = to_readable(amount_raw, decimals)
            value = amount * float(price)
            apy = float([r["rate"] for r in rates if r["type"] == modes[i]][0])

            borrow = {
                "name": name,
                "symbol": symbol,
                "amount": amount,
                "value": value,
                "apy": apy,
                "mode": mode,
            }

            total_balance += value
            apys.append(apy)
            weights.append(value)
            positions.append(borrow)
    if len(apys) == 0:
        average_apy = 0
    else:
        average_apy = np.average(apys, weights=weights)
    data = {
        "balance": total_balance,
        "apy": average_apy,
        "positions": positions,
    }
    return data


def get_lend_positions_for_revenue(address, version, blockchain):
    params = {"id": address.lower()}
    response = requests.post(
        f"https://api.thegraph.com/subgraphs/name/messari/aave-{version}-{blockchain}",
        json={"query": queries["lend_revenue"], "variables": params},
    )
    data = response.json()
    return data["data"]["account"]["positions"]


def get_borrow_positions_for_cost(address, version, blockchain):
    params = {"id": address.lower()}
    response = requests.post(
        f"https://api.thegraph.com/subgraphs/name/messari/aave-{version}-{blockchain}",
        json={"query": queries["borrow_cost"], "variables": params},
    )
    data = response.json()
    return data["data"]["account"]["positions"]


def get_lend_revenue(address, position, version, blockchain):
    token = position["market"]["inputToken"]
    token_address = token["id"]
    decimals = token["decimals"]

    events = []
    for deposit in position["deposits"]:
        deposit["action"] = "deposit"
        events.append(deposit)

    for withdraw in position["withdraws"]:
        withdraw["action"] = "withdraw"
        events.append(withdraw)
    events.sort(key=lambda x: x["timestamp"])

    snapshots = position["snapshots"]
    snapshots.sort(key=lambda x: x["timestamp"])

    total_revenue = 0
    prev_balance = 0
    for event, snapshot in zip(events, snapshots):
        cur_balance = int(snapshot["balance"])
        if event["action"] == "withdraw":
            amount = int(event["amount"])
            value = float(event["amountUSD"])
            price = value / amount  # Dollars/Wei
            balance_before_withdraw = amount + cur_balance
            revenue = (balance_before_withdraw - prev_balance) * price
            total_revenue += revenue

        prev_balance = cur_balance
    if prev_balance != 0:  # There is remaining deposit that is accruing interest
        provider = providers[version][blockchain]
        latest_balance = provider.get_user_reserve_data(token_address, address)[0]
        # If 0, aToken were removed by other means than withdrawal, ignore this case
        if latest_balance != 0:
            accrued_amount = (latest_balance - prev_balance) / 10**decimals
            latest_price = provider.get_asset_price(token_address)
            accrued_value = accrued_amount * latest_price
            total_revenue += accrued_value

    return total_revenue


def get_borrow_cost(address, position, version, blockchain):
    token = position["market"]["inputToken"]
    token_address = token["id"]
    decimals = token["decimals"]

    events = []
    for borrow in position["borrows"]:
        borrow["action"] = "borrow"
        events.append(borrow)

    for repay in position["repays"]:
        repay["action"] = "repay"
        events.append(repay)
    events.sort(key=lambda x: x["timestamp"])

    snapshots = position["snapshots"]
    snapshots.sort(key=lambda x: x["timestamp"])

    total_cost = 0
    prev_balance = 0
    for event, snapshot in zip(events, snapshots):
        cur_balance = int(snapshot["balance"])
        if event["action"] == "repay":
            amount = int(event["amount"])
            value = float(event["amountUSD"])
            price = value / amount
            balance_before_repay = amount + cur_balance
            cost = (balance_before_repay - prev_balance) * price
            total_cost += cost

        prev_balance = cur_balance
    if prev_balance != 0:  # There is remaining deposit that is accruing interest
        provider = providers[version][blockchain]
        latest_balance = sum(
            provider.get_user_reserve_data(token_address, address)[1:2]
        )
        # If 0, aToken were removed by other means than withdrawal, ignore this case
        if latest_balance != 0:
            accrued_amount = (latest_balance - prev_balance) / 10**decimals
            latest_price = provider.get_asset_price(token_address)
            accrued_cost = accrued_amount * latest_price
            total_cost += accrued_cost

    return total_cost
