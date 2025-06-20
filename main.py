# main.py
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import stripe
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Stripe secret key from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = "https://binstr-signup.onrender.com"

# Initialize Firebase once
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()

@app.get("/", response_class=HTMLResponse)
def home():
    with open("signup.html", "r") as f:
        return f.read()

@app.get("/stripe-test")
def test_stripe():
    try:
        balance = stripe.Balance.retrieve()
        return {"success": True, "live": balance["livemode"]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/signup")
async def signup(
    name: str = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    pickup_day: str = Form(...),
    referral: str = Form(None)
):
    print("SIGNUP:", name, address, phone, pickup_day, referral)

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Binstr Starter Plan",
                    "description": "Weekly bin service billed quarterly",
                },
                "unit_amount": 16200,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{YOUR_DOMAIN}/?success=true",
        cancel_url=f"{YOUR_DOMAIN}/?canceled=true",
    )

    return RedirectResponse(url=checkout_session.url, status_code=303)

@app.get("/create-stripe-account-link/{uid}")
def create_stripe_account_link(uid: str):
    try:
        account = stripe.Account.create(
            type="standard",
            country="US",
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True}
            }
        )

        # Save account ID to Firestore under the correct user UID
        db.collection("teens").document(uid).update({
            "stripe_account_id": account.id
        })

        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{YOUR_DOMAIN}/onboarding-failed",
            return_url=f"{YOUR_DOMAIN}/onboarding-complete",
            type="account_onboarding"
        )

        return JSONResponse(content={"url": account_link.url})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
