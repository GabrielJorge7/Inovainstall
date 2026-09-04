import json
import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from preparacao import STATE_FILE, resource_path, LOG_DIR


def get_process_status(process_name):
    """Lê o status e log de um processo de background"""
    log_path = os.path.join(LOG_DIR, f"{process_name}.log")
    status = "aguardando"
    last_lines = ""
    
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as log_file:
                content = log_file.read()
                lines = content.split("\n")
                # Mostrar mais linhas para recursos.exe (15 linhas)
                num_lines = 15 if process_name == "recursos.exe" else 10
                last_lines = "\n".join(lines[-num_lines:])
                
                if "Código de saída: 0" in content:
                    status = "✓ Concluído"
                elif "Código de saída:" in content:
                    status = "✗ Erro"
                elif content.strip():
                    status = "▶ Executando"
        except Exception:
            pass
    
    return status, last_lines


def update_background_status(status_labels, log_text, root):
    """Atualiza o status dos processos de background"""
    processes = ["terminal.exe", "recursos.exe"]
    
    for process in processes:
        status, log_content = get_process_status(process)
        if process in status_labels:
            status_labels[process].config(text=status)
    
    # Mostrar logs dos últimos processos - foco em recursos.exe
    if log_text:
        log_text.config(state=tk.NORMAL)
        log_text.delete("1.0", tk.END)
        
        # Mostrar recursos.exe primeiro (prioridade)
        _, recursos_log = get_process_status("recursos.exe")
        if recursos_log.strip():
            log_text.insert(tk.END, "=== RECURSOS.EXE (Preparação em Background) ===\n", "titulo")
            log_text.insert(tk.END, recursos_log + "\n\n")
        else:
            log_text.insert(tk.END, "=== RECURSOS.EXE ===\n", "titulo")
            log_text.insert(tk.END, "Aguardando logs...\n\n")
        
        # Mostrar terminal.exe em seguida
        _, terminal_log = get_process_status("terminal.exe")
        if terminal_log.strip():
            log_text.insert(tk.END, "=== TERMINAL.EXE ===\n", "titulo")
            log_text.insert(tk.END, terminal_log + "\n\n")
        
        # Configurar tags para estilo
        log_text.tag_config("titulo", foreground="white", background="blue")
        
        log_text.config(state=tk.DISABLED)
        log_text.see(tk.END)
    
    # Atualizar a cada 1 segundo para recursos.exe (mais frequente)
    root.after(1000, lambda: update_background_status(status_labels, log_text, root))


def run_installation(option, computer_name, restart, root, button, status_label, error_text):
    try:
        status_label.config(text="▶ Instalando...", foreground="orange")
        root.update()
        
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = subprocess.SW_HIDE
        subprocess.run(
            [resource_path("instalacao.exe"), option, computer_name],
            check=True,
            startupinfo=startup_info,
            creationflags=subprocess.CREATE_NO_WINDOW,
            cwd=os.path.dirname(resource_path("instalacao.exe")),
        )
        os.remove(STATE_FILE)
        status_label.config(text="✓ Instalação concluída", foreground="green")
        
        error_text.config(state=tk.NORMAL)
        error_text.delete("1.0", tk.END)
        error_text.insert(tk.END, "✓ Instalação finalizada com sucesso!")
        error_text.config(state=tk.DISABLED)
        
        root.after(0, lambda: messagebox.showinfo("Info", "Instalação concluída."))
    except (OSError, subprocess.CalledProcessError) as error:
        status_label.config(text="✗ Erro na instalação", foreground="red")
        
        error_text.config(state=tk.NORMAL)
        error_text.delete("1.0", tk.END)
        error_text.insert(tk.END, f"❌ ERRO:\n{str(error)}")
        error_text.config(state=tk.DISABLED)
        
        root.after(0, lambda: button.config(state=tk.NORMAL))


def start(option, computer_name, restart, root, button, status_label, error_text):
    button.config(state=tk.DISABLED)
    status_label.config(text="▶ Iniciando...", foreground="blue")
    threading.Thread(
        target=run_installation,
        args=(option, computer_name.get().strip(), restart, root, button, status_label, error_text),
        daemon=True,
    ).start()


def run():
    try:
        with open(STATE_FILE, encoding="utf-8") as state_file:
            state = json.load(state_file)
        option = state["option"]
        restart = state.get("restart", False)
    except (OSError, json.JSONDecodeError, KeyError) as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro", f"Não foi possível carregar a preparação:\n{error}")
        root.destroy()
        return

    root = tk.Tk()
    root.title("InovaInstall - Instalação")
    root.iconbitmap(resource_path("logo.ico"))
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = min(800, max(480, screen_width - 80))
    window_height = min(850, max(480, screen_height - 80))
    root.geometry(f"{window_width}x{window_height}")
    root.minsize(480, 480)
    root.resizable(True, True)
    
    # Seção 1: Status de Instalação
    install_status_frame = tk.LabelFrame(root, text="Status da Instalação", padx=10, pady=10)
    install_status_frame.pack(fill=tk.X, padx=10, pady=10)
    
    status_label = tk.Label(
        install_status_frame, 
        text="⏳ Aguardando início",
        foreground="gray",
        font=("Arial", 12, "bold")
    )
    status_label.pack(anchor="w")
    
    # Seção 2: Informações básicas
    info_frame = tk.LabelFrame(root, text="Configuração", padx=10, pady=10)
    info_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Label(info_frame, text="Nome do computador (opcional):").pack(anchor="w")
    computer_name = tk.Entry(info_frame)
    computer_name.pack(fill=tk.X, pady=(0, 10))
    tk.Label(info_frame, text="Em branco: manter o nome atual.", font=("Arial", 8)).pack(anchor="w")
    
    # Seção 3: Mensagens de Erro/Status
    error_frame = tk.LabelFrame(root, text="Mensagens", padx=10, pady=10)
    error_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    error_text = scrolledtext.ScrolledText(error_frame, height=6, width=80, state=tk.DISABLED)
    error_text.pack(fill=tk.BOTH, expand=True)
    
    # Seção 4: Status de processos em background
    status_frame = tk.LabelFrame(root, text="Status dos Processos de Preparação", padx=10, pady=10)
    status_frame.pack(fill=tk.X, padx=10, pady=10)
    
    status_labels = {}
    for process in ["terminal.exe", "recursos.exe"]:
        frame = tk.Frame(status_frame)
        frame.pack(fill=tk.X, pady=5)
        tk.Label(frame, text=f"{process}:", width=15, anchor="w").pack(side=tk.LEFT)
        status_labels[process] = tk.Label(frame, text="aguardando", foreground="blue")
        status_labels[process].pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Seção 5: Log de execução - FOCO EM RECURSOS.EXE
    log_frame = tk.LabelFrame(root, text="🔍 Log de Execução (Recursos em Background)", padx=10, pady=10)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    log_text = scrolledtext.ScrolledText(log_frame, height=12, width=80, state=tk.DISABLED, bg="black", fg="white")
    log_text.pack(fill=tk.BOTH, expand=True)
    
    # Seção 6: Botões de ação
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def refresh_status():
        update_background_status(status_labels, log_text, root)
    
    tk.Button(button_frame, text="Atualizar Status", command=refresh_status).pack(side=tk.LEFT, padx=5)
    
    button = tk.Button(
        button_frame,
        text="Iniciar Instalação",
        command=lambda: start(option, computer_name, restart, root, button, status_label, error_text),
    )
    button.pack(side=tk.LEFT, padx=5)
    
    # Iniciar atualização automática do status
    update_background_status(status_labels, log_text, root)
    
    root.mainloop()
