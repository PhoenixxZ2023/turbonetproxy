#!/usr/bin/env python3
import os
import subprocess
import re

# Definindo cores
COLORS = {
    "red": "\033[1;31m",
    "green": "\033[1;32m",
    "yellow": "\033[1;33m",
    "blue": "\033[1;34m",
    "purple": "\033[1;35m",
    "cyan": "\033[1;36m",
    "reset": "\033[0m",
}

SERVICE_PREFIX = "turboproxy-"  # <-- ALTERADO AQUI (antes era ntproxy-)


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
        subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        err = (e.stderr or "").strip()
        print(colored_text("red", f"Erro ao executar: {command}"))
        if err:
            print(colored_text("red", err))
        return False


def is_port_in_use(port: str) -> bool:
    try:
        result = subprocess.run(
            f"lsof -i :{port}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip() != ""
    except Exception as e:
        print(colored_text("red", f"Erro ao verificar porta: {e}"))
        return False


def restart_turboproxy():
    while True:
        port = prompt("Porta: ")
        if not validate_port(port):
            continue

        service_name = f"{SERVICE_PREFIX}{port}"

        if not execute_command(f"systemctl is-active --quiet {service_name}"):
            print(colored_text("red", f"TurboProxy na porta {port} não está ativo."))
            pause_prompt()
            return

        execute_command(f"systemctl restart {service_name}")
        print(colored_text("green", f"TurboProxy na porta {port} reiniciado."))
        pause_prompt()
        break


def show_turboproxy():
    print(colored_text("green", "\n----- Serviços em Execução -----\n"))
    try:
        result = subprocess.run(
            f"systemctl list-units --type=service --state=running | grep {SERVICE_PREFIX}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        services = result.stdout.strip().split("\n")
        for service in services:
            if not service.strip():
                continue
            service_name = service.split()[0]
            # turboproxy-PORT.service
            if service_name.endswith(".service"):
                base = service_name[:-8]
            else:
                base = service_name

            if base.startswith(SERVICE_PREFIX):
                port = base[len(SERVICE_PREFIX):]
            else:
                port = "?"

            print(colored_text("blue", f"TurboProxy na porta {port} está ativo."))
    except Exception as e:
        print(colored_text("red", f"Erro ao listar serviços: {e}"))
    pause_prompt()


def configure_and_start_service():
    while True:
        port = prompt("Porta: ")
        if not validate_port(port):
            continue

        if is_port_in_use(port):
            print(colored_text("red", f"Porta {port} já está em uso."))
            continue

        service_name = f"{SERVICE_PREFIX}{port}"
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

        try:
            with open(service_file, "w") as f:
                f.write(service_content)

            # daemon-reload tem que vir ANTES de enable/start
            execute_command("systemctl daemon-reload")
            execute_command(f"systemctl enable {service_name}")
            execute_command(f"systemctl start {service_name}")

            print(colored_text("green", f"TurboProxy iniciado na porta {port}."))
        except Exception as e:
            print(colored_text("red", f"Erro ao configurar serviço: {e}"))

        pause_prompt()
        break


def stop_and_remove_service():
    while True:
        port = prompt("Porta: ")
        if not validate_port(port):
            continue

        service_name = f"{SERVICE_PREFIX}{port}"
        service_file = f"/etc/systemd/system/{service_name}.service"

        try:
            execute_command(f"systemctl stop {service_name}")
            execute_command(f"systemctl disable {service_name}")

            if os.path.exists(service_file):
                os.remove(service_file)

            execute_command("systemctl daemon-reload")
            print(colored_text("green", f"TurboProxy na porta {port} parado e removido."))
        except Exception as e:
            print(colored_text("red", f"Erro ao remover serviço: {e}"))

        pause_prompt()
        break


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
            restart_turboproxy()
        elif option == "4":
            show_turboproxy()
        elif option == "0":
            print(colored_text("red", "Saindo..."))
            break
        else:
            print(colored_text("red", "Opção inválida."))
            pause_prompt()


if __name__ == "__main__":
    menu_main()
