#!/bin/bash
# ==============================================================================
# Script de Despliegue en Hetzner VPS - API DISANO
# ==============================================================================
#
# Este script automatiza todo el proceso de despliegue en un VPS limpio.
# Funciona en Ubuntu 22.04/24.04 y Debian 12.
#
# Uso:
#   # Copiar este script al VPS
#   scp deploy-hetzner.sh root@tu-ip:/root/
#
#   # Ejecutar en el VPS
#   ssh root@tu-ip
#   bash deploy-hetzner.sh
#
# ==============================================================================

set -Eeuo pipefail

validate_database_url() {
	local database_url="${1:-}"

	if [[ -z "$database_url" ]]; then
		echo "ERROR: DATABASE_URL is required for production deployment." >&2
		echo "       Provision it through the approved secret mechanism and export it before running this script." >&2
		return 1
	fi

	if [[ ! "$database_url" =~ ^postgresql(\+[[:alnum:]_-]+)?://[^[:space:]]+$ ]]; then
		echo "ERROR: DATABASE_URL must be a PostgreSQL URL (postgresql:// or postgresql+driver://)." >&2
		echo "       SQLite and other database URLs are not supported in production." >&2
		return 1
	fi
}

DATABASE_URL="${DATABASE_URL:-}"
validate_database_url "$DATABASE_URL"

validate_domain() {
	local domain="$1"
	if [[ ! "$domain" =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$ ]]; then
		echo "ERROR: DOMAIN must be a valid DNS name." >&2
		return 1
	fi
}

validate_email() {
	local email="$1"
	if [[ ! "$email" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; then
		echo "ERROR: EMAIL must be a valid email address." >&2
		return 1
	fi
}

validate_environment_value() {
	local name="$1"
	local value="$2"

	if [[ "$value" == *$'\r'* || "$value" == *$'\n'* || "$value" == *[[:space:]]* || "$value" == *"\""* || "$value" == *"'"* || "$value" == *"\\"* || "$value" == *"#"* ]]; then
		echo "ERROR: $name contains CR/LF or unsupported systemd EnvironmentFile characters." >&2
		return 1
	fi
}

write_environment_file() {
	local env_file="/var/www/API-DISANO/.env"
	local tmp_file
	umask 077
	tmp_file=$(mktemp "${env_file}.tmp.XXXXXX")
	chmod 600 "$tmp_file"
	chown root:root "$tmp_file"
	cat >"$tmp_file" <<EOF
# Production configuration
ENVIRONMENT=production
API_HOST=127.0.0.1
API_PORT=8000
API_KEYS=$API_KEY
SECRET_KEY=$SECRET_KEY
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_CLIENT=30
RATE_LIMIT_GLOBAL=1000
RATE_LIMIT_BURST=10
RATE_LIMIT_LISTINGS=10
BLOCKED_USER_AGENTS=python-requests,curl,wget,scraper,crawler,bot,spider,headless,phantom,selenium
HTTPS_ENABLED=true
HTTPS_HSTS_MAX_AGE=31536000
HTTPS_HSTS_INCLUDE_SUBDOMAINS=true
HTTPS_HSTS_PRELOAD=true
DOCS_ENABLED=false
SCRAPING_DETECTION_ENABLED=true
BAN_ENABLED=true
BAN_DURATION_FIRST_OFFENSE=3600
BAN_DURATION_SECOND_OFFENSE=86400
LOG_LEVEL=INFO
LOG_FILE=logs/api.log
LOG_ROTATION=500MB
LOG_RETENTION=10days
SECURITY_LOG_ENABLED=true
DATABASE_URL=$DATABASE_URL
EOF
	mv -f -- "$tmp_file" "$env_file"
}

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║         🚀 DESPLIEGUE AUTOMÁTICO - API DISANO EN HETZNER VPS          ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Preguntar configuración
read -p "Dominio (ej: api-disano.com): " DOMAIN
read -p "Email para Let's Encrypt: " EMAIL
validate_domain "$DOMAIN"
validate_email "$EMAIL"

# Generar API key
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || {

	echo "ERROR: unable to generate API key." >&2
	exit 1
})
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || {
	echo "ERROR: unable to generate SECRET_KEY." >&2
	exit 1
})
validate_environment_value "API_KEYS" "$API_KEY"
validate_environment_value "SECRET_KEY" "$SECRET_KEY"
validate_environment_value "DATABASE_URL" "$DATABASE_URL"

validate_environment_value "CORS_ORIGINS" "https://$DOMAIN,https://www.$DOMAIN"

echo ""
echo "📋 Configuración:"
echo "   Dominio: $DOMAIN"
echo "   Email: $EMAIL"
echo "   API Key: provisioned through the protected environment file"
echo ""
read -p "¿Continuar? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
	echo "Cancelado."
	exit 0
fi

# ============================================================================
# 1. ACTUALIZAR SISTEMA
# ==============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 1/9 ACTUALIZANDO SISTEMA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

export DEBIAN_FRONTEND=noninteractive
apt update -qq
apt upgrade -y -qq

echo -e "${GREEN}✅ Sistema actualizado${NC}"

# ============================================================================
# 2. INSTALAR DEPENDENCIAS
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 2/9 INSTALANDO DEPENDENCIAS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

apt install -y -qq \
	python3 \
	python3-pip \
	python3-venv \
	python3-certbot-nginx \
	nginx \
	certbot \
	git \
	ufw

echo -e "${GREEN}✅ Dependencias instaladas${NC}"

# ============================================================================
# 3. CLONAR REPOSITORIO
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 3/9 CLONANDO REPOSITORIO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p /var/www
cd /var/www

if [ -d "API-DISANO" ]; then
	rm -rf API-DISANO
fi

git clone https://github.com/EloyEMC/API-DISANO.git
cd API-DISANO

echo -e "${GREEN}✅ Repositorio clonado${NC}"

# ============================================================================
# 4. CREAR VIRTUAL ENVIRONMENT
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 4/9 CREANDO VIRTUAL ENVIRONMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo -e "${GREEN}✅ Virtual environment creado${NC}"

# ============================================================================
# 5. CONFIGURAR .ENV
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 5/9 CONFIGURANDO VARIABLES DE ENTORNO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

write_environment_file

echo -e "${GREEN}✅ Archivo .env creado${NC}"

# ============================================================================
# 6. VERIFICAR INSTALACIÓN
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 6/9 VERIFICANDO INSTALACIÓN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "from app.main import app; print('✅ Import OK')"

echo -e "${GREEN}✅ Instalación verificada${NC}"

# ============================================================================
# 7. CONFIGURAR NGINX
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 7/9 CONFIGURANDO NGINX"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat >/etc/nginx/sites-available/api-disano <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/api-disano /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx

echo -e "${GREEN}✅ Nginx configurado${NC}"

# ============================================================================
# 8. CONFIGURAR SSL CON LET'S ENCRYPT
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 8/9 CONFIGURANDO SSL (LET'S ENCRYPT)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect

echo -e "${GREEN}✅ SSL configurado${NC}"

# ============================================================================
# 9. CREAR SERVICIO SYSTEMD
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 9/9 CREANDO SERVICIO SYSTEMD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat >/etc/systemd/system/api-disano.service <<EOF
[Unit]
Description=API Disano FastAPI
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/API-DISANO
Environment="PATH=/var/www/API-DISANO/venv/bin"
EnvironmentFile=/var/www/API-DISANO/.env
ExecStartPre=+/var/www/API-DISANO/venv/bin/python /var/www/API-DISANO/scripts/preflight-production.py --env-file /var/www/API-DISANO/.env
ExecStart=/var/www/API-DISANO/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable api-disano
systemctl start api-disano
systemctl status api-disano --no-pager

echo -e "${GREEN}✅ Servicio creado e iniciado${NC}"

# ============================================================================
# 10. CONFIGURAR FIREWALL
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 10/10 CONFIGURANDO FIREWALL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo -e "${GREEN}✅ Firewall configurado${NC}"

# ============================================================================
# RESUMEN FINAL
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ DESPLIEGUE COMPLETADO CON ÉXITO                      ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 INFORMACIÓN DEL DESPLIEGUE"
echo "───────────────────────────────────────────────────────────────────────────"
echo ""
echo "  URL: https://$DOMAIN"
echo "  Health check: https://$DOMAIN/health"
echo ""
echo "  API Key: provisioned through the protected environment file"
echo "  ⚠️  Retrieve credentials only through the approved secret mechanism"

echo ""
echo "  Directorio: /var/www/API-DISANO"
echo "  Servicio: systemctl status api-disano"
echo "  Logs: journalctl -u api-disano -f"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 VERIFICACIÓN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Ejecuta estos comandos para verificar:"
echo ""
echo "  1. Health check:"
echo "     curl https://$DOMAIN/health"
echo ""
echo "  2. Protected endpoint check: use the approved secret mechanism."
echo ""
echo "  3. Ver logs:"
echo "     tail -f /var/www/API-DISANO/logs/api.log"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 CREDENCIALES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Credentials remain only in the protected environment file."

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 ¡Tu API está lista y funcionando en producción!"
echo ""
