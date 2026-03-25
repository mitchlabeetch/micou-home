# Micou Home: Custom Homepage Development Guide

This repository contains the dynamic foundation for your premium, containerized homepage. It's structured into two highly isolated layers: a **Frontend** (Static/UI) and an **API** (Backend Logic/Integration). 

This guide ensures you can safely build your application on top of this stack, swap out frameworks when needed, and fully wire into your centralized Authentik SSO system without breaking the infrastructure.

---

## 1. Directory Structure & Technologies

### `frontend/` (User Interface)
* **Default Setup:** Currently uses raw HTML, raw CSS, and Nginx. This ensures a stunningly fast, lightweight landing page with glassmorphism out of the box.
* **Replacing with Frameworks (React/Vue/Svelte):** You do NOT need to keep the raw HTML stack! If you want to use a modern framework, simply write your React/Svelte code inside `/frontend`, and update `/frontend/Dockerfile` to have a Node build stage that copies the compiled `dist/` into an Nginx base image. 
* **Important:** Ensure your frontend container exposes port `80` (which Traefik routes to `micou.org` by default in your `docker-compose.yml` labels).

### `api/` (Backend Logic via Python FastAPI)
* **Default Setup:** A Python `FastAPI` instance behind Uvicorn. This is the optimal lightweight engine for doing any complex network logic, DB pulls, or calling external APIs (like Authentik) securely across the background proxy network.
* **Usage:** Traefik strips the path `/api` and routes it here securely. If your frontend Javascript fetches `/api/users`, it reaches this Python container securely. Do not expose secrets directly on the `frontend`; pass them safely via this Python logic layer!

---

## 2. Integrating Authentik SSO

Authentik serves as your centralized identity provider. Because we rely on **Traefik**, integrating Authentik into your Homepage is incredibly seamless.

### The Traefik Forward Auth Approach (Zero-Code Auth)
You don't need to program complex OAuth2 flows in FastAPI. Instead, you tell Traefik to bounce any unauthenticated visitors to Authentik before they ever reach your homepage!

1. In your `dockge` or `/opt/stacks/homepage/docker-compose.yml`, add the ForwardAuth middleware label to your `frontend` or `api` service:
   `"traefik.http.routers.homepage-frontend.middlewares=authentik@docker"`
2. **How it Works:** Traefik intercepts the request. If the user is not logged in, Authentik forces them to login at `sso.micou.org`.
3. **Reading User Data in FastAPI:** Once the user successfully logs in, Authentik forwards the request to your Homepage API/Frontend and injects the user's data directly into the **HTTP Headers**.
   * Inside your FastAPI `main.py`, you can just read the header `X-authentik-username`, `X-authentik-email`, or `X-authentik-groups` to instantly know exactly who is logged in without writing a single line of OAuth verification code!

### Making API calls *to* Authentik (Machine-to-Machine)
If you want an administration dashboard on your homepage that lists users, resets passwords, or pulls metrics natively from Authentik:
1. Log into Authentik as an Admin and generate an API Token (`authentik Machine-to-Machine token`).
2. Add that API token into the `homepage` stack's `.env` file (e.g. `AUTHENTIK_API_KEY=xxx`).
3. Your Python `FastAPI` application can securely use the `requests` or `httpx` module to send API calls directly to `http://authentik-server-1:9000/api/v3/...` over the secure internal `proxy` network (without ever exposing the API token to the browser frontend!).

---

## 3. Automation and CI/CD (Watchtower)

The `.github/workflows/deploy.yml` template compiles your frontend and API code into two Docker images every time you merge to the `main` branch. 

**How deployment occurs:**
* **Polling (Currently Active):** Watchtower is set up to scan `ghcr.io` every 300 seconds (5 minutes). Within 5 minutes of your GitHub action turning green, Watchtower will detect the hash change, pull the new image, and gracefully recreate the containers automatically.
* **Instant Hooks (Future Upgrade):** If 5 minutes is too slow for your dev cycle, Watchtower can be configured with an HTTP Webhook (`--http-api-update`). You could add a simple `curl` command at the end of your GitHub action to ping your VPS's Watchtower endpoint, forcing it to pull the second compilation finishes!
