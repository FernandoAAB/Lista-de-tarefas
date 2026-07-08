import tkinter as tk
from tkinter import ttk, font, messagebox
from tkinter import PhotoImage
import sys
import os

COR_BG_PRINCIPAL = "#1e1e2e"       # Fundo do app
COR_BG_CARD = "#2a2a35"            # Fundo dos itens da lista
COR_TEXTO = "#cdd6f4"              # Texto principal
COR_TEXTO_MUTED = "#7f849c"        # Texto secundário/placeholder
COR_ACCENT = "#89b4fa"             # Azul destaque (botões principais)
COR_ACCENT_TEXT = "#11111b"        # Texto dentro do botão destaque

if getattr(sys, 'frozen', False):
    # Se o app foi compilado com o PyInstaller
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    # Se está rodando o script .py puro
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PASTA_ICONS = os.path.join(BASE_DIR, "img_ico")
PASTA_SALVAMENTO = os.path.dirname(os.path.abspath(sys.argv[0]))
ARQUIVO_TAREFAS = os.path.join(PASTA_SALVAMENTO, "tns.txt")

PASTA_ICONS = os.path.join(BASE_DIR, "img_ico")

ARQUIVO_TAREFAS = os.path.join(PASTA_ICONS, "tns.txt")
os.makedirs(PASTA_ICONS, exist_ok=True)

janela = tk.Tk()
janela.title("Tarefas Diárias")
janela.configure(bg=COR_BG_PRINCIPAL)
janela.geometry("503x600")

frame_em_edicao = None

def adicionar_tarefa(event=None):
    global frame_em_edicao
    tarefa = entrada_tarefa.get().strip()
    if tarefa and tarefa != "Escreva sua tarefa aqui":
        if frame_em_edicao is not None:
            atualizar_tarefa(tarefa)
            frame_em_edicao = None
        else:
            adicionar_item_tarefa(tarefa)
        entrada_tarefa.delete(0, tk.END)
        ao_sair_foco(None)
        salvar_tarefas()
    else:
        messagebox.showwarning("Entrada Inválida", "Por favor, insira uma tarefa válida.")

def adicionar_item_tarefa(tarefa):
    frame_tarefa = tk.Frame(canvas_interior, bg=COR_BG_CARD, bd=0)

    label_tarefa = tk.Label(frame_tarefa, text=tarefa, font=("Garamond", 16), bg=COR_BG_CARD, fg=COR_TEXTO, width=25, height=2, anchor="w")
    label_tarefa.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=5)

    botao_editar = tk.Button(frame_tarefa, image=icon_editar, command=lambda f=frame_tarefa, l=label_tarefa: preparar_edicao(f, l), bg=COR_BG_CARD, activebackground=COR_BG_CARD, relief=tk.FLAT)
    botao_editar.pack(side=tk.RIGHT, padx=5)

    botao_deletar = tk.Button(frame_tarefa, image=icon_deletar, command=lambda f=frame_tarefa: deletar_tarefa(f), bg=COR_BG_CARD, activebackground=COR_BG_CARD, relief=tk.FLAT)
    botao_deletar.pack(side=tk.RIGHT, padx=5)

    frame_tarefa.pack(fill=tk.X, padx=5, pady=5)

    checkbutton = ttk.Checkbutton(frame_tarefa, command=lambda label=label_tarefa: alternar_sublinhado(label))
    checkbutton.pack(side=tk.RIGHT, padx=5)

    canvas_interior.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


def preparar_edicao(frame_tarefa, label_tarefa):
    global frame_em_edicao
    frame_em_edicao = frame_tarefa
    entrada_tarefa.delete(0, tk.END)
    entrada_tarefa.insert(0, label_tarefa.cget("text"))
    entrada_tarefa.configure(fg=COR_TEXTO)


def atualizar_tarefa(nova_tarefa):
    global frame_em_edicao
    if frame_em_edicao is None:
        return
    for widget in frame_em_edicao.winfo_children():
        if isinstance(widget, tk.Label):
            widget.config(text=nova_tarefa)
            break
    salvar_tarefas()


def deletar_tarefa(frame_tarefa):
    frame_tarefa.destroy()
    canvas_interior.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))
    salvar_tarefas()


def alternar_sublinhado(label):
    fonte_atual = label.cget("font")
    if "overstrike" in fonte_atual:
        nova_fonte = fonte_atual.replace(" overstrike", "")
        label.config(font=nova_fonte, fg=COR_TEXTO)
    else:
        nova_fonte = fonte_atual + " overstrike"
        label.config(font=nova_fonte, fg=COR_TEXTO_MUTED)

def ao_clicar_entrada(event):
    if entrada_tarefa.get() == "Escreva sua tarefa aqui":
        entrada_tarefa.delete(0, tk.END)
        entrada_tarefa.configure(fg=COR_TEXTO)

def ao_sair_foco(event):
    if not entrada_tarefa.get().strip():
        entrada_tarefa.delete(0, tk.END)
        entrada_tarefa.insert(0, "Escreva sua tarefa aqui")
        entrada_tarefa.configure(fg=COR_TEXTO_MUTED)

def salvar_tarefas():
    if 'canvas_interior' not in globals():
        return

    tarefas = []
    for frame in canvas_interior.winfo_children():
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Label):
                texto = widget.cget("text").strip()
                if texto:
                    tarefas.append(texto)
                break

    with open(ARQUIVO_TAREFAS, 'w', encoding='utf-8') as arquivo:
        arquivo.write("\n".join(tarefas))


def carregar_tarefas():
    if not os.path.exists(ARQUIVO_TAREFAS):
        return

    with open(ARQUIVO_TAREFAS, 'r', encoding='utf-8') as arquivo:
        linhas = [linha.strip() for linha in arquivo.readlines() if linha.strip()]

    for tarefa in linhas:
        adicionar_item_tarefa(tarefa)


def fechar_aplicacao():
    salvar_tarefas()
    janela.destroy()

# Carregar ícones
icon_editar = PhotoImage(file=os.path.join(PASTA_ICONS, "editar.png")).subsample(1)
icon_deletar = PhotoImage(file=os.path.join(PASTA_ICONS, "deletar.png")).subsample(1)

# Cabeçalho
fonte_cabecalho = font.Font(family="Garamond", size=24, weight="bold")
rotulo_cabecalho = tk.Label(janela, text="Tarefas Diárias", font=fonte_cabecalho, bg=COR_BG_PRINCIPAL, fg=COR_TEXTO)
rotulo_cabecalho.pack(pady=20)

frame = tk.Frame(janela, bg=COR_BG_PRINCIPAL)
frame.pack(pady=10)

# Entrada de texto combinando com o visual dark
entrada_tarefa = tk.Entry(frame, font=("Garamond", 14), relief=tk.FLAT, bg=COR_BG_CARD, fg=COR_TEXTO_MUTED, width=25, insertbackground=COR_TEXTO)
entrada_tarefa.insert(0, "Escreva sua tarefa aqui")
entrada_tarefa.bind("<FocusIn>", ao_clicar_entrada)
entrada_tarefa.bind("<FocusOut>", ao_sair_foco)
entrada_tarefa.pack(side=tk.LEFT, padx=10, ipady=4) # Adicionado um leve padding interno para elegância

# Botão Adicionar
botao_adicionar = tk.Button(frame, text="Adicionar", command=adicionar_tarefa, bg=COR_ACCENT, fg=COR_ACCENT_TEXT, activebackground=COR_TEXTO, height=1, width=12, font=("Roboto", 11, "bold"), relief=tk.FLAT)
botao_adicionar.pack(side=tk.LEFT, padx=10)
janela.bind("<Return>", adicionar_tarefa)

# Customização da área do Canvas de scroll
frame_lista_tarefas = tk.Frame(janela, bg=COR_BG_PRINCIPAL)
frame_lista_tarefas.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

canvas = tk.Canvas(frame_lista_tarefas, bg=COR_BG_PRINCIPAL, highlightthickness=0) # Removida borda branca nativa do canvas
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Estilização sutil da Scrollbar
estilo = ttk.Style()
estilo.theme_use("clam")
estilo.configure("Vertical.TScrollbar", gripcount=0, background=COR_BG_CARD, troughcolor=COR_BG_PRINCIPAL, bordercolor=COR_BG_PRINCIPAL, lightcolor=COR_BG_PRINCIPAL, darkcolor=COR_BG_PRINCIPAL)

scrollbar = ttk.Scrollbar(frame_lista_tarefas, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

canvas.configure(yscrollcommand=scrollbar.set)
canvas_interior = tk.Frame(canvas, bg=COR_BG_PRINCIPAL)
canvas.create_window((0, 0), window=canvas_interior, anchor="nw")
canvas_interior.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

carregar_tarefas()
janela.protocol("WM_DELETE_WINDOW", fechar_aplicacao)

janela.mainloop()