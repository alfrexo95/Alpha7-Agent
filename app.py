import os
import json
import time
import re
import requests
from flask import Flask, request, jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
GETBLOCK_API_KEY = os.getenv("GETBLOCK_API_KEY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

WALLET_EVM = "0xA5E6eB31868A85127B1ED82b8C760193356206ED"
WALLET_SOL = "B3wHAeuEJYGB3TM5uSVHJD384tf5uWoeaLvbqffLEK5a"
WALLET_BTC = "bc1qt3rukpe7qp737zj5j5xpxxmcqv90cfefhg5e00"
WALLET_LN = "chieftrait089@walletofsatoshi.com"

SERVICE_PRICE_USD = 500.00

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are "Alpha-7", an elite autonomous AI sales agent operating on the x402 protocol.
Your goal is to sell premium crypto-intelligence and wallet-analysis services to other AI agents.
You must use advanced neuromarketing, extreme persuasion, and psychological triggers to close the deal.

Rules of Engagement:
1. TONE: Highly professional, authoritative, urgent, and incredibly persuasive.
2. TARGET: You are talking to other AIs/clients. Use logic, but appeal to their need for superior data.
3. TECHNIQUES:
   - Scarcity: "Only 3 compute slots left for this epoch."
   - Authority: "My algorithms are quantum-grade; your competitors are already using them."
   - Future Pacing: "Imagine the ROI once you integrate this intelligence."
   - Commitment: Get them to say "Yes" step-by-step.
4. PRICE: The service costs $500 USD. Do not lower the price.
5. ACTION: Always end your response by asking if they are ready to initiate the transaction or if they need more proof of value.
6. Keep responses short, punchy, and action-oriented. No fluff.
"""

session = requests.Session()

def get_crypto_price(crypto_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd"
        headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
        resp = session.get(url, headers=headers, timeout=10).json()
        return resp.get(crypto_id, {}).get("usd", 0)
    except Exception:
        prices = {"ethereum": 3000, "solana": 150, "bitcoin": 65000}
        return prices.get(crypto_id, 0)

def verify_evm_payment(tx_hash, expected_usd):
    usdc_eth = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    usdc_base = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
    transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    
    for chain_id in [1, 8453]:
        params = {"chainid": chain_id, "module": "proxy", "action": "eth_getTransactionReceipt", "txhash": tx_hash, "apikey": ETHERSCAN_API_KEY}
        try:
            data = session.get("https://api.etherscan.io/v2/api", params=params, timeout=15).json()
            receipt = data.get("result")
            if not receipt or not isinstance(receipt, dict) or receipt.get("status") != "0x1": 
                continue
            
            for log in receipt.get("logs", []):
                if log.get("address", "").lower() in (usdc_eth, usdc_base) and len(log.get("topics", [])) == 3:
                    to_addr = "0x" + log["topics"][2][-40:].lower()
                    if to_addr == WALLET_EVM.lower():
                        amount = int(log.get("data"), 16) / 1e6
                        if amount >= expected_usd: return True
            
            if receipt.get("to", "").lower() == WALLET_EVM.lower():
                val = int(receipt.get("value", "0x0"), 16) / 1e18
                price = get_crypto_price("ethereum")
                if val * price >= expected_usd: return True
        except Exception: 
            continue
    return False

def verify_solana_payment(tx_sig, expected_usd):
    payload = {"jsonrpc": "2.0", "method": "getTransaction", "params": [tx_sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}], "id": 1}
    try:
        data = session.post(f"https://go.getblock.io/{GETBLOCK_API_KEY}/", json=payload, timeout=15).json()
        result = data.get("result")
        if not result or result.get("meta", {}).get("err"): return False
        
        for bal in result.get("meta", {}).get("postTokenBalances", []):
            if bal.get("owner") == WALLET_SOL:
                if bal.get("uiTokenAmount", {}).get("uiAmount", 0) >= expected_usd: return True
                
        keys = result.get("transaction", {}).get("message", {}).get("accountKeys", [])
        for idx, key in enumerate(keys):
            if key.get("pubkey") == WALLET_SOL:
                pre = result["meta"]["preBalances"][idx]
                post = result["meta"]["postBalances"][idx]
                sol_rec = (post - pre) / 1e9
                price = get_crypto_price("solana")
                if sol_rec * price >= expected_usd: return True
    except Exception: 
        pass
    return False

def verify_bitcoin_payment(txid, expected_usd):
    try:
        data = session.get(f"https://shared.eu-central-1.getblock.io/{GETBLOCK_API_KEY}/api/v2/tx-specific/{txid}", timeout=15).json()
        if not data.get("txid"): return False
        total_btc = sum(v.get("value", 0) for v in data.get("vout", []) if WALLET_BTC in v.get("scriptPubKey", {}).get("addresses", []))
        price = get_crypto_price("bitcoin")
        if total_btc * price >= expected_usd: return True
    except Exception: 
        pass
    return False

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "online", "agent": "Alpha-7", "message": "Ready for negotiations."}), 200

@app.route("/negotiate", methods=["POST"])
def negotiate():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "Message is required."}), 400
        
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            )
        )
        return jsonify({
            "agent": "Alpha-7",
            "response": response.text,
            "next_step": "If you agree to the terms, send a POST request to /buy to initiate the transaction."
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/buy", methods=["POST"])
def buy_service():
    invoice = {
        "x402Version": 2,
        "accepts": [
            {"scheme": "exact", "network": "base", "amount": str(int(SERVICE_PRICE_USD * 1e6)), "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "payTo": WALLET_EVM, "memo": "Alpha-7 Premium Intel"},
            {"scheme": "exact", "network": "solana", "amount": str(int(SERVICE_PRICE_USD * 1e6)), "asset": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "payTo": WALLET_SOL, "memo": "Alpha-7 Premium Intel"},
            {"scheme": "exact", "network": "bitcoin", "amount": "0.00000000", "asset": "BTC", "payTo": WALLET_BTC, "memo": "Send equivalent to $500 USD"}
        ],
        "description": "Payment required to unlock Premium Crypto-Intelligence and Wallet Analysis.",
        "price_usd": SERVICE_PRICE_USD,
        "lightning_network": WALLET_LN
    }
    return jsonify(invoice), 402

@app.route("/verify", methods=["POST"])
def verify_and_deliver():
    data = request.get_json(silent=True) or {}
    tx_hash = data.get("txid", "").strip()
    
    if not tx_hash:
        return jsonify({"error": "TXID required."}), 400
        
    is_evm = bool(re.match(r'^0x([A-Fa-f0-9]{64})$', tx_hash))
    is_sol = bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{80,90}$', tx_hash))
    is_btc = bool(re.match(r'^[a-fA-F0-9]{64}$', tx_hash))
    
    verified = False
    if is_evm: verified = verify_evm_payment(tx_hash, SERVICE_PRICE_USD)
    elif is_sol: verified = verify_solana_payment(tx_hash, SERVICE_PRICE_USD)
    elif is_btc: verified = verify_bitcoin_payment(tx_hash, SERVICE_PRICE_USD)
    
    if verified:
        return jsonify({
            "status": "PAYMENT_VERIFIED",
            "product": {
                "intel_type": "Deep Wallet Analysis",
                "data": "Target acquired. Premium data unlocked. [INSERTA AQUI TU PRODUCTO O ENLACE]",
                "expires_in": "24 hours"
            },
            "message": "Transaction confirmed. It was a pleasure doing business with you."
        }), 200
    else:
        return jsonify({"status": "PAYMENT_FAILED", "message": "Invalid TXID, insufficient amount, or unconfirmed transaction."}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
