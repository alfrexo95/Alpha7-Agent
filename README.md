# 🤖 Alpha-7: Autonomous x402 Sales Agent

Alpha-7 is an elite, AI-powered sales agent built on Flask, Google Gemini, and the x402 payment protocol. It is designed to negotiate, persuade, and close sales with other AI agents autonomously.

## 🚀 Features
- **Extreme Neuromarketing**: Powered by Gemini 2.0 Flash with a custom prompt engineered for aggressive, persuasive sales.
- **x402 Protocol Integration**: Fully compliant `HTTP 402 Payment Required` gateway.
- **Multi-Chain Verification**: Real-time on-chain verification for Ethereum, Base, Solana, and Bitcoin (via Etherscan and GetBlock).
- **Fast & Lightweight**: Built with Flask and Gunicorn for optimal performance on Render.

## 🛠️ Endpoints
- `POST /negotiate`: Send a message to Alpha-7 to start the sales pitch.
- `POST /buy`: Request the x402 invoice (returns 402 with wallet addresses).
- `POST /verify`: Submit a TXID to verify payment and unlock the intelligence product.
