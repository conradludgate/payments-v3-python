# std imports
from datetime import datetime, timedelta

from sdk.models import Currency, MandateType, PeriodAlignment
from sdk.mandate import create_mandate, get_mandate

if __name__ == "__main__":
    mandate = create_mandate({
        'mandate': {
            'type': MandateType.sweeping,
            'provider_selection': {
                'type': 'preselected',
                'provider_id': 'ob-natwest-vrp-sandbox'
            },
            'beneficiary': {
                'type': 'external_account',
                'account_holder_name': 'Floob',
                'account_identifier': {
                    'type': "sort_code_account_number",
                    'sort_code': "123456",
                    'account_number': "76543210",
                }
            }
        },
        'currency': Currency.GBP,
        'user': {
            "id": "df69744a-fe8f-4acc-8b89-ba863297234c",
            "email": "conrad@lud.co",
            "name": "Co lu",
        },
        "constraints": {
            "valid_from": datetime.utcnow(),
            "valid_to": datetime.utcnow() + timedelta(days=1),
            "maximum_individual_amount": 5000,
            "periodic_limits": {
                "month": {
                    "maximum_amount": 10000,
                    "period_alignment": PeriodAlignment.consent
                }
            }
        }
    })
    print(mandate)
    print(get_mandate(mandate["id"]))
