#!/bin/bash
# =============================================================================
# Script de Configuración Producción - API DISANO
# =============================================================================
#
# Este script genera una API key segura y actualiza la configuración
# en el servidor para producción con seguridad activada.
#
# =============================================================================

set -Eeuo pipefail

validate_database_url() {
	local database_url="${1:-}"

	if [[ -z "$database_url" ]]; then
		echo "ERROR: DATABASE_URL is required for production configuration." >&2
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
RATE_LIMIT_PER_CLIENT=30
CORS_ORIGINS=https://eloymartinezcuesta.com,https://disano.eloymartinezcuesta.com
DATABASE_URL=$DATABASE_URL
EOF
	mv -f -- "$tmp_file" "$env_file"
}

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║       🔐 CONFIGURACIÓN DE SEGURIDAD - API DISANO PRODUCCIÓN            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Generate independent secrets without exposing them in output.
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
validate_environment_value "API_KEYS" "$API_KEY"
validate_environment_value "SECRET_KEY" "$SECRET_KEY"
validate_environment_value "DATABASE_URL" "$DATABASE_URL"

echo "🔑 API Key generated and stored in the protected environment file."
echo ""
write_environment_file
echo "✅ Archivo .env creado"
echo ""

# Restart service
echo "🔄 Reiniciando servicio..."
systemctl restart api-disano
sleep 3

echo "🧪 Verificando servicio..."
systemctl status api-disano --no-pager -n 15

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ CONFIGURACIÓN COMPLETADA                            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Resumen:"
echo "   Environment: production"
echo "   API Key: provisioned through the protected environment file"
echo "   Rate limiting: 30 req/min"
echo "   CORS: https://eloymartinezcuesta.com"
echo ""
echo "🧪 Prueba la API usando el mecanismo aprobado de secretos."
echo ""
