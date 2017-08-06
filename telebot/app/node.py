import os
import uuid
from collections import defaultdict

import ethereum
from ethereum.tools import tester as t
from ethereum.utils import sha3, privtoaddr, to_string
from ethereum.pow import chain as pow_chain
from ethereum.config import config_spurious, default_config, config_homestead, config_tangerine, config_spurious, \
    config_metropolis, Env
from ethereum.utils import sha3, privtoaddr, to_string
from ethereum.genesis_helpers import mk_basic_state

from . import settings


_ETHER_COST = 10 ** 18


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Chain(t.Chain, metaclass=Singleton):
    def __init__(self, bank_address):
        alloc = {bank_address: {'balance': _ETHER_COST * 10000}}
        t.Chain.__init__(self, alloc=alloc)


class ChainUser:
    def __init__(self, key=None):
        if key is None:
            self.address, self.key = self._create_pair()
        else:
            self.address, self.key = privtoaddr(key), key

        self.chain = Chain(self.address)

    def __hash__(self):
        return hash(self.address)

    def _create_pair(self):
        uuid_str = str(uuid.uuid4())
        key = sha3(uuid_str)
        address = privtoaddr(key)

        return address, key

    def get_keypair(self):
        return self.address, self.key

    def make_transaction(self, address, money):
        eth = self.money_to_eth(money)
        self.chain.tx(self.key, address, eth)
        self.chain.mine()

    def money_to_eth(self, money):
        return int(money * _ETHER_COST)

    def eth_to_money(self, eth):
        return eth / _ETHER_COST

    def get_balance(self):
        return self.eth_to_money(self.chain.head_state.get_balance(self.address))


class Bank(ChainUser, metaclass=Singleton):
    def __init__(self):
        super().__init__(key=b'\xb7\x8f&A\xa6z<\xe6T f\xf1?_s?c\xcd\xa1x\xacW|\xe5\xe0.\xc4\xd1@\x9d\x91\xe7')
        self._not_confirmed_transactions = defaultdict(set)
        self._client_to_contract = {}

    def create_wallet(self, client):
        contract = self.chain.contract(
            self._get_contract_code(settings.CLIENT_BANK_WALLET_CONTRACT),
            args=[client.address, self.address],
            language='solidity'
        )
        self.make_transaction(contract.address, 100)
        self.chain.mine()
        self._client_to_contract[client.address] = contract
        return contract

    def make_wallet_transaction(self, client_from, client_to, money):
        id_ = client_from.wallet.submitTransaction(
            client_to.wallet.address, self.money_to_eth(money), '', sender=client_from.key
        )
        self._not_confirmed_transactions[client_from.address].add(id_)

    def get_not_confirmed_transactions(self):
        return self._not_confirmed_transactions

    def confirm_wallet_transaction(self, address, id_):
        self._client_to_contract[address].confirmTransaction(id_, sender=self.key)
        self._not_confirmed_transactions[address].remove(id_)
        if len(self._not_confirmed_transactions[address]) == 0:
            del self._not_confirmed_transactions[address]
        self.chain.mine()

    def _get_contract_code(self, contract_file):
        return open(os.path.join(settings.CONTRACTS_FOLDER, contract_file)).read()


class Client(ChainUser):
    def __init__(self):
        super().__init__()
        self._bank = Bank()
        self.wallet = self._bank.create_wallet(self)

        self._not_confirmed_transactions = set()

    def send_money(self, client, money):
        self._bank.make_wallet_transaction(self, client, money)

    def get_wallet_balance(self):
        return self.eth_to_money(self.chain.head_state.get_balance(self.wallet.address))
