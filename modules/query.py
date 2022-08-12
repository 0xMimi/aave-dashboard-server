query_v2 = """
query($id: ID!) {
	account(id: $id) {
		deposits {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}
		borrows {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}
		repays {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}
		withdraws {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}
		liquidations {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}

		lend_positions: positions(where: { timestampClosed: null, side: LENDER }) {
			market {
				name
				inputToken {
					name
					symbol
					decimals
				}
				inputTokenPriceUSD
				rates {
					rate
					side
					type
				}
			}
			balance
			isCollateral
		}
		borrow_positions: positions(where: { timestampClosed: null, side: BORROWER }) {
			market {
				name
				inputToken {
                    id
					name
					symbol
					decimals
				}
				inputTokenPriceUSD
				rates {
					rate
					side
					type
				}
			}
			balance
		}
	}
}

"""

query_v3 = """
query($id: ID!) {
	account(id: $id) {
		deposits {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}
		borrows {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}
		repays {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}
		withdraws {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}
		liquidations {
			hash
			timestamp
			asset {
				name
				symbol
				decimals
			}
			amount
			amountUSD
			market {
				name
			}
		}

		lend_positions: positions(where: { timestampClosed: null, side: LENDER }) {
			market {
				name
				inputToken {
					name
					symbol
					decimals
				}
				inputTokenPriceUSD
				rates {
					rate
					side
					type
				}
			}
			balance
			isCollateral
		}
		borrow_positions: openPositions(where: { side: BORROWER }) {
			market {
				name
				inputToken {
					name
					symbol
					decimals
				}
				inputTokenPriceUSD
				rates {
					rate
					side
					type
				}
			}
			balance
			_variableDebtBalance
			_stableDebtBalance
		}
	}
}

"""

query_lend_revenue = """
query($id: ID!) {
  account(id: $id) {
    positions(where: {side:LENDER}) {
      market {
        name
        inputToken {
          id
          symbol
          decimals
        }
      }
      balance
      deposits {
        timestamp
        amount
        amountUSD
      }
      withdraws {
        timestamp
        amount
        amountUSD
      }
      snapshots {
        timestamp
        balance
      }
    }
  }
}"""

query_borrow_cost = """
query($id: ID!) {
  account(id: $id) {
    positions(where: {side:BORROWER}) {
      market {
        name
        inputToken {
          id
          symbol
          decimals
        }
      }
      balance
      borrows {
        timestamp
        amount
        amountUSD
      }
      repays {
        timestamp
        amount
        amountUSD
      }
      snapshots {
        timestamp
        balance
      }
    }
  }
}"""

queries = {
    "v2": query_v2,
    "v3": query_v3,
    "lend_revenue": query_lend_revenue,
    "borrow_cost": query_borrow_cost,
}
