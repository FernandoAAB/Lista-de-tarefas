import tkinter as tk
from tkinter import ttk, font, messagebox
from tkinter import PhotoImage
import sys
import os
import json
import uuid


# Paleta de cores (mais elegante / mais contraste)

COR_BG_PRINCIPAL = "#181825"       # Fundo do app
COR_BG_CARD = "#232336"            # Fundo dos itens da lista
COR_BG_CARD_HOVER = "#2b2b42"      # Hover do card
COR_BORDA_CARD = "#31324a"         # Borda sutil do card
COR_TEXTO = "#cdd6f4"              # Texto principal
COR_TEXTO_MUTED = "#6c7086"        # Texto secundário/placeholder
COR_TEXTO_CONCLUIDA = "#585b70"    # Texto de tarefas concluídas
COR_ACCENT = "#89b4fa"             # Azul destaque
COR_ACCENT_HOVER = "#a6c8ff"
COR_ACCENT_TEXT = "#11111b"        # Texto dentro do botão destaque
COR_PERIGO = "#f38ba8"             # Vermelho suave (deletar)
COR_PERIGO_HOVER = "#fb7fa4"

FONTE_BASE = "Segoe UI"            # Fallback melhor entre plataformas que "Garamond"


# Caminhos

if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PASTA_ICONS = os.path.join(BASE_DIR, "img_ico")
os.makedirs(PASTA_ICONS, exist_ok=True)

# Correção: o arquivo de dados agora fica junto do app, não dentro de img_ico
PASTA_SALVAMENTO = os.path.dirname(os.path.abspath(sys.argv[0]))
ARQUIVO_TAREFAS = os.path.join(PASTA_SALVAMENTO, "tns.txt")


# Fonte com fallback seguro

def escolher_fonte():
    familias = set(font.families())
    for candidata in (FONTE_BASE, "Garamond", "Segoe UI", "Helvetica", "Arial"):
        if candidata in familias:
            return candidata
    return "TkDefaultFont"


class AppTarefas:
    def __init__(self):
        self.janela = tk.Tk()
        self.janela.title("Tarefas Diárias")
        self.janela.configure(bg=COR_BG_PRINCIPAL)
        self.janela.geometry("520x640")
        self.janela.minsize(420, 420)

        self.fonte_nome = escolher_fonte()
        self.tarefas = []          # lista de dicts: {id, texto, feita}
        self.widgets_por_id = {}   # id -> dict com referências de widgets
        self.id_em_edicao = None
        self.campo_com_placeholder = True

        self._definir_icone_janela()
        self._carregar_icones_acao()
        self._montar_interface()
        self._carregar_tarefas()

        self.janela.protocol("WM_DELETE_WINDOW", self._fechar_aplicacao)

    
    # Ícones
    
    def _definir_icone_janela(self):
        caminho_icone = os.path.join(PASTA_ICONS, "app.png")
        try:
            icone = PhotoImage(file=caminho_icone)
            self.janela.iconphoto(True, icone)
            self._icone_janela_ref = icone  # evitar garbage collection
        except Exception:
            pass  # segue sem ícone customizado, não é crítico

    def _carregar_icones_acao(self):
        self.icon_editar = self._carregar_png_seguro("editar.png")
        self.icon_deletar = self._carregar_png_seguro("deletar.png")

    @staticmethod
    def _carregar_png_seguro(nome_arquivo):
        caminho = os.path.join(PASTA_ICONS, nome_arquivo)
        try:
            return PhotoImage(file=caminho)
        except Exception:
            return None  # os botões usam texto/emoji como fallback

    
    # Interface
    
    def _montar_interface(self):
        # Cabeçalho
        cabecalho = tk.Frame(self.janela, bg=COR_BG_PRINCIPAL)
        cabecalho.pack(pady=(24, 4), fill=tk.X, padx=24)

        fonte_titulo = font.Font(family=self.fonte_nome, size=22, weight="bold")
        tk.Label(
            cabecalho, text="Tarefas Diárias", font=fonte_titulo,
            bg=COR_BG_PRINCIPAL, fg=COR_TEXTO, anchor="w"
        ).pack(fill=tk.X)

        self.label_progresso = tk.Label(
            cabecalho, text="", font=(self.fonte_nome, 11),
            bg=COR_BG_PRINCIPAL, fg=COR_TEXTO_MUTED, anchor="w"
        )
        self.label_progresso.pack(fill=tk.X, pady=(2, 0))

        linha_accent = tk.Frame(self.janela, bg=COR_ACCENT, height=2)
        linha_accent.pack(fill=tk.X, padx=24, pady=(10, 0))

        # Entrada + botão adicionar
        frame_entrada = tk.Frame(self.janela, bg=COR_BG_PRINCIPAL)
        frame_entrada.pack(pady=16, padx=24, fill=tk.X)

        self.entrada_tarefa = tk.Entry(
            frame_entrada, font=(self.fonte_nome, 13), relief=tk.FLAT,
            bg=COR_BG_CARD, fg=COR_TEXTO_MUTED, insertbackground=COR_TEXTO,
        )
        self.entrada_tarefa.insert(0, "Escreva sua tarefa aqui")
        self.entrada_tarefa.bind("<FocusIn>", self._ao_focar_entrada)
        self.entrada_tarefa.bind("<FocusOut>", self._ao_desfocar_entrada)
        self.entrada_tarefa.bind("<Return>", self._confirmar_entrada)
        self.entrada_tarefa.bind("<Escape>", self._cancelar_edicao)
        self.entrada_tarefa.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=8)

        self.botao_confirmar = self._botao(
            frame_entrada, "Adicionar", self._confirmar_entrada,
            bg=COR_ACCENT, bg_hover=COR_ACCENT_HOVER, fg=COR_ACCENT_TEXT, width=12
        )
        self.botao_confirmar.pack(side=tk.LEFT, padx=(10, 0))

        self.botao_cancelar = self._botao(
            frame_entrada, "Cancelar", self._cancelar_edicao,
            bg=COR_BG_CARD, bg_hover=COR_BORDA_CARD, fg=COR_TEXTO, width=10
        )
        # só aparece durante a edição (pack sob demanda)

        # Área de rolagem com a lista de tarefas
        frame_lista = tk.Frame(self.janela, bg=COR_BG_PRINCIPAL)
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 18))

        self.canvas = tk.Canvas(frame_lista, bg=COR_BG_PRINCIPAL, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Vertical.TScrollbar", gripcount=0, background=COR_BORDA_CARD,
            troughcolor=COR_BG_PRINCIPAL, bordercolor=COR_BG_PRINCIPAL,
            lightcolor=COR_BG_PRINCIPAL, darkcolor=COR_BG_PRINCIPAL, arrowsize=12,
        )
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas_interior = tk.Frame(self.canvas, bg=COR_BG_PRINCIPAL)
        self._janela_canvas = self.canvas.create_window((0, 0), window=self.canvas_interior, anchor="nw")
        self.canvas_interior.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._janela_canvas, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._rolar_mouse)

        self.label_vazio = tk.Label(
            self.canvas_interior, text="Nenhuma tarefa por aqui ✨\nAdicione a primeira acima.",
            font=(self.fonte_nome, 12), bg=COR_BG_PRINCIPAL, fg=COR_TEXTO_MUTED, justify="center",
        )

    def _rolar_mouse(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _botao(self, parent, texto, comando, bg, bg_hover, fg, width=None, small=False):
        botao = tk.Button(
            parent, text=texto, command=comando, bg=bg, fg=fg,
            activebackground=bg_hover, activeforeground=fg, relief=tk.FLAT,
            font=(self.fonte_nome, 10 if small else 11, "bold"), width=width,
            bd=0, cursor="hand2", padx=6 if small else 0, pady=4 if small else 8,
        )
        botao.bind("<Enter>", lambda e: botao.config(bg=bg_hover))
        botao.bind("<Leave>", lambda e: botao.config(bg=bg))
        return botao

    
    # Entrada de texto (placeholder / foco)
    
    def _ao_focar_entrada(self, event):
        if self.campo_com_placeholder:
            self.entrada_tarefa.delete(0, tk.END)
            self.entrada_tarefa.configure(fg=COR_TEXTO)
            self.campo_com_placeholder = False

    def _ao_desfocar_entrada(self, event):
        if not self.entrada_tarefa.get().strip():
            self._mostrar_placeholder()

    def _mostrar_placeholder(self):
        self.entrada_tarefa.delete(0, tk.END)
        self.entrada_tarefa.insert(0, "Escreva sua tarefa aqui")
        self.entrada_tarefa.configure(fg=COR_TEXTO_MUTED)
        self.campo_com_placeholder = True

    
    # CRUD de tarefas
    
    def _confirmar_entrada(self, event=None):
        texto = "" if self.campo_com_placeholder else self.entrada_tarefa.get().strip()
        if not texto:
            messagebox.showwarning("Entrada inválida", "Por favor, insira uma tarefa válida.")
            return

        if self.id_em_edicao is not None:
            self._atualizar_texto_tarefa(self.id_em_edicao, texto)
            self._sair_modo_edicao()
        else:
            self._criar_tarefa(texto)

        self._mostrar_placeholder()
        self.entrada_tarefa.focus_set()
        self._mostrar_placeholder()
        self._salvar_tarefas()

    def _criar_tarefa(self, texto, feita=False, tarefa_id=None):
        tarefa_id = tarefa_id or str(uuid.uuid4())
        dados = {"id": tarefa_id, "texto": texto, "feita": feita}
        self.tarefas.append(dados)
        self._renderizar_item(dados)
        self._atualizar_estado_vazio()
        self._atualizar_progresso()
        return tarefa_id

    def _renderizar_item(self, dados):
        card = tk.Frame(self.canvas_interior, bg=COR_BG_CARD, bd=0, highlightthickness=1,
                         highlightbackground=COR_BORDA_CARD, highlightcolor=COR_BORDA_CARD)
        card.pack(fill=tk.X, padx=4, pady=5)

        def on_enter(e):
            card.config(bg=COR_BG_CARD_HOVER)
            for w in (checkbox, label, botao_editar, botao_deletar):
                w.config(bg=COR_BG_CARD_HOVER)

        def on_leave(e):
            card.config(bg=COR_BG_CARD)
            for w in (checkbox, label, botao_editar, botao_deletar):
                w.config(bg=COR_BG_CARD)

        checkbox = tk.Label(
            card, text=("☑" if dados["feita"] else "☐"), font=(self.fonte_nome, 15),
            bg=COR_BG_CARD, fg=(COR_ACCENT if dados["feita"] else COR_TEXTO_MUTED), cursor="hand2",
        )
        checkbox.pack(side=tk.LEFT, padx=(12, 4), pady=10)
        checkbox.bind("<Button-1>", lambda e, i=dados["id"]: self._alternar_concluida(i))

        cor_texto = COR_TEXTO_CONCLUIDA if dados["feita"] else COR_TEXTO
        label = tk.Label(
            card, text=dados["texto"], font=(self.fonte_nome, 13), bg=COR_BG_CARD, fg=cor_texto,
            anchor="w", justify="left", wraplength=300,
        )
        if dados["feita"]:
            label.config(font=(self.fonte_nome, 13, "overstrike"))
        label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, pady=10)

        botao_deletar = tk.Button(
            card, image=self.icon_deletar, text=("" if self.icon_deletar else "🗑"),
            command=lambda i=dados["id"]: self._confirmar_delete(i), bg=COR_BG_CARD,
            activebackground=COR_PERIGO_HOVER, relief=tk.FLAT, bd=0, cursor="hand2",
            fg=COR_PERIGO, font=(self.fonte_nome, 12),
        )
        botao_deletar.pack(side=tk.RIGHT, padx=8)

        botao_editar = tk.Button(
            card, image=self.icon_editar, text=("" if self.icon_editar else "✎"),
            command=lambda i=dados["id"]: self._entrar_modo_edicao(i), bg=COR_BG_CARD,
            activebackground=COR_ACCENT_HOVER, relief=tk.FLAT, bd=0, cursor="hand2",
            fg=COR_ACCENT, font=(self.fonte_nome, 12),
        )
        botao_editar.pack(side=tk.RIGHT, padx=4)

        for w in (card, checkbox, label):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        self.widgets_por_id[dados["id"]] = {
            "card": card, "checkbox": checkbox, "label": label,
        }
        self.canvas_interior.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _alternar_concluida(self, tarefa_id):
        dados = self._buscar_tarefa(tarefa_id)
        if not dados:
            return
        dados["feita"] = not dados["feita"]
        refs = self.widgets_por_id[tarefa_id]
        refs["checkbox"].config(
            text=("☑" if dados["feita"] else "☐"),
            fg=(COR_ACCENT if dados["feita"] else COR_TEXTO_MUTED),
        )
        fonte_base = (self.fonte_nome, 13, "overstrike") if dados["feita"] else (self.fonte_nome, 13)
        refs["label"].config(font=fonte_base, fg=(COR_TEXTO_CONCLUIDA if dados["feita"] else COR_TEXTO))
        self._atualizar_progresso()
        self._salvar_tarefas()

    def _entrar_modo_edicao(self, tarefa_id):
        dados = self._buscar_tarefa(tarefa_id)
        if not dados:
            return
        self.id_em_edicao = tarefa_id
        self.campo_com_placeholder = False
        self.entrada_tarefa.delete(0, tk.END)
        self.entrada_tarefa.insert(0, dados["texto"])
        self.entrada_tarefa.configure(fg=COR_TEXTO)
        self.entrada_tarefa.focus_set()
        self.botao_confirmar.config(text="Salvar")
        self.botao_cancelar.pack(side=tk.LEFT, padx=(8, 0))
        self.widgets_por_id[tarefa_id]["card"].config(highlightbackground=COR_ACCENT)

    def _sair_modo_edicao(self):
        if self.id_em_edicao and self.id_em_edicao in self.widgets_por_id:
            self.widgets_por_id[self.id_em_edicao]["card"].config(highlightbackground=COR_BORDA_CARD)
        self.id_em_edicao = None
        self.botao_confirmar.config(text="Adicionar")
        self.botao_cancelar.pack_forget()

    def _cancelar_edicao(self, event=None):
        if self.id_em_edicao is not None:
            self._sair_modo_edicao()
            self._mostrar_placeholder()

    def _atualizar_texto_tarefa(self, tarefa_id, novo_texto):
        dados = self._buscar_tarefa(tarefa_id)
        if dados:
            dados["texto"] = novo_texto
            self.widgets_por_id[tarefa_id]["label"].config(text=novo_texto)

    def _confirmar_delete(self, tarefa_id):
        dados = self._buscar_tarefa(tarefa_id)
        if not dados:
            return
        if messagebox.askyesno("Excluir tarefa", f'Excluir "{dados["texto"]}"?'):
            self._deletar_tarefa(tarefa_id)

    def _deletar_tarefa(self, tarefa_id):
        if self.id_em_edicao == tarefa_id:
            self._sair_modo_edicao()
        refs = self.widgets_por_id.pop(tarefa_id, None)
        if refs:
            refs["card"].destroy()
        self.tarefas = [t for t in self.tarefas if t["id"] != tarefa_id]
        self.canvas_interior.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self._atualizar_estado_vazio()
        self._atualizar_progresso()
        self._salvar_tarefas()

    def _buscar_tarefa(self, tarefa_id):
        return next((t for t in self.tarefas if t["id"] == tarefa_id), None)

    def _atualizar_estado_vazio(self):
        if self.tarefas:
            self.label_vazio.pack_forget()
        else:
            self.label_vazio.pack(pady=40)

    def _atualizar_progresso(self):
        total = len(self.tarefas)
        feitas = sum(1 for t in self.tarefas if t["feita"])
        if total == 0:
            self.label_progresso.config(text="")
        else:
            self.label_progresso.config(text=f"{feitas} de {total} concluídas")

    
    # Persistência (JSON simples em tns.txt)
    
    def _salvar_tarefas(self):
        try:
            with open(ARQUIVO_TAREFAS, "w", encoding="utf-8") as arquivo:
                json.dump(self.tarefas, arquivo, ensure_ascii=False, indent=2)
        except OSError as erro:
            messagebox.showerror("Erro ao salvar", f"Não foi possível salvar as tarefas:\n{erro}")

    def _carregar_tarefas(self):
        if not os.path.exists(ARQUIVO_TAREFAS):
            self._atualizar_estado_vazio()
            self._atualizar_progresso()
            return
        try:
            with open(ARQUIVO_TAREFAS, "r", encoding="utf-8") as arquivo:
                conteudo = arquivo.read().strip()
            if not conteudo:
                dados_salvos = []
            elif conteudo.startswith("["):
                dados_salvos = json.loads(conteudo)
            else:
                # Compatibilidade com o formato antigo (uma tarefa por linha)
                dados_salvos = [{"id": str(uuid.uuid4()), "texto": linha, "feita": False}
                                 for linha in conteudo.splitlines() if linha.strip()]
        except (json.JSONDecodeError, OSError):
            dados_salvos = []

        for item in dados_salvos:
            self._criar_tarefa(item.get("texto", ""), item.get("feita", False), item.get("id"))

        self._atualizar_estado_vazio()
        self._atualizar_progresso()

    def _fechar_aplicacao(self):
        self._salvar_tarefas()
        self.janela.destroy()

    def executar(self):
        self.janela.mainloop()


if __name__ == "__main__":
    AppTarefas().executar()
