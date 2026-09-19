# Raspberry Pi Chatbot

A small FastAPI web service that sends chat prompts to Ollama. Nginx is the local reverse proxy, and the service can be exposed through an existing Cloudflare Tunnel.

## Local setup

```bash
sudo apt update
sudo apt install -y python3-venv
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Install Ollama on the Pi, then download the model configured in `.env`:

```bash
ollama pull <MODEL_NAME>
```

Replace `<MODEL_NAME>` with the model value from your private `.env` file.

Start the app directly for local development:

```bash
. .venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000
```

The API documentation is available at `/api/docs`. Check `/api/health` before troubleshooting the web UI.

## Nginx

Install Nginx and adapt the generic configuration to your local deployment:

```bash
sudo apt install -y nginx
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/chatbot
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/chatbot
sudo nginx -t
sudo systemctl reload nginx
```

Replace the placeholder server name in the copied configuration. Nginx forwards requests to Uvicorn on the loopback interface.

## Cloudflare Tunnel

Keep Uvicorn and Nginx bound to local interfaces; let `cloudflared` be the only public-facing process. Point the existing tunnel to Nginx with an ingress rule similar to this:

```yaml
ingress:
  - hostname: <YOUR_HOSTNAME>
    service: http://127.0.0.1:80
  - service: http_status:404
```

Then restart the tunnel service and test the public hostname. Protect the hostname with Cloudflare Access before exposing it to the internet. Do not expose Ollama port `11434` publicly.

## Important next steps

1. Set `OLLAMA_URL` and `OLLAMA_MODEL` only in the private `.env` file; use a private network path for Ollama.
2. Create a dedicated Linux user and replace the placeholders in `deploy/chatbot.service`; do not run the production service from an interactive shell.
3. Configure Cloudflare Access authentication, HTTPS, and a restrictive tunnel ingress rule.
4. Add conversation history and persistent storage only after the basic request path is stable.
5. Add rate limiting, request logging without prompt secrets, input limits, and a process restart policy.
6. Monitor Pi CPU, memory, temperature, disk space, Ollama latency, and tunnel status. Quantized models are usually the practical choice on 8 GB RAM.
7. Pin dependency versions after the first successful deployment and keep `.env` out of Git.

The included `deploy/chatbot.service` uses one Uvicorn worker, which keeps memory use predictable on an 8 GB Pi. Replace `<SERVICE_USER>` and `<APP_DIRECTORY>` before installing it:

```bash
sudo useradd --system <SERVICE_USER>
sudo cp deploy/chatbot.service /etc/systemd/system/chatbot.service
sudo systemctl daemon-reload
sudo systemctl enable --now chatbot
sudo systemctl status chatbot
```
