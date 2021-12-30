from django.db import models
from django.core.exceptions import ValidationError
from web3 import Web3
import base58, hashlib, binascii
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone

from django_web3.managers import Web3UserManager

class WalletField(models.CharField):

    description = "A wallet of type"

    def __init__(self, network, *args, **kwargs):
        self.network = network
        if isinstance(self.network, str):
            if self.network == "all":
                pass
            networks = [self.network]
        networks = self.network
        if isinstance(networks, list):
            for network in networks:
                if network not in ["eth", "btc", "ltc"]:
                    raise Exception("The network must be one of the following: 'eth', 'btn', 'ltc', 'all'")

        kwargs['max_length'] = 104
        kwargs['validators'] = [self.validateWallet]
        super().__init__(*args, **kwargs)


    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Only include kwarg if it's not the default
        if self.network != ",":
            kwargs['network'] = self.network
        return name, path, args, kwargs

    def validateEthWallet(self, wallet):
        if not Web3.isAddress(wallet):
            return False
        else:
            return True

    def validateBtcWallet(self, wallet):
        base58Decoder = base58.b58decode(wallet).hex()
        prefixAndHash = base58Decoder[:len(base58Decoder) - 8]
        checksum = base58Decoder[len(base58Decoder) - 8:]
        hash = prefixAndHash
        for x in range(1, 3):
            hash = hashlib.sha256(binascii.unhexlify(hash)).hexdigest()
        if checksum != hash[:8]:
            return False

        return True

    def validateWallet(self, value):
        # validate ethereum addresses
        if self.network == "eth":
            if not self.validateEthWallet(value):
                raise ValidationError("This address is invalid")

        # validate btc addresses
        elif self.network == "btc":
            if not self.validateBtcWallet(value):
                raise ValidationError("This address is invalid")

        # wildcard checker
        elif self.network == "all":
            if not any([self.validateBtcWallet(value), self.validateEthWallet(value)]):
                raise ValidationError("This address is invalid")

class Web3User(AbstractBaseUser, PermissionsMixin):
    wallet = WalletField("eth", unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'wallet'
    REQUIRED_FIELDS = []

    objects = Web3UserManager()

    def __str__(self):
        return self.wallet
