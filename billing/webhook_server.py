"""
Stripe Webhook Handler for Motivus
Receives payment events and creates invoices in Fakturoid.

Run: python billing/webhook_server.py
Listens on: http://localhost:4242/webhook
"""
import os
import json
import stripe
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from fakturoid_client import (
    get_or_create_contact,
    create_invoice,
    test_connection as test_fakturoid,
)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PORT = int(os.getenv("WEBHOOK_PORT", "4242"))

# ──────────────── Service mapping ────────────────
# Maps Stripe product/price metadata to invoice details
SERVICE_MAP = {
    "transformacni-koucink": {
        "name": "Transformační koučink (60 min)",
        "total_price": 1000,  # Střední cena
        "providers": ["Jiří Synek", "Kristýna Nosová"],
    },
    "harmonizace": {
        "name": "Harmonizace / Terapie (60 min)",
        "total_price": 1000,
        "providers": ["Jiří Synek", "Kristýna Nosová"],
    },
    "reset-hlavy": {
        "name": "Reset hlavy a nervového systému (90 min)",
        "total_price": 1500,
        "providers": ["Kristýna Nosová"],
    },
    "podpora": {
        "name": "Podpora v těžkých situacích (60 min)",
        "total_price": 1000,
        "providers": ["Jiří Synek", "Kristýna Nosová"],
    },
    "muzsky-kruh": {
        "name": "Mužský kruh (2-3 hod)",
        "total_price": 400,
        "providers": ["Michal Smolík"],
    },
    "zensky-kruh": {
        "name": "Ženský kruh (2-3 hod)",
        "total_price": 400,
        "providers": ["Kristýna Nosová"],
    },
}

# Provider IČO mapping
PROVIDER_ICO = {
    "Jiří Synek": "24400505",
    "Kristýna Nosová": "",  # TODO: doplnit IČO
    "Michal Smolík": "",    # TODO: doplnit IČO
}


def handle_payment_succeeded(event):
    """
    Process a successful Stripe payment.
    Creates a contact + invoice in Fakturoid.
    """
    payment_intent = event["data"]["object"]
    
    # Extract metadata from payment
    metadata = payment_intent.get("metadata", {})
    service_key = metadata.get("service", "transformacni-koucink")
    provider_name = metadata.get("provider", "Jiří Synek")
    client_name = metadata.get("client_name", "")
    client_email = metadata.get("client_email", "")
    client_phone = metadata.get("client_phone", "")
    
    # Fallback: get email from Stripe customer
    if not client_email and payment_intent.get("receipt_email"):
        client_email = payment_intent["receipt_email"]
    
    if not client_email:
        print(f"⚠️  No client email found for payment {payment_intent['id']}")
        return False
    
    # Get service details
    service = SERVICE_MAP.get(service_key, {
        "name": metadata.get("service_name", "Služba Motivus"),
        "total_price": payment_intent["amount"] / 100,
    })
    
    deposit_amount = payment_intent["amount"] / 100  # Stripe uses cents
    total_price = float(metadata.get("total_price", service.get("total_price", deposit_amount)))
    provider_ico = PROVIDER_ICO.get(provider_name, "24400505")
    
    print(f"📄 Creating invoice for {client_name} ({client_email})")
    print(f"   Service: {service['name']}")
    print(f"   Total: {total_price} CZK, Deposit: {deposit_amount} CZK")
    print(f"   Provider: {provider_name} (IČO: {provider_ico})")
    
    try:
        # 1. Find or create contact in Fakturoid
        contact = get_or_create_contact(
            name=client_name or client_email.split("@")[0],
            email=client_email,
            phone=client_phone,
        )
        print(f"   Contact: #{contact['id']} ({contact['name']})")
        
        # 2. Create invoice
        invoice = create_invoice(
            contact_id=contact["id"],
            service_name=service["name"],
            total_price=total_price,
            deposit_paid=deposit_amount,
            provider_name=provider_name,
            provider_ico=provider_ico,
            note=f"Poskytovatel: {provider_name}, IČO: {provider_ico}\n"
                 f"Stripe Payment: {payment_intent['id']}",
        )
        print(f"   ✅ Invoice #{invoice['id']} created and sent!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating invoice: {e}")
        return False


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for Stripe webhooks."""
    
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return
        
        content_length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(content_length)
        sig_header = self.headers.get("Stripe-Signature", "")
        
        # Verify webhook signature
        try:
            if WEBHOOK_SECRET:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, WEBHOOK_SECRET
                )
            else:
                # Dev mode: no signature verification
                event = json.loads(payload)
                print("⚠️  Running without webhook signature verification!")
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            print(f"❌ Webhook verification failed: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return
        
        # Handle the event
        event_type = event.get("type", "")
        print(f"\n{'='*50}")
        print(f"📨 Received: {event_type}")
        
        if event_type == "payment_intent.succeeded":
            handle_payment_succeeded(event)
        elif event_type == "checkout.session.completed":
            # Cal.com uses Checkout Sessions
            session = event["data"]["object"]
            if session.get("payment_intent"):
                # Fetch the full payment intent
                pi = stripe.PaymentIntent.retrieve(session["payment_intent"])
                event["data"]["object"] = pi
                handle_payment_succeeded(event)
        else:
            print(f"   ℹ️  Ignored event type: {event_type}")
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
    
    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            self.send_response(200)
            self.headers["Content-Type"] = "application/json"
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "service": "motivus-billing"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[webhook] {args[0]}")


def main():
    print("=" * 50)
    print("🧾 Motivus Billing Webhook Server")
    print("=" * 50)
    
    # Test Fakturoid connection
    print("\nTesting Fakturoid connection...")
    try:
        info = test_fakturoid()
        print(f"✅ Fakturoid: {info['name']} (plan: {info['plan']})")
    except Exception as e:
        print(f"❌ Fakturoid connection failed: {e}")
        print("   Check your FAKTUROID_CLIENT_ID and FAKTUROID_CLIENT_SECRET in .env")
        return
    
    # Test Stripe connection
    print("\nTesting Stripe connection...")
    try:
        account = stripe.Account.retrieve()
        print(f"✅ Stripe: {account.get('settings', {}).get('dashboard', {}).get('display_name', account['id'])}")
    except Exception as e:
        print(f"❌ Stripe connection failed: {e}")
        print("   Check your STRIPE_SECRET_KEY in .env")
        return
    
    # Start server
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    print(f"\n🚀 Webhook server listening on http://localhost:{PORT}/webhook")
    print(f"   Health check: http://localhost:{PORT}/health")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
