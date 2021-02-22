#!/usr/bin/env python3

import sys
import time
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware

try:
    my_addr = sys.argv[1]
    vault_addr = sys.argv[2]
except:
    print("Usage: %s <wallet address> <vault1 address> [<vault2 address> .. <vaultN address>]" % sys.argv[0])
    sys.exit(-1)

w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.default_account = my_addr

# XXX: use bscscan api to retrieve contract ABIs
autofarm_v2_abi = json.load(open('./autofarm_v2_abi.json'))
vault_abi = json.load(open('./autofarm_vault_abi.json'))
erc20_token_abi = json.load(open('./erc20_token_abi.json'))
pancake_token_abi = json.load(open('./pancake_token_abi.json'))

autofarm_v2_addr = '0x0895196562C7868C5Be92459FaE7f877ED450452'
autofarm_v2 = w3.eth.contract(autofarm_v2_addr, abi=autofarm_v2_abi['result'])

auto_token_addr = autofarm_v2.functions.AUTOv2().call()
auto_token = w3.eth.contract(auto_token_addr, abi=erc20_token_abi['result'])
auto_symbol = auto_token.functions.symbol().call()
auto_decimals = 10 ** (auto_token.functions.decimals().call())

vaults = []

for vault_addr in sys.argv[2:]:
    vault = w3.eth.contract(vault_addr, abi=vault_abi['result'])
    want_token_addr = vault.functions.wantAddress().call()

    try:
        want_token = w3.eth.contract(want_token_addr, abi=pancake_token_abi['result'])
        token0_addr = want_token.functions.token0().call()
        token0 = w3.eth.contract(token0_addr, abi=erc20_token_abi['result'])
        token1_addr = want_token.functions.token1().call()
        token1 = w3.eth.contract(token1_addr, abi=erc20_token_abi['result'])
        want_symbol = "%s-%s LP" % (token1.functions.symbol().call(), token0.functions.symbol().call())
    except:
        want_token = w3.eth.contract(want_token_addr, abi=erc20_token_abi['result'])
        want_symbol = want_token.functions.symbol().call()

    want_decimals = 10 ** (want_token.functions.decimals().call())

    for i in range(0, autofarm_v2.functions.poolLength().call()):
        info = autofarm_v2.functions.poolInfo(i).call()
        if info[4] == vault_addr:
            vault_pid = i
            break

    print("Monitoring vault %s (pid=%u)" % (want_symbol, vault_pid))
    vaults.append({'pid': vault_pid, 'want_symbol': want_symbol, 'want_decimals': want_decimals})

print("===================")

while True:
    total_pending = 0.0

    for vault in vaults:
        amount = autofarm_v2.functions.stakedWantTokens(vault['pid'], my_addr).call() / float(vault['want_decimals'])
        print("staked %s amount: %f" % (vault['want_symbol'], amount))

        pending = autofarm_v2.functions.pendingAUTO(vault['pid'], my_addr).call() / float(auto_decimals)
        print("pending %s reward: %f" % (auto_symbol, pending))
        total_pending += pending

    print("\ntotal pending %s reward: %f" % (auto_symbol, total_pending))
    print("===================")

    time.sleep(60)
