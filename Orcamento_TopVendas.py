# -*- coding: utf-8 -*-
"""
================================================================================
 ORCAMENTO TopVendas - Formulario de Orcamento (Firebird 2.5)
================================================================================
Formulario de ORCAMENTO com layout inspirado na tela principal do TopVendas.

Recursos:
  - Conexao ao banco Firebird 2.5 (TOPVENDAS.FDB)
  - Escolha de produtos por DIGITACAO (codigo / codigo de barras) ou
    por GRUPO -> produto (botoes)
  - Escolha do cliente (com cliente padrao "CLIENTE NAO INFORMADO")
  - Desconto por ITEM ou desconto em TODA a venda (R$ ou %)
  - Impressao em formato de CUPOM (visualizacao + impressao + salvar TXT)

Tabelas usadas:
  - THOSPEDES         -> clientes   (ID_HOSPEDE, NOME, CPF, CELULAR ...)
  - TPRODUTOS         -> produtos   (ID_PRODUTO, CODIGO, CODIGO_BARRAS,
                                     DESCRICAO, ID_GRUPO_PRODUTO, PRECO_VENDA,
                                     UNIDADE, ATIVO ...)
  - TGRUPOS_PRODUTOS  -> grupos     (ID_GRUPO_PRODUTO, DESCRICAO, EXIBIR_PDV ...)

Caminho do banco: C:\\Topvendas\\BD\\TOPVENDAS.FDB

Requisitos:
  pip install fdb
  (o cliente Firebird - fbclient.dll - ja vem instalado com o TopVendas)
================================================================================
"""

import os
import sys
import json
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext

# ----------------------------------------------------------------------------
# Driver Firebird (fdb). Import protegido para exibir mensagem amigavel.
# ----------------------------------------------------------------------------
try:
    import fdb
    HAS_FDB = True
    _FDB_IMPORT_ERR = ""
except Exception as _e:
    HAS_FDB = False
    _FDB_IMPORT_ERR = str(_e)

# ============================================================================
# CONFIGURACAO
# ============================================================================
APP_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
CONFIG_FILE = os.path.join(APP_DIR, "orcamento_config.json")

# Valores padrao de conexao (podem ser alterados pela engrenagem "Config")
DEFAULT_CONFIG = {
    "host": "localhost",
    "database": r"C:\Topvendas\BD\TOPVENDAS.FDB",
    "user": "SYSDBA",
    "password": "masterkey",
    "charset": "WIN1252",
    "empresa_nome": "TopVendas",
    "validade_dias": 7,
    "somente_ativos": True,
    "impressora": ""
}

CLIENTE_PADRAO = "CLIENTE NAO INFORMADO"

# ============================================================================
# PALETA DE CORES (inspirada na tela do TopVendas)
# ============================================================================
COR_TOPBAR   = "#0C4C8A"   # barra de titulo (azul escuro)
COR_STATUS   = "#0C4C8A"   # barra de status inferior
COR_AZUL     = "#2E97D4"   # painel azul principal
COR_AZUL_ESC = "#1F7CB5"   # divisor / detalhes
COR_BRANCO   = "#FFFFFF"
COR_NAVY     = "#0C4C8A"   # texto navy nos botoes brancos
COR_CINZA    = "#F0F3F7"   # fundo painel direito
COR_TOTALBG  = "#E7EEF6"   # caixa do valor total
COR_TEXTO    = "#222222"
COR_VERDE    = "#1E9E5A"
COR_VERMELHO = "#C0392B"
COR_CINZA_BTN = "#D9E2EC"


# ============================================================================
# UTILITARIOS
# ============================================================================
def fmt_money(v):
    """Formata numero no padrao brasileiro: 1.234,56"""
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"


def parse_money(txt):
    """Converte texto '1.234,56' ou '1234.56' em float."""
    try:
        s = str(txt).strip().replace("R$", "").strip()
        if not s:
            return 0.0
        # remove separador de milhar e usa ponto como decimal
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def parse_qtd(txt):
    try:
        s = str(txt).strip().replace(",", ".")
        return float(s) if s else 0.0
    except (ValueError, TypeError):
        return 0.0


def fmt_qtd(v):
    try:
        v = float(v)
        return str(int(v)) if v == int(v) else f"{v:.3f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return "0"


def as_ativo(valor):
    """Interpreta o campo ATIVO (pode ser 'S'/'N', 1/0, True/False)."""
    if valor is None:
        return True
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return int(valor) != 0
    s = str(valor).strip().upper()
    return s not in ("N", "0", "F", "FALSE", "NAO", "NÃO")


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update({k: saved[k] for k in saved if k in DEFAULT_CONFIG})
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print("Erro ao salvar config:", e)
        return False


# ============================================================================
# CAMADA DE BANCO DE DADOS (Firebird)
# ============================================================================
class Database:
    def __init__(self, config):
        self.config = config
        self.con = None

    def connect(self):
        if not HAS_FDB:
            raise RuntimeError(
                "A biblioteca 'fdb' nao esta instalada.\n\n"
                "Instale com:  pip install fdb\n\n"
                f"Detalhe: {_FDB_IMPORT_ERR}")
        host = (self.config.get("host") or "localhost").strip()
        database = (self.config.get("database") or "").strip()
        # DSN no formato host:caminho (recomendado no Firebird 2.5)
        if host and host.lower() not in ("", "none"):
            dsn = f"{host}:{database}"
        else:
            dsn = database
        self.con = fdb.connect(
            dsn=dsn,
            user=self.config.get("user", "SYSDBA"),
            password=self.config.get("password", "masterkey"),
            charset=self.config.get("charset", "WIN1252"),
        )
        return self.con

    def close(self):
        try:
            if self.con:
                self.con.close()
        except Exception:
            pass
        self.con = None

    def _ensure(self):
        if self.con is None:
            self.connect()
        return self.con

    def _column_exists(self, table, column):
        try:
            cur = self._ensure().cursor()
            cur.execute(
                "SELECT COUNT(*) FROM RDB$RELATION_FIELDS "
                "WHERE RDB$RELATION_NAME = ? AND RDB$FIELD_NAME = ?",
                (table.upper(), column.upper()))
            return (cur.fetchone()[0] or 0) > 0
        except Exception:
            return False

    def testar(self):
        """Testa a conexao e retorna (ok, mensagem)."""
        try:
            con = self.connect()
            cur = con.cursor()
            cur.execute("SELECT 1 FROM RDB$DATABASE")
            cur.fetchone()
            return True, "Conexao realizada com sucesso!"
        except Exception as e:
            return False, str(e)
        finally:
            self.close()

    def listar_grupos(self):
        """Retorna [(id, descricao)] dos grupos de produtos."""
        cur = self._ensure().cursor()
        tem_exibir = self._column_exists("TGRUPOS_PRODUTOS", "EXIBIR_PDV")
        if tem_exibir:
            cur.execute(
                "SELECT ID_GRUPO_PRODUTO, DESCRICAO, EXIBIR_PDV "
                "FROM TGRUPOS_PRODUTOS ORDER BY DESCRICAO")
        else:
            cur.execute(
                "SELECT ID_GRUPO_PRODUTO, DESCRICAO "
                "FROM TGRUPOS_PRODUTOS ORDER BY DESCRICAO")
        grupos = []
        for row in cur.fetchall():
            gid = row[0]
            desc = (row[1] or "").strip() if row[1] else ""
            if tem_exibir:
                exibir = row[2]
                if not as_ativo(exibir):
                    continue
            grupos.append((gid, desc or f"Grupo {gid}"))
        return grupos

    def listar_produtos(self, somente_ativos=True):
        """Retorna lista de dicts de produtos."""
        cur = self._ensure().cursor()
        tem_ativo = self._column_exists("TPRODUTOS", "ATIVO")
        tem_barras = self._column_exists("TPRODUTOS", "CODIGO_BARRAS")
        tem_unidade = self._column_exists("TPRODUTOS", "UNIDADE")

        campos = ["ID_PRODUTO", "CODIGO", "DESCRICAO", "ID_GRUPO_PRODUTO", "PRECO_VENDA"]
        if tem_barras:
            campos.append("CODIGO_BARRAS")
        if tem_unidade:
            campos.append("UNIDADE")
        if tem_ativo:
            campos.append("ATIVO")

        sql = "SELECT " + ", ".join(campos) + " FROM TPRODUTOS ORDER BY DESCRICAO"
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        produtos = []
        for row in cur.fetchall():
            r = dict(zip(cols, row))
            if somente_ativos and tem_ativo and not as_ativo(r.get("ATIVO")):
                continue
            produtos.append({
                "id": r.get("ID_PRODUTO"),
                "codigo": (str(r.get("CODIGO")).strip() if r.get("CODIGO") is not None else ""),
                "barras": (str(r.get("CODIGO_BARRAS")).strip() if r.get("CODIGO_BARRAS") else ""),
                "descricao": ((r.get("DESCRICAO") or "").strip() if r.get("DESCRICAO") else ""),
                "grupo_id": r.get("ID_GRUPO_PRODUTO"),
                "preco": float(r.get("PRECO_VENDA") or 0),
                "unidade": ((r.get("UNIDADE") or "UN").strip() if r.get("UNIDADE") else "UN"),
            })
        return produtos

    def buscar_produto_por_codigo(self, codigo, somente_ativos=True):
        """Busca 1 produto por CODIGO ou CODIGO_BARRAS."""
        cur = self._ensure().cursor()
        tem_barras = self._column_exists("TPRODUTOS", "CODIGO_BARRAS")
        tem_unidade = self._column_exists("TPRODUTOS", "UNIDADE")
        campos = ["ID_PRODUTO", "CODIGO", "DESCRICAO", "ID_GRUPO_PRODUTO", "PRECO_VENDA"]
        if tem_barras:
            campos.append("CODIGO_BARRAS")
        if tem_unidade:
            campos.append("UNIDADE")
        sel = "SELECT " + ", ".join(campos) + " FROM TPRODUTOS WHERE "
        if tem_barras:
            sel += "CODIGO = ? OR CODIGO_BARRAS = ?"
            params = (codigo, codigo)
        else:
            sel += "CODIGO = ?"
            params = (codigo,)
        cur.execute(sel, params)
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        r = dict(zip(cols, row))
        return {
            "id": r.get("ID_PRODUTO"),
            "codigo": (str(r.get("CODIGO")).strip() if r.get("CODIGO") is not None else ""),
            "barras": (str(r.get("CODIGO_BARRAS")).strip() if r.get("CODIGO_BARRAS") else ""),
            "descricao": ((r.get("DESCRICAO") or "").strip() if r.get("DESCRICAO") else ""),
            "grupo_id": r.get("ID_GRUPO_PRODUTO"),
            "preco": float(r.get("PRECO_VENDA") or 0),
            "unidade": ((r.get("UNIDADE") or "UN").strip() if r.get("UNIDADE") else "UN"),
        }

    def listar_clientes(self, filtro=""):
        """Retorna [(id, nome, cpf, celular)] dos clientes (THOSPEDES)."""
        cur = self._ensure().cursor()
        tem_cpf = self._column_exists("THOSPEDES", "CPF")
        tem_cel = self._column_exists("THOSPEDES", "CELULAR")
        campos = ["ID_HOSPEDE", "NOME"]
        if tem_cpf:
            campos.append("CPF")
        if tem_cel:
            campos.append("CELULAR")
        sql = "SELECT " + ", ".join(campos) + " FROM THOSPEDES"
        params = ()
        if filtro:
            sql += " WHERE UPPER(NOME) LIKE ?"
            params = (f"%{filtro.upper()}%",)
        sql += " ORDER BY NOME"
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        result = []
        for row in cur.fetchall():
            r = dict(zip(cols, row))
            result.append((
                r.get("ID_HOSPEDE"),
                (r.get("NOME") or "").strip() if r.get("NOME") else "",
                (str(r.get("CPF")).strip() if r.get("CPF") else ""),
                (str(r.get("CELULAR")).strip() if r.get("CELULAR") else ""),
            ))
        return result

    def obter_nome_empresa(self):
        """Tenta obter o nome da empresa/hotel do banco (best effort)."""
        for tabela, campo in (("THOTEL", "NOME"), ("THOTEL", "RAZAO_SOCIAL"),
                              ("TEMPRESA", "NOME"), ("TEMPRESA", "RAZAO_SOCIAL")):
            try:
                if self._column_exists(tabela, campo):
                    cur = self._ensure().cursor()
                    cur.execute(f"SELECT FIRST 1 {campo} FROM {tabela}")
                    row = cur.fetchone()
                    if row and row[0]:
                        return str(row[0]).strip()
            except Exception:
                continue
        return None


# ============================================================================
# ITEM DO ORCAMENTO
# ============================================================================
class ItemOrcamento:
    def __init__(self, produto_id, descricao, unitario, qtd=1.0, unidade="UN"):
        self.produto_id = produto_id
        self.descricao = descricao
        self.unitario = float(unitario)
        self.qtd = float(qtd)
        self.unidade = unidade
        self.desconto = 0.0  # desconto em R$ no item

    @property
    def bruto(self):
        return self.qtd * self.unitario

    @property
    def total(self):
        t = self.bruto - self.desconto
        return t if t > 0 else 0.0


# ============================================================================
# APLICACAO
# ============================================================================
class OrcamentoApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.db = Database(self.config)

        self.produtos = []          # todos os produtos carregados
        self.grupos = []            # [(id, desc)]
        self.itens = []             # itens do orcamento
        self.grupo_filtro = None    # None = TODOS
        self.cliente_id = None
        self.cliente_nome = CLIENTE_PADRAO
        self.desc_geral_tipo = "R$"  # "R$" ou "%"
        self.desc_geral_valor = 0.0

        self.root.title("TopVendas - Orcamento")
        self.root.configure(bg=COR_AZUL)
        self.root.geometry("1024x640")
        self.root.minsize(960, 600)
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        self._setup_style()
        self._build_ui()

        # Carrega dados apos montar a UI
        self.root.after(200, self._conectar_e_carregar)

    # ---------------------------------------------------------------- style
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Orc.Treeview",
                        background=COR_BRANCO, fieldbackground=COR_BRANCO,
                        foreground=COR_TEXTO, rowheight=26,
                        font=("Segoe UI", 10), borderwidth=0)
        style.configure("Orc.Treeview.Heading",
                        background="#DCE6F1", foreground=COR_NAVY,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Orc.Treeview", background=[("selected", "#2E97D4")],
                  foreground=[("selected", "#FFFFFF")])

    # ------------------------------------------------------------------- UI
    def _build_ui(self):
        # ---- Header ----
        header = tk.Frame(self.root, bg=COR_TOPBAR, height=58)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(header, text="TopVendas", bg=COR_TOPBAR, fg="#FFFFFF",
                 font=("Georgia", 26, "bold italic")).pack(side="left", padx=18)

        tk.Label(header, text="ORCAMENTO", bg=COR_TOPBAR, fg="#BBD4EC",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=6, pady=18)

        # botao config (engrenagem)
        btn_cfg = tk.Label(header, text="\u2699", bg=COR_TOPBAR, fg="#FFFFFF",
                           font=("Segoe UI", 20), cursor="hand2")
        btn_cfg.pack(side="right", padx=16)
        btn_cfg.bind("<Button-1>", lambda e: self._abrir_config())

        # Botao chamativo: abrir o sistema de vendas
        self.btn_vender = tk.Button(
            header, text="\U0001F6D2  ABRIR O SISTEMA PARA VENDER",
            command=self._abrir_sistema_vender,
            bg=COR_VERDE, fg="#FFFFFF",
            activebackground="#17A85A", activeforeground="#FFFFFF",
            relief="flat", bd=0, cursor="hand2",
            font=("Segoe UI", 12, "bold"), padx=18, pady=6)
        self.btn_vender.pack(side="right", padx=10, pady=8)

        # efeito hover para deixar o botao mais vistoso
        def _hover_in(_e):
            self.btn_vender.config(bg="#25B869")
        def _hover_out(_e):
            self.btn_vender.config(bg=COR_VERDE)
        self.btn_vender.bind("<Enter>", _hover_in)
        self.btn_vender.bind("<Leave>", _hover_out)

        # ---- Status bar ----
        self.status = tk.Frame(self.root, bg=COR_STATUS, height=24)
        self.status.pack(fill="x", side="bottom")
        self.status.pack_propagate(False)
        self.lbl_status = tk.Label(
            self.status,
            text=f"{self.config.get('host')}:{self.config.get('database')}",
            bg=COR_STATUS, fg="#CFE0F0", font=("Segoe UI", 8))
        self.lbl_status.pack(side="left", padx=10)
        self.lbl_conn = tk.Label(self.status, text="Conectando...",
                                 bg=COR_STATUS, fg="#FFD27F", font=("Segoe UI", 8))
        self.lbl_conn.pack(side="right", padx=10)

        # ---- Corpo: esquerda (azul) + direita (branco) ----
        body = tk.Frame(self.root, bg=COR_AZUL)
        body.pack(fill="both", expand=True)

        # Painel direito (montado primeiro para reservar largura)
        right = tk.Frame(body, bg=COR_CINZA, width=390)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._build_right_panel(right)

        # Painel esquerdo azul
        left = tk.Frame(body, bg=COR_AZUL)
        left.pack(side="left", fill="both", expand=True)
        self._build_left_panel(left)

    def _build_left_panel(self, parent):
        # Area de grupos
        grupos_wrap = tk.Frame(parent, bg=COR_AZUL)
        grupos_wrap.pack(fill="x", padx=14, pady=(14, 6))
        tk.Label(grupos_wrap, text="Grupos", bg=COR_AZUL, fg="#DCEAF6",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.frame_grupos = tk.Frame(grupos_wrap, bg=COR_AZUL)
        self.frame_grupos.pack(fill="x")

        # Divisor
        tk.Frame(parent, bg="#BFE0F2", height=2).pack(fill="x", padx=14, pady=4)

        # Area de produtos (scroll)
        prod_wrap = tk.Frame(parent, bg=COR_AZUL)
        prod_wrap.pack(fill="both", expand=True, padx=14, pady=(4, 12))
        tk.Label(prod_wrap, text="Produtos", bg=COR_AZUL, fg="#DCEAF6",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))

        canvas = tk.Canvas(prod_wrap, bg=COR_AZUL, highlightthickness=0)
        vsb = ttk.Scrollbar(prod_wrap, orient="vertical", command=canvas.yview)
        self.frame_produtos = tk.Frame(canvas, bg=COR_AZUL)
        self.frame_produtos.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._prod_win = canvas.create_window((0, 0), window=self.frame_produtos, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(self._prod_win, width=e.width))
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _wheel(ev):
            try:
                canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")
            except Exception:
                pass
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        self._prod_canvas = canvas

    def _build_right_panel(self, parent):
        pad = 10

        # ===================================================================
        # TOPO (fixo no alto): Cliente + Codigo/Qtde
        # ===================================================================
        # --- Cliente ---
        cli = tk.Frame(parent, bg=COR_CINZA)
        cli.pack(side="top", fill="x", padx=pad, pady=(pad, 2))
        tk.Label(cli, text="Cliente", bg=COR_CINZA, fg=COR_NAVY,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        cli_row = tk.Frame(cli, bg=COR_CINZA)
        cli_row.pack(fill="x", pady=(2, 0))
        self.lbl_cliente = tk.Label(cli_row, text=self.cliente_nome,
                                    bg="#FFFFFF", fg=COR_VERMELHO,
                                    font=("Segoe UI", 10, "bold"),
                                    anchor="w", relief="solid", bd=1, padx=6)
        self.lbl_cliente.pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(cli_row, text="...", command=self._selecionar_cliente,
                  bg=COR_CINZA_BTN, fg=COR_NAVY, relief="flat", width=3,
                  font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left", padx=(4, 0))

        # --- Codigo + Qtde ---
        top_row = tk.Frame(parent, bg=COR_CINZA)
        top_row.pack(side="top", fill="x", padx=pad, pady=(4, 2))

        col_cod = tk.Frame(top_row, bg=COR_CINZA)
        col_cod.pack(side="left", fill="x", expand=True)
        tk.Label(col_cod, text="Codigo", bg=COR_CINZA, fg=COR_NAVY,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cod_row = tk.Frame(col_cod, bg=COR_CINZA)
        cod_row.pack(fill="x", pady=(2, 0))
        self.ent_codigo = tk.Entry(cod_row, font=("Segoe UI", 11), relief="solid", bd=1)
        self.ent_codigo.pack(side="left", fill="x", expand=True, ipady=3)
        self.ent_codigo.bind("<Return>", lambda e: self._add_por_codigo())
        tk.Button(cod_row, text="...", command=self._buscar_produto_dialog,
                  bg=COR_CINZA_BTN, fg=COR_NAVY, relief="flat", width=3,
                  font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left", padx=(4, 0))

        tk.Label(top_row, text="x", bg=COR_CINZA, fg="#8AA0B4",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=6, pady=(18, 0))

        col_qtd = tk.Frame(top_row, bg=COR_CINZA)
        col_qtd.pack(side="left")
        tk.Label(col_qtd, text="Qtde", bg=COR_CINZA, fg=COR_NAVY,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        qtd_row = tk.Frame(col_qtd, bg=COR_CINZA)
        qtd_row.pack(fill="x", pady=(2, 0))
        self.ent_qtd = tk.Entry(qtd_row, font=("Segoe UI", 11), width=4,
                                relief="solid", bd=1, justify="center")
        self.ent_qtd.insert(0, "1")
        self.ent_qtd.pack(side="left", ipady=3)
        tk.Button(qtd_row, text="-", command=lambda: self._ajusta_qtd(-1),
                  bg=COR_CINZA_BTN, fg=COR_NAVY, relief="flat", width=2,
                  font=("Segoe UI", 11, "bold"), cursor="hand2").pack(side="left", padx=(3, 0))
        tk.Button(qtd_row, text="+", command=lambda: self._ajusta_qtd(1),
                  bg=COR_CINZA_BTN, fg=COR_NAVY, relief="flat", width=2,
                  font=("Segoe UI", 11, "bold"), cursor="hand2").pack(side="left", padx=(3, 0))
        tk.Button(qtd_row, text="\U0001F5D1", command=self._remover_item,
                  bg="#F3D2CE", fg=COR_VERMELHO, relief="flat", width=2,
                  font=("Segoe UI", 11), cursor="hand2").pack(side="left", padx=(3, 0))

        # ===================================================================
        # RODAPE (fixo embaixo) - empacotado de baixo para cima com side=bottom
        # Assim os botoes e o total ficam SEMPRE visiveis, mesmo em telas baixas
        # ===================================================================
        # --- Botoes finais (na base) ---
        btns = tk.Frame(parent, bg=COR_CINZA)
        btns.pack(side="bottom", fill="x", padx=pad, pady=(4, pad))
        tk.Button(btns, text="Cancelar", command=self._cancelar,
                  bg="#E3E9EF", fg="#44586B", relief="flat",
                  font=("Segoe UI", 10, "bold"), height=2, cursor="hand2").pack(
                      side="left", fill="x", expand=True, padx=(0, 3))
        tk.Button(btns, text="Imprimir", command=self._gerar_orcamento,
                  bg=COR_NAVY, fg="#FFFFFF", relief="flat",
                  font=("Segoe UI", 10, "bold"), height=2, cursor="hand2").pack(
                      side="left", fill="x", expand=True, padx=3)
        tk.Button(btns, text="Gerar Orcamento", command=self._gerar_orcamento,
                  bg=COR_VERDE, fg="#FFFFFF", relief="flat",
                  font=("Segoe UI", 10, "bold"), height=2, cursor="hand2").pack(
                      side="left", fill="x", expand=True, padx=(3, 0))

        # --- Caixa Valor Total ---
        total_box = tk.Frame(parent, bg=COR_TOTALBG, relief="solid", bd=1)
        total_box.pack(side="bottom", fill="x", padx=pad, pady=(0, 4))
        self.lbl_subtotal = tk.Label(total_box, text="Subtotal: R$ 0,00",
                                     bg=COR_TOTALBG, fg="#5A6B7B",
                                     font=("Segoe UI", 9))
        self.lbl_subtotal.pack(anchor="e", padx=10, pady=(3, 0))
        self.lbl_desc = tk.Label(total_box, text="Desconto: R$ 0,00",
                                 bg=COR_TOTALBG, fg=COR_VERMELHO,
                                 font=("Segoe UI", 9))
        self.lbl_desc.pack(anchor="e", padx=10)
        self.lbl_total = tk.Label(total_box, text="R$ 0,00", bg=COR_TOTALBG,
                                  fg="#111111", font=("Segoe UI", 22, "bold"))
        self.lbl_total.pack(anchor="e", padx=10, pady=(0, 4))

        # --- Rotulo Valor Total ---
        tk.Label(parent, text="Valor Total", bg=COR_CINZA, fg=COR_NAVY,
                 font=("Segoe UI", 12, "bold")).pack(side="bottom", anchor="w",
                                                      padx=pad, pady=(4, 0))

        # --- Desconto geral (venda) ---
        dg = tk.Frame(parent, bg=COR_CINZA)
        dg.pack(side="bottom", fill="x", padx=pad, pady=(2, 2))
        tk.Label(dg, text="Desconto (venda):", bg=COR_CINZA, fg=COR_NAVY,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        self.combo_desc = ttk.Combobox(dg, values=["R$", "%"], width=4,
                                       state="readonly")
        self.combo_desc.current(0)
        self.combo_desc.pack(side="left", padx=4)
        self.combo_desc.bind("<<ComboboxSelected>>", lambda e: self._atualizar_totais())
        self.ent_desc = tk.Entry(dg, font=("Segoe UI", 10), width=10,
                                 relief="solid", bd=1, justify="right")
        self.ent_desc.insert(0, "0,00")
        self.ent_desc.pack(side="left", padx=4, ipady=2)
        self.ent_desc.bind("<KeyRelease>", lambda e: self._atualizar_totais())

        # --- Botoes de item (editar qtd / desconto item / remover) ---
        item_btns = tk.Frame(parent, bg=COR_CINZA)
        item_btns.pack(side="bottom", fill="x", padx=pad, pady=(2, 2))
        tk.Button(item_btns, text="Editar Qtde", command=self._editar_qtd_item,
                  bg=COR_CINZA_BTN, fg=COR_NAVY, relief="flat",
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="left", padx=(0, 4))
        tk.Button(item_btns, text="Desconto Item", command=self._desconto_item,
                  bg=COR_CINZA_BTN, fg=COR_NAVY, relief="flat",
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="left", padx=4)
        tk.Button(item_btns, text="Remover", command=self._remover_item,
                  bg="#F3D2CE", fg=COR_VERMELHO, relief="flat",
                  font=("Segoe UI", 9, "bold"), cursor="hand2").pack(side="left", padx=4)

        # ===================================================================
        # MEIO (preenche o espaco restante): Tabela de itens
        # ===================================================================
        tab = tk.Frame(parent, bg=COR_CINZA)
        tab.pack(side="top", fill="both", expand=True, padx=pad, pady=(4, 2))
        cols = ("produto", "qtde", "unit", "total")
        self.tree = ttk.Treeview(tab, columns=cols, show="headings",
                                 style="Orc.Treeview", height=5)
        self.tree.heading("produto", text="Produto")
        self.tree.heading("qtde", text="Qtde")
        self.tree.heading("unit", text="Unitario")
        self.tree.heading("total", text="Total")
        self.tree.column("produto", width=160, anchor="w")
        self.tree.column("qtde", width=45, anchor="center")
        self.tree.column("unit", width=75, anchor="e")
        self.tree.column("total", width=75, anchor="e")
        vsb2 = ttk.Scrollbar(tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb2.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._editar_qtd_item())

    # ------------------------------------------------------- carregar dados
    def _conectar_e_carregar(self):
        try:
            self.db.connect()
            self.lbl_conn.config(text="Conectado", fg="#9BE29B")
            # nome empresa
            nome = self.db.obter_nome_empresa()
            if nome:
                self.config["empresa_nome"] = nome
            self.grupos = self.db.listar_grupos()
            self.produtos = self.db.listar_produtos(
                somente_ativos=self.config.get("somente_ativos", True))
            self._render_grupos()
            self._render_produtos()
        except Exception as e:
            self.lbl_conn.config(text="Sem conexao", fg="#FF9B9B")
            messagebox.showerror(
                "Erro de Conexao",
                "Nao foi possivel conectar ao banco de dados Firebird.\n\n"
                f"Caminho: {self.config.get('host')}:{self.config.get('database')}\n\n"
                "VERIFIQUE:\n"
                "1. O servico do Firebird esta em execucao\n"
                "2. O caminho do banco esta correto\n"
                "3. Usuario/senha (padrao: SYSDBA/masterkey)\n"
                "4. A biblioteca 'fdb' esta instalada (pip install fdb)\n\n"
                f"Detalhe tecnico:\n{e}")

    def _render_grupos(self):
        for w in self.frame_grupos.winfo_children():
            w.destroy()

        def _btn(texto, cmd, ativo=False):
            b = tk.Button(self.frame_grupos, text=texto, command=cmd,
                          bg=(COR_NAVY if ativo else COR_BRANCO),
                          fg=("#FFFFFF" if ativo else COR_NAVY),
                          relief="flat", font=("Segoe UI", 9, "bold"),
                          width=15, height=2, cursor="hand2",
                          wraplength=110, activebackground="#EAF2FA")
            return b

        # Botao TODOS
        b = _btn("TODOS", lambda: self._filtrar_grupo(None),
                 ativo=(self.grupo_filtro is None))
        b.grid(row=0, column=0, padx=4, pady=4, sticky="w")

        col = 1
        row = 0
        max_cols = 6
        for gid, desc in self.grupos:
            b = _btn(desc.upper(), lambda g=gid: self._filtrar_grupo(g),
                     ativo=(self.grupo_filtro == gid))
            b.grid(row=row, column=col, padx=4, pady=4, sticky="w")
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _render_produtos(self):
        for w in self.frame_produtos.winfo_children():
            w.destroy()

        lista = self.produtos
        if self.grupo_filtro is not None:
            lista = [p for p in self.produtos if p["grupo_id"] == self.grupo_filtro]

        if not lista:
            tk.Label(self.frame_produtos,
                     text="Nenhum produto neste grupo.",
                     bg=COR_AZUL, fg="#DCEAF6",
                     font=("Segoe UI", 11)).grid(row=0, column=0, padx=6, pady=10)
            return

        col = 0
        row = 0
        max_cols = 6
        for p in lista:
            texto = f"{p['descricao']}\nR$ {fmt_money(p['preco'])}"
            b = tk.Button(self.frame_produtos, text=texto,
                          command=lambda pr=p: self._add_produto(pr),
                          bg=COR_BRANCO, fg=COR_NAVY, relief="flat",
                          font=("Segoe UI", 8, "bold"), width=15, height=3,
                          cursor="hand2", wraplength=110, justify="center",
                          activebackground="#EAF2FA")
            b.grid(row=row, column=col, padx=5, pady=5, sticky="nw")
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _filtrar_grupo(self, gid):
        self.grupo_filtro = gid
        self._render_grupos()
        self._render_produtos()

    # ------------------------------------------------------- itens / carrinho
    def _get_qtd_entry(self):
        q = parse_qtd(self.ent_qtd.get())
        return q if q > 0 else 1.0

    def _ajusta_qtd(self, delta):
        q = self._get_qtd_entry() + delta
        if q < 1:
            q = 1
        self.ent_qtd.delete(0, tk.END)
        self.ent_qtd.insert(0, fmt_qtd(q))

    def _add_produto(self, prod, qtd=None):
        if qtd is None:
            qtd = self._get_qtd_entry()
        # se ja existe, soma quantidade
        for it in self.itens:
            if it.produto_id == prod["id"]:
                it.qtd += qtd
                self._render_itens()
                return
        item = ItemOrcamento(prod["id"], prod["descricao"], prod["preco"],
                             qtd, prod.get("unidade", "UN"))
        self.itens.append(item)
        self._render_itens()
        # reset qtd para 1
        self.ent_qtd.delete(0, tk.END)
        self.ent_qtd.insert(0, "1")

    def _add_por_codigo(self):
        codigo = self.ent_codigo.get().strip()
        if not codigo:
            return
        # primeiro tenta no cache
        prod = None
        for p in self.produtos:
            if p["codigo"] == codigo or (p["barras"] and p["barras"] == codigo):
                prod = p
                break
        if not prod:
            try:
                prod = self.db.buscar_produto_por_codigo(
                    codigo, self.config.get("somente_ativos", True))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao buscar produto:\n{e}")
                return
        self.ent_codigo.delete(0, tk.END)
        if prod:
            self._add_produto(prod)
        else:
            messagebox.showwarning("Nao encontrado",
                                   f"Nenhum produto com o codigo '{codigo}'.")

    def _buscar_produto_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Buscar Produto")
        dlg.geometry("620x460")
        dlg.configure(bg="#FFFFFF")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Buscar produto:", bg="#FFFFFF", fg=COR_NAVY,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        ent = tk.Entry(dlg, font=("Segoe UI", 11), relief="solid", bd=1)
        ent.pack(fill="x", padx=12, ipady=3)
        ent.focus_set()

        cols = ("cod", "desc", "preco")
        tv = ttk.Treeview(dlg, columns=cols, show="headings",
                          style="Orc.Treeview", height=14)
        tv.heading("cod", text="Codigo")
        tv.heading("desc", text="Descricao")
        tv.heading("preco", text="Preco")
        tv.column("cod", width=90, anchor="w")
        tv.column("desc", width=360, anchor="w")
        tv.column("preco", width=90, anchor="e")
        tv.pack(fill="both", expand=True, padx=12, pady=8)

        def _fill(filtro=""):
            tv.delete(*tv.get_children())
            f = filtro.lower()
            for p in self.produtos:
                if f and f not in p["descricao"].lower() and f not in p["codigo"].lower():
                    continue
                tv.insert("", "end", iid=str(p["id"]),
                          values=(p["codigo"], p["descricao"], fmt_money(p["preco"])))

        _fill()
        ent.bind("<KeyRelease>", lambda e: _fill(ent.get()))

        def _sel():
            s = tv.selection()
            if not s:
                return
            pid = int(s[0])
            prod = next((p for p in self.produtos if p["id"] == pid), None)
            if prod:
                self._add_produto(prod)
            dlg.destroy()

        tv.bind("<Double-1>", lambda e: _sel())
        tk.Button(dlg, text="Adicionar", command=_sel, bg=COR_VERDE, fg="#FFFFFF",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2").pack(pady=(0, 10))

    def _item_selecionado(self):
        s = self.tree.selection()
        if not s:
            return None
        idx = self.tree.index(s[0])
        if 0 <= idx < len(self.itens):
            return idx
        return None

    def _editar_qtd_item(self):
        idx = self._item_selecionado()
        if idx is None:
            messagebox.showinfo("Selecione", "Selecione um item na lista.")
            return
        it = self.itens[idx]
        nova = simpledialog.askfloat("Editar Quantidade",
                                     f"Nova quantidade para:\n{it.descricao}",
                                     initialvalue=it.qtd, minvalue=0.001,
                                     parent=self.root)
        if nova:
            it.qtd = nova
            self._render_itens()

    def _desconto_item(self):
        idx = self._item_selecionado()
        if idx is None:
            messagebox.showinfo("Selecione", "Selecione um item na lista.")
            return
        it = self.itens[idx]
        dlg = tk.Toplevel(self.root)
        dlg.title("Desconto no Item")
        dlg.configure(bg="#FFFFFF")
        dlg.geometry("340x210")
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Label(dlg, text=it.descricao, bg="#FFFFFF", fg=COR_NAVY,
                 font=("Segoe UI", 10, "bold"), wraplength=300).pack(pady=(12, 4), padx=12)
        tk.Label(dlg, text=f"Bruto: R$ {fmt_money(it.bruto)}", bg="#FFFFFF",
                 fg="#555").pack()
        frm = tk.Frame(dlg, bg="#FFFFFF")
        frm.pack(pady=8)
        tipo = ttk.Combobox(frm, values=["R$", "%"], width=4, state="readonly")
        tipo.current(0)
        tipo.pack(side="left", padx=4)
        ent = tk.Entry(frm, font=("Segoe UI", 11), width=12, relief="solid", bd=1,
                       justify="right")
        ent.insert(0, fmt_money(it.desconto))
        ent.pack(side="left", padx=4, ipady=2)
        ent.focus_set()

        def _ok():
            val = parse_money(ent.get())
            if tipo.get() == "%":
                desc = it.bruto * val / 100.0
            else:
                desc = val
            if desc < 0:
                desc = 0
            if desc > it.bruto:
                desc = it.bruto
            it.desconto = desc
            self._render_itens()
            dlg.destroy()

        tk.Button(dlg, text="Aplicar", command=_ok, bg=COR_VERDE, fg="#FFFFFF",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2").pack(pady=8)

    def _remover_item(self):
        idx = self._item_selecionado()
        if idx is None:
            messagebox.showinfo("Selecione", "Selecione um item para remover.")
            return
        del self.itens[idx]
        self._render_itens()

    def _render_itens(self):
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.itens):
            desc = it.descricao
            if it.desconto > 0:
                desc = f"{desc}  (desc. R$ {fmt_money(it.desconto)})"
            self.tree.insert("", "end", values=(
                desc, fmt_qtd(it.qtd),
                fmt_money(it.unitario), fmt_money(it.total)))
        self._atualizar_totais()

    def _calc_totais(self):
        subtotal = sum(it.total for it in self.itens)
        val = parse_money(self.ent_desc.get())
        if self.combo_desc.get() == "%":
            desc_geral = subtotal * val / 100.0
        else:
            desc_geral = val
        if desc_geral < 0:
            desc_geral = 0
        if desc_geral > subtotal:
            desc_geral = subtotal
        # desconto total = descontos de item ja aplicados no it.total + desconto geral
        desc_itens = sum(it.desconto for it in self.itens)
        total = subtotal - desc_geral
        if total < 0:
            total = 0
        return subtotal, desc_geral, desc_itens, total

    def _atualizar_totais(self):
        subtotal, desc_geral, desc_itens, total = self._calc_totais()
        self.lbl_subtotal.config(text=f"Subtotal: R$ {fmt_money(subtotal)}")
        desc_total = desc_geral + desc_itens
        self.lbl_desc.config(text=f"Desconto: R$ {fmt_money(desc_total)}")
        self.lbl_total.config(text=f"R$ {fmt_money(total)}")

    # ------------------------------------------------------------- cliente
    def _selecionar_cliente(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Selecionar Cliente")
        dlg.geometry("640x480")
        dlg.configure(bg="#FFFFFF")
        dlg.transient(self.root)
        dlg.grab_set()

        top = tk.Frame(dlg, bg="#FFFFFF")
        top.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(top, text="Buscar cliente:", bg="#FFFFFF", fg=COR_NAVY,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ent = tk.Entry(top, font=("Segoe UI", 11), relief="solid", bd=1)
        ent.pack(fill="x", ipady=3)
        ent.focus_set()

        cols = ("nome", "cpf", "cel")
        tv = ttk.Treeview(dlg, columns=cols, show="headings",
                          style="Orc.Treeview", height=14)
        tv.heading("nome", text="Nome")
        tv.heading("cpf", text="CPF")
        tv.heading("cel", text="Celular")
        tv.column("nome", width=340, anchor="w")
        tv.column("cpf", width=140, anchor="w")
        tv.column("cel", width=120, anchor="w")
        tv.pack(fill="both", expand=True, padx=12, pady=8)

        cache = {}

        def _fill(filtro=""):
            tv.delete(*tv.get_children())
            cache.clear()
            try:
                lista = self.db.listar_clientes(filtro)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao buscar clientes:\n{e}", parent=dlg)
                return
            for cid, nome, cpf, cel in lista[:500]:
                iid = tv.insert("", "end", values=(nome, cpf, cel))
                cache[iid] = (cid, nome)

        _fill()
        ent.bind("<Return>", lambda e: _fill(ent.get()))

        def _sel():
            s = tv.selection()
            if not s:
                return
            cid, nome = cache.get(s[0], (None, None))
            if nome:
                self.cliente_id = cid
                self.cliente_nome = nome
                self.lbl_cliente.config(text=nome, fg=COR_NAVY)
            dlg.destroy()

        tv.bind("<Double-1>", lambda e: _sel())

        btns = tk.Frame(dlg, bg="#FFFFFF")
        btns.pack(fill="x", padx=12, pady=(0, 10))
        tk.Button(btns, text="Selecionar", command=_sel, bg=COR_VERDE, fg="#FFFFFF",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2").pack(side="left")

        def _limpar():
            self.cliente_id = None
            self.cliente_nome = CLIENTE_PADRAO
            self.lbl_cliente.config(text=CLIENTE_PADRAO, fg=COR_VERMELHO)
            dlg.destroy()

        tk.Button(btns, text="Cliente Padrao", command=_limpar,
                  bg=COR_CINZA_BTN, fg=COR_NAVY, relief="flat",
                  font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left", padx=8)

    # ----------------------------------------------------------- acoes finais
    def _cancelar(self):
        if self.itens and not messagebox.askyesno(
                "Cancelar", "Deseja limpar o orcamento atual?"):
            return
        self.itens = []
        self.cliente_id = None
        self.cliente_nome = CLIENTE_PADRAO
        self.lbl_cliente.config(text=CLIENTE_PADRAO, fg=COR_VERMELHO)
        self.ent_desc.delete(0, tk.END)
        self.ent_desc.insert(0, "0,00")
        self.combo_desc.current(0)
        self._render_itens()

    def _gerar_orcamento(self):
        if not self.itens:
            messagebox.showwarning("Orcamento vazio",
                                   "Adicione ao menos um produto ao orcamento.")
            return
        cupom = self._montar_cupom()
        self._preview_cupom(cupom)

    # --------------------------------------------------------------- cupom
    def _montar_cupom(self, largura=48):
        subtotal, desc_geral, desc_itens, total = self._calc_totais()
        sep = "-" * largura
        eq = "=" * largura
        L = []

        def center(t):
            t = str(t)[:largura]
            return t.center(largura)

        def right(t):
            t = str(t)[:largura]
            return t.rjust(largura)

        L.append(eq)
        L.append(center(self.config.get("empresa_nome", "TopVendas")))
        L.append(center("ORCAMENTO / PROPOSTA"))
        L.append(sep)
        agora = datetime.datetime.now()
        L.append(f"Data....: {agora.strftime('%d/%m/%Y %H:%M')}")
        validade = self.config.get("validade_dias", 7)
        venc = agora + datetime.timedelta(days=int(validade))
        L.append(f"Validade: {int(validade)} dias (ate {venc.strftime('%d/%m/%Y')})")
        L.append(f"Cliente.: {self.cliente_nome}")
        L.append(sep)
        # cabecalho itens
        L.append(f"{'ITEM':<4}{'DESCRICAO':<24}{'QTD':>4}{'UNIT':>8}{'TOTAL':>8}")
        L.append(sep)
        for i, it in enumerate(self.itens, 1):
            nome = it.descricao
            qtd = fmt_qtd(it.qtd)
            unit = fmt_money(it.unitario)
            tot = fmt_money(it.total)
            if len(nome) > 24 or it.desconto > 0:
                L.append(f"{i}. {nome}")
                if it.desconto > 0:
                    L.append(f"   desconto item: -R$ {fmt_money(it.desconto)}")
                L.append(right(f"{qtd} x {unit} = R$ {tot}"))
            else:
                L.append(f"{i:<4}{nome:<24}{qtd:>4}{unit:>8}{tot:>8}")
        L.append(sep)
        L.append(right(f"SUBTOTAL: R$ {fmt_money(subtotal)}"))
        if desc_geral > 0:
            tipo = self.combo_desc.get()
            valor_txt = self.ent_desc.get().strip()
            if tipo == "%":
                L.append(right(f"DESCONTO ({valor_txt}%): -R$ {fmt_money(desc_geral)}"))
            else:
                L.append(right(f"DESCONTO: -R$ {fmt_money(desc_geral)}"))
        L.append(right(f"TOTAL: R$ {fmt_money(total)}"))
        L.append(eq)
        L.append(center("*** Este documento nao e fiscal ***"))
        L.append(center("Orcamento sujeito a alteracao"))
        L.append(center("Obrigado pela preferencia!"))
        L.append(eq)
        return "\n".join(L)

    def _preview_cupom(self, texto):
        dlg = tk.Toplevel(self.root)
        dlg.title("Orcamento - Cupom")
        dlg.geometry("460x620")
        dlg.configure(bg="#FFFFFF")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Orcamento", bg="#FFFFFF", fg=COR_NAVY,
                 font=("Segoe UI", 14, "bold")).pack(pady=8)

        txt = scrolledtext.ScrolledText(dlg, font=("Courier New", 10),
                                        bg="#F8FAFC", fg="#111111", wrap="none")
        txt.pack(fill="both", expand=True, padx=12, pady=4)
        txt.insert("1.0", texto)
        txt.config(state="disabled")

        lbl_st = tk.Label(dlg, text="", bg="#FFFFFF", fg="#555",
                          font=("Segoe UI", 9, "italic"))
        lbl_st.pack()

        btns = tk.Frame(dlg, bg="#FFFFFF")
        btns.pack(fill="x", padx=12, pady=10)

        def _imprimir():
            ok, msg = self._imprimir_texto(texto)
            lbl_st.config(text=msg, fg=(COR_VERDE if ok else COR_VERMELHO))
            if ok:
                messagebox.showinfo("Impressao", msg, parent=dlg)
            else:
                messagebox.showerror("Impressao", msg, parent=dlg)

        def _salvar():
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = filedialog.asksaveasfilename(
                parent=dlg, defaultextension=".txt",
                initialfile=f"orcamento_{ts}.txt",
                filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(texto)
                    lbl_st.config(text=f"Salvo: {os.path.basename(path)}", fg=COR_VERDE)
                except Exception as e:
                    messagebox.showerror("Erro", str(e), parent=dlg)

        def _copiar():
            self.root.clipboard_clear()
            self.root.clipboard_append(texto)
            lbl_st.config(text="Copiado para a area de transferencia.", fg=COR_VERDE)

        tk.Button(btns, text="Imprimir", command=_imprimir, bg=COR_NAVY, fg="#FFFFFF",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2", width=10).pack(side="left", padx=3)
        tk.Button(btns, text="Salvar TXT", command=_salvar, bg=COR_VERDE, fg="#FFFFFF",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2", width=10).pack(side="left", padx=3)
        tk.Button(btns, text="Copiar", command=_copiar, bg=COR_CINZA_BTN, fg=COR_NAVY,
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2", width=8).pack(side="left", padx=3)
        tk.Button(btns, text="Fechar", command=dlg.destroy, bg="#E3E9EF", fg="#44586B",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2", width=8).pack(side="right", padx=3)

    def _imprimir_texto(self, texto):
        """Imprime o cupom. No Windows usa win32print (RAW) e cai em metodos
        alternativos. Retorna (ok, mensagem)."""
        import platform
        sistema = platform.system()
        impressora = (self.config.get("impressora") or "").strip()

        if sistema == "Windows":
            # 1) win32print RAW
            try:
                import win32print
                nome = impressora or win32print.GetDefaultPrinter()
                dados = ("\x1b\x40" + texto + "\n\n\n\n\x1d\x56\x42\x00")
                h = win32print.OpenPrinter(nome)
                try:
                    win32print.StartDocPrinter(h, 1, ("Orcamento", None, "RAW"))
                    win32print.StartPagePrinter(h)
                    win32print.WritePrinter(h, dados.encode("utf-8", errors="replace"))
                    win32print.EndPagePrinter(h)
                    win32print.EndDocPrinter(h)
                finally:
                    win32print.ClosePrinter(h)
                return True, f"Enviado para impressora: {nome}"
            except ImportError:
                pass
            except Exception as e:
                # tenta metodo notepad
                try:
                    import tempfile, subprocess
                    tmp = os.path.join(tempfile.gettempdir(), "orcamento_print.txt")
                    with open(tmp, "w", encoding="utf-8", errors="replace") as f:
                        f.write(texto)
                    subprocess.run(["notepad.exe", "/p", tmp], timeout=30)
                    return True, "Enviado via Bloco de Notas (impressora padrao)."
                except Exception as e2:
                    return False, f"Falha ao imprimir: {e} / {e2}"
            # 2) fallback notepad se win32print ausente
            try:
                import tempfile, subprocess
                tmp = os.path.join(tempfile.gettempdir(), "orcamento_print.txt")
                with open(tmp, "w", encoding="utf-8", errors="replace") as f:
                    f.write(texto)
                subprocess.run(["notepad.exe", "/p", tmp], timeout=30)
                return True, "Enviado via Bloco de Notas (impressora padrao)."
            except Exception as e:
                return False, f"Nao foi possivel imprimir: {e}"
        else:
            # Linux / macOS
            try:
                import tempfile, subprocess
                tmp = os.path.join(tempfile.gettempdir(), "orcamento_print.txt")
                with open(tmp, "w", encoding="utf-8", errors="replace") as f:
                    f.write(texto)
                cmd = ["lp"]
                if impressora:
                    cmd += ["-d", impressora]
                cmd.append(tmp)
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if r.returncode == 0:
                    return True, "Enviado para impressao (lp)."
                return False, f"Erro lp: {r.stderr}"
            except Exception as e:
                return False, f"Nao foi possivel imprimir: {e}"

    # ---------------------------------------------------- abrir sistema vender
    def _abrir_sistema_vender(self):
        """Fecha o orcamento e abre o sistema de vendas do TopVendas."""
        exe = r"C:\Topvendas\Topvendas_vender.exe"
        if self.itens:
            if not messagebox.askyesno(
                    "Abrir sistema de vendas",
                    "Existe um orcamento em andamento que sera descartado.\n\n"
                    "Deseja fechar o orcamento e abrir o sistema para vender?"):
                return
        import platform
        import subprocess
        try:
            if platform.system() == "Windows":
                if not os.path.exists(exe):
                    messagebox.showerror(
                        "Executavel nao encontrado",
                        f"Nao foi possivel localizar:\n{exe}\n\n"
                        "Verifique se o TopVendas esta instalado nesse caminho.")
                    return
                # abre o executavel de forma independente
                os.startfile(exe)  # noqa: S606 (Windows)
            else:
                # Ambientes nao-Windows (apenas para teste)
                subprocess.Popen([exe])
        except Exception as e:
            messagebox.showerror(
                "Erro ao abrir o sistema",
                f"Nao foi possivel abrir o sistema de vendas.\n\n"
                f"Caminho: {exe}\n\nDetalhe: {e}")
            return
        # fecha a conexao e encerra o formulario de orcamento
        try:
            self.db.close()
        except Exception:
            pass
        self.root.destroy()

    # ------------------------------------------------------------- config UI
    def _abrir_config(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Configuracao de Conexao")
        dlg.geometry("480x430")
        dlg.configure(bg="#FFFFFF")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Conexao Firebird", bg="#FFFFFF", fg=COR_NAVY,
                 font=("Segoe UI", 14, "bold")).pack(pady=10)

        frm = tk.Frame(dlg, bg="#FFFFFF")
        frm.pack(fill="x", padx=16)

        campos = [
            ("Host", "host"),
            ("Banco (caminho)", "database"),
            ("Usuario", "user"),
            ("Senha", "password"),
            ("Charset", "charset"),
            ("Nome Empresa", "empresa_nome"),
            ("Validade (dias)", "validade_dias"),
            ("Impressora (opcional)", "impressora"),
        ]
        entries = {}
        for i, (label, key) in enumerate(campos):
            tk.Label(frm, text=label + ":", bg="#FFFFFF", fg=COR_TEXTO,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=3)
            e = tk.Entry(frm, font=("Segoe UI", 10), width=34, relief="solid", bd=1)
            e.insert(0, str(self.config.get(key, "")))
            if key == "password":
                e.config(show="*")
            e.grid(row=i, column=1, sticky="w", padx=6, pady=3, ipady=2)
            entries[key] = e

        var_ativos = tk.BooleanVar(value=self.config.get("somente_ativos", True))
        tk.Checkbutton(frm, text="Mostrar somente produtos ativos",
                       variable=var_ativos, bg="#FFFFFF", fg=COR_TEXTO,
                       font=("Segoe UI", 10)).grid(row=len(campos), column=0,
                                                    columnspan=2, sticky="w", pady=6)

        def _coletar():
            cfg = dict(self.config)
            for key, e in entries.items():
                cfg[key] = e.get().strip()
            try:
                cfg["validade_dias"] = int(cfg.get("validade_dias") or 7)
            except ValueError:
                cfg["validade_dias"] = 7
            cfg["somente_ativos"] = var_ativos.get()
            return cfg

        def _testar():
            cfg = _coletar()
            ok, msg = Database(cfg).testar()
            if ok:
                messagebox.showinfo("Conexao", msg, parent=dlg)
            else:
                messagebox.showerror("Conexao", f"Falha:\n{msg}", parent=dlg)

        def _salvar():
            cfg = _coletar()
            self.config = cfg
            save_config(cfg)
            self.db.close()
            self.db = Database(cfg)
            self.lbl_status.config(text=f"{cfg.get('host')}:{cfg.get('database')}")
            dlg.destroy()
            self._conectar_e_carregar()

        btns = tk.Frame(dlg, bg="#FFFFFF")
        btns.pack(fill="x", padx=16, pady=12)
        tk.Button(btns, text="Testar", command=_testar, bg=COR_NAVY, fg="#FFFFFF",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2", width=10).pack(side="left", padx=4)
        tk.Button(btns, text="Salvar", command=_salvar, bg=COR_VERDE, fg="#FFFFFF",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2", width=10).pack(side="left", padx=4)
        tk.Button(btns, text="Fechar", command=dlg.destroy, bg="#E3E9EF",
                  fg="#44586B", relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2", width=10).pack(side="right", padx=4)


def main():
    root = tk.Tk()
    OrcamentoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
