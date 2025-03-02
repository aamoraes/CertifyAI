import psycopg2
from fastapi import FastAPI, HTTPException, Request
import os

app = FastAPI()

# Configurar a API Key do Stripe
stripe.api_key = "sk_test_51QwdYZPRsTWI4Hbxqr3p70dPMSIfjhcPHbO5JjGsX9MsPTErAliJGnqySOxRjBvV2EbSOO1LIm1mlJHByo7tu8QT00xSdIbIrG"

# Pegar a URL do banco de dados do Render
DATABASE_URL = os.getenv("postgresql://certifyai_db_user:j5z2zv5I1Z4CIX2Jqdu8faKcNOG7cDlb@dpg-cv1q75pu0jms738na1ag-a/certifyai_db")

# Conectar ao PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Criar tabela se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    api_key TEXT PRIMARY KEY,
    credits INTEGER DEFAULT 25
)
""")
conn.commit()

@app.get("/credits/")
async def get_credits(api_key: str):
    cursor.execute("SELECT credits FROM users WHERE api_key = %s", (api_key,))
    user = cursor.fetchone()
    if user:
        return {"remaining_credits": user[0]}
    raise HTTPException(status_code=404, detail="Usuário não encontrado")




# Mapeamento de planos do Stripe para créditos
PLAN_CREDITS_MAPPING = {
    "price_1QxyVEPRsTWI4HbxjpOAaKdf": 150,  # Substituir pelo ID real do Stripe
    "price_1QxyVaPRsTWI4Hbx6nbWz3XY": 500,   # Substituir pelo ID real do Stripe
    "price_1QxyW7PRsTWI4Hbxb4XtIEjk": 3000    # Substituir pelo ID real do Stripe
}

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    # Verificar assinatura do webhook
    endpoint_secret = "whsec_ARQKM8LGl9skn8zYsD46MexMWvgv5ylO"
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Webhook inválido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Assinatura do webhook inválida")

    # Processar pagamento do Stripe
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session["customer_email"]
        plan_id = session["metadata"]["plan_id"]

        if plan_id in PLAN_CREDITS_MAPPING:
            credits_to_add = PLAN_CREDITS_MAPPING[plan_id]
            cursor.execute("UPDATE users SET credits = credits + ? WHERE api_key = ?", 
                           (credits_to_add, customer_email))
            conn.commit()
            return {"status": "success", "message": f"{credits_to_add} créditos adicionados"}

    return {"status": "ignored"}

# Endpoint para verificar créditos do usuário
@app.get("/credits/")
async def get_credits(api_key: str):
    cursor.execute("SELECT credits FROM users WHERE api_key = ?", (api_key,))
    user = cursor.fetchone()
    if user:
        return {"remaining_credits": user[0]}
    raise HTTPException(status_code=404, detail="Usuário não encontrado")
