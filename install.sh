#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_BASE="https://raw.githubusercontent.com/PhoenixxZ2023/turbonetproxy/main"

APP_DIR="/opt/NTProxy"
PROXY_DST="${APP_DIR}/ntproxy.py"
MANAGER_DST="${APP_DIR}/ntproxy_manager.py"

BIN_LINK="/usr/local/bin/ntproxy"

need_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "[ERRO] Execute como root: sudo bash <(wget -qO- ${REPO_RAW_BASE}/install.sh)"
    exit 1
  fi
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERRO] Comando obrigatório não encontrado: $1"
    exit 1
  }
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

  # Baixa arquivos do GitHub (raw)
  wget -qO "${PROXY_DST}"  "${REPO_RAW_BASE}/turboproxy.py"
  wget -qO "${MANAGER_DST}" "${REPO_RAW_BASE}/turboproxy_manager.py"

  chmod +x "${PROXY_DST}" "${MANAGER_DST}"
}

create_launcher() {
  cat > "${BIN_LINK}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/env python3 /opt/NTProxy/ntproxy_manager.py "$@"
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

  need_cmd wget
  need_cmd python3
  need_cmd lsof

  download_files
  create_launcher
  reload_systemd

  echo "========================================"
  echo "[OK] Instalado em: ${APP_DIR}"
  echo "[OK] Comando disponível: ntproxy"
  echo
  echo "Abra o menu com:"
  echo "  ntproxy"
  echo "========================================"
}

main "$@"
