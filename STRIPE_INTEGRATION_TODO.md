# Stripe Checkout setup

## Values to Replace

There are no placeholder values in the existing Checkout Session call. The store builds `line_items` from its own product database with `price_data`, so no Stripe catalog or Stripe Price IDs are required. Shipping is configured inline in the Checkout Session; no Stripe Dashboard shipping product or rate is required.

**Files containing Checkout Session parameters:**
- [shop/views.py](shop/views.py)

| Field | Current Value | What to Set |
|---|---|---|
| `mode` | `payment` | Already correct for one-time product purchases. |
| `success_url` | Current site's `checkout_success` route with `{CHECKOUT_SESSION_ID}` | Already uses the app's real route. |
| `cancel_url` | Current site's `bag` route | Already uses the app's real route. |
| `line_items` | Product names, prices, and quantities from the Django product database | Already populated from the customer's validated bag; no Stripe Price IDs to replace. |
| `shipping_options` | One-time $10.00 USD flat shipping charge | Already set inline in `shop/views.py`. |

## Configured Parameters

**File containing these parameters:**
- [shop/views.py](shop/views.py)

| Parameter | Value |
|---|---|
| `ui_mode` | `hosted_page` (the running Stripe API rejected `hosted` and requested `hosted_page`) |
| `mode` | `payment` |
| `billing_address_collection` | `auto` |
| `shipping_address_collection` | Collect address for North America, South America, and Europe destinations |
| `shipping_options` | Flat $10.00 USD standard shipping per order |
| `phone_number_collection` | `{"enabled": false}` |
| `automatic_tax` | `{"enabled": false}` |
| `allow_promotion_codes` | `false` |
| `submit_type` | `auto` |
| `integration_identifier` | `hosted_web_0002` |
| `origin_context` | `web` |
| `success_url` | Current site's `checkout_success` route with the Checkout Session ID template |
| `cancel_url` | Current site's `bag` route |
| `line_items` | Dynamic `price_data` generated from the Django catalog and bag |

`payment_method_collection` is omitted because this is a one-time `payment` Session; the Checkout Studio setting applies only to subscription mode.

## Setup and next steps

1. Keep `STRIPE_SECRET_KEY` server-side only. For a test deployment, set a Stripe **test** secret key in Render's Environment settings. Do not commit `.env` or any Stripe key. Redeploy the branch Render is connected to after committing and pushing this change.
2. Test the deployed checkout using Stripe test mode, not a live key or a real card. Use the test card `4242 4242 4242 4242`, any future expiry date, and any CVC. Confirm the browser is redirected to Stripe Checkout and returns to the store after payment.
3. Verify order creation, webhook delivery, inventory updates, and customer email in the test environment before enabling live payments. Configure the matching test webhook secret in Render if it is not already set.
4. Before live mode, configure the live Stripe key and live webhook signing secret in Render, complete Stripe's account activation steps, and redeploy. Live keys charge real cards.
5. Update this TODO if you later add Stripe catalog Price IDs, subscriptions, taxes, change shipping regions/rates, or other Checkout parameters.

## Project structure and flow

No files or routes were added for this Scenario A update. The existing bag view creates the Checkout Session using current database-backed product details, then redirects to Stripe's hosted payment page. The existing success route and webhook handle the return and payment confirmation flow.

This Checkout Session uses the supplied Checkout Studio settings, including disabled automatic tax. Checkout collects shipping addresses for the configured North America, South America, and Europe destinations, then adds a flat $10.00 USD shipping fee. The rate is created inline by the server; no Stripe catalog item or dashboard shipping rate is needed.

Resources: [Stripe support](https://support.stripe.com), [Stripe Checkout documentation](https://docs.stripe.com/checkout), [Stripe testing](https://docs.stripe.com/testing), and [Stripe docs MCP](https://docs.stripe.com/mcp).
