# Mobbex for Odoo

This plugin provides integration between Odoo and Mobbex Payment Solution. With the provided solution you will be able to get your store integrated with our payment gateway in a matter of seconds. Just install it, enable the plugin and provide your credentials. That's all!!! You can get paid now ;).

## Compatibility

Compatible with **Odoo 19.0** only.

## Requirements

- Odoo 19.0 (Community or Enterprise, on-premise or Odoo.sh).
- Odoo modules: `payment` and `website_sale` (eCommerce).
- A public HTTPS URL for your Odoo instance, so Mobbex can reach the webhook.
- Mobbex credentials: **API Key** and **Access Token** (available in the Mobbex developer portal).

## Installation

Choose one of the following options.

### Option 1: Git clone

1. Clone the repository using the `19.0` branch:
   ```bash
   git clone -b 19.0 https://github.com/mobbexco/odoo-mobbex-projects.git
   ```
2. Make the module available to Odoo, using **one** of these approaches:
   - Copy (or symlink) the `payment_mobbex_checkout` folder into your addons directory:
     ```bash
     cp -r odoo-mobbex-projects/payment_mobbex_checkout /path/to/odoo/addons/
     ```
   - Or add the cloned repository folder to `addons_path` in your `odoo.conf`:
     ```ini
     addons_path = /path/to/odoo/addons,/path/to/odoo-mobbex-projects
     ```
3. Restart Odoo.
4. In the Odoo backend, enable **Developer Mode**, go to **Apps → Update Apps List**, search for **Mobbex Checkout** and click **Install**.

### Option 2: ZIP file

1. Download `payment_mobbex_checkout-<version>.zip` from the [Releases](https://github.com/mobbexco/odoo-mobbex-projects/releases) section of the repository.
2. Extract it into your addons directory. The result must be:
   ```
   /path/to/odoo/addons/payment_mobbex_checkout/__manifest__.py
   ```
3. Restart Odoo.
4. In the Odoo backend, enable **Developer Mode**, go to **Apps → Update Apps List**, search for **Mobbex Checkout** and click **Install**.

### Option 3: Command line

Once the module files are in your addons path (see Option 1 or 2), you can install it without using the web interface:

```bash
odoo -c /etc/odoo/odoo.conf -d <database> -i payment_mobbex_checkout --stop-after-init
```

If the module folder is not in the `addons_path` of your configuration file, pass it explicitly:

```bash
odoo -d <database> --addons-path=/path/to/odoo/addons,/path/to/custom/addons -i payment_mobbex_checkout --stop-after-init
```

When running Odoo with Docker:

```bash
docker exec -it <odoo_container> odoo -d <database> -i payment_mobbex_checkout --stop-after-init
docker restart <odoo_container>
```

### General notes

These apply to every installation option:

- **Folder name**: the module folder must be named exactly `payment_mobbex_checkout`. Folders such as `odoo-mobbex-projects-19.0` (the default name of a GitHub ZIP download) will not be recognized by Odoo.
- **Addons path**: `addons_path` must point to the directory that *contains* the module folder, not to the module folder itself.
- **Restart**: always restart the Odoo service after adding or updating the module files.
- **Permissions**: the system user running Odoo needs read access to the module folder.
- **Dependencies**: the eCommerce app (`website_sale`) must be installed.
- **Apps → Import Module is not supported**: uploading a ZIP from the Odoo interface only works for data modules without Python code, so it can't be used to install this module.
- **Odoo Online (SaaS) is not supported**, because it doesn't allow custom Python modules. Use an on-premise installation or Odoo.sh.
- **Webhook**: Mobbex must be able to reach `https://<your-domain>/payment/mobbex/webhook`. For local development, expose your instance with a tunnel such as ngrok.

## Configuration

1. Go to **Website → Configuration → Payment Providers** (or **Invoicing → Configuration → Payment Providers**).
2. Open **Mobbex**.
3. In the **Credentials** tab, enter your **API Key** and **Access Token**.
4. Set the **State**:
   - **Test Mode** for sandbox payments.
   - **Enabled** for production.
5. Optionally, enable **Modo Debug** in the **Configuration** tab to get detailed logs. Don't use it in production, because it may expose sensitive information.
6. Publish the provider and save.

## Updating

1. Replace the `payment_mobbex_checkout` folder with the new version (or run `git pull` on the `19.0` branch).
2. Restart Odoo.
3. Upgrade the module, either from **Apps → Mobbex Checkout → Upgrade** or from the command line:
   ```bash
   odoo -c /etc/odoo/odoo.conf -d <database> -u payment_mobbex_checkout --stop-after-init
   ```

## Changelog

### 19.0.1.0.0
- First release for Odoo 19 (breaking: requires Odoo 19.0).
- Remade provider and transaction models.
- Added security checks on redirects.
- Return renewal.
- Added webhook process.
- Added debug configuration for development logs.
- Several code improvements.

### 1.0.2
- Fix checkout return redirect after payment.

### 1.0.1
- Added DNI field in checkout.
- Test Mode.
- Fix Currency.
- Fix Description Images.

### 1.0.0
- Initial release.
