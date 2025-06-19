from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import stripe
import os

app = FastAPI()

# Optional: Enable CORS for local testing or frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve signup.html for GET requests to "/"
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("signup.html", "r") as file:
        return file.read()

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # Set this in Render dashboard securely
YOUR_DOMAIN = "https://binstr-signup.onrender.com"  # Replace with actual domain

# Receive form data and redirect to Stripe Checkout
@app.post("/signup")
async def signup(
    name: str = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    pickup_day: str = Form(...),
    referral: str = Form(None)
):
    # Here, you'd log to a database or file
    print("New signup:", name, address, phone, pickup_day, referral)

    # Create Stripe Checkout Session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Binstr Starter Plan",
                    "description": "Quarterly billing for weekly bin service",
                },
                "unit_amount": 16200,  # $162 in cents
            },
            "quantity": 1,
        }],
        mode="subscription",
        success_url=f"{YOUR_DOMAIN}/?success=true",
        cancel_url=f"{YOUR_DOMAIN}/?canceled=true",
    )

    return RedirectResponse(url=checkout_session.url, status_code=303)
