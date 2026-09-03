import json
import ctypes
import os
import subprocess
import sys
import threading
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import messagebox
import winreg


APP_NAME = "InovaInstall"
STATE_FILE = os.path.join(
    os.environ.get("PROGRAMDATA", os.path.dirname(os.path.abspath(__file__))),
    "InovaInstall",
    "estado.json",
)
LOG_DIR = os.path.join(os.path.dirname(STATE_FILE), "logs")
RELEASES_URL = (
    "https://api.github.com/repos/precisaosistemas/inovafarma/releases?per_page=100"
)


def resource_path(name):
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, name)


def child_process_ids(parent_ids):
    if not parent_ids:
        return set()

    command = (
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,ParentProcessId | ConvertTo-Json -Compress"
    )
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = subprocess.SW_HIDE
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            startupinfo=startup_info,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=True,
        )
        processes = json.loads(result.stdout or "[]")
        if isinstance(processes, dict):
            processes = [processes]
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return set()

    return {
        int(process["ProcessId"])
        for process in processes
        if int(process["ParentProcessId"]) in parent_ids
    }


def run_executable(name, args, input_text, status, states, errors):
    log_path = os.path.join(LOG_DIR, f"{name}.log")
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(log_path, "w", encoding="utf-8", errors="replace") as log_file:
            executable_path = resource_path(name)
            log_file.write(f"Iniciando: {executable_path} {' '.join(args)}\n")
            log_file.flush()
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup_info.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                [executable_path, *args],
                stdin=subprocess.PIPE if input_text else None,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                startupinfo=startup_info,
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=os.path.dirname(resource_path(name)),
            )
            if input_text:
                process.stdin.write(input_text.encode())
                process.stdin.close()
            process.wait()
            log_file.write(f"\nCódigo de saída: {process.returncode}\n")
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, process.args)
        states[name] = "concluído"
        status(name, "concluído")
    except Exception as error:
        states[name] = "falhou"
        errors.append(f"{name}: {error} - log: {log_path}")
        status(name, "falhou (ver log)")


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as state_file:
        json.dump(state, state_file)


def latest_preview_version():
    request = urllib.request.Request(
        RELEASES_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": APP_NAME},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        releases = json.load(response)

    previews = [
        release
        for release in releases
        if release.get("prerelease")
        and not release.get("draft")
        and release.get("assets")
    ]
    if not previews:
        raise RuntimeError("Nenhuma versão Preview disponível foi encontrada.")

    release = max(previews, key=lambda item: item.get("published_at", ""))
    return release["tag_name"].removeprefix("v")


def latest_stable_version():
    request = urllib.request.Request(
        "https://api.github.com/repos/precisaosistemas/inovafarma/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": APP_NAME},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        release = json.load(response)
    return release["tag_name"].removeprefix("v")


def download_inovafarma(version, release_channel, status, states, errors):
    name = "inovafarma.exe"
    log_path = os.path.join(LOG_DIR, f"{name}.log")
    try:
        if not version:
            version = (
                latest_preview_version()
                if release_channel == "preview"
                else latest_stable_version()
            )
        request = urllib.request.Request(
            f"https://github.com/precisaosistemas/inovafarma/releases/download/"
            f"v{version}/inovafarma-{version}.exe",
            headers={"User-Agent": APP_NAME},
        )
        destination = os.path.join(os.environ.get("TEMP", r"C:\TEMP"), f"inovafarma-{version}.exe")
        with urllib.request.urlopen(request, timeout=60) as response, open(
            destination, "wb"
        ) as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"Download concluído: {destination}\nCódigo de saída: 0\n")
        states[name] = "concluído"
        status(name, "concluído")
    except Exception as error:
        states[name] = "falhou"
        errors.append(f"{name}: {error} - log: {log_path}")
        status(name, "falhou (ver log)")


def schedule_installation():
    command = f'"{sys.executable}" --install'
    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
    ) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)


def continue_to_installation(root):
    root.destroy()
    from segunda_etapa import run

    run()


def execute(
    version,
    computer_name,
    option,
    release_channel,
    sql_variant,
    restart,
    status,
    root,
    button,
):
    errors = []
    automation_names = ["terminal.exe", "recursos.exe"]
    if option == "Servidor":
        automation_names.append("download.exe")
    states = {name: "executando" for name in automation_names}
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(
        os.path.join(LOG_DIR, "preparacao.log"),
        "w",
        encoding="utf-8",
        errors="replace",
    ) as log_file:
        log_file.write("Iniciando as automações:\n")
        for name in automation_names:
            log_file.write(f"{name}: {resource_path(name)}\n")
        log_file.flush()
    processes = [
        threading.Thread(
            target=run_executable,
            args=("terminal.exe", [], computer_name + "\n", status, states, errors),
        ),
        threading.Thread(
            target=run_executable,
            args=("recursos.exe", [], "", status, states, errors),
        ),
    ]
    if option == "Servidor":
        processes.append(
            threading.Thread(
                target=run_executable,
                args=(
                    "download.exe",
                    [version, sql_variant],
                    "",
                    status,
                    states,
                    errors,
                ),
            )
        )

    for process in processes:
        process.start()
    
    # Aguardar apenas o download terminar (se for Servidor)
    if option == "Servidor" and len(processes) > 2:
        processes[2].join()
    
    # Verificar se o download (quando aplicável) foi bem-sucedido
    if option == "Servidor" and states.get("download.exe") != "concluído":
        if not errors:
            errors.append("O download não foi concluído")
        root.after(
            0,
            lambda: messagebox.showerror(
                "Erro", "O download falhou:\n" + "\n".join(errors)
            ),
        )
        root.after(0, lambda: button.config(state=tk.NORMAL))
        return

    try:
        save_state(
            {
                "version": version,
                "sql_variant": sql_variant,
                "option": option,
                "restart": restart,
            }
        )
        if restart:
            # Agendar a segunda etapa para rodar após reinício
            schedule_installation()
            # Fazer a reinicialização
            root.after(
                0,
                lambda: messagebox.showinfo(
                    "Preparação concluída",
                    "O computador será reiniciado.\nApós o reinício, a instalação continuará automaticamente.",
                ),
            )
            root.after(
                1000,
                lambda: subprocess.Popen(
                    [
                        "shutdown",
                        "/r",
                        "/t",
                        "5",
                        "/c",
                        "Preparação concluída. Reiniciando para continuar a instalação.",
                    ]
                ),
            )
            root.after(2000, lambda: root.destroy())
        else:
            root.after(0, lambda: continue_to_installation(root))
    except OSError as error:
        root.after(
            0,
            lambda: messagebox.showerror(
                "Erro", f"Não foi possível salvar a preparação:\n{error}"
            ),
        )
        root.after(0, lambda: button.config(state=tk.NORMAL))


def start(
    version_entry,
    computer_name_entry,
    option,
    release_channel,
    sql_variant,
    restart,
    status,
    root,
    button,
):
    if str(button.cget("state")) == tk.DISABLED:
        return
    button.config(state=tk.DISABLED)
    status("terminal.exe", "executando")
    status("recursos.exe", "executando")
    if option.get() == "Servidor":
        status("download.exe", "executando")
    threading.Thread(
        target=execute,
        args=(
            version_entry.get().strip(),
            computer_name_entry.get().strip(),
            option.get(),
            release_channel.get(),
            sql_variant.get(),
            restart.get(),
            status,
            root,
            button,
        ),
        daemon=True,
    ).start()


def run():
    root = tk.Tk()
    root.title("InovaInstall - Preparação")

    tk.Label(root, text="Versão do InovaFarma:").grid(
        row=0, column=0, padx=10, pady=10
    )
    version_entry = tk.Entry(root, width=30)
    version_entry.grid(row=0, column=1, padx=10, pady=10)
    tk.Label(root, text="Em branco: baixar a última versão.").grid(
        row=1, column=0, columnspan=2
    )

    tk.Label(root, text="Nome do computador:").grid(
        row=2, column=0, padx=10, pady=10
    )
    computer_name_entry = tk.Entry(root, width=30)
    computer_name_entry.grid(row=2, column=1, padx=10, pady=10)
    tk.Label(root, text="Em branco: manter o nome atual.").grid(
        row=3, column=0, columnspan=2
    )

    tk.Label(root, text="Tipo de instalação:").grid(
        row=4, column=0, padx=10, pady=10
    )
    option = tk.StringVar(value="Servidor")
    tk.Radiobutton(
        root, text="Servidor", variable=option, value="Servidor"
    ).grid(row=4, column=1, sticky="w")
    tk.Radiobutton(
        root, text="Terminal", variable=option, value="Terminal"
    ).grid(row=5, column=1, sticky="w")

    tk.Label(root, text="Canal do InovaFarma:").grid(
        row=6, column=0, padx=10, pady=10
    )
    release_channel = tk.StringVar(value="stable")
    tk.Radiobutton(
        root, text="Normal", variable=release_channel, value="stable"
    ).grid(row=6, column=1, sticky="w")
    tk.Radiobutton(
        root, text="Preview", variable=release_channel, value="preview"
    ).grid(row=7, column=1, sticky="w")

    tk.Label(root, text="SQL para download:").grid(
        row=8, column=0, padx=10, pady=10
    )
    sql_variant = tk.StringVar(value="sql2016")
    tk.Radiobutton(
        root, text="sql2016", variable=sql_variant, value="sql2016"
    ).grid(row=8, column=1, sticky="w")
    tk.Radiobutton(
        root, text="sqldev2016", variable=sql_variant, value="sqldev2016"
    ).grid(row=9, column=1, sticky="w")

    restart = tk.BooleanVar(value=True)
    tk.Checkbutton(
        root, 
        text="Reiniciar o computador após a instalação",
        variable=restart,
    ).grid(row=10, column=0, columnspan=2, padx=10, pady=10)

    status_labels = {}
    status_frame = tk.Frame(root)
    status_frame.grid(row=11, column=0, columnspan=2, padx=10, pady=10)
    status_names = ("terminal.exe", "recursos.exe", "download.exe")
    for row, name in enumerate(status_names):
        tk.Label(status_frame, text=f"{name}: ").grid(row=row, column=0, sticky="e")
        status_labels[name] = tk.Label(status_frame, text="aguardando")
        status_labels[name].grid(row=row, column=1, sticky="w")

    def update_status(name, state):
        try:
            root.after(0, lambda: status_labels[name].config(text=state))
        except tk.TclError:
            pass

    button = tk.Button(
        root,
        text="Preparar e continuar",
        command=lambda: start(
            version_entry,
            computer_name_entry,
            option,
            release_channel,
            sql_variant,
            restart,
            update_status,
            root,
            button,
        ),
    )
    button.grid(row=12, column=0, columnspan=2, padx=10, pady=15)
    root.mainloop()
