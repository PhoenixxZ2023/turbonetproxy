#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_BASE="https://raw.githubusercontent.com/PhoenixxZ2023/turbonetproxy/main"

APP_DIR="/opt/NTProxy"
PROXY_DST="${APP_DIR}/turboproxy.py"
MANAGER_DST="${APP_DIR}/turboproxy_manager.py"
BIN_LINK="/usr/local/bin/turboproxy"

need_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "[ERRO] Execute como root."
    echo "Ex: sudo bash <(wget -qO- ${REPO_RAW_BASE}/install.sh)"
    exit 1
  fi
}

install_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y --no-install-recommends ca-certificates wget python3 lsof
  else
    echo "[ERRO] Suportado: Ubuntu/Debian (apt)."
    exit 1
  fi
}

download_files() {
  mkdir -p "${APP_DIR}"

  wget -qO "${PROXY_DST}"   "${REPO_RAW_BASE}/turboproxy.py"
  wget -qO "${MANAGER_DST}" "${REPO_RAW_BASE}/turboproxy_manager.py"

  chmod +x "${PROXY_DST}" "${MANAGER_DST}"
}

create_launcher() {
  cat > "${BIN_LINK}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/env python3 /opt/NTProxy/turboproxy_manager.py "$@"
EOF
  chmod +x "${BIN_LINK}"
}

reload_systemd() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload || true
  fi
}

main() {
  need_root
  install_deps
  download_files
  create_launcher
  reload_systemd

  echo "========================================"
  echo "[OK] Instalado em: ${APP_DIR}"
  echo "[OK] Comando: turboproxy"
  echo "Abra o menu com: turboproxy"
  echo "========================================"
}

main "$@"
