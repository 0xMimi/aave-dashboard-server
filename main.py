from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3


from modules.fetcher import (
    get_aave_data,
    get_activity,
    get_borrow_positions,
    get_lend_positions,
    get_lend_positions_for_revenue,
    get_borrow_positions_for_cost,
    get_borrow_cost,
    get_lend_revenue,
)

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/account")
def get_account(version, market, address):
    if not Web3.isAddress(address):
        return {"error": "invalid address"}

    data = get_aave_data(address, version, market)

    if data == None:
        return {"data": None}
    (
        deposits,
        borrows,
        repays,
        withdrawals,
        liquidations,
        lend_pos,
        borrow_pos,
    ) = data.values()

    activity = get_activity((deposits, borrows, repays, withdrawals, liquidations))
    lend_positions = get_lend_positions(lend_pos)
    borrow_positions = get_borrow_positions(borrow_pos, address, version, market)

    lend_revenue = 0
    lend_positions_for_revenue = get_lend_positions_for_revenue(
        address, version, market
    )
    for lend in lend_positions_for_revenue:
        revenue = get_lend_revenue(address, lend, version, market)
        lend_revenue += revenue

    borrow_cost = 0
    borrow_positions_for_cost = get_borrow_positions_for_cost(address, version, market)
    for borrow in borrow_positions_for_cost:
        cost = get_borrow_cost(address, borrow, version, market)
        borrow_cost += cost

    return {
        "data": {
            "activity": activity,
            "lend_positions": lend_positions,
            "borrow_positions": borrow_positions,
            "lend_revenue": lend_revenue,
            "borrow_cost": borrow_cost,
        }
    }
