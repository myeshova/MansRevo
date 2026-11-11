# Stripe integration setup

## Values to Replace

The checkout currently uses project-defined URLs and product prices. Confirm or change the success and return destinations before going live.

**Files containing placeholders or values to review:**
- [.env](.env)
- [shop/views.py](shop/views.py)

| Field | Current Value | What to Set |
|-------|--------------|-------------|
| STRIPE_SECRET_KEY | `sk_test_...` in `.env` | Replace with your Stripe test secret key; use the live key only in the deployment environment. |
| success_url | `checkout_success` route (`/checkout/success/`) with the Checkout Session ID | Set the final customer confirmation destination and preserve `{CHECKOUT_SESSION_ID}`. |
| cancel_url | Bag route (`/bag/`) | Set the intended cancel/return destination. |
| currency | `usd` | Change to the store's settlement and display currency if needed. |
| mode | `payment` | Keep for one-time product purchases; change to `subscription` only if the store sells recurring billing. |

## Configured Parameters

**Files containing these parameters:**
- [shop/views.py](shop/views.py)

| Parameter | Value |
|-----------|-------|
| ui_mode | `hosted` (Stripe Python SDK 16.x is below 21.0.0) |
| mode | `payment` |
| billing_address_collection | `auto` |
| phone_number_collection | `{"enabled": false}` |
| automatic_tax | `{"enabled": false}` |
| allow_promotion_codes | `false` |
| submit_type | `auto` |
| integration_identifier | `hosted_web_0001` (stored in Session metadata) |
| origin_context | `web` (stored in Session metadata) |
| payment_method_collection | Omitted because mode is `payment`; include `always` only for subscription mode. |
| line_items | Built from current bag items and database prices using `price_data` |

## Setup and next steps

- Replace the `STRIPE_SECRET_KEY=sk_test_...` placeholder in the project `.env` with your Stripe test secret key for local testing. Keep secret keys server-side and out of source control.
- Install dependencies with `pip install -r requirements.txt`. This project uses Stripe Python SDK `stripe>=16,<17`; this is below 21.0.0, so the hosted UI mode value is `hosted`. If the SDK is upgraded to 21.0.0 or later, update it to `hosted_page`.
- Set live keys only in the deployment environment after successful test mode checkout.
- The new app files are [shop/views.py](shop/views.py), [shop/urls.py](shop/urls.py), [shop/templates/shop/bag.html](shop/templates/shop/bag.html), and [shop/templates/shop/checkout_success.html](shop/templates/shop/checkout_success.html).
- Flow: the bag form posts to Django, which validates bag products and quantities, creates a hosted Checkout Session using database prices, then redirects the customer to Stripe. A success route displays a confirmation page.
- The success page is not proof of payment. Add a signed Stripe webhook and fulfillment/order tracking before shipping products; no webhook or order persistence exists yet.
- Verify inventory again during fulfillment to prevent overselling.
- Test in Stripe test mode with `4242 4242 4242 4242`, any future expiry date, and any CVC. Use Stripe Dashboard test data; never use real card data for test mode.
- Confirm `usd` and the success/cancel destinations for the store, then implement fulfillment and order tracking.

Resources: [Stripe Support](https://support.stripe.com) · [Stripe MCP documentation](https://docs.stripe.com/mcp) · [Stripe API keys best practices](https://docs.stripe.com/keys-best-practices)
