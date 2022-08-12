from web3 import Web3

blockchains = {
    "arbitrum": {
        "rpc": "https://arb1.arbitrum.io/rpc",
        "oracle": "0xb56c2F0B653B2e0b10C9b928C8580Ac5Df02C7C7",
        "contracts": [
            {
                "version": "v3",
                "contract_address": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
            },
        ],
    },
    "avalanche": {
        "rpc": "https://api.avax.network/ext/bc/C/rpc",
        "oracle": "0xEBd36016B3eD09D4693Ed4251c67Bd858c3c7C9C",
        "contracts": [
            {
                "version": "v2",
                "contract_address": "0x65285E9dfab318f57051ab2b139ccCf232945451",
            },
            {
                "version": "v3",
                "contract_address": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
            },
        ],
    },
    "ethereum": {
        "rpc": "https://eth-rpc.gateway.pokt.network",
        "oracle": "0xA50ba011c48153De246E5192C8f9258A2ba79Ca9",
        "contracts": [
            {
                "version": "v2",
                "contract_address": "0x057835Ad21a177dbdd3090bB1CAE03EaCF78Fc6d",
            }
        ],
    },
    "fantom": {
        "rpc": "https://rpc.ankr.com/fantom/",
        "oracle": "0xfd6f3c1845604C8AE6c6E402ad17fb9885160754",
        "contracts": [
            {
                "version": "v3",
                "contract_address": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
            }
        ],
    },
    "harmony": {
        "rpc": "https://api.harmony.one",
        "oracle": "0x3C90887Ede8D65ccb2777A5d577beAb2548280AD",
        "contracts": [
            {
                "version": "v3",
                "contract_address": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
            }
        ],
    },
    "optimism": {
        "rpc": "https://mainnet.optimism.io",
        "oracle": "0xD81eb3728a631871a7eBBaD631b5f424909f0c77",
        "contracts": [
            {
                "version": "v3",
                "contract_address": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
            }
        ],
    },
    "polygon": {
        "rpc": "https://polygon-rpc.com",
        "oracle": "0xb023e699F5a33916Ea823A16485e259257cA8Bd1",
        "contracts": [
            {
                "version": "v2",
                "contract_address": "0x7551b5D2763519d4e37e8B81929D336De671d46d",
            },
            {
                "version": "v3",
                "contract_address": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654",
            },
        ],
    },
}

data_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "address", "name": "user", "type": "address"},
        ],
        "name": "getUserReserveData",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "currentATokenBalance",
                "type": "uint256",
            },
            {"internalType": "uint256", "name": "currentStableDebt", "type": "uint256"},
            {
                "internalType": "uint256",
                "name": "currentVariableDebt",
                "type": "uint256",
            },
            {
                "internalType": "uint256",
                "name": "principalStableDebt",
                "type": "uint256",
            },
            {
                "internalType": "uint256",
                "name": "scaledVariableDebt",
                "type": "uint256",
            },
            {"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidityRate", "type": "uint256"},
            {
                "internalType": "uint40",
                "name": "stableRateLastUpdated",
                "type": "uint40",
            },
            {
                "internalType": "bool",
                "name": "usageAsCollateralEnabled",
                "type": "bool",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

oracle_abi = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getAssetPrice",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

eth_oracle_abi = [
    {
        "inputs": [],
        "name": "latestAnswer",
        "outputs": [{"internalType": "int256", "name": "", "type": "int256"}],
        "stateMutability": "view",
        "type": "function",
    }
]


class Provider:
    def __init__(self, chain, rpc_url, oracle, contract_address):
        self.chain = chain
        provider = Web3.HTTPProvider(rpc_url)
        self.w3 = Web3(provider)
        self.oracle = self.w3.eth.contract(
            address=Web3.toChecksumAddress(oracle), abi=oracle_abi
        )
        self.data_contract = self.w3.eth.contract(
            address=Web3.toChecksumAddress(contract_address), abi=data_abi
        )
        if chain == "ethereum":  # Chainlink ETH/USD oracle
            self.eth_oracle = self.w3.eth.contract(
                address=Web3.toChecksumAddress(
                    "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
                ),
                abi=eth_oracle_abi,
            )

    def get_user_reserve_data(self, asset, address):
        result = self.data_contract.functions.getUserReserveData(
            Web3.toChecksumAddress(asset),
            Web3.toChecksumAddress(address),
        ).call()

        return result

    def get_asset_price(self, asset):
        try:
            result = (
                self.oracle.functions.getAssetPrice(
                    Web3.toChecksumAddress(asset)
                ).call()
                / 10**8
            )
            if self.chain == "ethereum":
                eth_price = (
                    self.eth_oracle.functions.latestAnswer().call() / 10**8
                )  # Dollar/Eth
                result /= 10**10
                result *= eth_price
        except:
            return 0
        return result  # Dollar/Unit


providers = {}

for chain in blockchains:
    rpc = blockchains[chain]["rpc"]
    oracle = blockchains[chain]["oracle"]
    for x in blockchains[chain]["contracts"]:
        version = x["version"]
        address = x["contract_address"]
        provider = Provider(chain, rpc, oracle, address)
        if version not in providers:
            providers[version] = {}

        providers[version][chain] = provider
