#!/bin/bash
# Read-only deployment verification for API DISANO.
#
# Usage:
#   DOMAIN=api.example.com DATABASE_URL=postgresql://user:password@host/db \
#     bash scripts/verify-deployment.sh
#
# DOMAIN and DATABASE_URL are supplied by the approved production secret/configuration mechanism;
# this script validates them without printing or connecting with DATABASE_URL.

set -Eeuo pipefail

validate_database_url() {
	local database_url="${1:-}"

	if [[ -z "$database_url" ]]; then
		echo "ERROR: DATABASE_URL is required before verifying production deployment." >&2
		echo "       Provision it through the approved secret mechanism and export it before running this script." >&2
		return 1
	fi

	if [[ ! "$database_url" =~ ^(postgres|postgresql)(\+[[:alnum:]_-]+)?://[^/[:space:]]+/.+$ ]]; then
		echo "ERROR: DATABASE_URL must be a PostgreSQL URL with a host and database path." >&2
		return 1
	fi
}

DATABASE_URL="${DATABASE_URL:-}"
DOMAIN="${DOMAIN:-}"
validate_database_url "$DATABASE_URL"

if [[ -z "$DOMAIN" ]]; then
	echo "ERROR: DOMAIN is required before verifying the deployment certificate." >&2
	exit 1
fi

PASS=0
FAIL=0

check() {
	local description="$1"
	shift

	if "$@"; then
		printf 'PASS: %s\n' "$description"
		((PASS += 1))
	else
		printf 'FAIL: %s\n' "$description"
		((FAIL += 1))
	fi
}

check_health_status() {
	curl --fail --silent --show-error http://127.0.0.1:8000/health |
		grep -q '"status":"ok"'
}

check_certificate() {
	certbot certificates 2>/dev/null | grep -Fq -- "$DOMAIN"
}

printf '%s\n' '=== API DISANO deployment verification (read-only) ==='
printf '%s\n' 'Checks are observational; no processes are stopped or restarted.'

check "service is active" systemctl is-active --quiet api-disano
check "service is enabled for auto-start" systemctl is-enabled --quiet api-disano
check "Restart=always is configured" grep -q '^Restart=always$' /etc/systemd/system/api-disano.service
check "RestartSec=10 is configured" grep -q '^RestartSec=10$' /etc/systemd/system/api-disano.service
check "API health endpoint is successful" curl --fail --silent --show-error --output /dev/null http://127.0.0.1:8000/health
check "API health endpoint reports healthy" check_health_status
check "Nginx configuration is valid" nginx -t
check "Nginx site is enabled" test -f /etc/nginx/sites-enabled/api-disano
# Preflight is intentionally not executed here: it reads production .env and connects to PostgreSQL.
check "production preflight script is present" test -r "$(dirname -- "${BASH_SOURCE[0]}")/preflight-production.py"
check "SSL certificate is installed" check_certificate
check "service restart history is readable" systemctl show api-disano -p NRestarts --value >/dev/null
check "service journal is readable" journalctl -u api-disano --no-pager -n 20 >/dev/null

printf '\nPassed: %d\nFailed: %d\n' "$PASS" "$FAIL"

if ((FAIL == 0)); then
	printf '%s\n' 'All deployment checks passed.'
	exit 0
fi

printf '%s\n' 'Deployment checks failed; review the failed checks above.' >&2
exit 1
