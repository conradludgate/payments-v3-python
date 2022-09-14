from datetime import datetime
from enum import Enum
from typing import Any, Dict, Union, Literal, Optional, TypedDict

class SortCodeAccountNumber(TypedDict):
    type: Literal["sort_code_account_number"]
    sort_code: str
    account_number: str

class Iban(TypedDict):
    type: Literal["iban"]
    iban: str

AccountIdentifier = Union[SortCodeAccountNumber, Iban]

class ExternalAccount(TypedDict):
    type: Literal["external_account"]
    account_holder_name: str
    account_identifier: AccountIdentifier

class MerchantAccount(TypedDict):
    type: Literal["merchant_account"]
    merchant_account_id: str
    account_holder_name: Optional[str]

Beneficiary = Union[ExternalAccount, MerchantAccount]

class Currency(str, Enum):
    GBP = "GBP"
    EUR = "EUR"

class MandateType(str, Enum):
    sweeping = "sweeping"
    commercial = "commercial"

class Remitter(TypedDict):
    account_holder_name: str
    account_identifier: AccountIdentifier

class MandateProviderPreselected(TypedDict, total=False):
    type: Literal["preselected"]
    provider_id: str
    remitter: Optional[Remitter]

class MandateProviderUserSelected(TypedDict):
    type: Literal["user_selected"]

MandateProviderSelection = Union[MandateProviderPreselected, MandateProviderUserSelected]

class Mandate(TypedDict):
    type: MandateType
    provider_selection: MandateProviderSelection
    beneficiary: Beneficiary

class User(TypedDict, total=False):
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]

class PeriodAlignment(str, Enum):
    consent = "consent"
    calendar = "calendar"

class PeriodicLimit(TypedDict):
    maximum_amount: int
    period_alignment: PeriodAlignment

class PeriodicLimits(TypedDict, total=False):
    day: Optional[PeriodicLimit]
    week: Optional[PeriodicLimit]
    fortnight: Optional[PeriodicLimit]
    month: Optional[PeriodicLimit]
    half_year: Optional[PeriodicLimit]
    year: Optional[PeriodicLimit]

class Constraints(TypedDict):
    valid_from: Optional[datetime]
    valid_to: Optional[datetime]
    maximum_individual_amount: int
    periodic_limits: PeriodicLimits

class CreateMandateRequest(TypedDict):
    mandate: Mandate
    currency: Currency
    user: User
    constraints: Constraints
