#!/usr/bin/env python3
import os
import subprocess
import re

COLORS = {
    "red": "\033[1;31m",
    "green": "\033[1;32m",
    "yellow": "\033[1;33m",
    "blue": "\033[1;34m",
    "reset": "\033[0m",
}

def colored_text(color, text):
    return f"{COLORS[color]}{text}{COLORS['reset']}"

def prompt(message):
    return input(colored_text("yellow", message))

def pause_prompt():
    input(colored_text("yellow", "Pressione Enter para continuar..."))

def validate_port(port: str) -> bool:
    if not re.match(r"^\d+$", port):
        print(colored_text("red", "Porta inválida."))
        return False
    p = int(port)
    if p <= 0 or p > 65535:
        print(colored_text("red", "Porta fora do intervalo permitido."))
        return False
    return True

def execute_command(command: str) -> bool:
    try:
        subprocess.run(command, shell=True, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except subprocess.CalledProcessError as e:
        err = (e.stderr or "").strip()
        print(colored_text("red", f"Erro ao executar: {command}"))
        if err:
            print(colored_text("red", err))
        return False

def is_port_in_use(port: str) -> bool:
    result = subprocess.run(f"lsof -i :{port}", shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout.strip() != ""

def configure_and_start_service():
    while True:
        port = prompt("Porta: ")
        if not validate_port(port):
            continue
        if is_port_in_use(port):
            print(colored_text("red", f"Porta {port} já está em uso."))
            continue

        service_name = f"ntproxy-{port}"
        service_file = f"/etc/systemd/system/{service_name}.service"

        # turboproxy.py usa -p <port>
        service_content = f"""
[Unit]
Description=TurboProxy Service on Port {port}
After=network.target

[Service]
LimitNOFILE=infinity
ExecStart=/usr/bin/env python3 /opt/NTProxy/turboproxy.py -p {port}
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
        """.strip()

        with open(service_file, "w") as f:
            f.write(service_content)

        execute_command("systemctl daemon-reload")
        execute_command(f"systemctl enable {service_name}")
        execute_command(f"systemctl start {service_name}")

        print(colored_text("green", f"Proxy iniciado na porta {port}."))
        pause_prompt()
        break

def stop_and_remove_service():
    while True:
        port = prompt("Porta: ")
        if not validate_port(port):
            continue

        service_name = f"ntproxy-{port}"
        service_file = f"/etc/systemd/system/{service_name}.service"

        execute_command(f"systemctl stop {service_name}")
        execute_command(f"systemctl disable {service_name}")
        if os.path.exists(service_file):
            os.remove(service_file)
        execute_command("systemctl daemon-reload")

        print(colored_text("green", f"Proxy na porta {port} parado e removido."))
        pause_prompt()
        break

def restart_ntproxy():
    while True:
        port = prompt("Porta: ")
        if not validate_port(port):
            continue

        service_name = f"ntproxy-{port}"
        if not execute_command(f"systemctl is-active --quiet {service_name}"):
            print(colored_text("red", f"Proxy na porta {port} não está ativo."))
            pause_prompt()
            return

        execute_command(f"systemctl restart {service_name}")
        print(colored_text("green", f"Proxy na porta {port} reiniciado."))
        pause_prompt()
        break

def show_ntproxy():
    print(colored_text("green", "\n----- Serviços em Execução -----\n"))
    result = subprocess.run(
        "systemctl list-units --type=service --state=running | grep ntproxy-",
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    lines = result.stdout.strip().splitlines()
    for line in lines:
        if not line.strip():
            continue
        svc = line.split()[0]
        base = svc[:-8] if svc.endswith(".service") else svc
        parts = base.split("-")
        port = parts[1] if len(parts) > 1 else "?"
        print(colored_text("blue", f"Proxy na porta {port} está ativo."))
    pause_prompt()

def menu_main():
    while True:
        os.system("clear")
        print(colored_text("blue", "╔═════════════════════════════╗"))
        print(colored_text("blue", "║") + colored_text("green", "        TurboProxy Menu       ") + colored_text("blue", "║"))
        print(colored_text("blue", "║═════════════════════════════║"))
        print(colored_text("blue", "║ [1] ABRIR PORTA            ║"))
        print(colored_text("blue", "║ [2] FECHAR PORTA           ║"))
        print(colored_text("blue", "║ [3] REINICIAR PORTA        ║"))
        print(colored_text("blue", "║ [4] MONITOR                ║"))
        print(colored_text("blue", "║ [0] SAIR                   ║"))
        print(colored_text("blue", "╚═════════════════════════════╝"))

        option = prompt("Escolha uma opção: ")
        if option == "1":
            configure_and_start_service()
        elif option == "2":
            stop_and_remove_service()
        elif option == "3":
            restart_ntproxy()
        elif option == "4":
            show_ntproxy()
        elif option == "0":
            print(colored_text("red", "Saindo..."))
            break
        else:
            print(colored_text("red", "Opção inválida."))
            pause_prompt()

if __name__ == "__main__":
    menu_main()
