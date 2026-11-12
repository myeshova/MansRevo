# Stripe Checkout production setup

## Values to Replace

Do not commit `.env`, Stripe keys, webhook secrets, or Gmail app passwords. `.env` is ignored by Git. Enter production secrets directly in the Render service’s Environment settings.

**Files with placeholders or configurable values:**
- [.env](.env) for local development only
- [shop/views.py](shop/views.py) for shipping-rate environment-variable names

| Setting | Current value | What to set |
|---|---|---|
| `STRIPE_SECRET_KEY` | Test key in local `.env`; not configured in Render | Use an `sk_test_...` key for test deploys, then an `sk_live_...` key only after all launch checks pass. |
| `STRIPE_WEBHOOK_SECRET` | Blank locally; not configured in Render | Add the signing secret (`whsec_...`) for the matching test or live webhook endpoint. |
| `STRIPE_SHIPPING_NORTH_AMERICA_USD` | Blank | Your flat USD shipping charge for North America. Required before checkout is enabled. |
| `STRIPE_SHIPPING_SOUTH_AMERICA_USD` | Blank | Your flat USD shipping charge for South America. Required before checkout is enabled. |
| `STRIPE_SHIPPING_EUROPE_USD` | Blank | Your flat USD shipping charge for Europe. Required before checkout is enabled. |
| `STRIPE_SHIPPING_*_COUNTRIES` | Default country groups in `shop/views.py` | Optional comma-separated ISO country codes to replace a region’s defaults. |
| `EMAIL_HOST_PASSWORD` | Blank | Gmail App Password for `mansrevo@gmail.com`; enter privately in Render. |
| `DJANGO_SECRET_KEY` | Generated in local `.env` | Copy this private value into Render before deploying the updated settings. Do not commit it or share it in chat. |

## Configured Checkout Parameters

**Files:** [shop/views.py](shop/views.py)

| Parameter | Value |
|---|---|
| `ui_mode` | `hosted_page` |
| `mode` | `payment` |
| `billing_address_collection` | `auto` |
| `shipping_address_collection` | Country groups for North America, South America, and Europe |
| `shipping_options` | Region-specific fixed USD rates read from Render environment variables |
| `automatic_tax` | Enabled; register U.S. tax locations and set apparel tax defaults in Stripe before live mode |
| `allow_promotion_codes` | `false` |
| `phone_number_collection` | `{"enabled": false}` |
| `submit_type` | `auto` |
| `integration_identifier` | `hosted_web_0001` |
| `origin_context` | `web` |
| `line_items` | Product names, prices, and quantities from the validated bag/database |
| `success_url` | Current site’s verified checkout return route |
| `cancel_url` | Current site’s bag route |

## Setup and launch steps

1. Confirm Render is connected to the production PostgreSQL database. Orders and inventory updates use Django’s default database.
2. In Render, set `DJANGO_SECRET_KEY` before deploying this version. The code now refuses to start in production without it; the prior hard-coded development key was removed.
3. Set the three `STRIPE_SHIPPING_*_USD` amounts in Render. Checkout stays blocked until all three are configured. The defaults cover the U.S., Canada, Mexico, Central America and Caribbean countries listed in code; South American countries; and EU countries plus the UK, Switzerland, Norway, Iceland, and Liechtenstein. Override country lists if your carrier coverage differs.
4. Configure Stripe Tax in the Stripe Dashboard: activate U.S. registrations where your business is registered to collect, and choose the appropriate default tax category for your apparel. Checkout adds tax to the listed prices and shipping where Stripe Tax applies.
5. Configure Gmail SMTP in Render: `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`, `EMAIL_HOST_USER=mansrevo@gmail.com`, `EMAIL_HOST_PASSWORD=<Gmail app password>`, `DEFAULT_FROM_EMAIL=mansrevo@gmail.com`. Never put the app password in Git or chat. Google requires 2-Step Verification for App Passwords, and may restrict their availability. [Google App Password guidance](https://support.google.com/mail/answer/185833)
6. Add a Stripe webhook endpoint at `https://mansrevo.onrender.com/stripe/webhook/` for `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, and `checkout.session.expired`. Put that endpoint’s signing secret in Render as `STRIPE_WEBHOOK_SECRET`. Use separate test and live endpoints/secrets.
7. Set Render’s pre-deploy command to `python manage.py migrate` so migration `shop.0005_order_orderitem` creates the order tables before the new service starts.
8. Deploy with test keys first. Verify checkout, test webhook delivery, order records in Django admin, inventory decrement, tax, shipping, and a customer email. Do not use real cards with test keys or test cards with live keys.
9. After successful staging checks, complete Stripe’s account activation and go-live checklist, replace the Render test Stripe key and webhook secret with live-mode values, and redeploy. Live mode processes real payments.

## Flow and fulfillment

The bag POST creates a pending order and line-item snapshots, then creates a Stripe hosted Checkout Session. The signed webhook verifies payment, updates shipping/tax totals, decrements stock once, and sends the order email. Repeated webhook events do not decrement inventory again. If inventory is insufficient when payment is confirmed, the paid order is marked for admin review.

The success page also verifies the session with Stripe; it is not the source of truth for payment. Orders are visible in Django admin. Store emails use Gmail SMTP and require the Render settings above.

Stripe resources: [API keys](https://docs.stripe.com/keys), [Checkout fulfillment/webhooks](https://docs.stripe.com/checkout/fulfillment.md?ui=full-page), [Stripe Tax](https://docs.stripe.com/tax), and [Go-live checklist](https://docs.stripe.com/get-started/checklist/go-live.md).
