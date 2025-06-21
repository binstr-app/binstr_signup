from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import stripe
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe Setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = "https://binstr-signup.onrender.com"

# ✅ Firebase Admin Init (Safe for Production)
if not firebase_admin._apps:
    firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
    firebase_creds_dict = json.loads(firebase_creds)
    cred = credentials.Certificate(firebase_creds_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Routes
@app.get("/", response_class=HTMLResponse)
def home():
    with open("signup.html", "r") as f:
        return f.read()

@app.post("/signup")
async def signup(
    name: str = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    pickup_day: str = Form(...),
    referral: str = Form(None)
):
    # Save to Firestore
    doc_ref = db.collection("signups").document()
    doc_ref.set({
        "name": name,
        "address": address,
        "phone": phone,
        "pickup_day": pickup_day,
        "referral": referral,
    })

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
def create_stripe_account(uid: str):
    try:
        account = stripe.Account.create(
            type="standard",
            country="US",
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True}
            }
        )
        link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f"{YOUR_DOMAIN}/onboarding-failed",
            return_url=f"{YOUR_DOMAIN}/onboarding-complete",
            type="account_onboarding"
        )
        # Save to Firestore
        db.collection("stripe_accounts").document(uid).set({
            "stripe_account_id": account.id,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        return JSONResponse(content={"url": link.url})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
