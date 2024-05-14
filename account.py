import datetime
import json

DAY_IN_MS = 86400000

class Account():
    def __init__(self, jdata=None):
        self.accountNumber = None
        self.hashValue = None
        if jdata is not None:
            self.from_json(jdata)

    def to_json(self):
        d = {}
        for k in self.__dict__:
            d[k] = getattr(self, k)
        return d

    def from_json(self,j):
        for k in j:
            setattr(self, k, j[k])

class AccountList (object):
    def __init__(self, jdata=None, **kwargs):
        self.expiration_time = None
        self.accounts = []
        self._by_account = {}
        self._by_hash = {}
        try:
            self.account_list_file = kwargs['account_list_file']
        except KeyError:
            self.account_list_file = "account_list.json"
        if jdata is not None:
            self.from_json(j=jdata)

    def to_json(self):
        d = {}
        for k in self.__dict__:
            if k[0] == "_":
                continue
            elif k == "accounts":
                d[k] = []
                for a in getattr(self, k):
                    d[k].append(a.to_json())
            else:
                d[k] = getattr(self,k)
        return d


    def read_alfile(self, account_list_file=None):
        alfile = account_list_file
        if alfile is None:
            alfile = self.account_list_file
        try:
            with open(alfile, 'r') as alfh:
                al_json = json.load(alfh)
            for k in al_json:
                setattr(self, k, al_json[k])
        except FileNotFoundError:
            return None

    def build(self, account_list_file=None,
              jdata=None,
              client=None
    ):
        if jdata is not None:
            self.from_json(jdata)
        if self.read_alfile(account_list_file) is None:
            if jdata is not None:
                self.from_json(j)
                self.expiration_time = datetime.datetime.timestamp() + DAY_IN_MS





    def from_json(self, j):
        for entry in j:
            acc = Account(jdata=entry)
            self.add_account(acc)

    def add_account(self, a: Account):
        self.accounts.append(a)
        self._by_account[a.accountNumber] = a
        self._by_hash[a.hashValue] = a

    def save(self, account_list_file=None):

        target_file = self.account_list_file
        target_file = account_list_file
        if target_file is None:
            raise Exception("No account list file provided")
        acc_json = self.__to_json()
        with open(target_file, 'w') as alistfh:
            json.dump(acc_json, alistfh)

    def update(self, jdata=None, client=None):
        if jdata is not None:
            self.update_accounts(jdata)
            return
        if datetime.datetime.now() > self.expiration_time:
            if client is None:
                raise Exception("No client to update accounts")


        return


    def update_accounts(self, account_json: dict):
        for entry in account_json:
            a = Account(jdata=entry)
            self.add_account(a)
        self.expiration_time = datetime.datetime.now().timestamp() + (DAY_IN_MS)

    def check_expiration(self):
        if datetime.datetime.timestamp() > self.expiration_time:
            self.update_accounts()

    def __to_json(self):
        d = {}
        d['expiration'] = self.expiration_time
        for a in self.accounts:
            d.append(
                {
                    "accountNumber": a.accountnumber,
                    "hashValue": a.accounthash
                }
            )
        return d
    def get_account_numbers(self):
        return self._by_account.keys()

    def get_hash(self, account_number):
        try:
            hv = self._by_account[account_number].hashValue
            return hv
        except KeyError as ke:
            print(ke)