# Mobbex Integration for Odoo

This repository contains the source code for integrating the Mobbex payment gateway into an Odoo system. This integration allows Odoo users to process payments using Mobbex, a popular payment provider from Argentina.

## Features

- **Payment Provider Integration:** Adds Mobbex as a payment provider in the Odoo system.
- **Integrates Mobbex as a Payment Method**
- **Merchant Configuration:** Supports configuration of Mobbex Api Key and Access Token.
- **Payment Processing:** Handles payment transactions securely with Mobbex.
- **Webhook Handling:** Processes webhooks from Mobbex to update transaction status.
- **Return URL Handling:** Redirects users to the payment status page after a transaction is completed.

## Files Overview

### `payment_provider.py`

This file extends the Odoo `payment.provider` model to include Mobbex-specific configurations and functionality.

- **Mobbex Configuration Fields:** Adds fields for `Mobbex_merchant_id`, `Mobbex_access_code`, and `Mobbex_secret_key`.
- **Payment URL Generation:** Generates the Mobbex payment URL with secure hash verification.
- **Supported Currencies:** Ensures that only supported currencies are used with Mobbex.
- **Compatibility Checks:** Filters the providers based on currency support and other criteria.

### `main.py`

This file contains the main controller (`MobbexController`) responsible for handling the interactions with Mobbex.

- **Return URL Handling:** 
  - Route: `/payment/mobbex/return`
  - Handles the redirection of users after a payment, usually redirecting to a status page.
- **Webhook Handling:** 
  - Route: `/payment/mobbex/webhook`
  - Processes webhooks from Mobbex and updates the transaction status based on the response.
  - Once implemented, it will listen for notifications from Mobbex to automatically update transaction statuses without user intervention.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/mobbexco/odoo-mobbex-projects.git
   ```
2. **Place the Module in Odoo Addons Directory:**
   Move the cloned repository to your Odoo addons directory.
3. **Install the Module:**
    In your Odoo backend, navigate to the Apps menu and install the Mobbex integration module.
4. **Configure Mobbex Settings:**
  - Go to the Payment Providers section in Odoo.
  - Select Mobbex and enter your api-key and access-token
  - Save the settings.
## Contributing
Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.
## License
AGPL
