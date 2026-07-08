MOBBEX_ODOO_VERSION = '1.0'

MOBBEX_CHECKOUT = 'https://api.mobbex.com/p/checkout'

RETURN_URL = '/payment/mobbex/return'
WEBHOOK_URL = '/payment/mobbex/webhook'

SUPPORTED_COUNTRIES = {
    'AR',
    'CHL',
    'URY',
    'MEX',
    'COL',
    'ESP',
}

SUPPORTED_CURRENCIES = {
    'ARS',  # Argentina - Argentine Peso
    'CLP',  # Chile - Chilean Peso
    'UYU',  # Uruguay - Uruguayan Peso
    'MXN',  # Mexico - Mexican Peso
    'COP',  # Colombia - Colombian Peso
    'EUR',  # Spain - Euro
    'USD',  # United States - US Dollar
}

DEFAULT_PAYMENT_METHOD_CODES = {
    'mobbex',
}

TRANSACTION_STATUS_MAPPING = {
    'pending': [0, 1, 2, 3, 100, 201],
    'approved': [200],
    'canceled': [401, 402, 601, 602, 603, 610],
}
