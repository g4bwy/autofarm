#!/usr/bin/env python3

import sys
import time
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware

try:
    my_addr = sys.argv[1]
except:
    print("Usage: %s <BEP20 wallet address>" % sys.argv[0])
    sys.exit(-1)

w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.default_account = my_addr

# XXX: use bscscan api to retrieve contract ABIs

autofarm_v2_addr = '0x0895196562C7868C5Be92459FaE7f877ED450452'
autofarm_v2_abi = json.load(open('./autofarm_v2_abi.json'))
autofarm_v2 = w3.eth.contract(autofarm_v2_addr, abi=autofarm_v2_abi['result'])

wbnb_auto_lp_vault_addr = '0x65168C89a16FBEd4e2e418D5245FF626Bd66874b'
wbnb_auto_lp_vault_abi = json.load(open('./wbnb_auto_lp_vault_abi.json'))
wbnb_auto_lp_vault = w3.eth.contract(wbnb_auto_lp_vault_addr, abi=wbnb_auto_lp_vault_abi['result'])

auto_token_addr = wbnb_auto_lp_vault.functions.AUTOAddress().call()
auto_token_abi = json.load(open('./auto_token_abi.json'))
auto_token = w3.eth.contract(auto_token_addr, abi=auto_token_abi['result'])
auto_decimals = 10 ** (auto_token.functions.decimals().call())

poolInfo = ["want", "allocPoint", "lastRewardBlock", "accAUTOPerShare", "strat"]
userInfo = ["shares", "rewardDebt"]

for i in range(0, autofarm_v2.functions.poolLength().call()):
    info = autofarm_v2.functions.poolInfo(i).call()
    if info[4] == wbnb_auto_lp_vault_addr:
        wbnb_auto_lp_vault_pid = i
        break

while True:
    wbnb_auto_lp_vault_info = dict(zip(poolInfo, autofarm_v2.functions.poolInfo(wbnb_auto_lp_vault_pid).call()))

    print("wbnb_auto_lp_vault: pid=%d, info=%s" % (wbnb_auto_lp_vault_pid, wbnb_auto_lp_vault_info))
    my_info = dict(zip(userInfo, autofarm_v2.functions.userInfo(wbnb_auto_lp_vault_pid, my_addr).call()))
    print(my_info)

    amount = (my_info['shares'] / wbnb_auto_lp_vault.functions.sharesTotal().call() * wbnb_auto_lp_vault.functions.wantLockedTotal().call()) / float(auto_decimals)
    print("AUTO amount: %f" % amount)

    pending = autofarm_v2.functions.pendingAUTO(wbnb_auto_lp_vault_pid, my_addr).call() / float(auto_decimals)
    print("pending AUTO reward: %f" % pending)

    time.sleep(60)
