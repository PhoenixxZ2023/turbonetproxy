#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/NTProxy"
PROXY_SRC="./turboproxy.py"
MANAGER_SRC="./turboproxy_manager.py"

PROXY_DST="${APP_DIR}/ntproxy.py"
MANAGER_DST="${APP_DIR}/ntproxy_manager.py"

BIN_LINK="/usr/local/bin/ntproxy"

need_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "[ERRO] Execute como root: sudo bash install.sh"
    exit 1
  fi
}

require_files() {
  [[ -f "${PROXY_SRC}" ]] || { echo "[ERRO] Não achei ${PROXY_SRC} na pasta atual."; exit 1; }
  [[ -f "${MANAGER_SRC}" ]] || { echo "[ERRO] Não achei ${MANAGER_SRC} na pasta atual."; exit 1; }
}

install_deps_apt() {
  apt-get update -y
  apt-get install -y --no-install-recommends \
    python3 lsof
}

install_files() {
  mkdir -p "${APP_DIR}"
  cp -f "${PROXY_SRC}" "${PROXY_DST}"
  cp -f "${MANAGER_SRC}" "${MANAGER_DST}"
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
  require_files
  command -v apt-get >/dev/null 2>&1 || { echo "[ERRO] Suportado: Ubuntu/Debian (apt)."; exit 1; }

  install_deps_apt
  install_files
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
