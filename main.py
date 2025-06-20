# main.py
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import stripe
import os

app = FastAPI()

# Enable CORS (optional, useful for frontend testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

YOUR_DOMAIN = "https://binstr-signup.onrender.com"

@app.get("/", response_class=HTMLResponse)
def home():
    with open("signup.html", "r") as f:
        return f.read()
@app.get("/env-check")
def check_env():
    return {"STRIPE_SECRET_KEY": os.getenv("STRIPE_SECRET_KEY")}

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
