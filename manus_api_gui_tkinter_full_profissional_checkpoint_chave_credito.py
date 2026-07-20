# ============================================================
# MANUS API GUI TKINTER - VERSÃO FULL PROFISSIONAL
# Mantém as funções anteriores e adiciona:
# - Tema visual profissional
# - Atalhos de teclado
# - Tooltips
# - Preferências locais
# - Painel de integridade
# - Auto-save de prompt
# - Exportação de sessão
# - Modo foco
# - Diagnóstico local
# - Melhor experiência comercial
# Compatível com Python 32-bit, mantendo dependências leves.
# ============================================================


# manus_api_gui_tkinter_final_completo.py
# Manus API v2 - GUI Tkinter completa:
# - Começa a tarefa e acompanha ATÉ TERMINAR, sem timeout automático.
# - Mostra resposta em tempo real.
# - Baixa automaticamente arquivos/anexos gerados pelo Manus.
# - Salva resposta final em TXT.
# - Salva logs TXT e JSONL.
# - Aceita anexar qualquer extensão localmente.
# - Modo automação por linha de comando.
# - Botão para responder quando o Manus ficar aguardando pergunta.
# - Permite anexar arquivos junto com a resposta enviada ao Manus.
# - Botão para confirmar ação pendente, quando existir confirmação manual.
# - Lista tarefas concluídas pela API e histórico local.
# - Abre tarefas concluídas dentro do próprio aplicativo.
# - Permite continuar a mesma tarefa já concluída usando o mesmo Task ID.
# - Permite colar imagens da área de transferência como anexo (tarefa e resposta).
# - Salvamento contínuo (autosave) de todos os dados da tarefa em disco.
# - Se a chave ficar sem crédito ou for inativada, pergunta se quer continuar:
#   pode escolher outra chave cadastrada ou cadastrar uma nova e a tarefa é
#   retomada de onde parou; se a nova chave for de outra conta, o contexto e os
#   arquivos salvos localmente são reenviados em uma nova tarefa de continuação.
# - Sessão HTTP com tentativas automáticas, barra de status animada (relógio +
#   spinner), tema polido com efeitos de hover e janela de Ajuda/Atalhos (F1).
# - Salvamento completo automático também ao fechar o aplicativo.
#
# Instalar:
#   python -m pip install requests
#
# Rodar interface:
#   python manus_api_gui_tkinter_final_completo.py
#
# Rodar automação sem interface, esperando até terminar:
#   python manus_api_gui_tkinter_final_completo.py --auto --prompt "Crie um app simples e entregue um zip"
#
# Com anexos:
#   python manus_api_gui_tkinter_final_completo.py --auto --prompt "Analise esse arquivo" --file "C:\temp\arquivo.pdf"
#
# Pastas criadas:
#   manus_logs
#   manus_downloads
#
# Chave:
#   1) MANUS_API_KEY
#   2) manus_api_key.local na mesma pasta
#   3) campo da interface

import argparse
import base64
import ftplib
import hashlib
import json
import mimetypes
import os
import queue
import re
import sys
import threading
import time
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, unquote

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

# ===== Constantes profissionais locais =====
PREFERENCES_FILE = Path("manus_gui_preferencias.json")
SESSION_EXPORT_DIR = Path("manus_sessoes_exportadas")
DRAFT_FILE = Path("manus_prompt_rascunho.txt")
TASK_STATE_DIR = Path("manus_estados_tarefas")
TASK_STATE_CURRENT_FILE = TASK_STATE_DIR / "tarefa_atual_estado.json"
try:
    import requests
except ModuleNotFoundError:
    raise SystemExit(
        "O módulo 'requests' não está instalado.\n"
        "Instale com:\n"
        "python -m pip install requests"
    )


# Pillow é opcional: usado apenas para colar imagens da área de transferência.
# Se não estiver instalado, o app continua funcionando normalmente e apenas
# avisa o usuário quando ele tentar colar uma imagem.
try:
    from PIL import ImageGrab, Image  # type: ignore
    PIL_DISPONIVEL = True
except Exception:
    ImageGrab = None  # type: ignore
    Image = None  # type: ignore
    PIL_DISPONIVEL = False

# Driver MySQL opcional (cache/persistência das conversas e respostas).
# Tenta PyMySQL (puro Python, ideal para 32 bits/PyInstaller); se não houver,
# tenta mysql.connector. Se nenhum existir, o app funciona normal só pela API.
try:
    import pymysql as _mysqldrv  # type: ignore
    MYSQL_DRIVER = "pymysql"
except Exception:
    try:
        import mysql.connector as _mysqldrv  # type: ignore
        MYSQL_DRIVER = "mysqlconnector"
    except Exception:
        _mysqldrv = None  # type: ignore
        MYSQL_DRIVER = ""
MYSQL_DISPONIVEL = bool(MYSQL_DRIVER)


BASE_URL = "https://api.manus.ai"
KEY_FILE = Path(__file__).with_name("manus_api_key.local")
KEY_RING_FILE = Path(__file__).with_name("manus_api_keys.local.json")
OTHER_AI_PROVIDERS_FILE = Path(__file__).with_name("outras_ias_provedores.local.json")
LOG_DIR = Path(__file__).with_name("manus_logs")
DOWNLOAD_DIR = Path(__file__).with_name("manus_downloads")
COMPLETED_HISTORY_FILE = Path(__file__).with_name("manus_tarefas_concluidas.json")
# Pasta onde as imagens coladas da área de transferência são salvas como arquivo.
CLIPBOARD_DIR = Path(__file__).with_name("manus_imagens_coladas")
# Extensões aceitas quando o usuário copia arquivos de imagem (e não um bitmap).
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"}

# Arquivos locais de recursos avançados.
INJECTIONS_FILE = Path(__file__).with_name("manus_injecoes.local.json")
PROMPT_PRESETS_FILE = Path(__file__).with_name("manus_prompt_presets.json")
# Pool de chaves fundidas (créditos somados / uso em cadeia automática).
FUSION_FILE = Path(__file__).with_name("manus_chaves_fundidas.local.json")
# Edições LOCAIS dos campos de créditos (refresh, quota, próximo refresh, etc.).
# Esses valores são apenas locais/visuais: o servidor do Manus não permite gravar
# saldo/quota, então persistimos as edições aqui para não se perderem ao reabrir.
CREDITOS_EDITADOS_FILE = Path(__file__).with_name("manus_creditos_editados.local.json")
# Estúdio de Outras IAs: histórico de tarefas/conversas e pasta de downloads própria.
ESTUDIO_TAREFAS_FILE = Path(__file__).with_name("estudio_ia_tarefas.json")
ESTUDIO_DOWNLOAD_DIR = DOWNLOAD_DIR / "estudio_ia"

# ===== Backup/sincronização automática via FTPS (dados embutidos a pedido do usuário) =====
APP_DIR = Path(__file__).resolve().parent
FTP_HOST = "ftps2.50webs.com"
FTP_USER = "manuss"
FTP_PASS = "manuss"
FTP_REMOTE_BASE = "manus_backup"

# ===== MySQL: cache/persistência de conversas e respostas (dados embutidos) =====
MYSQL_HOST = "mysql.50webs.com"
MYSQL_DB = "manuss_s"
MYSQL_USER = "manuss_s"
MYSQL_PASS = "manuss_s"

# Presets rápidos de provedores de IA compatíveis com o padrão OpenAI
# (/chat/completions). A Manus continua sendo SEMPRE a IA preferencial do app.
PROVEDORES_IA_PRESETS = [
    {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "endpoint": "/chat/completions", "model": "gpt-4o-mini", "auth_mode": "bearer"},
    {"name": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "endpoint": "/chat/completions", "model": "openai/gpt-4o-mini", "auth_mode": "bearer"},
    {"name": "Groq", "base_url": "https://api.groq.com/openai/v1", "endpoint": "/chat/completions", "model": "llama-3.3-70b-versatile", "auth_mode": "bearer"},
    {"name": "DeepSeek", "base_url": "https://api.deepseek.com", "endpoint": "/chat/completions", "model": "deepseek-chat", "auth_mode": "bearer"},
    {"name": "Mistral", "base_url": "https://api.mistral.ai/v1", "endpoint": "/chat/completions", "model": "mistral-large-latest", "auth_mode": "bearer"},
    {"name": "Together", "base_url": "https://api.together.xyz/v1", "endpoint": "/chat/completions", "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "auth_mode": "bearer"},
    {"name": "xAI (Grok)", "base_url": "https://api.x.ai/v1", "endpoint": "/chat/completions", "model": "grok-2-latest", "auth_mode": "bearer"},
    {"name": "Google Gemini (OpenAI)", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "endpoint": "/chat/completions", "model": "gemini-2.0-flash", "auth_mode": "bearer"},
    {"name": "Anthropic (Claude)", "base_url": "https://api.anthropic.com", "endpoint": "/v1/messages", "model": "claude-3-5-sonnet-latest", "auth_mode": "x-api-key", "provider_type": "anthropic"},
    {"name": "Perplexity", "base_url": "https://api.perplexity.ai", "endpoint": "/chat/completions", "model": "sonar", "auth_mode": "bearer"},
    {"name": "Fireworks", "base_url": "https://api.fireworks.ai/inference/v1", "endpoint": "/chat/completions", "model": "accounts/fireworks/models/llama-v3p3-70b-instruct", "auth_mode": "bearer"},
    {"name": "DeepInfra", "base_url": "https://api.deepinfra.com/v1/openai", "endpoint": "/chat/completions", "model": "meta-llama/Llama-3.3-70B-Instruct", "auth_mode": "bearer"},
    {"name": "Cerebras", "base_url": "https://api.cerebras.ai/v1", "endpoint": "/chat/completions", "model": "llama-3.3-70b", "auth_mode": "bearer"},
    {"name": "Novita", "base_url": "https://api.novita.ai/v3/openai", "endpoint": "/chat/completions", "model": "meta-llama/llama-3.3-70b-instruct", "auth_mode": "bearer"},
    {"name": "Hyperbolic", "base_url": "https://api.hyperbolic.xyz/v1", "endpoint": "/chat/completions", "model": "meta-llama/Llama-3.3-70B-Instruct", "auth_mode": "bearer"},
    {"name": "Kiro (gateway local)", "base_url": "http://localhost:8000/v1", "endpoint": "/chat/completions", "model": "claude-sonnet-4-5", "auth_mode": "bearer"},
    {"name": "Ollama (local)", "base_url": "http://localhost:11434/v1", "endpoint": "/chat/completions", "model": "llama3.1", "auth_mode": "bearer"},
    {"name": "LM Studio (local)", "base_url": "http://localhost:1234/v1", "endpoint": "/chat/completions", "model": "local-model", "auth_mode": "bearer"},
]

# ===== Listas completas de opções selecionáveis para a aba "Outras IAs / APIs" =====
# (são editáveis: o usuário pode escolher da lista OU digitar um valor próprio)
OUTRAS_IA_TIPOS = ["openai_compatible", "openai", "azure_openai", "anthropic", "google_gemini", "custom"]
OUTRAS_IA_AUTH = ["bearer", "x-api-key", "apikey"]
OUTRAS_IA_ENDPOINTS = [
    "/chat/completions", "/v1/chat/completions", "/completions", "/responses",
    "/messages", "/v1/messages", "/embeddings", "/models",
]
OUTRAS_IA_BASE_URLS = [p["base_url"] for p in PROVEDORES_IA_PRESETS]
OUTRAS_IA_NOMES = [p["name"] for p in PROVEDORES_IA_PRESETS]
OUTRAS_IA_MODELOS = [
    # OpenAI
    "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o3", "o3-mini", "o4-mini", "gpt-4-turbo", "gpt-3.5-turbo",
    # Anthropic
    "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-7-sonnet-latest", "claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-opus-latest",
    # Google
    "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.5-flash",
    # DeepSeek
    "deepseek-chat", "deepseek-reasoner",
    # Mistral
    "mistral-large-latest", "mistral-small-latest", "open-mixtral-8x22b", "codestral-latest",
    # xAI
    "grok-2-latest", "grok-2-vision-latest", "grok-beta",
    # Meta Llama (vários provedores)
    "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "meta-llama/Llama-3.1-405B-Instruct-Turbo", "llama-3.3-70b",
    # Qwen / outros
    "qwen-2.5-72b-instruct", "qwen2.5-coder-32b-instruct",
    # Perplexity
    "sonar", "sonar-pro", "sonar-reasoning",
    # Kiro (via gateway local - modelos Claude expostos pela conta Kiro)
    "claude-opus-4-5", "claude-sonnet-4-5", "claude-sonnet-4", "claude-haiku-4-5", "claude-3-7-sonnet-20250219",
    # Local
    "local-model", "llama3.1", "llama3.2", "qwen2.5",
]
OUTRAS_IA_TEMPS = ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0", "1.2", "1.5", "2.0"]
OUTRAS_IA_MAXTOKENS = ["256", "512", "1024", "2048", "4096", "8192", "16384", "32768", "65536", "131072"]
# Mapa nome -> preset, para autopreencher os campos ao escolher o provedor.
PROVEDORES_IA_POR_NOME = {p["name"]: p for p in PROVEDORES_IA_PRESETS}


def detectar_provedor_por_chave(key: str) -> Optional[Dict[str, Any]]:
    """
    Identifica o provedor a partir do PREFIXO da APIKEY e devolve o preset
    correspondente (Base URL, Endpoint, Modelo, Auth, Tipo). Reconhece os
    formatos de chave mais comuns. Para 'sk-...' genérico assume OpenAI.
    """
    k = str(key or "").strip()
    if not k:
        return None
    kl = k.lower()
    nome = None
    if k.startswith("sk-or-"):
        nome = "OpenRouter"
    elif k.startswith("sk-ant-"):
        nome = "Anthropic (Claude)"
    elif k.startswith("gsk_"):
        nome = "Groq"
    elif k.startswith("xai-"):
        nome = "xAI (Grok)"
    elif kl.startswith("pplx-"):
        nome = "Perplexity"
    elif k.startswith("fw_"):
        nome = "Fireworks"
    elif k.startswith("csk-"):
        nome = "Cerebras"
    elif k.startswith("AIza"):
        nome = "Google Gemini (OpenAI)"
    elif k.startswith("sk-"):
        # sk- é usado por OpenAI e também DeepSeek; assume OpenAI por padrão.
        nome = "OpenAI"
    if nome and nome in PROVEDORES_IA_POR_NOME:
        return dict(PROVEDORES_IA_POR_NOME[nome])
    return None


def escrever_json_atomico(path: Path, data) -> bool:
    """
    Grava JSON de forma ATÔMICA: escreve em um arquivo temporário e só então
    troca pelo arquivo final (os.replace). Evita arquivos corrompidos se o app
    fechar/cair no meio da escrita. Garante integridade dos dados em tempo real.
    """
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + f".tmp_{os.getpid()}")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        os.replace(str(tmp), str(path))
        return True
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return False


def contar_palavras(texto: str) -> int:
    try:
        return len([p for p in str(texto or "").split() if p.strip()])
    except Exception:
        return 0


def estimar_tokens(texto: str) -> int:
    """Estimativa simples de tokens (~4 caracteres por token)."""
    try:
        return max(0, int(len(str(texto or "")) / 4))
    except Exception:
        return 0


class FTPBackup:
    """
    Cliente de backup para servidor FTP/FTPS.

    Tenta primeiro FTPS explícito (FTP_TLS) e, se o servidor não suportar TLS,
    cai para FTP simples automaticamente. Cria os diretórios remotos conforme
    necessário e envia arquivos preservando a estrutura de pastas.
    """

    def __init__(self, host: str = FTP_HOST, user: str = FTP_USER, password: str = FTP_PASS, base: str = FTP_REMOTE_BASE):
        self.host = host
        self.user = user
        self.password = password
        self.base = str(base or "").strip("/") or "manus_backup"
        self.ftp = None

    def conectar(self):
        self.fechar()
        ftp = None
        # 1) FTPS explícito (recomendado).
        try:
            ftp = ftplib.FTP_TLS(timeout=60)
            ftp.connect(self.host, 21)
            ftp.login(self.user, self.password)
            try:
                ftp.prot_p()
            except Exception:
                pass
        except Exception:
            # 2) Fallback para FTP simples, caso o host não tenha TLS.
            ftp = ftplib.FTP(timeout=60)
            ftp.connect(self.host, 21)
            ftp.login(self.user, self.password)
        self.ftp = ftp
        self._garantir_dir(self.base)
        return ftp

    def fechar(self):
        try:
            if self.ftp:
                self.ftp.quit()
        except Exception:
            try:
                if self.ftp:
                    self.ftp.close()
            except Exception:
                pass
        self.ftp = None

    def _garantir_dir(self, remote_dir: str):
        """Cria/entra em diretórios aninhados a partir da raiz."""
        try:
            self.ftp.cwd("/")
        except Exception:
            pass
        for parte in [p for p in str(remote_dir).split("/") if p]:
            try:
                self.ftp.cwd(parte)
            except Exception:
                try:
                    self.ftp.mkd(parte)
                except Exception:
                    pass
                try:
                    self.ftp.cwd(parte)
                except Exception:
                    pass

    def enviar(self, local_path, remote_rel: str) -> bool:
        local_path = Path(local_path)
        if not local_path.exists() or not local_path.is_file():
            return False
        remote_rel = str(remote_rel).replace("\\", "/").strip("/")
        partes = [p for p in remote_rel.split("/") if p]
        if not partes:
            partes = [local_path.name]
        nome = partes[-1]
        subdir = "/".join(partes[:-1])
        destino_dir = self.base + ("/" + subdir if subdir else "")
        self._garantir_dir(destino_dir)
        with local_path.open("rb") as f:
            self.ftp.storbinary("STOR " + nome, f)
        return True


class MySQLCache:
    """
    Cache/persistência em MySQL das conversas e respostas.

    - Cria automaticamente as tabelas e colunas necessárias se não existirem.
    - Permite buscar uma resposta já existente (por hash do prompt) ANTES de
      chamar a API, e salvar a resposta nova depois que a API responde.
    - Registra todo o histórico de conversa (prompt do usuário, mensagens do
      Manus e respostas enviadas).

    Compatível com PyMySQL (preferencial) e mysql.connector como fallback.
    Se nenhum driver/conexão estiver disponível, todos os métodos falham de
    forma silenciosa e o app continua usando apenas a API.
    """

    TABELA_CACHE = "manus_cache"
    TABELA_CONVERSAS = "manus_conversas"

    def __init__(self, host=MYSQL_HOST, db=MYSQL_DB, user=MYSQL_USER, password=MYSQL_PASS):
        self.host = host
        self.db = db
        self.user = user
        self.password = password

    def disponivel(self) -> bool:
        return MYSQL_DISPONIVEL

    def _conn(self):
        if not MYSQL_DISPONIVEL:
            raise RuntimeError("Nenhum driver MySQL instalado (instale PyMySQL).")
        if MYSQL_DRIVER == "pymysql":
            return _mysqldrv.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db,
                charset="utf8mb4",
                connect_timeout=20,
                autocommit=True,
            )
        # mysql.connector
        return _mysqldrv.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db,
            connection_timeout=20,
            autocommit=True,
        )

    @staticmethod
    def hash_prompt(agent_profile: str, prompt: str) -> str:
        base = (str(agent_profile or "").strip() + "\n" + " ".join(str(prompt or "").split())).lower()
        return hashlib.sha256(base.encode("utf-8", "ignore")).hexdigest()

    def _garantir_colunas(self, cur, tabela: str, colunas: Dict[str, str]):
        for col, ddl in colunas.items():
            try:
                cur.execute(
                    "SELECT COUNT(*) FROM information_schema.columns "
                    "WHERE table_schema=%s AND table_name=%s AND column_name=%s",
                    (self.db, tabela, col),
                )
                existe = cur.fetchone()[0]
                if not existe:
                    cur.execute("ALTER TABLE " + tabela + " ADD COLUMN " + col + " " + ddl)
            except Exception:
                pass

    def inicializar(self):
        """Cria tabelas e colunas automaticamente caso não existam."""
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS " + self.TABELA_CACHE + " ("
                "id INT AUTO_INCREMENT PRIMARY KEY,"
                "prompt_hash VARCHAR(64) NOT NULL,"
                "agent_profile VARCHAR(120),"
                "prompt LONGTEXT,"
                "response LONGTEXT,"
                "source VARCHAR(60),"
                "hits INT DEFAULT 0,"
                "created_at DATETIME,"
                "updated_at DATETIME,"
                "UNIQUE KEY uniq_prompt_hash (prompt_hash)"
                ") DEFAULT CHARSET=utf8mb4"
            )
            cur.execute(
                "CREATE TABLE IF NOT EXISTS " + self.TABELA_CONVERSAS + " ("
                "id INT AUTO_INCREMENT PRIMARY KEY,"
                "task_id VARCHAR(120),"
                "role VARCHAR(40),"
                "content LONGTEXT,"
                "created_at DATETIME"
                ") DEFAULT CHARSET=utf8mb4"
            )
            self._garantir_colunas(cur, self.TABELA_CACHE, {
                "agent_profile": "VARCHAR(120)",
                "prompt": "LONGTEXT",
                "response": "LONGTEXT",
                "source": "VARCHAR(60)",
                "hits": "INT DEFAULT 0",
                "created_at": "DATETIME",
                "updated_at": "DATETIME",
            })
            self._garantir_colunas(cur, self.TABELA_CONVERSAS, {
                "task_id": "VARCHAR(120)",
                "role": "VARCHAR(40)",
                "content": "LONGTEXT",
                "created_at": "DATETIME",
            })
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def buscar_resposta(self, agent_profile: str, prompt: str) -> Optional[str]:
        if not str(prompt or "").strip():
            return None
        ph = self.hash_prompt(agent_profile, prompt)
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT response FROM " + self.TABELA_CACHE + " WHERE prompt_hash=%s LIMIT 1",
                (ph,),
            )
            row = cur.fetchone()
            if row and row[0]:
                try:
                    cur.execute(
                        "UPDATE " + self.TABELA_CACHE + " SET hits=hits+1 WHERE prompt_hash=%s",
                        (ph,),
                    )
                except Exception:
                    pass
                return str(row[0])
            return None
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def salvar_resposta(self, agent_profile: str, prompt: str, response: str, source: str = "manus_api"):
        if not str(prompt or "").strip() or not str(response or "").strip():
            return
        ph = self.hash_prompt(agent_profile, prompt)
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO " + self.TABELA_CACHE +
                " (prompt_hash, agent_profile, prompt, response, source, hits, created_at, updated_at) "
                "VALUES (%s,%s,%s,%s,%s,1,NOW(),NOW()) "
                "ON DUPLICATE KEY UPDATE response=VALUES(response), agent_profile=VALUES(agent_profile), "
                "prompt=VALUES(prompt), source=VALUES(source), updated_at=NOW()",
                (ph, str(agent_profile or ""), str(prompt or ""), str(response or ""), str(source or "manus_api")),
            )
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def registrar_conversa(self, task_id: str, role: str, content: str):
        if not str(content or "").strip():
            return
        conn = self._conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO " + self.TABELA_CONVERSAS + " (task_id, role, content, created_at) "
                "VALUES (%s,%s,%s,NOW())",
                (str(task_id or ""), str(role or ""), str(content or "")),
            )
        finally:
            try:
                conn.close()
            except Exception:
                pass


def _criar_sessao_http() -> "requests.Session":
    """
    Cria uma sessão HTTP profissional com reuso de conexão (keep-alive) e
    tentativas automáticas para falhas transitórias de rede/servidor.

    Importante: NÃO faz retry de 429 (crédito/limite) nem de 401/403 (chave),
    pois esses casos têm tratamento próprio na aplicação. Apenas 5xx e erros
    de conexão são re-tentados, deixando o app muito mais robusto.

    Compatível com versões antigas e novas do urllib3 (Python 32 bits incluso).
    """
    sess = requests.Session()
    try:
        from requests.adapters import HTTPAdapter
        try:
            from urllib3.util.retry import Retry
        except Exception:  # pragma: no cover - fallback p/ empacotamentos antigos
            from requests.packages.urllib3.util.retry import Retry  # type: ignore

        try:
            # urllib3 >= 1.26 / 2.x
            retry = Retry(
                total=3,
                connect=3,
                read=3,
                backoff_factor=0.6,
                status_forcelist=(500, 502, 503, 504),
                allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "PATCH"]),
                raise_on_status=False,
            )
        except TypeError:
            # urllib3 antigo usava method_whitelist
            retry = Retry(
                total=3,
                connect=3,
                read=3,
                backoff_factor=0.6,
                status_forcelist=(500, 502, 503, 504),
                method_whitelist=frozenset(["GET", "POST", "PUT", "DELETE", "PATCH"]),
            )

        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        sess.mount("https://", adapter)
        sess.mount("http://", adapter)
    except Exception:
        # Se algo falhar, a sessão simples ainda funciona perfeitamente.
        pass
    return sess


# Sessão HTTP única e reaproveitada por toda a aplicação.
HTTP_SESSION = _criar_sessao_http()

DOWNLOAD_EXTS = {
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".pdf", ".txt", ".md", ".csv", ".json", ".xml",
    ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ppt",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
    ".py", ".js", ".html", ".css", ".php", ".sql",
    ".mp3", ".wav", ".mp4", ".mov", ".avi",
}


def agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def titulo_nova_tarefa() -> str:
    """
    Título automático exigido:
    data + hora + nome Nova Tarefa.
    Exemplo:
    21-06-2026 14-35-08 - Nova Tarefa
    """
    return datetime.now().strftime("%d-%m-%Y %H-%M-%S") + " - Nova Tarefa"


def erro_credito_esgotado(valor: Any) -> bool:
    """
    Detecta respostas da Manus indicando limite/crédito esgotado.
    Exemplos:
    HTTP 429
    code: resource_exhausted
    message: credit limit exceeded
    """
    try:
        texto = ""
        if isinstance(valor, dict):
            texto = json.dumps(valor, ensure_ascii=False).lower()
        else:
            texto = str(valor or "").lower()

        pistas = [
            "http 429",
            "resource_exhausted",
            "credit limit exceeded",
            "credit exceeded",
            "limit exceeded",
            "crédito",
            "credito",
            "sem crédito",
            "sem credito",
        ]
        return any(p in texto for p in pistas)
    except Exception:
        return False


def formatar_timestamp_credito(ts) -> str:
    """Formata timestamp Unix da Manus em data local."""
    try:
        ts = int(ts or 0)
        if ts <= 0:
            return "--"
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "--"


def formatar_creditos_manus(data: Dict[str, Any]) -> str:
    """Cria texto amigável do saldo de créditos."""
    d = data.get("data") if isinstance(data, dict) else {}
    if not isinstance(d, dict):
        d = data if isinstance(data, dict) else {}

    total = d.get("total_credits", "--")
    free = d.get("free_credits", "--")
    periodic = d.get("periodic_credits", "--")
    addon = d.get("addon_credits", "--")
    pro_monthly = d.get("pro_monthly_credits", "--")
    event = d.get("event_credits", "--")
    refresh = d.get("refresh_credits", "--")
    max_refresh = d.get("max_refresh_credits", "--")
    next_refresh = formatar_timestamp_credito(d.get("next_refresh_time"))
    refresh_interval = d.get("refresh_interval") or "--"

    return (
        f"Saldo disponível: {total} crédito(s) | "
        f"grátis={free}, periódicos={periodic}, addon={addon}, evento={event}, "
        f"refresh={refresh}/{max_refresh}, quota_mensal={pro_monthly}, "
        f"próximo_refresh={next_refresh}, intervalo={refresh_interval}"
    )


def total_creditos_manus(data: Dict[str, Any]):
    """Extrai total_credits com segurança."""
    try:
        d = data.get("data") if isinstance(data, dict) else {}
        if isinstance(d, dict):
            return d.get("total_credits")
    except Exception:
        pass
    return None


def mascarar_chave_api(chave: str) -> str:
    """Mostra a chave de forma segura, sem revelar o valor completo."""
    chave = str(chave or "").strip()
    if not chave:
        return "(vazia)"
    if len(chave) <= 10:
        return chave[:2] + "***" + chave[-2:]
    return chave[:6] + "..." + chave[-4:]


def erro_permite_failover_chave(valor: Any) -> bool:
    """
    Detecta problemas técnicos em que vale tentar outra chave cadastrada:
    - chave inválida/revogada/sem permissão
    - HTTP 401/403/408/5xx
    - timeout/conexão/SSL/proxy
    Não inclui 429/crédito/limite para evitar troca automática indevida de limite.
    """
    if erro_credito_esgotado(valor):
        return False

    texto = str(valor or "").lower()
    pistas = [
        "http 401",
        "http 403",
        "http 408",
        "http 500",
        "http 502",
        "http 503",
        "http 504",
        "unauthorized",
        "forbidden",
        "invalid api",
        "invalid key",
        "api key",
        "apikey",
        "permission",
        "permiss",
        "revoked",
        "expired",
        "timeout",
        "timed out",
        "connection",
        "conexão",
        "conexao",
        "ssl",
        "proxy",
        "temporarily unavailable",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
        "remote disconnected",
        "connection aborted",
    ]
    return any(p in texto for p in pistas)


def erro_chave_invalida(valor: Any) -> bool:
    """
    Detecta especificamente que a CHAVE foi inativada/invalidada ou não tem
    permissão (HTTP 401/403, unauthenticated, permission denied, revoked...).

    Diferente de 'erro_permite_failover_chave', NÃO inclui timeouts/conexão/5xx,
    porque esses são problemas transitórios de rede em que vale a pena continuar
    tentando com a MESMA chave (não significa que a chave morreu).
    """
    if erro_credito_esgotado(valor):
        return False
    try:
        if isinstance(valor, dict):
            texto = json.dumps(valor, ensure_ascii=False).lower()
        else:
            texto = str(valor or "").lower()
    except Exception:
        texto = str(valor or "").lower()

    pistas = [
        "http 401",
        "http 403",
        "unauthenticated",
        "unauthorized",
        "forbidden",
        "permission_denied",
        "permission denied",
        "invalid api key",
        "invalid_api_key",
        "invalid apikey",
        "api key inválida",
        "api key invalida",
        "chave inválida",
        "chave invalida",
        "invalid key",
        "revoked",
        "revogada",
        "expired",
        "expirou",
        "expirada",
        "disabled",
        "deactivated",
        "inativ",
        "key not found",
    ]
    return any(p in texto for p in pistas)


class ToolTip:
    """Tooltip simples e leve, compatível com Tkinter puro."""

    def __init__(self, widget, text: str, delay: int = 550):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.after_id = None
        try:
            widget.bind("<Enter>", self.schedule, add="+")
            widget.bind("<Leave>", self.hide, add="+")
            widget.bind("<ButtonPress>", self.hide, add="+")
        except Exception:
            pass

    def schedule(self, event=None):
        self.cancel()
        try:
            self.after_id = self.widget.after(self.delay, self.show)
        except Exception:
            self.after_id = None

    def cancel(self):
        if self.after_id:
            try:
                self.widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def show(self):
        if self.tipwindow or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 18
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            label = tk.Label(
                tw,
                text=self.text,
                justify="left",
                background="#111827",
                foreground="#F9FAFB",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 9),
                padx=8,
                pady=5,
                wraplength=420,
            )
            label.pack(ipadx=1)
        except Exception:
            self.tipwindow = None

    def hide(self, event=None):
        self.cancel()
        if self.tipwindow:
            try:
                self.tipwindow.destroy()
            except Exception:
                pass
            self.tipwindow = None


def ler_json_seguro(path: Path, default):
    try:
        if Path(path).exists():
            return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def salvar_json_seguro(path: Path, data) -> bool:
    return escrever_json_atomico(path, data)


def resumo_texto(texto: str, limite: int = 160) -> str:
    texto = " ".join(str(texto or "").split())
    if len(texto) <= limite:
        return texto
    return texto[: max(0, limite - 3)] + "..."


def caminho_estado_tarefa(task_id: str) -> Path:
    """Arquivo local de checkpoint para um Task ID."""
    tid = nome_seguro(str(task_id or "sem_task_id"))
    return TASK_STATE_DIR / f"{tid}.estado.json"


def lista_str_segura(valores) -> List[str]:
    """Converte uma lista qualquer para lista de strings."""
    out = []
    try:
        for v in valores or []:
            try:
                out.append(str(v))
            except Exception:
                pass
    except Exception:
        pass
    return out


def nome_seguro(texto: str, limite: int = 80) -> str:
    texto = str(texto or "")
    out = []
    for ch in texto:
        if ch.isalnum() or ch in ("-", "_", "."):
            out.append(ch)
        elif ch.isspace():
            out.append("_")
    safe = "".join(out).strip("._")
    return (safe or "arquivo")[:limite]


def tamanho_legivel(bytes_size: int) -> str:
    valor = float(bytes_size or 0)
    for unidade in ["B", "KB", "MB", "GB"]:
        if valor < 1024:
            return f"{valor:.1f} {unidade}"
        valor /= 1024
    return f"{valor:.1f} TB"


class UploadProgressReader:
    """
    Leitor de arquivo com progresso real de upload.

    A porcentagem é calculada assim:
        bytes_lidos_para_envio / tamanho_total_do_arquivo * 100

    O requests chama read() várias vezes durante o PUT.
    Cada leitura atualiza o progresso.
    """

    def __init__(self, file_path: Path, progress_cb=None):
        self.file_path = Path(file_path)
        self.file = self.file_path.open("rb")
        self.total = self.file_path.stat().st_size
        self.sent = 0
        self.progress_cb = progress_cb
        self.last_percent_int = -1

    def __len__(self):
        return self.total

    def read(self, size=-1):
        chunk = self.file.read(size)
        if chunk:
            self.sent += len(chunk)
            percent = 100.0 if self.total <= 0 else min(100.0, (self.sent / self.total) * 100.0)
            percent_int = int(percent)

            # Atualiza sempre que muda a porcentagem inteira.
            if percent_int != self.last_percent_int:
                self.last_percent_int = percent_int
                if self.progress_cb:
                    self.progress_cb(
                        percent=percent,
                        sent=self.sent,
                        total=self.total,
                        filename=self.file_path.name,
                    )

        return chunk

    def close(self):
        try:
            self.file.close()
        except Exception:
            pass


def formatar_timestamp(ts: Any) -> str:
    try:
        if ts is None or ts == "":
            return ""
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(ts or "")


def carregar_historico_concluidas() -> List[Dict[str, Any]]:
    if not COMPLETED_HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(COMPLETED_HISTORY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except Exception:
        return []
    return []


def salvar_tarefa_concluida_local(task: Dict[str, Any]) -> None:
    task_id = str(task.get("id") or task.get("task_id") or "").strip()
    if not task_id:
        return

    hist = carregar_historico_concluidas()
    merged = {}
    for item in hist:
        old_id = str(item.get("id") or item.get("task_id") or "").strip()
        if old_id:
            merged[old_id] = item

    registro = {
        "id": task_id,
        "status": task.get("status") or "stopped",
        "title": task.get("title") or task.get("task_title") or "",
        "task_url": task.get("task_url") or "",
        "created_at": task.get("created_at") or "",
        "updated_at": task.get("updated_at") or int(time.time()),
        "finished_at_local": agora_iso(),
        "source": task.get("source") or "app_local",
    }

    for k, v in task.items():
        if k not in registro and v not in (None, ""):
            registro[k] = v

    merged[task_id] = registro
    saida = sorted(merged.values(), key=lambda x: str(x.get("updated_at") or x.get("finished_at_local") or ""), reverse=True)
    COMPLETED_HISTORY_FILE.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")


class AutoLogger:
    def __init__(self, enabled: bool = True, prefix: str = "manus", task_id: str = "sem_task"):
        self.enabled = enabled
        self.prefix = nome_seguro(prefix)
        self.task_id = task_id or "sem_task"
        self.started = datetime.now()
        self.log_path: Optional[Path] = None
        self.jsonl_path: Optional[Path] = None
        self.final_path: Optional[Path] = None
        if self.enabled:
            self.prepare_paths(self.task_id)

    def prepare_paths(self, task_id: str = ""):
        if not self.enabled:
            return
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if task_id:
            self.task_id = task_id
        stamp = self.started.strftime("%Y-%m-%d_%H-%M-%S")
        base = f"{stamp}_{nome_seguro(self.task_id)}"
        self.log_path = LOG_DIR / f"{base}.log"
        self.jsonl_path = LOG_DIR / f"{base}.jsonl"
        self.final_path = LOG_DIR / f"{base}_resposta_final.txt"

    def update_task_id(self, task_id: str):
        if not self.enabled:
            return
        self.task_id = task_id or self.task_id
        self.prepare_paths(self.task_id)

    def log(self, event: str, message: str, **extra: Any):
        if not self.enabled:
            return
        if not self.log_path or not self.jsonl_path:
            self.prepare_paths(self.task_id)

        line = f"[{agora_iso()}] [{event.upper()}] {message}\n"
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line)

        payload = {
            "time": agora_iso(),
            "event": event,
            "task_id": self.task_id,
            "message": message,
            **extra,
        }
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def save_final(self, text: str) -> Optional[Path]:
        if not self.enabled:
            return None
        if not self.final_path:
            self.prepare_paths(self.task_id)
        self.final_path.write_text(text or "", encoding="utf-8")
        self.log("final_saved", f"Resposta final salva em {self.final_path}", path=str(self.final_path))
        return self.final_path


class ManusAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 90,
    ) -> Dict[str, Any]:
        url = BASE_URL.rstrip("/") + path
        headers = {
            "x-manus-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        resp = HTTP_SESSION.request(
            method.upper(),
            url,
            headers=headers,
            params=params,
            json=body,
            timeout=timeout,
        )

        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(
                f"A resposta não veio em JSON.\nHTTP {resp.status_code}\n\n{resp.text[:2000]}"
            )

        if not resp.ok or data.get("ok") is False:
            error_obj = data.get("error") or {}
            error_code = str(error_obj.get("code") or "").strip()
            error_msg = str(error_obj.get("message") or "").strip()

            if resp.status_code == 429 or erro_credito_esgotado(data):
                raise RuntimeError(
                    "CRÉDITO/LIMITE DA MANUS ESGOTADO.\n"
                    "HTTP 429\n\n"
                    "O servidor respondeu, então ele está ONLINE, mas a sua conta/chave "
                    "não tem crédito ou limite disponível para continuar.\n\n"
                    "Solução: aguarde o limite renovar, adicione créditos/plano na Manus "
                    "ou use outra API key com crédito disponível.\n\n"
                    f"Detalhe técnico: code={error_code or 'resource_exhausted'} | "
                    f"message={error_msg or 'credit limit exceeded'}\n\n"
                    f"{json.dumps(data, ensure_ascii=False, indent=2)}"
                )

            raise RuntimeError(
                f"Erro da API.\nHTTP {resp.status_code}\n\n"
                f"{json.dumps(data, ensure_ascii=False, indent=2)}"
            )

        return data

    def available_credits(self) -> Dict[str, Any]:
        """
        Consulta o saldo de créditos da chave atual.

        Endpoint oficial:
        GET /v2/usage.availableCredits

        O campo total_credits é o saldo gastável principal.
        """
        return self.request("GET", "/v2/usage.availableCredits")

    def list_skills(self) -> Dict[str, Any]:
        return self.request("GET", "/v2/skill.list")

    def list_tasks(self, limit: int = 100, cursor: str = "", order: str = "desc", scope: str = "all") -> Dict[str, Any]:
        params = {
            "limit": max(1, min(int(limit or 100), 100)),
            "order": order or "desc",
            "scope": scope or "all",
        }
        if cursor:
            params["cursor"] = cursor
        return self.request("GET", "/v2/task.list", params=params)

    def most_recent_task(self) -> Dict[str, Any]:
        """
        Retorna a tarefa mais recente da conta (dict) consultando o servidor
        via /v2/task.list, ou {} se a conta não tiver tarefas.
        """
        data = self.list_tasks(limit=1, order="desc", scope="all")
        tasks = []
        if isinstance(data, dict):
            tasks = data.get("data") or data.get("tasks") or []
        if isinstance(tasks, list) and tasks and isinstance(tasks[0], dict):
            return tasks[0]
        return {}

    def current_model(self) -> str:
        """
        Descobre o MODELO em uso no momento consultando DIRETAMENTE o servidor
        do Manus (endpoint /v2/task.list). Pega a tarefa mais recente da conta e
        extrai o campo oficial 'agent_profile' dela (que reflete o último turno,
        inclusive overrides feitos via task.sendMessage).

        Retorna:
        - o nome do modelo (ex.: "manus-1.6-lite") quando disponível;
        - "sem tarefas" quando a conta não possui tarefas;
        - "--" quando não é possível determinar o modelo (ex.: tarefas antigas).
        """
        t = self.most_recent_task()
        if not t:
            return "sem tarefas"

        # Campo oficial é 'agent_profile'; mantém alternativas por segurança.
        for campo in ("agent_profile", "agentProfile", "model", "profile"):
            valor = t.get(campo)
            if valor:
                return str(valor)

        return "--"

    def task_detail(self, task_id: str) -> Dict[str, Any]:
        """Detalhes de uma tarefa específica (inclui o campo agent_profile)."""
        return self.request("GET", "/v2/task.detail", params={"task_id": task_id})

    def model_of_task(self, task_id: str) -> str:
        """
        Lê o modelo (agent_profile) de UMA tarefa específica direto do servidor
        via /v2/task.detail. Retorna '' quando não disponível.
        """
        try:
            data = self.task_detail(task_id)
        except Exception:
            return ""
        t = data.get("task") if isinstance(data, dict) else {}
        if not isinstance(t, dict):
            return ""
        for campo in ("agent_profile", "agentProfile", "model", "profile"):
            valor = t.get(campo)
            if valor:
                return str(valor)
        return ""

    def list_completed_tasks(self, max_pages: int = 5, scope: str = "all") -> List[Dict[str, Any]]:
        concluidas: List[Dict[str, Any]] = []
        cursor = ""
        for _ in range(max(1, max_pages)):
            data = self.list_tasks(limit=100, cursor=cursor, order="desc", scope=scope)
            tasks = data.get("data") or []
            for task in tasks:
                if str(task.get("status") or "").lower() == "stopped":
                    task = dict(task)
                    task["source"] = "api"
                    concluidas.append(task)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor") or ""
            if not cursor:
                break
        return concluidas


    def list_unfinished_tasks(self, max_pages: int = 5, scope: str = "all") -> List[Dict[str, Any]]:
        """
        Lista tarefas ainda não finalizadas.

        Inclui:
        - running
        - waiting
        - error
        - pending
        - qualquer status diferente de stopped/completed/finished/done
        """
        abertas: List[Dict[str, Any]] = []
        cursor = ""
        finais = {"stopped", "completed", "complete", "finished", "done"}

        for _ in range(max(1, max_pages)):
            data = self.list_tasks(limit=100, cursor=cursor, order="desc", scope=scope)
            tasks = data.get("data") or data.get("tasks") or []

            for task in tasks:
                status = str(task.get("status") or task.get("agent_status") or task.get("state") or "").lower().strip()
                if status and status not in finais:
                    task = dict(task)
                    task["source"] = "api"
                    abertas.append(task)

            if not data.get("has_more"):
                break

            cursor = data.get("next_cursor") or data.get("cursor") or data.get("nextCursor") or ""
            if not cursor:
                break

        return abertas

    def create_file_record(self, filename: str) -> Dict[str, Any]:
        return self.request("POST", "/v2/file.upload", body={"filename": filename})

    def upload_file_bytes(self, upload_url: str, file_path: Path, progress_cb=None):
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        total = file_path.stat().st_size

        reader = UploadProgressReader(file_path, progress_cb=progress_cb)
        try:
            # Content-Length ajuda o servidor a receber o arquivo corretamente
            # e mantém o cálculo de progresso fiel ao tamanho real do arquivo.
            headers = {
                "Content-Type": content_type,
                "Content-Length": str(total),
            }

            if progress_cb:
                progress_cb(
                    percent=0.0,
                    sent=0,
                    total=total,
                    filename=file_path.name,
                )

            resp = requests.put(
                upload_url,
                data=reader,
                headers=headers,
                timeout=900,
            )

            if progress_cb:
                progress_cb(
                    percent=100.0,
                    sent=total,
                    total=total,
                    filename=file_path.name,
                )

        finally:
            reader.close()

        if not (200 <= resp.status_code < 300):
            raise RuntimeError(
                f"Falha no envio do arquivo {file_path.name}.\nHTTP {resp.status_code}\n\n{resp.text[:2000]}"
            )

    def file_detail(self, file_id: str) -> Dict[str, Any]:
        return self.request("GET", "/v2/file.detail", params={"file_id": file_id})

    def wait_file_uploaded(self, file_id: str, filename: str, logger: Optional[AutoLogger] = None, cb=None):
        while True:
            data = self.file_detail(file_id)
            file_info = data.get("file") or {}
            status = str(file_info.get("status") or "").lower()

            msg = f"{filename}: status {status or 'desconhecido'}"
            if logger:
                logger.log("file_status", msg, file_id=file_id, filename=filename, status=status)
            if cb:
                cb(msg)

            if status == "uploaded":
                return

            if status == "error":
                erro = file_info.get("error_message") or "Erro desconhecido no upload."
                raise RuntimeError(f"Upload de {filename} falhou: {erro}")

            time.sleep(1)

    def upload_local_file(self, file_path: Path, logger: Optional[AutoLogger] = None, cb=None, progress_cb=None) -> Dict[str, str]:
        if not file_path.exists() or not file_path.is_file():
            raise RuntimeError(f"Arquivo não encontrado: {file_path}")

        if logger:
            logger.log("file_upload_start", f"Iniciando upload: {file_path.name}", path=str(file_path), size=file_path.stat().st_size)
        if cb:
            cb(f"Iniciando upload: {file_path.name}")

        data = self.create_file_record(file_path.name)
        file_obj = data.get("file") or {}
        file_id = file_obj.get("id")
        upload_url = data.get("upload_url")

        if not file_id or not upload_url:
            raise RuntimeError("A API não retornou file.id ou upload_url.\n\n" + json.dumps(data, ensure_ascii=False, indent=2))

        self.upload_file_bytes(upload_url, file_path, progress_cb=progress_cb)
        if logger:
            logger.log("file_put_done", f"PUT concluído: {file_path.name}", file_id=file_id)

        self.wait_file_uploaded(file_id, file_path.name, logger=logger, cb=cb)

        if logger:
            logger.log("file_upload_done", f"Upload concluído: {file_path.name}", file_id=file_id)

        return {"file_id": file_id, "filename": file_path.name, "path": str(file_path)}

    def create_task(self, prompt: str, agent_profile: str, title: str, uploaded_files: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        content = [{"type": "text", "text": prompt}]
        uploaded_files = uploaded_files or []

        for item in uploaded_files:
            content.append({"type": "file", "file_id": item["file_id"], "filename": item["filename"]})

        body = {
            "message": {"content": content},
            "locale": "pt-BR",
            "interactive_mode": False,
            "hide_in_task_list": False,
            "share_visibility": "private",
            "agent_profile": agent_profile,
            "title": title or "Tarefa Manus",
        }

        try:
            return self.request("POST", "/v2/task.create", body=body)
        except RuntimeError as e:
            # Fallback se a API rejeitar filename.
            if uploaded_files and "filename" in str(e).lower():
                content = [{"type": "text", "text": prompt}]
                for item in uploaded_files:
                    content.append({"type": "file", "file_id": item["file_id"]})
                body["message"]["content"] = content
                return self.request("POST", "/v2/task.create", body=body)
            raise

    def send_message(
        self,
        task_id: str,
        text: str,
        uploaded_files: Optional[List[Dict[str, str]]] = None,
        agent_profile: str = "",
    ) -> Dict[str, Any]:
        """
        Envia uma resposta/continuação para uma tarefa já existente.

        Permite anexar arquivos como resposta, do mesmo jeito que task.create:
        os arquivos precisam ter sido enviados antes (upload_local_file) e
        chegam aqui apenas como {"file_id": ..., "filename": ...}.

        Se 'agent_profile' for informado, ele é enviado como override do MODELO
        para este turno (campo oficial da API /v2/task.sendMessage). Isso faz o
        servidor passar a usar o modelo escolhido na tarefa existente; o valor
        aparece depois em task.list/task.detail como 'agent_profile'.
        Observação da API: contas pessoais gratuitas são rebaixadas para
        manus-1.6-lite independentemente do valor solicitado.
        """
        uploaded_files = uploaded_files or []
        content: List[Dict[str, Any]] = []

        # O texto é opcional quando há anexos; mantém pelo menos um item de texto
        # para a API não receber um conteúdo totalmente vazio.
        if text or not uploaded_files:
            content.append({"type": "text", "text": text})

        for item in uploaded_files:
            content.append({"type": "file", "file_id": item["file_id"], "filename": item["filename"]})

        body: Dict[str, Any] = {
            "task_id": task_id,
            "message": {"content": content},
        }
        if str(agent_profile or "").strip():
            body["agent_profile"] = str(agent_profile).strip()

        try:
            return self.request("POST", "/v2/task.sendMessage", body=body)
        except RuntimeError as e:
            # Fallback se a API rejeitar o campo filename no conteúdo do anexo.
            if uploaded_files and "filename" in str(e).lower():
                content = []
                if text or not uploaded_files:
                    content.append({"type": "text", "text": text})
                for item in uploaded_files:
                    content.append({"type": "file", "file_id": item["file_id"]})
                body["message"]["content"] = content
                return self.request("POST", "/v2/task.sendMessage", body=body)
            raise

    def confirm_action(self, task_id: str, event_id: str, input_obj: Dict[str, Any]) -> Dict[str, Any]:
        body = {
            "task_id": task_id,
            "event_id": event_id,
            "input": input_obj,
        }
        return self.request("POST", "/v2/task.confirmAction", body=body)

    def list_messages(self, task_id: str, limit: int = 200, slides_format: str = "pptx") -> Dict[str, Any]:
        return self.request(
            "GET",
            "/v2/task.listMessages",
            params={
                "task_id": task_id,
                "order": "desc",
                "limit": limit,
                "verbose": "false",
                "slides_format": slides_format,
            },
        )

    # ===================================================================
    # ===== Cobertura COMPLETA da API v2 (todos os endpoints) ===========
    # ===================================================================
    # Métodos abaixo cobrem leitura e escrita de todos os recursos da API
    # oficial do Manus: uso/créditos, tarefas, agentes, conectores, projetos,
    # arquivos, navegadores, webhooks e sites.

    # ---- Uso / créditos (somente leitura) ----
    def usage_list(self, limit: int = 20, cursor: str = "") -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": max(1, min(int(limit or 20), 100))}
        if cursor:
            params["cursor"] = cursor
        return self.request("GET", "/v2/usage.list", params=params)

    def usage_team_log(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("GET", "/v2/usage.teamLog", params=params or {})

    def usage_team_statistic(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request("GET", "/v2/usage.teamStatistic", params=params or {})

    # ---- Agentes personalizados ----
    def agent_list(self) -> Dict[str, Any]:
        return self.request("GET", "/v2/agent.list")

    def agent_detail(self, agent_id: str) -> Dict[str, Any]:
        return self.request("GET", "/v2/agent.detail", params={"agent_id": agent_id})

    def agent_update(self, agent_id: str, nickname: str = "", about: str = "") -> Dict[str, Any]:
        body: Dict[str, Any] = {"agent_id": agent_id}
        if nickname:
            body["nickname"] = nickname
        if about:
            body["about"] = about
        return self.request("POST", "/v2/agent.update", body=body)

    # ---- Conectores / projetos / navegadores ----
    def connector_list(self) -> Dict[str, Any]:
        return self.request("GET", "/v2/connector.list")

    def project_list(self) -> Dict[str, Any]:
        return self.request("GET", "/v2/project.list")

    def project_create(self, name: str, instruction: str = "") -> Dict[str, Any]:
        body: Dict[str, Any] = {"name": name}
        if instruction:
            body["instruction"] = instruction
        return self.request("POST", "/v2/project.create", body=body)

    def browser_online_list(self) -> Dict[str, Any]:
        return self.request("GET", "/v2/browser.onlineList")

    # ---- Arquivos ----
    def file_delete(self, file_id: str) -> Dict[str, Any]:
        return self.request("POST", "/v2/file.delete", body={"file_id": file_id})

    # ---- Tarefas (escrita) ----
    def task_update(
        self,
        task_id: str,
        title: Optional[str] = None,
        share_visibility: Optional[str] = None,
        enable_visible_in_task_list: Optional[bool] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"task_id": task_id}
        if title is not None:
            body["title"] = title
        if share_visibility is not None:
            body["share_visibility"] = share_visibility
        if enable_visible_in_task_list is not None:
            body["enable_visible_in_task_list"] = bool(enable_visible_in_task_list)
        return self.request("POST", "/v2/task.update", body=body)

    def task_stop(self, task_id: str) -> Dict[str, Any]:
        return self.request("POST", "/v2/task.stop", body={"task_id": task_id})

    def task_delete(self, task_id: str) -> Dict[str, Any]:
        return self.request("POST", "/v2/task.delete", body={"task_id": task_id})

    # ---- Webhooks ----
    def webhook_list(self) -> Dict[str, Any]:
        return self.request("GET", "/v2/webhook.list")

    def webhook_public_key(self) -> Dict[str, Any]:
        return self.request("GET", "/v2/webhook.publicKey")

    def webhook_create(self, url: str, events: Optional[List[str]] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"url": url}
        if events:
            body["events"] = events
        return self.request("POST", "/v2/webhook.create", body=body)

    def webhook_delete(self, webhook_id: str) -> Dict[str, Any]:
        return self.request("POST", "/v2/webhook.delete", body={"webhook_id": webhook_id})

    # ---- Sites gerados pelo Manus ----
    def website_status(self, task_id: str = "", website_id: str = "") -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if task_id:
            params["task_id"] = task_id
        if website_id:
            params["website_id"] = website_id
        return self.request("GET", "/v2/website.status", params=params)

    def website_list_checkpoints(self, task_id: str = "", website_id: str = "") -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if task_id:
            params["task_id"] = task_id
        if website_id:
            params["website_id"] = website_id
        return self.request("GET", "/v2/website.listCheckpoints", params=params)

    def website_publish(self, task_id: str = "", website_id: str = "", visibility: str = "public") -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if task_id:
            body["task_id"] = task_id
        if website_id:
            body["website_id"] = website_id
        if visibility:
            body["visibility"] = visibility
        return self.request("POST", "/v2/website.publish", body=body)

    def website_update(
        self,
        task_id: str = "",
        website_id: str = "",
        title: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {}
        if task_id:
            body["task_id"] = task_id
        if website_id:
            body["website_id"] = website_id
        if title is not None:
            body["title"] = title
        if visibility is not None:
            body["visibility"] = visibility
        return self.request("POST", "/v2/website.update", body=body)


def get_msg_id(msg: Dict[str, Any]) -> str:
    return str(msg.get("id") or msg.get("timestamp") or hash(json.dumps(msg, sort_keys=True, default=str)))


def extrair_texto_assistente(assistant_message: Any) -> str:
    if not assistant_message:
        return ""
    if isinstance(assistant_message, str):
        return assistant_message.strip()
    if isinstance(assistant_message, dict):
        content = assistant_message.get("content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            partes = []
            for item in content:
                if isinstance(item, str):
                    partes.append(item)
                elif isinstance(item, dict):
                    txt = item.get("text") or item.get("content") or ""
                    if txt:
                        partes.append(str(txt))
            return "\n".join(partes).strip()
    return ""


def extrair_anexos_assistente(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
    assistant = msg.get("assistant_message")
    if not isinstance(assistant, dict):
        return []
    attachments = assistant.get("attachments") or []
    if not isinstance(attachments, list):
        return []
    out = []
    for a in attachments:
        if isinstance(a, dict) and a.get("url"):
            out.append(a)
    return out


def status_mais_recente(messages: list) -> Tuple[str, Dict[str, Any]]:
    for msg in messages:
        status_update = msg.get("status_update")
        if not status_update:
            continue
        agent_status = str(status_update.get("agent_status") or "").strip().lower()
        brief = str(status_update.get("brief") or "").strip()
        if agent_status:
            return agent_status, status_update
        if brief:
            return brief.lower(), status_update
    return "", {}


def eventos_da_tarefa(messages: list) -> List[Dict[str, Any]]:
    eventos = []
    for msg in reversed(messages):
        msg_id = get_msg_id(msg)

        status_update = msg.get("status_update")
        if status_update:
            status = str(status_update.get("agent_status") or "").strip()
            brief = str(status_update.get("brief") or "").strip()
            desc = str(status_update.get("description") or "").strip()
            detail = status_update.get("status_detail") or {}
            text = " | ".join([x for x in [status, brief, desc] if x])
            if text:
                eventos.append({"kind": "status", "id": f"status:{msg_id}:{text}", "text": text, "raw": status_update})
            if detail:
                waiting_desc = str(detail.get("waiting_description") or "").strip()
                if waiting_desc:
                    eventos.append({"kind": "waiting_detail", "id": f"waiting:{msg_id}:{waiting_desc}", "text": waiting_desc, "raw": detail})

        text = extrair_texto_assistente(msg.get("assistant_message"))
        if text:
            eventos.append({"kind": "assistant", "id": f"assistant:{msg_id}:{hash(text)}", "text": text, "raw": msg.get("assistant_message")})

        for a in extrair_anexos_assistente(msg):
            aid = f"attachment:{msg_id}:{a.get('filename') or a.get('file_name') or a.get('url')}"
            eventos.append({"kind": "attachment", "id": aid, "text": a.get("filename") or a.get("file_name") or a.get("url"), "raw": a})

        error_message = msg.get("error_message")
        if error_message:
            eventos.append({"kind": "error", "id": f"error:{msg_id}", "text": json.dumps(error_message, ensure_ascii=False, indent=2), "raw": error_message})

    return eventos


URL_RE = re.compile(r"https?://[^\s\)\]\}\"'<>,]+", re.IGNORECASE)


def extrair_urls_baixaveis(texto: str) -> List[str]:
    urls = []
    for match in URL_RE.findall(texto or ""):
        url = match.rstrip(".,;:")
        path = urlparse(url).path
        ext = Path(path).suffix.lower()
        if ext in DOWNLOAD_EXTS:
            urls.append(url)
    return list(dict.fromkeys(urls))


def filename_from_url(url: str, fallback: str = "arquivo") -> str:
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name
    if not name:
        name = fallback
    return nome_seguro(name, 120)


def caminho_unico(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 2
    while True:
        novo = parent / f"{stem}_{i}{suffix}"
        if not novo.exists():
            return novo
        i += 1


def baixar_url(url: str, destino: Path, logger: Optional[AutoLogger] = None, cb=None) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino = caminho_unico(destino)

    if cb:
        cb(f"Baixando: {url}")

    if logger:
        logger.log("download_start", f"Baixando {url}", url=url, path=str(destino))

    with HTTP_SESSION.get(url, stream=True, timeout=900) as resp:
        resp.raise_for_status()
        with destino.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    if logger:
        logger.log("download_done", f"Arquivo baixado: {destino}", url=url, path=str(destino), size=destino.stat().st_size)

    if cb:
        cb(f"[OK] Baixado: {destino}")

    return destino


def baixar_anexo(anexo: Dict[str, Any], task_id: str, logger: Optional[AutoLogger] = None, cb=None) -> Optional[Path]:
    url = anexo.get("url")
    if not url:
        return None

    filename = anexo.get("filename") or anexo.get("file_name") or filename_from_url(url, "anexo")
    filename = nome_seguro(filename, 160)
    pasta = DOWNLOAD_DIR / nome_seguro(task_id)
    return baixar_url(url, pasta / filename, logger=logger, cb=cb)


def carregar_api_key(api_key_arg: str = "") -> str:
    key = (api_key_arg or "").strip()
    if key:
        return key
    key = os.getenv("MANUS_API_KEY", "").strip()
    if key:
        return key
    if KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key
    raise RuntimeError("API key não encontrada. Use MANUS_API_KEY, manus_api_key.local ou --api-key.")


def run_automation(
    *,
    api_key: str,
    prompt: str,
    files: List[str],
    agent_profile: str,
    title: str,
    poll_interval: int = 3,
    log_enabled: bool = True,
    download_enabled: bool = True,
) -> int:
    logger = AutoLogger(enabled=log_enabled, prefix=title or "automacao_manus")
    api = ManusAPI(api_key)

    def out(msg: str):
        print(msg, flush=True)
        logger.log("console", msg)

    try:
        out("=== MANUS API AUTOMAÇÃO COMPLETA ===")
        out("Este modo não tem timeout automático. Ele fica rodando até stopped/error/waiting ou Ctrl+C.")

        skills = api.list_skills().get("data", [])
        out(f"OK: autenticação funcionando. Skills encontradas: {len(skills)}")

        uploaded = []
        for idx, f in enumerate(files, start=1):
            p = Path(f)
            out(f"[UPLOAD {idx}/{len(files)}] {p}")
            last_printed_percent = {"value": -1}

            def auto_progress(percent, sent, total, filename):
                percent_int = int(percent)
                if percent_int != last_printed_percent["value"]:
                    last_printed_percent["value"] = percent_int
                    out(f"[UPLOAD %] {filename}: {percent:.2f}% - {tamanho_legivel(sent)} de {tamanho_legivel(total)}")

            info = api.upload_local_file(
                p,
                logger=logger,
                cb=lambda m: out(f"[UPLOAD] {m}"),
                progress_cb=auto_progress,
            )
            uploaded.append(info)
            out(f"[OK] Upload concluído: {info['filename']} | file_id={info['file_id']}")

        out("Criando tarefa...")
        data = api.create_task(prompt, agent_profile, title, uploaded_files=uploaded)
        task_id = data.get("task_id") or ""
        task_url = data.get("task_url") or ""
        task_title = data.get("task_title") or title

        if task_id:
            logger.update_task_id(task_id)

        logger.log("task_created", "Tarefa criada", task_id=task_id, task_url=task_url, title=task_title)
        out(f"Tarefa criada: {task_title}")
        out(f"task_id: {task_id}")
        out(f"url: {task_url}")

        vistos = set()
        baixados_urls = set()
        ultima_resposta = ""

        while True:
            data = api.list_messages(task_id, limit=200, slides_format="pptx")
            messages = data.get("messages", [])
            status, status_raw = status_mais_recente(messages)
            if status:
                out(f"[STATUS] {status}")
                logger.log("status", status, raw=status_raw)

            for ev in eventos_da_tarefa(messages):
                if ev["id"] in vistos:
                    continue
                vistos.add(ev["id"])

                kind = ev["kind"]
                text = ev["text"]

                if kind == "assistant":
                    ultima_resposta = text
                    print("\n[MENSAGEM DO MANUS]")
                    print(text)
                    print()
                    logger.log("assistant_message", text)

                    if download_enabled:
                        for url in extrair_urls_baixaveis(text):
                            if url in baixados_urls:
                                continue
                            baixados_urls.add(url)
                            fname = filename_from_url(url)
                            path = baixar_url(url, DOWNLOAD_DIR / nome_seguro(task_id) / fname, logger=logger, cb=lambda m: out(f"[DOWNLOAD] {m}"))
                            out(f"[ARQUIVO BAIXADO] {path}")

                elif kind == "attachment":
                    anexo = ev["raw"]
                    url = anexo.get("url")
                    if download_enabled and url and url not in baixados_urls:
                        baixados_urls.add(url)
                        path = baixar_anexo(anexo, task_id, logger=logger, cb=lambda m: out(f"[DOWNLOAD] {m}"))
                        if path:
                            out(f"[ANEXO BAIXADO] {path}")

                elif kind == "waiting_detail":
                    out(f"[AGUARDANDO USUÁRIO] {text}")
                    logger.log("waiting", text, raw=ev["raw"])

                elif kind == "error":
                    out("[ERRO NA TAREFA]")
                    out(text)
                    logger.log("task_error", text)
                    return 2

            if status == "stopped":
                out("[OK] Tarefa finalizada.")
                salvar_tarefa_concluida_local({
                    "id": task_id,
                    "title": task_title,
                    "task_url": task_url,
                    "status": "stopped",
                    "updated_at": int(time.time()),
                    "source": "auto_local",
                })
                if ultima_resposta:
                    final_path = logger.save_final(ultima_resposta)
                    print("\n================ RESPOSTA FINAL ================")
                    print(ultima_resposta)
                    print("================================================")
                    if final_path:
                        out(f"Resposta final salva em: {final_path}")
                out(f"Arquivos baixados ficam em: {DOWNLOAD_DIR / nome_seguro(task_id)}")
                return 0

            if status == "error":
                out("[ERRO] A tarefa terminou com erro.")
                return 2

            if status == "waiting":
                out("[ATENÇÃO] A tarefa está aguardando resposta/confirmação. No modo GUI use os botões de responder/confirmar. No modo --auto, abra a URL ou rode outra ação manual.")
                return 3

            time.sleep(max(1, poll_interval))

    except KeyboardInterrupt:
        out("Interrompido pelo usuário.")
        return 130
    except Exception as e:
        err = f"{e}\n\n{traceback.format_exc()}"
        logger.log("fatal_error", err)
        print("[ERRO]", err, file=sys.stderr)
        return 1


class OtherAIClient:
    """
    Cliente genérico para outras IAs/APIs.

    Suporta principalmente APIs do tipo:
    - OpenAI-compatible / Chat Completions
      POST {base_url}{endpoint}
      Authorization: Bearer <api_key>
      body: model, messages, temperature, max_tokens

    Também suporta modo header x-api-key para APIs que usam esse cabeçalho.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        endpoint: str = "/chat/completions",
        auth_mode: str = "bearer",
        provider_type: str = "openai_compatible",
    ):
        self.name = str(name or "Outra IA").strip()
        self.base_url = str(base_url or "").strip().rstrip("/")
        self.api_key = str(api_key or "").strip()
        self.model = str(model or "").strip()
        self.endpoint = str(endpoint or "/chat/completions").strip()
        self.auth_mode = str(auth_mode or "bearer").strip().lower()
        self.provider_type = str(provider_type or "openai_compatible").strip().lower()

        if not self.base_url:
            raise RuntimeError("Base URL da outra IA está vazia.")
        if not self.api_key:
            raise RuntimeError("APIKEY da outra IA está vazia.")
        if not self.model:
            raise RuntimeError("Modelo da outra IA está vazio.")

    def headers(self) -> Dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self._eh_anthropic():
            # API nativa da Anthropic (Claude): usa x-api-key + anthropic-version.
            h["x-api-key"] = self.api_key
            h["anthropic-version"] = "2023-06-01"
            return h

        if self.auth_mode in {"x-api-key", "x_api_key", "apikey"}:
            h["x-api-key"] = self.api_key
        else:
            h["Authorization"] = f"Bearer {self.api_key}"

        return h

    def _eh_anthropic(self) -> bool:
        """Detecta se deve usar o protocolo nativo da Anthropic (Claude)."""
        return ("anthropic" in str(self.provider_type or "").lower()) or ("anthropic.com" in str(self.base_url or "").lower())

    def url(self) -> str:
        endpoint = self.endpoint or "/chat/completions"
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return self.base_url + endpoint

    def chat(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.4,
        max_tokens: int = 2048,
        timeout: int = 180,
    ) -> Dict[str, Any]:
        prompt = str(prompt or "").strip()
        if not prompt:
            raise RuntimeError("Prompt vazio para outra IA.")

        if self._eh_anthropic():
            # Formato nativo da Anthropic (Claude): /v1/messages
            body = {
                "model": self.model,
                "max_tokens": int(max_tokens),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": float(temperature),
            }
            if system_prompt.strip():
                body["system"] = system_prompt.strip()
        else:
            messages = []
            if system_prompt.strip():
                messages.append({"role": "system", "content": system_prompt.strip()})
            messages.append({"role": "user", "content": prompt})

            body = {
                "model": self.model,
                "messages": messages,
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
            }

        resp = requests.post(
            self.url(),
            headers=self.headers(),
            json=body,
            timeout=timeout,
        )

        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}

        if not resp.ok:
            raise RuntimeError(
                f"Erro na outra IA/API: {self.name}\n"
                f"HTTP {resp.status_code}\n\n"
                f"{json.dumps(data, ensure_ascii=False, indent=2)[:4000]}"
            )

        return data

    def chat_mensagens(self, messages, temperature: float = 0.4, max_tokens: int = 2048, timeout: int = 300) -> Dict[str, Any]:
        """
        Envia uma lista de mensagens (formato OpenAI) e devolve a resposta crua.
        Suporta conteúdo multimodal (texto + image_url) no modo OpenAI-compatible
        e converte para o formato nativo da Anthropic quando necessário.
        """
        msgs = list(messages or [])
        if self._eh_anthropic():
            sistema = ""
            conv = []
            for m in msgs:
                role = m.get("role")
                cont = m.get("content")
                if role == "system":
                    if isinstance(cont, str):
                        sistema = (sistema + "\n" + cont).strip()
                    continue
                if isinstance(cont, list):
                    textos = [b.get("text", "") for b in cont if isinstance(b, dict) and b.get("type") == "text"]
                    cont = "\n".join(t for t in textos if t)
                conv.append({"role": ("assistant" if role == "assistant" else "user"), "content": cont})
            body = {
                "model": self.model,
                "max_tokens": int(max_tokens),
                "messages": conv,
                "temperature": float(temperature),
            }
            if sistema:
                body["system"] = sistema
        else:
            body = {
                "model": self.model,
                "messages": msgs,
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
            }

        resp = requests.post(self.url(), headers=self.headers(), json=body, timeout=timeout)
        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}
        if not resp.ok:
            raise RuntimeError(
                f"Erro na outra IA/API: {self.name}\nHTTP {resp.status_code}\n\n"
                f"{json.dumps(data, ensure_ascii=False, indent=2)[:4000]}"
            )
        return data

    @staticmethod
    def extrair_texto(data: Dict[str, Any]) -> str:
        """
        Extrai texto de respostas comuns:
        - OpenAI-compatible: choices[0].message.content
        - Algumas APIs retornam output_text/text/content
        """
        try:
            # Anthropic (Claude): conteúdo é uma lista de blocos no topo.
            conteudo_anthropic = data.get("content")
            if isinstance(conteudo_anthropic, list):
                partes_a = []
                for item in conteudo_anthropic:
                    if isinstance(item, dict) and (item.get("type") == "text" or item.get("text")):
                        partes_a.append(str(item.get("text") or ""))
                if any(p.strip() for p in partes_a):
                    return "\n".join(p for p in partes_a if p.strip())
        except Exception:
            pass

        try:
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0] or {}
                msg = first.get("message") or {}
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, str):
                        return content
                    if isinstance(content, list):
                        partes = []
                        for item in content:
                            if isinstance(item, dict):
                                partes.append(str(item.get("text") or item.get("content") or ""))
                            else:
                                partes.append(str(item))
                        return "\n".join(p for p in partes if p.strip())
                if first.get("text"):
                    return str(first.get("text"))
        except Exception:
            pass

        for key in ("output_text", "text", "content", "answer", "response"):
            try:
                val = data.get(key)
                if isinstance(val, str) and val.strip():
                    return val
            except Exception:
                pass

        return json.dumps(data, ensure_ascii=False, indent=2)


class ManusAPIFailover(ManusAPI):
    """
    Cliente ManusAPI com múltiplas chaves e failover técnico.

    Mantém a mesma interface de ManusAPI, porque herda todos os métodos:
    list_skills, create_task, list_messages, upload_local_file, etc.

    A troca automática acontece quando:
    - a chave atual falha por autenticação/permissão,
    - ocorre timeout/conexão/erro transitório,
    - erro 5xx/408.

    Para HTTP 429/crédito/limite, o app informa o bloqueio e não troca
    automaticamente por padrão.
    """

    def __init__(
        self,
        keys: List[str],
        *,
        on_key_change=None,
        on_key_problem=None,
        allow_credit_failover: bool = False,
    ):
        keys_limpos = []
        vistos = set()
        for key in keys or []:
            key = str(key or "").strip()
            if key and key not in vistos:
                keys_limpos.append(key)
                vistos.add(key)

        if not keys_limpos:
            raise RuntimeError("Nenhuma APIKEY disponível para usar.")

        self.keys = keys_limpos
        self.current_index = 0
        self.on_key_change = on_key_change
        self.on_key_problem = on_key_problem
        self.allow_credit_failover = bool(allow_credit_failover)
        super().__init__(self.keys[0])

    def _avisar_troca(self, old_index: int, new_index: int, reason: str):
        try:
            if self.on_key_change:
                self.on_key_change(
                    new_index,
                    self.keys[new_index],
                    f"Troca automática: chave {old_index + 1} -> {new_index + 1}. Motivo: {reason}",
                )
        except Exception:
            pass

    def _avisar_problema(self, index: int, key: str, exc: Exception):
        try:
            if self.on_key_problem:
                self.on_key_problem(index, key, str(exc))
        except Exception:
            pass

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 90,
    ) -> Dict[str, Any]:
        total = len(self.keys)
        ultimo_erro = None
        tentadas = set()

        for _ in range(total):
            idx = self.current_index
            tentadas.add(idx)
            self.api_key = self.keys[idx]

            try:
                return super().request(method, path, params=params, body=body, timeout=timeout)

            except Exception as e:
                ultimo_erro = e
                self._avisar_problema(idx, self.keys[idx], e)

                # Crédito/limite: não troca automaticamente por padrão.
                if erro_credito_esgotado(e) and not self.allow_credit_failover:
                    raise

                # Só troca se houver outra chave e o erro for elegível.
                pode_trocar = erro_permite_failover_chave(e) or (erro_credito_esgotado(e) and self.allow_credit_failover)
                if total <= 1 or not pode_trocar:
                    raise

                proximo = (self.current_index + 1) % total
                while proximo in tentadas and len(tentadas) < total:
                    proximo = (proximo + 1) % total

                if proximo in tentadas:
                    break

                antigo = self.current_index
                self.current_index = proximo
                self.api_key = self.keys[self.current_index]
                self._avisar_troca(antigo, self.current_index, str(e)[:500])
                continue

        if ultimo_erro:
            raise RuntimeError(
                "Todas as APIKEYs cadastradas foram tentadas e nenhuma conseguiu concluir a chamada.\n\n"
                f"Último erro:\n{ultimo_erro}"
            )

        raise RuntimeError("Falha desconhecida no failover de APIKEY.")


# ============================================================
# CATÁLOGO COMPLETO DOS ENDPOINTS DA API v2 DO MANUS
# Usado pela aba "Central da API Manus" para permitir executar
# QUALQUER endpoint (leitura GET e escrita POST) direto no servidor.
# Cada item traz um "template" de parâmetros/corpo em JSON para edição.
# ============================================================
MANUS_API_ENDPOINTS: List[Dict[str, Any]] = [
    # ---------- LEITURA (GET) ----------
    {"name": "usage.availableCredits", "method": "GET", "path": "/v2/usage.availableCredits", "kind": "params",
     "template": {}, "desc": "Saldo de créditos e informações de refresh (somente leitura)."},
    {"name": "usage.list", "method": "GET", "path": "/v2/usage.list", "kind": "params",
     "template": {"limit": 20}, "desc": "Histórico de mudanças de crédito, mais recente primeiro (somente leitura)."},
    {"name": "usage.teamLog", "method": "GET", "path": "/v2/usage.teamLog", "kind": "params",
     "template": {}, "desc": "Contagem de tarefas e consumo de crédito por membro da equipe (somente leitura)."},
    {"name": "usage.teamStatistic", "method": "GET", "path": "/v2/usage.teamStatistic", "kind": "params",
     "template": {}, "desc": "Totais diários de consumo de crédito da equipe (somente leitura)."},
    {"name": "skill.list", "method": "GET", "path": "/v2/skill.list", "kind": "params",
     "template": {}, "desc": "Lista as skills disponíveis."},
    {"name": "task.list", "method": "GET", "path": "/v2/task.list", "kind": "params",
     "template": {"limit": 20, "order": "desc", "scope": "all"}, "desc": "Lista tarefas (filtros: order, scope, agent_id, project_id, cursor)."},
    {"name": "task.detail", "method": "GET", "path": "/v2/task.detail", "kind": "params",
     "template": {"task_id": ""}, "desc": "Detalhes de uma tarefa (inclui status e agent_profile/modelo)."},
    {"name": "task.listMessages", "method": "GET", "path": "/v2/task.listMessages", "kind": "params",
     "template": {"task_id": "", "order": "desc", "limit": 50}, "desc": "Mensagens/eventos de uma tarefa."},
    {"name": "agent.list", "method": "GET", "path": "/v2/agent.list", "kind": "params",
     "template": {}, "desc": "Lista os agentes personalizados da conta."},
    {"name": "agent.detail", "method": "GET", "path": "/v2/agent.detail", "kind": "params",
     "template": {"agent_id": ""}, "desc": "Detalhes de um agente."},
    {"name": "connector.list", "method": "GET", "path": "/v2/connector.list", "kind": "params",
     "template": {}, "desc": "Lista os connectors instalados na conta."},
    {"name": "project.list", "method": "GET", "path": "/v2/project.list", "kind": "params",
     "template": {}, "desc": "Lista os projetos."},
    {"name": "browser.onlineList", "method": "GET", "path": "/v2/browser.onlineList", "kind": "params",
     "template": {}, "desc": "Lista os navegadores online do usuário."},
    {"name": "file.detail", "method": "GET", "path": "/v2/file.detail", "kind": "params",
     "template": {"file_id": ""}, "desc": "Detalhes de um arquivo enviado (status, tamanho, expiração)."},
    {"name": "webhook.list", "method": "GET", "path": "/v2/webhook.list", "kind": "params",
     "template": {}, "desc": "Lista os webhooks cadastrados."},
    {"name": "webhook.publicKey", "method": "GET", "path": "/v2/webhook.publicKey", "kind": "params",
     "template": {}, "desc": "Chave pública para verificar assinaturas de webhook."},
    {"name": "website.status", "method": "GET", "path": "/v2/website.status", "kind": "params",
     "template": {"task_id": ""}, "desc": "Status de publicação, URL e visibilidade de um site (task_id OU website_id)."},
    {"name": "website.listCheckpoints", "method": "GET", "path": "/v2/website.listCheckpoints", "kind": "params",
     "template": {"task_id": ""}, "desc": "Lista os checkpoints/versões de um site (task_id OU website_id)."},

    # ---------- ESCRITA (POST) ----------
    {"name": "task.create", "method": "POST", "path": "/v2/task.create", "kind": "body",
     "template": {"message": {"content": [{"type": "text", "text": "Escreva seu prompt aqui"}]},
                  "agent_profile": "manus-1.6-lite", "title": "", "hide_in_task_list": False, "share_visibility": "private"},
     "desc": "Cria uma nova tarefa (define modelo, prompt, título, visibilidade)."},
    {"name": "task.sendMessage", "method": "POST", "path": "/v2/task.sendMessage", "kind": "body",
     "template": {"task_id": "", "message": {"content": [{"type": "text", "text": "sua mensagem"}]}, "agent_profile": ""},
     "desc": "Envia mensagem a uma tarefa. agent_profile faz override do MODELO; deixe vazio para manter."},
    {"name": "task.update", "method": "POST", "path": "/v2/task.update", "kind": "body",
     "template": {"task_id": "", "title": "", "share_visibility": "private", "enable_visible_in_task_list": True},
     "desc": "Muda título, visibilidade (private/team/public) e mostrar/ocultar na lista."},
    {"name": "task.stop", "method": "POST", "path": "/v2/task.stop", "kind": "body",
     "template": {"task_id": ""}, "desc": "Para uma tarefa em execução."},
    {"name": "task.delete", "method": "POST", "path": "/v2/task.delete", "kind": "body",
     "template": {"task_id": ""}, "desc": "Apaga uma tarefa permanentemente."},
    {"name": "task.confirmAction", "method": "POST", "path": "/v2/task.confirmAction", "kind": "body",
     "template": {"task_id": "", "event_id": "", "input": {"accept": True}}, "desc": "Confirma uma ação pendente da tarefa."},
    {"name": "agent.update", "method": "POST", "path": "/v2/agent.update", "kind": "body",
     "template": {"agent_id": "", "nickname": "", "about": ""}, "desc": "Muda o nome (nickname) e a descrição (about) de um agente."},
    {"name": "file.upload", "method": "POST", "path": "/v2/file.upload", "kind": "body",
     "template": {"filename": "arquivo.txt"}, "desc": "Cria o registro do arquivo e retorna upload_url (o envio dos bytes é feito à parte)."},
    {"name": "file.delete", "method": "POST", "path": "/v2/file.delete", "kind": "body",
     "template": {"file_id": ""}, "desc": "Apaga um arquivo enviado."},
    {"name": "project.create", "method": "POST", "path": "/v2/project.create", "kind": "body",
     "template": {"name": "Meu projeto", "instruction": ""}, "desc": "Cria um projeto (agrupa tarefas + instrução compartilhada)."},
    {"name": "webhook.create", "method": "POST", "path": "/v2/webhook.create", "kind": "body",
     "template": {"url": "https://seu-endpoint.exemplo/webhook"}, "desc": "Cria um webhook para notificações de eventos de tarefa."},
    {"name": "webhook.delete", "method": "POST", "path": "/v2/webhook.delete", "kind": "body",
     "template": {"webhook_id": ""}, "desc": "Apaga um webhook."},
    {"name": "website.publish", "method": "POST", "path": "/v2/website.publish", "kind": "body",
     "template": {"task_id": "", "visibility": "public"}, "desc": "Publica/implanta o último checkpoint de um site."},
    {"name": "website.update", "method": "POST", "path": "/v2/website.update", "kind": "body",
     "template": {"task_id": "", "title": "", "visibility": "public"}, "desc": "Muda título/visibilidade do site (sem redeploy)."},
]


class ManusGui(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Manus API Pro FULL - Profissional, Seguro, Robusto e Animado")
        self.geometry("1380x920")
        self.minsize(1180, 820)

        # Abre maximizado no Windows. Em outros sistemas tenta usar -zoomed.
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

        # Abre maximizado no Windows. Em outros sistemas tenta usar -zoomed.
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

        self.msg_queue = queue.Queue()
        self.stop_polling = threading.Event()

        self.current_task_id = ""
        self.current_task_url = ""
        self.textos_mostrados = set()
        self.eventos_vistos = set()
        self.urls_baixadas = set()
        self.selected_files: List[Path] = []
        self.reply_files: List[Path] = []
        self.downloaded_files: List[Path] = []
        # Guarda as últimas mensagens completas da tarefa para o salvamento contínuo.
        self.ultimas_mensagens: List[Dict[str, Any]] = []
        # Intervalo do salvamento automático periódico (em milissegundos).
        self.autosave_intervalo_ms = 12000

        # ===== Barra de status animada / dinâmica =====
        self.statusbar_var = tk.StringVar(value="Pronto. Bem-vindo ao Manus API Pro FULL.")
        self.clock_var = tk.StringVar(value="")
        self.spinner_var = tk.StringVar(value="[ ok ]")
        self._spinner_frames = [
            "[>    ]", "[=>   ]", "[==>  ]", "[===> ]", "[====>]",
            "[ ===>]", "[  ==>]", "[   =>]", "[    >]", "[     ]",
        ]
        self._spinner_idx = 0
        self._threads_ativas = 0

        # Tema (claro/escuro) persistido nas preferências locais.
        _prefs_tema = ler_json_seguro(PREFERENCES_FILE, {})
        self.tema_atual = str((_prefs_tema or {}).get("tema") or "claro").strip().lower()
        if self.tema_atual not in ("claro", "escuro"):
            self.tema_atual = "claro"
        self._tema_text_bg = "#FFFFFF"
        self._tema_text_fg = "#111827"
        self._tema_sel = "#2563EB"

        # ===== Recursos avançados (Turbo / IA / Injeção / Furtivo) =====
        self.turbo_var = tk.BooleanVar(value=False)
        self.stealth_var = tk.BooleanVar(value=False)
        self.injection_enabled_var = tk.BooleanVar(value=False)
        self.prefer_manus_var = tk.BooleanVar(value=True)
        self.best_model_var = tk.BooleanVar(value=False)
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.bip_var = tk.BooleanVar(value=True)
        self.turbo_status_var = tk.StringVar(value="Turbo: desligado")
        self.stealth_status_var = tk.StringVar(value="Furtivo: desligado")
        self.injection_status_var = tk.StringVar(value="Injeção: desativada")
        self.prompt_metrics_var = tk.StringVar(value="Prompt: 0 palavras / ~0 tokens")
        self.multi_ia_status_var = tk.StringVar(value="Multi-IA: pronto (Manus é a IA preferencial)")
        self.injection_presets_status_var = tk.StringVar(value="Injeções salvas: 0")
        self.prompt_presets_status_var = tk.StringVar(value="Presets de prompt: 0")
        self.injection_name_var = tk.StringVar(value="")
        self.prompt_preset_name_var = tk.StringVar(value="")
        # Intervalo dinâmico da fila de UI (tempo real). Turbo reduz para resposta instantânea.
        self.fila_intervalo_ms = 100
        self._poll_interval_anterior = ""
        # Bibliotecas locais carregadas do disco.
        self.injecoes: List[Dict[str, Any]] = self._carregar_injecoes()
        self.prompt_presets: List[Dict[str, Any]] = self._carregar_prompt_presets()

        # ===== Fusão de chaves Manus (créditos somados / uso em cadeia automática) =====
        self.fusion_enabled_var = tk.BooleanVar(value=False)
        self.fused_keys: List[str] = []
        self.fusion_status_var = tk.StringVar(value="Fusão: desativada")
        self.fused_credits_var = tk.StringVar(value="Créditos somados: -- (consulte para calcular)")
        try:
            _fz = ler_json_seguro(FUSION_FILE, {})
            if isinstance(_fz, dict):
                self.fused_keys = [str(k).strip() for k in (_fz.get("keys") or []) if str(k).strip()]
                self.fusion_enabled_var.set(bool(_fz.get("enabled")))
                if self.fusion_enabled_var.get() and len(self.fused_keys) >= 2:
                    self.fusion_status_var.set(f"Fusão: ATIVADA com {len(self.fused_keys)} chaves (créditos somados, cadeia automática)")
        except Exception:
            pass

        # ===== Backup automático via FTPS (dados embutidos a pedido do usuário) =====
        self.ftp_enabled_var = tk.BooleanVar(value=True)
        self.ftp_status_var = tk.StringVar(value=f"Backup FTP: automático ativado ({FTP_HOST})")
        self.ftp_queue = queue.Queue()
        self._ftp_backup = None
        self._ultimo_backup_checkpoint = 0.0
        self._ultimo_backup_full = 0.0

        # ===== Cache/persistência MySQL (busca a resposta no banco antes da API) =====
        self.mysql_enabled_var = tk.BooleanVar(value=True)
        self.mysql_lookup_var = tk.BooleanVar(value=True)
        self.mysql_status_var = tk.StringVar(
            value=(f"MySQL: pronto ({MYSQL_HOST}/{MYSQL_DB})" if MYSQL_DISPONIVEL
                   else "MySQL: driver PyMySQL não instalado (use 01_instalar_dependencias.bat)")
        )
        self._mysql = MySQLCache()
        self._ultimo_prompt_enviado = ""
        self._ultimo_agent_enviado = ""

        # ===== Estúdio de Outras IAs (workspace completo das outras APIs) =====
        self.estudio_anexos: List[Path] = []
        self.estudio_downloads: List[Path] = []
        self.estudio_tarefa_atual: Dict[str, Any] = {}
        self.estudio_ultima_resposta = ""
        self.estudio_tarefas: List[Dict[str, Any]] = self._estudio_carregar_tarefas_disco()
        self.estudio_status_var = tk.StringVar(value="Estúdio: pronto. Configure o provedor na aba 'Outras IAs / APIs'.")
        self.estudio_anexos_var = tk.StringVar(value="Nenhum anexo.")
        self.estudio_info_var = tk.StringVar(value="Provedor atual: --")
        self.last_waiting_detail: Dict[str, Any] = {}

        self.logger = AutoLogger(enabled=True, prefix="gui")

        self.privacy_var = tk.BooleanVar(value=False)
        self.auto_log_var = tk.BooleanVar(value=True)
        self.auto_follow_var = tk.BooleanVar(value=True)
        self.auto_download_var = tk.BooleanVar(value=True)
        self.api_key_var = tk.StringVar(value=self.carregar_chave_local())
        self.show_key_var = tk.BooleanVar(value=False)
        self.api_keys: List[str] = self.carregar_chaves_multiplas()
        self.keyring_status_var = tk.StringVar(value="Chaves cadastradas: carregando...")
        self.failover_status_var = tk.StringVar(value="Failover: ativo para falha técnica/autenticação. 429/crédito exige ação manual.")

        # Créditos Manus
        self.credit_status_var = tk.StringVar(value="Créditos: ainda não consultado")
        self.credit_detail_var = tk.StringVar(value="Detalhes dos créditos: --")
        self.credit_key_var = tk.StringVar(value="Chave consultada: --")
        self.credit_last_update_var = tk.StringVar(value="Créditos atualizados em: --")

        # Outras IAs / APIs
        self.other_ai_providers: List[Dict[str, Any]] = self.carregar_outros_provedores_ia()
        self.other_ai_name_var = tk.StringVar(value="OpenAI Compatível")
        self.other_ai_type_var = tk.StringVar(value="openai_compatible")
        self.other_ai_base_url_var = tk.StringVar(value="https://api.openai.com/v1")
        self.other_ai_endpoint_var = tk.StringVar(value="/chat/completions")
        self.other_ai_model_var = tk.StringVar(value="gpt-4o-mini")
        self.other_ai_key_var = tk.StringVar(value="")
        self.other_ai_auth_var = tk.StringVar(value="bearer")
        self.other_ai_temp_var = tk.StringVar(value="0.4")
        self.other_ai_max_tokens_var = tk.StringVar(value="2048")
        self.other_ai_status_var = tk.StringVar(value="Outras IAs: nenhum provedor ativo | provedores salvos persistem após reiniciar")

        # Checkpoint local da tarefa atual
        self.task_checkpoint_status_var = tk.StringVar(value="Checkpoint: nenhuma tarefa salva ainda")
        self.current_task_state: Dict[str, Any] = {}
        self.checkpoint_enabled_var = tk.BooleanVar(value=True)
        self.agent_var = tk.StringVar(value="manus-1.6-lite")
        self.title_var = tk.StringVar(value=titulo_nova_tarefa())
        self.task_id_var = tk.StringVar(value="")
        self.task_url_var = tk.StringVar(value="")
        self.poll_interval_var = tk.StringVar(value="3")
        self.upload_percent_var = tk.DoubleVar(value=0.0)
        self.upload_status_var = tk.StringVar(value="Upload: aguardando arquivo.")
        self.upload_detail_var = tk.StringVar(value="")

        # Status em tempo real do servidor e da tarefa.
        self.server_status_var = tk.StringVar(value="Servidor: ainda não testado")
        self.server_last_seen_var = tk.StringVar(value="Última resposta do servidor: --")
        self.task_status_var = tk.StringVar(value="Tarefa: nenhuma tarefa iniciada")
        self.task_phase_var = tk.StringVar(value="Fase atual: --")
        self.task_clue_var = tk.StringVar(value="Pistas do servidor: --")
        self.task_activity_var = tk.StringVar(value="Atividade: --")

        # Recursos profissionais adicionais.
        self.professional_mode_var = tk.BooleanVar(value=True)
        self.autosave_prompt_var = tk.BooleanVar(value=True)
        self.compact_mode_var = tk.BooleanVar(value=False)
        self.integrity_status_var = tk.StringVar(value="Integridade: aguardando verificação")
        self.security_status_var = tk.StringVar(value="Segurança: chave oculta e armazenamento local")
        self.session_status_var = tk.StringVar(value="Sessão: pronta")
        self.quick_hint_var = tk.StringVar(value="Dica: checkpoint salva tudo; se crédito acabar, escolha outra chave e continue sem perda")

        self.aplicar_tema_profissional()
        self.carregar_preferencias_locais()
        self.criar_layout()
        try:
            self._recolorir_widgets_tk()
        except Exception:
            pass
        self.aplicar_chave_ativa_persistida()
        self.atualizar_lista_chaves()
        self.atualizar_lista_outros_provedores_ia()
        self.configurar_atalhos_profissionais()
        self.carregar_rascunho_prompt()
        self.verificar_integridade_local()
        try:
            self.protocol("WM_DELETE_WINDOW", self.fechar_app_salvando)
        except Exception:
            pass
        self.after(100, self.processar_fila)
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        # Inicia o salvamento contínuo de todos os dados da tarefa.
        self.after(self.autosave_intervalo_ms, self.autosave_periodico)

        # Inicia a barra de status animada (relógio + spinner dinâmico).
        self.after(450, self._heartbeat_ui)

        # Inicia o worker de backup FTP (envio automático em segundo plano).
        try:
            self._ftp_thread = threading.Thread(target=self._ftp_worker, daemon=True)
            self._ftp_thread.start()
        except Exception:
            pass
        # Sincronização inicial automática (app, pastas e arquivos de trabalho).
        self.after(8000, self._backup_inicial_automatico)
        # Inicializa o MySQL (cria tabelas/colunas) em segundo plano.
        self.after(2000, self.inicializar_mysql_bg)

        if self.api_key_var.get().strip():
            self.log("[OK] Chave carregada de manus_api_key.local.\n")
        else:
            self.log("[INFO] Cole sua chave da Manus e clique em 'Salvar chave', ou use sem salvar.\n")

        self.log(f"[LOG] Pasta de logs: {LOG_DIR}\n")
        self.log(f"[DOWNLOAD] Pasta de arquivos: {DOWNLOAD_DIR}\n")

    def criar_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Notebook principal com abas separadas.
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # ===== Barra de status inferior, animada e informativa =====
        self.rowconfigure(1, weight=0)
        statusbar = ttk.Frame(self, style="StatusBar.TFrame", padding=(12, 5))
        statusbar.grid(row=1, column=0, sticky="ew")
        statusbar.columnconfigure(2, weight=1)

        ttk.Label(statusbar, textvariable=self.spinner_var, style="StatusBarAccent.TLabel").grid(row=0, column=0, padx=(0, 10))
        ttk.Label(statusbar, text="Manus API Pro FULL", style="StatusBarOk.TLabel").grid(row=0, column=1, padx=(0, 16))
        ttk.Label(statusbar, textvariable=self.statusbar_var, style="StatusBar.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Label(statusbar, textvariable=self.credit_status_var, style="StatusBar.TLabel").grid(row=0, column=3, padx=12)
        ttk.Label(statusbar, textvariable=self.keyring_status_var, style="StatusBar.TLabel").grid(row=0, column=4, padx=12)
        ttk.Label(statusbar, textvariable=self.server_status_var, style="StatusBar.TLabel").grid(row=0, column=5, padx=12)
        ttk.Label(statusbar, textvariable=self.clock_var, style="StatusBarAccent.TLabel").grid(row=0, column=6, padx=(12, 0))

        self.main_tab = ttk.Frame(self.notebook, padding=0)
        self.config_tab = ttk.Frame(self.notebook, padding=10)
        self.exec_tab = ttk.Frame(self.notebook, padding=10)
        self.pro_tab = ttk.Frame(self.notebook, padding=10)
        self.other_ai_tab = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.main_tab, text="Principal")
        self.notebook.add(self.config_tab, text="Configuração / IDs")
        self.notebook.add(self.exec_tab, text="Modo de execução")
        self.notebook.add(self.pro_tab, text="Painel Pro")
        self.notebook.add(self.other_ai_tab, text="Outras IAs / APIs")

        # Nova aba isolada com a Central Avançada (Turbo / IA / Injeção).
        self.turbo_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.turbo_tab, text="Turbo / IA / Injeção")
        self.construir_aba_turbo()

        # Estúdio completo das outras IAs (prompt, anexos, histórico, downloads...)
        self.estudio_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.estudio_tab, text="Estúdio Outras IAs")
        self.construir_aba_estudio_ia()

        # Central da API Manus: acesso a TODOS os endpoints (leitura e escrita).
        self.api_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.api_tab, text="Central da API Manus")
        self.construir_aba_api_manus()

        # ============================================================
        # ABA CONFIGURAÇÃO / IDS
        # ============================================================
        self.config_tab.columnconfigure(0, weight=1)

        api_box = ttk.LabelFrame(self.config_tab, text="APIKEY / Chave da Manus", padding=12)
        api_box.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        api_box.columnconfigure(1, weight=1)

        ttk.Label(api_box, text="APIKEY:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.key_entry = ttk.Entry(api_box, textvariable=self.api_key_var, show="*", width=90)
        self.key_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ttk.Checkbutton(
            api_box,
            text="Mostrar",
            variable=self.show_key_var,
            command=self.toggle_key_visibility,
        ).grid(row=0, column=2, padx=(0, 8))

        self.save_key_button = ttk.Button(api_box, text="Salvar chave", command=self.salvar_chave)
        self.save_key_button.grid(row=0, column=3, padx=(0, 6))

        ttk.Button(api_box, text="Apagar chave", command=self.apagar_chave).grid(row=0, column=4)

        keyring_box = ttk.LabelFrame(api_box, text="Múltiplas APIKEYs / Failover automático / Persistência local", padding=10)
        keyring_box.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(10, 0))
        keyring_box.columnconfigure(0, weight=1)

        self.keys_listbox = tk.Listbox(keyring_box, height=5)
        self.keys_listbox.grid(row=0, column=0, columnspan=7, sticky="ew")

        keys_scroll = ttk.Scrollbar(keyring_box, orient="vertical", command=self.keys_listbox.yview)
        keys_scroll.grid(row=0, column=7, sticky="ns")
        self.keys_listbox.configure(yscrollcommand=keys_scroll.set)

        ttk.Label(keyring_box, textvariable=self.keyring_status_var).grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))
        ttk.Label(keyring_box, textvariable=self.failover_status_var).grid(row=2, column=0, columnspan=7, sticky="w", pady=(4, 0))

        ttk.Button(keyring_box, text="Adicionar chave do campo", command=self.adicionar_chave_do_campo).grid(row=3, column=0, sticky="ew", padx=(0, 4), pady=(8, 0))
        ttk.Button(keyring_box, text="Usar selecionada", command=self.usar_chave_selecionada).grid(row=3, column=1, sticky="ew", padx=4, pady=(8, 0))
        ttk.Button(keyring_box, text="Remover selecionada", command=self.remover_chave_selecionada).grid(row=3, column=2, sticky="ew", padx=4, pady=(8, 0))
        ttk.Button(keyring_box, text="Salvar lista", command=self.salvar_chaves_multiplas).grid(row=3, column=3, sticky="ew", padx=4, pady=(8, 0))
        ttk.Button(keyring_box, text="Próxima chave", command=self.usar_proxima_chave_manual).grid(row=3, column=4, sticky="ew", padx=4, pady=(8, 0))
        ttk.Button(keyring_box, text="Testar chave atual", command=self.testar_conexao).grid(row=3, column=5, sticky="ew", padx=4, pady=(8, 0))
        ttk.Button(keyring_box, text="Apagar lista", command=self.apagar_lista_chaves).grid(row=3, column=6, sticky="ew", padx=(4, 0), pady=(8, 0))

        credito_box = ttk.LabelFrame(api_box, text="Créditos disponíveis da chave atual", padding=10)
        credito_box.grid(row=2, column=0, columnspan=5, sticky="ew", pady=(10, 0))
        credito_box.columnconfigure(0, weight=1)

        ttk.Label(credito_box, textvariable=self.credit_status_var).grid(row=0, column=0, sticky="w")
        ttk.Label(credito_box, textvariable=self.credit_key_var).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(credito_box, textvariable=self.credit_last_update_var).grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Button(credito_box, text="Consultar créditos agora", command=self.consultar_creditos).grid(row=0, column=1, sticky="e", padx=(8, 0))
        ttk.Button(credito_box, text="Créditos de todas as chaves", command=self.consultar_creditos_todas_chaves).grid(row=1, column=1, sticky="e", padx=(8, 0), pady=(4, 0))

        tarefa_cfg = ttk.LabelFrame(self.config_tab, text="Título automático e modelo da tarefa", padding=12)
        tarefa_cfg.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        tarefa_cfg.columnconfigure(1, weight=1)

        ttk.Label(tarefa_cfg, text="TÍTULO AUTOMÁTICO:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(tarefa_cfg, textvariable=self.title_var).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(tarefa_cfg, text="Gerar agora", command=self.gerar_titulo_agora).grid(row=0, column=2, padx=(0, 12))

        ttk.Label(tarefa_cfg, text="Modelo:").grid(row=0, column=3, sticky="w", padx=(0, 8))
        ttk.Combobox(
            tarefa_cfg,
            textvariable=self.agent_var,
            values=["manus-1.6-lite", "manus-1.6", "manus-1.6-max"],
            state="readonly",
            width=18,
        ).grid(row=0, column=4, sticky="w")

        task_box = ttk.LabelFrame(self.config_tab, text="Task ID e URL da tarefa atual", padding=12)
        task_box.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        task_box.columnconfigure(1, weight=1)

        ttk.Label(task_box, text="TASK ID:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(task_box, textvariable=self.task_id_var).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(task_box, text="Copiar ID", command=self.copiar_task_id).grid(row=0, column=2, padx=(0, 6))

        ttk.Label(task_box, text="URL:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        ttk.Entry(task_box, textvariable=self.task_url_var).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(8, 0))
        ttk.Button(task_box, text="Copiar URL", command=self.copiar_task_url).grid(row=1, column=2, padx=(0, 6), pady=(8, 0))

        ttk.Button(task_box, text="Abrir tarefa no navegador", command=self.abrir_tarefa).grid(
            row=2, column=1, sticky="w", pady=(10, 0)
        )

        atalhos_box = ttk.LabelFrame(self.config_tab, text="Pastas e manutenção", padding=12)
        atalhos_box.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(atalhos_box, text="Abrir pasta de downloads", command=self.abrir_pasta_downloads).pack(side="left", padx=(0, 8))
        ttk.Button(atalhos_box, text="Abrir pasta de logs", command=self.abrir_pasta_logs).pack(side="left", padx=8)
        ttk.Button(atalhos_box, text="Limpar dados locais", command=self.limpar_dados_locais).pack(side="left", padx=8)
        ttk.Button(atalhos_box, text="Ir para modo de execução", command=lambda: self.notebook.select(self.exec_tab)).pack(side="left", padx=8)

        ttk.Label(
            self.config_tab,
            text="Nesta aba ficam APIKEY, Mostrar, Salvar chave, Apagar chave, Título automático, Task ID e URL.",
        ).grid(row=4, column=0, sticky="w", pady=(8, 0))

        # ============================================================
        # ABA MODO DE EXECUÇÃO
        # ============================================================
        self.exec_tab.columnconfigure(0, weight=1)

        exec_box = ttk.LabelFrame(self.exec_tab, text="Modo de execução", padding=14)
        exec_box.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        exec_box.columnconfigure(1, weight=1)

        ttk.Checkbutton(
            exec_box,
            text="Modo Privacidade Local",
            variable=self.privacy_var,
            command=self.aplicar_privacidade,
        ).grid(row=0, column=0, sticky="w", padx=(0, 20), pady=4)

        ttk.Label(
            exec_box,
            text="Não salva dados sensíveis na tela/local quando usado com limpeza local.",
        ).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Checkbutton(
            exec_box,
            text="Salvar logs TXT/JSONL",
            variable=self.auto_log_var,
            command=self.aplicar_logs,
        ).grid(row=1, column=0, sticky="w", padx=(0, 20), pady=4)

        ttk.Label(
            exec_box,
            text="Salva logs para automação na pasta manus_logs.",
        ).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Checkbutton(
            exec_box,
            text="Acompanhar até terminar",
            variable=self.auto_follow_var,
        ).grid(row=2, column=0, sticky="w", padx=(0, 20), pady=4)

        ttk.Label(
            exec_box,
            text="O app fica acompanhando até stopped, error, waiting ou botão Parar.",
        ).grid(row=2, column=1, sticky="w", pady=4)

        ttk.Checkbutton(
            exec_box,
            text="Baixar anexos automaticamente",
            variable=self.auto_download_var,
        ).grid(row=3, column=0, sticky="w", padx=(0, 20), pady=4)

        ttk.Label(
            exec_box,
            text="Baixa anexos e links de arquivos para a pasta manus_downloads.",
        ).grid(row=3, column=1, sticky="w", pady=4)

        polling_box = ttk.LabelFrame(self.exec_tab, text="Polling / acompanhamento", padding=14)
        polling_box.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        polling_box.columnconfigure(1, weight=1)

        ttk.Label(polling_box, text="Polling em segundos:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(polling_box, textvariable=self.poll_interval_var, width=10).grid(row=0, column=1, sticky="w")
        ttk.Label(
            polling_box,
            text="Recomendado: 2 a 5 segundos. Valor menor consulta mais vezes a API.",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        exec_actions = ttk.LabelFrame(self.exec_tab, text="Ações rápidas", padding=14)
        exec_actions.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(exec_actions, text="Abrir pasta de downloads", command=self.abrir_pasta_downloads).pack(side="left", padx=(0, 8))
        ttk.Button(exec_actions, text="Abrir pasta de logs", command=self.abrir_pasta_logs).pack(side="left", padx=8)
        ttk.Button(exec_actions, text="Limpar dados locais", command=self.limpar_dados_locais).pack(side="left", padx=8)
        ttk.Button(exec_actions, text="Salvar preferências", command=self.salvar_preferencias_locais).pack(side="left", padx=8)
        ttk.Button(exec_actions, text="Painel Pro", command=lambda: self.notebook.select(self.pro_tab)).pack(side="left", padx=8)
        ttk.Button(exec_actions, text="Voltar para Principal", command=lambda: self.notebook.select(self.main_tab)).pack(side="left", padx=8)

        ttk.Label(
            self.exec_tab,
            text="Esta aba concentra todas as opções de execução. A tela principal fica limpa para prompt, anexos e respostas.",
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))

        # ============================================================
        # ABA PAINEL PRO
        # ============================================================
        self.pro_tab.columnconfigure(0, weight=1)

        pro_header = ttk.LabelFrame(self.pro_tab, text="Painel Pro / Integridade / Produtividade", padding=14)
        pro_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        pro_header.columnconfigure(0, weight=1)

        ttk.Label(pro_header, textvariable=self.integrity_status_var).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(pro_header, textvariable=self.security_status_var).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(pro_header, textvariable=self.session_status_var).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(pro_header, textvariable=self.credit_status_var).grid(row=3, column=0, sticky="w", pady=2)
        ttk.Label(pro_header, textvariable=self.credit_detail_var).grid(row=4, column=0, sticky="w", pady=2)
        ttk.Label(pro_header, textvariable=self.task_checkpoint_status_var).grid(row=5, column=0, sticky="w", pady=2)
        ttk.Label(pro_header, textvariable=self.quick_hint_var).grid(row=6, column=0, sticky="w", pady=(8, 2))

        pro_options = ttk.LabelFrame(self.pro_tab, text="Recursos profissionais", padding=14)
        pro_options.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        pro_options.columnconfigure(1, weight=1)

        ttk.Checkbutton(
            pro_options,
            text="Modo profissional ativo",
            variable=self.professional_mode_var,
            command=self.salvar_preferencias_locais,
        ).grid(row=0, column=0, sticky="w", padx=(0, 16), pady=4)

        ttk.Checkbutton(
            pro_options,
            text="Auto-salvar rascunho do prompt",
            variable=self.autosave_prompt_var,
            command=self.salvar_preferencias_locais,
        ).grid(row=1, column=0, sticky="w", padx=(0, 16), pady=4)

        ttk.Label(pro_options, text="Atalhos: Ctrl+Enter iniciar, Ctrl+O anexar, F5 testar, F6 concluídas, F7 continuar, F8 exportar, Esc parar.").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        pro_actions = ttk.LabelFrame(self.pro_tab, text="Ações avançadas", padding=14)
        pro_actions.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(pro_actions, text="Verificar integridade", command=self.verificar_integridade_local).pack(side="left", padx=(0, 8))
        ttk.Button(pro_actions, text="Consultar créditos", command=self.consultar_creditos).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Outras IAs / APIs", command=lambda: self.notebook.select(self.other_ai_tab)).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Diagnóstico local", command=self.diagnostico_visual).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Salvar preferências", command=self.salvar_preferencias_locais).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Salvar rascunho", command=self.salvar_rascunho_prompt).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Exportar sessão", command=self.exportar_sessao_atual).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Modo foco", command=self.alternar_modo_foco).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Salvar checkpoint", command=self.salvar_checkpoint_manual).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Carregar checkpoint", command=self.carregar_ultimo_checkpoint).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Pasta checkpoints", command=self.abrir_pasta_checkpoints).pack(side="left", padx=8)
        ttk.Button(pro_actions, text="Continuar checkpoint c/ chave atual", command=self.continuar_checkpoint_com_chave_atual).pack(side="left", padx=8)

        pro_info = ttk.LabelFrame(self.pro_tab, text="Garantia de integridade funcional", padding=14)
        pro_info.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(
            pro_info,
            text=(
                "Esta versão mantém as funções anteriores: iniciar tarefa, anexar arquivos, porcentagem fiel de upload, "
                "status online/offline, tratamento HTTP 429, tarefas concluídas, continuar mesma tarefa, downloads automáticos, "
                "logs TXT/JSONL, rolagem inteligente, abas, abertura de tarefa no app e múltiplas APIKEYs com failover técnico e retomada de tarefas não terminadas e barra de rolagem horizontal e integração com outras IAs/APIs e persistência local das chaves cadastradas, checkpoint completo da tarefa e escolha manual de outra chave quando houver limite/crédito."
            ),
            wraplength=1100,
        ).pack(anchor="w")

        # ============================================================
        # ABA OUTRAS IAS / APIS
        # ============================================================
        self.other_ai_tab.columnconfigure(0, weight=1)
        self.other_ai_tab.rowconfigure(1, weight=1)

        outras_header = ttk.LabelFrame(self.other_ai_tab, text="Cadastro de outras IAs / APIs com persistência local", padding=12)
        outras_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        outras_header.columnconfigure(1, weight=1)
        outras_header.columnconfigure(3, weight=1)

        ttk.Label(outras_header, text="Nome:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.other_ai_name_combo = ttk.Combobox(
            outras_header,
            textvariable=self.other_ai_name_var,
            values=OUTRAS_IA_NOMES,
            state="normal",
        )
        self.other_ai_name_combo.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=4)
        self.other_ai_name_combo.bind("<<ComboboxSelected>>", self._ao_escolher_provedor_nome)

        ttk.Label(outras_header, text="Tipo:").grid(row=0, column=2, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            outras_header,
            textvariable=self.other_ai_type_var,
            values=OUTRAS_IA_TIPOS,
            state="readonly",
            width=22,
        ).grid(row=0, column=3, sticky="w", pady=4)

        ttk.Label(outras_header, text="Base URL:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            outras_header,
            textvariable=self.other_ai_base_url_var,
            values=OUTRAS_IA_BASE_URLS,
            state="normal",
        ).grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=4)

        ttk.Label(outras_header, text="Endpoint:").grid(row=1, column=2, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            outras_header,
            textvariable=self.other_ai_endpoint_var,
            values=OUTRAS_IA_ENDPOINTS,
            state="normal",
        ).grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(outras_header, text="Modelo:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        self.other_ai_model_combo = ttk.Combobox(
            outras_header,
            textvariable=self.other_ai_model_var,
            values=OUTRAS_IA_MODELOS,
            state="normal",
        )
        self.other_ai_model_combo.grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=4)

        ttk.Label(outras_header, text="Auth:").grid(row=2, column=2, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            outras_header,
            textvariable=self.other_ai_auth_var,
            values=OUTRAS_IA_AUTH,
            state="readonly",
            width=18,
        ).grid(row=2, column=3, sticky="w", pady=4)

        ttk.Label(outras_header, text="APIKEY:").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        self.other_ai_key_entry = ttk.Entry(outras_header, textvariable=self.other_ai_key_var, show="*")
        self.other_ai_key_entry.grid(row=3, column=1, sticky="ew", padx=(0, 12), pady=4)
        # Ao colocar/colar a APIKEY, o sistema identifica o provedor e preenche tudo.
        try:
            self.other_ai_key_entry.bind("<KeyRelease>", lambda e: self.autodetectar_provedor_chave(silencioso=True, online=False))
            self.other_ai_key_entry.bind("<FocusOut>", lambda e: self.autodetectar_provedor_chave(silencioso=True, online=True))
            self.other_ai_key_entry.bind("<Return>", lambda e: self.autodetectar_provedor_chave(silencioso=False, online=True))
        except Exception:
            pass

        ttk.Label(outras_header, text="Temp.:").grid(row=3, column=2, sticky="w", padx=(0, 8), pady=4)
        temp_frame = ttk.Frame(outras_header)
        temp_frame.grid(row=3, column=3, sticky="w", pady=4)
        ttk.Combobox(temp_frame, textvariable=self.other_ai_temp_var, values=OUTRAS_IA_TEMPS, state="normal", width=6).pack(side="left", padx=(0, 8))
        ttk.Label(temp_frame, text="Max tokens:").pack(side="left", padx=(0, 6))
        ttk.Combobox(temp_frame, textvariable=self.other_ai_max_tokens_var, values=OUTRAS_IA_MAXTOKENS, state="normal", width=10).pack(side="left")

        botoes_outras = ttk.Frame(outras_header)
        botoes_outras.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        ttk.Button(botoes_outras, text="Adicionar/Salvar provedor", command=self.salvar_provedor_outra_ia_atual).pack(side="left", padx=(0, 8))
        ttk.Button(botoes_outras, text="Detectar pela APIKEY", command=lambda: self.autodetectar_provedor_chave(silencioso=False, online=True)).pack(side="left", padx=8)
        ttk.Button(botoes_outras, text="Usar selecionado", command=self.usar_provedor_outra_ia_selecionado).pack(side="left", padx=8)
        ttk.Button(botoes_outras, text="Remover selecionado", command=self.remover_provedor_outra_ia).pack(side="left", padx=8)
        ttk.Button(botoes_outras, text="Testar outra IA", command=self.testar_outra_ia).pack(side="left", padx=8)
        ttk.Button(botoes_outras, text="Enviar prompt atual para outra IA", command=self.enviar_prompt_para_outra_ia).pack(side="left", padx=8)
        ttk.Button(botoes_outras, text="Mostrar/Ocultar chave", command=self.toggle_other_ai_key).pack(side="left", padx=8)

        ttk.Label(outras_header, textvariable=self.other_ai_status_var).grid(row=5, column=0, columnspan=4, sticky="w", pady=(10, 0))

        outras_body = ttk.PanedWindow(self.other_ai_tab, orient="horizontal")
        outras_body.grid(row=1, column=0, sticky="nsew")

        prov_box = ttk.LabelFrame(outras_body, text="Provedores cadastrados", padding=10)
        prov_box.columnconfigure(0, weight=1)
        prov_box.rowconfigure(0, weight=1)

        self.other_ai_listbox = tk.Listbox(prov_box, height=14)
        self.other_ai_listbox.grid(row=0, column=0, sticky="nsew")
        other_scroll = ttk.Scrollbar(prov_box, orient="vertical", command=self.other_ai_listbox.yview)
        other_scroll.grid(row=0, column=1, sticky="ns")
        self.other_ai_listbox.configure(yscrollcommand=other_scroll.set)

        resposta_box = ttk.LabelFrame(outras_body, text="Resposta da outra IA / API", padding=10)
        resposta_box.columnconfigure(0, weight=1)
        resposta_box.rowconfigure(0, weight=1)

        self.other_ai_response_text = ScrolledText(resposta_box, height=16, wrap="word")
        self.other_ai_response_text.grid(row=0, column=0, sticky="nsew")

        outras_body.add(prov_box, weight=1)
        outras_body.add(resposta_box, weight=3)

        info_outras = ttk.LabelFrame(self.other_ai_tab, text="Observação importante", padding=10)
        info_outras.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Label(
            info_outras,
            text=(
                "Esta aba é independente da Manus. Ela envia o prompt atual para outra API de IA no padrão OpenAI-compatible. "
                "Use somente chaves suas e endpoints oficiais/permitidos. Arquivos anexados na Manus não são enviados automaticamente "
                "para outras IAs; envie no prompt apenas o que você quiser compartilhar."
            ),
            wraplength=1200,
        ).pack(anchor="w")

        ttk.Label(
            info_outras,
            text=(
                "Kiro: o Kiro NÃO tem API OpenAI-compatível nativa. Para usar a chave do Kiro aqui, rode um gateway local "
                "(ex.: kiro-openai-gateway) que sobe em http://localhost:8000/v1. No campo APIKEY use a senha do proxy "
                "(PROXY_API_KEY) definida no gateway. Selecione 'Kiro (gateway local)' no Nome para preencher tudo."
            ),
            wraplength=1200,
            style="Warn.TLabel",
        ).pack(anchor="w", pady=(6, 0))
        self.main_tab.columnconfigure(0, weight=1)
        self.main_tab.columnconfigure(1, weight=0)
        self.main_tab.rowconfigure(0, weight=1)
        self.main_tab.rowconfigure(1, weight=0)

        self.main_canvas = tk.Canvas(self.main_tab, highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(self.main_tab, orient="vertical", command=self.main_canvas.yview)
        self.main_hscrollbar = ttk.Scrollbar(self.main_tab, orient="horizontal", command=self.main_canvas.xview)
        self.main_canvas.configure(
            yscrollcommand=self.main_scrollbar.set,
            xscrollcommand=self.main_hscrollbar.set,
        )

        self.main_canvas.grid(row=0, column=0, sticky="nsew")
        self.main_scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_hscrollbar.grid(row=1, column=0, sticky="ew")

        self.main_content = ttk.Frame(self.main_canvas, padding=0)
        self.main_window_id = self.main_canvas.create_window((0, 0), window=self.main_content, anchor="nw")

        def _atualizar_scrollregion(event=None):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

        def _ajustar_largura(event):
            # Mantém a área interna pelo menos do tamanho da tela,
            # mas permite que ela seja maior para a barra horizontal funcionar.
            try:
                largura_requerida = self.main_content.winfo_reqwidth()
                largura_final = max(event.width, largura_requerida)
                self.main_canvas.itemconfigure(self.main_window_id, width=largura_final)
                self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
            except Exception:
                self.main_canvas.itemconfigure(self.main_window_id, width=event.width)

        self.main_content.bind("<Configure>", _atualizar_scrollregion)
        self.main_canvas.bind("<Configure>", _ajustar_largura)

        def _mousewheel(event):
            """
            Rolagem inteligente:
            - Se o mouse estiver sobre um subcomponente com rolagem própria,
              como Prompt, lista de arquivos, resposta em tempo real, downloads ou logs,
              deixa esse componente cuidar da rolagem.
            - Se estiver fora dessas áreas, rola o formulário principal na vertical.
            """
            try:
                if self.widget_tem_rolagem_interna(event.widget):
                    return None

                self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
            except Exception:
                return None

        def _shift_mousewheel(event):
            """
            Shift + roda do mouse rola o formulário principal na horizontal.
            """
            try:
                if self.widget_tem_rolagem_interna(event.widget):
                    return None

                self.main_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
            except Exception:
                return None

        self.main_canvas.bind_all("<MouseWheel>", _mousewheel)
        self.main_canvas.bind_all("<Shift-MouseWheel>", _shift_mousewheel)

        self.main_content.columnconfigure(0, weight=1)
        self.main_content.rowconfigure(1, weight=2, minsize=300)
        self.main_content.rowconfigure(7, weight=2, minsize=320)

        top_main = ttk.LabelFrame(self.main_content, text="Central de comando", padding=10)
        top_main.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        top_main.columnconfigure(0, weight=1)

        iniciar_btn = ttk.Button(top_main, text="INICIAR TAREFA", command=self.criar_tarefa, style="Accent.TButton")
        iniciar_btn.pack(side="left", padx=(0, 8))
        self.criar_tooltip(iniciar_btn, "Cria a tarefa, envia arquivos anexados, acompanha até terminar e baixa anexos.")
        ttk.Button(top_main, text="Anexar arquivos", command=self.adicionar_arquivos).pack(side="left", padx=8)
        ttk.Button(top_main, text="Configuração / IDs", command=lambda: self.notebook.select(self.config_tab)).pack(side="left", padx=8)
        ttk.Button(top_main, text="Modo de execução", command=lambda: self.notebook.select(self.exec_tab)).pack(side="left", padx=8)
        ttk.Button(top_main, text="Painel Pro", command=lambda: self.notebook.select(self.pro_tab)).pack(side="left", padx=8)
        ttk.Button(top_main, text="Outras IAs", command=lambda: self.notebook.select(self.other_ai_tab)).pack(side="left", padx=8)
        ttk.Button(top_main, text="Tarefas não terminadas", command=self.abrir_tarefas_nao_terminadas).pack(side="left", padx=8)
        ttk.Button(top_main, text="Ver créditos", command=self.consultar_creditos).pack(side="left", padx=8)
        ttk.Button(top_main, text="Checkpoint", command=self.carregar_ultimo_checkpoint).pack(side="left", padx=8)
        ttk.Button(top_main, text="Downloads", command=self.abrir_pasta_downloads).pack(side="left", padx=8)
        ttk.Button(top_main, text="Logs", command=self.abrir_pasta_logs).pack(side="left", padx=8)

        ttk.Label(
            top_main,
            text="Botão INICIAR TAREFA cria a tarefa, envia anexos e acompanha até terminar.",
        ).pack(side="left", padx=16)

        status_box = ttk.LabelFrame(self.main_content, text="Status do servidor e da tarefa", padding=10)
        status_box.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        status_box.columnconfigure(1, weight=1)
        status_box.columnconfigure(3, weight=1)

        ttk.Label(status_box, textvariable=self.server_status_var).grid(row=0, column=0, sticky="w", padx=(0, 18))
        ttk.Label(status_box, textvariable=self.server_last_seen_var).grid(row=0, column=1, sticky="w", padx=(0, 18))

        ttk.Label(status_box, textvariable=self.task_status_var).grid(row=0, column=2, sticky="w", padx=(0, 18))
        ttk.Label(status_box, textvariable=self.task_phase_var).grid(row=0, column=3, sticky="w")

        ttk.Label(status_box, textvariable=self.task_clue_var).grid(row=1, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ttk.Label(status_box, textvariable=self.task_activity_var).grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))
        ttk.Label(status_box, textvariable=self.integrity_status_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(status_box, textvariable=self.session_status_var).grid(row=3, column=2, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(status_box, textvariable=self.credit_status_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(status_box, textvariable=self.credit_last_update_var).grid(row=4, column=2, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(status_box, textvariable=self.task_checkpoint_status_var).grid(row=5, column=0, columnspan=4, sticky="w", pady=(4, 0))

        meio = ttk.PanedWindow(self.main_content, orient="horizontal", height=320)
        meio.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))

        prompt_box = ttk.LabelFrame(meio, text="Prompt para o Manus", padding=10)
        prompt_box.columnconfigure(0, weight=1)
        prompt_box.rowconfigure(0, weight=1)

        self.prompt_text = ScrolledText(prompt_box, height=13, wrap="word")
        self.prompt_text.grid(row=0, column=0, sticky="nsew")
        self.prompt_text.insert(
            "1.0",
            "Use os arquivos anexados se houver. Execute a tarefa até terminar. Se eu pedir um arquivo, gere e anexe o resultado para download."
        )
        try:
            self.prompt_text.bind("<FocusOut>", lambda e: self.salvar_rascunho_prompt() if self.autosave_prompt_var.get() else None, add="+")
        except Exception:
            pass

        arquivos_box = ttk.LabelFrame(meio, text="ANEXAR ARQUIVOS AO MANUS - qualquer extensão (*.*)", padding=10)
        arquivos_box.columnconfigure(0, weight=1)
        arquivos_box.rowconfigure(0, weight=1)

        self.files_list = tk.Listbox(arquivos_box, height=13)
        self.files_list.grid(row=0, column=0, columnspan=4, sticky="nsew")

        scroll_files = ttk.Scrollbar(arquivos_box, orient="vertical", command=self.files_list.yview)
        scroll_files.grid(row=0, column=4, sticky="ns")
        self.files_list.configure(yscrollcommand=scroll_files.set)

        ttk.Button(arquivos_box, text="Adicionar arquivo(s)", command=self.adicionar_arquivos).grid(row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 4))
        ttk.Button(arquivos_box, text="Remover selecionado", command=self.remover_arquivo).grid(row=1, column=1, sticky="ew", pady=(8, 0), padx=4)
        ttk.Button(arquivos_box, text="Limpar lista", command=self.limpar_arquivos).grid(row=1, column=2, sticky="ew", pady=(8, 0), padx=4)
        ttk.Button(arquivos_box, text="Abrir pasta", command=self.abrir_pasta_arquivo).grid(row=1, column=3, sticky="ew", pady=(8, 0), padx=(4, 0))

        btn_colar_img = ttk.Button(arquivos_box, text="Colar imagem da área de transferência (Ctrl+V)", command=self.colar_imagem_arquivos)
        btn_colar_img.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        self.criar_tooltip(btn_colar_img, "Cola uma imagem copiada (Print Screen, navegador, etc.) e anexa como arquivo à tarefa.")

        self.files_info_label = ttk.Label(arquivos_box, text="Nenhum arquivo selecionado.")
        self.files_info_label.grid(row=3, column=0, columnspan=5, sticky="w", pady=(8, 0))

        # Permite colar imagem com Ctrl+V quando a lista de arquivos está focada.
        try:
            self.files_list.bind("<Control-v>", self.colar_imagem_arquivos)
            self.files_list.bind("<Control-V>", self.colar_imagem_arquivos)
        except Exception:
            pass

        meio.add(prompt_box, weight=3)
        meio.add(arquivos_box, weight=2)

        botoes = ttk.Frame(self.main_content, padding=(10, 0, 10, 8))
        botoes.grid(row=3, column=0, sticky="ew")

        ttk.Button(botoes, text="Testar conexão", command=self.testar_conexao).pack(side="left", padx=(0, 6))
        ttk.Button(botoes, text="Anexar arquivos", command=self.adicionar_arquivos).pack(side="left", padx=6)
        ttk.Button(botoes, text="Expandir prompt/anexos", command=self.expandir_prompt_arquivos).pack(side="left", padx=6)
        ttk.Button(botoes, text="INICIAR TAREFA", command=self.criar_tarefa).pack(side="left", padx=6)
        ttk.Button(botoes, text="Acompanhar Task ID", command=self.acompanhar_tarefa_atual).pack(side="left", padx=6)
        ttk.Button(botoes, text="Continuar tarefa atual", command=self.continuar_tarefa_atual).pack(side="left", padx=6)
        ttk.Button(botoes, text="Parar", command=self.parar_acompanhamento).pack(side="left", padx=6)
        ttk.Button(botoes, text="Abrir tarefa", command=self.abrir_tarefa).pack(side="left", padx=6)
        ttk.Button(botoes, text="Tarefas concluídas", command=self.abrir_tarefas_concluidas).pack(side="left", padx=6)
        ttk.Button(botoes, text="Tarefas não terminadas", command=self.abrir_tarefas_nao_terminadas).pack(side="left", padx=6)
        ttk.Button(botoes, text="Ver créditos", command=self.consultar_creditos).pack(side="left", padx=6)
        ttk.Button(botoes, text="Enviar para outra IA", command=self.enviar_prompt_para_outra_ia).pack(side="left", padx=6)
        ttk.Button(botoes, text="Salvar checkpoint", command=self.salvar_checkpoint_manual).pack(side="left", padx=6)
        ttk.Button(botoes, text="Carregar checkpoint", command=self.carregar_ultimo_checkpoint).pack(side="left", padx=6)
        ttk.Button(botoes, text="Continuar checkpoint c/ chave atual", command=self.continuar_checkpoint_com_chave_atual).pack(side="left", padx=6)
        ttk.Button(botoes, text="Salvar resposta", command=self.salvar_resposta_manual).pack(side="left", padx=6)
        ttk.Button(botoes, text="Exportar sessão", command=self.exportar_sessao_atual).pack(side="left", padx=6)
        ttk.Button(botoes, text="Modo foco", command=self.alternar_modo_foco).pack(side="left", padx=6)
        ttk.Button(botoes, text="Diagnóstico", command=self.diagnostico_visual).pack(side="left", padx=6)
        ttk.Button(botoes, text="Tema claro/escuro", command=self.alternar_tema).pack(side="left", padx=6)
        ttk.Button(botoes, text="Ajuda (F1)", command=self.mostrar_ajuda).pack(side="left", padx=6)
        ttk.Button(botoes, text="Limpar", command=self.limpar_log).pack(side="right", padx=(6, 0))

        upload_box = ttk.LabelFrame(self.main_content, text="Progresso fiel do upload", padding=10)
        upload_box.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 8))
        upload_box.columnconfigure(0, weight=1)

        ttk.Label(upload_box, textvariable=self.upload_status_var).grid(row=0, column=0, sticky="w")
        self.upload_progressbar = ttk.Progressbar(
            upload_box,
            variable=self.upload_percent_var,
            maximum=100,
            mode="determinate",
        )
        self.upload_progressbar.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Label(upload_box, textvariable=self.upload_detail_var).grid(row=2, column=0, sticky="w", pady=(4, 0))

        task_resumo = ttk.LabelFrame(self.main_content, text="Tarefa atual - resumo rápido", padding=8)
        task_resumo.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 8))
        task_resumo.columnconfigure(1, weight=1)
        task_resumo.columnconfigure(3, weight=0)
        task_resumo.columnconfigure(4, weight=0)

        ttk.Label(task_resumo, text="ID:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Label(task_resumo, textvariable=self.task_id_var).grid(row=0, column=1, sticky="w", padx=(0, 18))

        ttk.Label(task_resumo, text="Modelo:").grid(row=0, column=2, sticky="w", padx=(0, 6))
        ttk.Label(task_resumo, textvariable=self.agent_var).grid(row=0, column=3, sticky="w", padx=(0, 18))

        ttk.Button(
            task_resumo,
            text="Ver/editar ID, URL, título, modelo e APIKEY",
            command=lambda: self.notebook.select(self.config_tab)
        ).grid(row=0, column=4, sticky="e")

        wait_box = ttk.LabelFrame(self.main_content, text="Quando o Manus pedir informação ou confirmação", padding=10)
        wait_box.grid(row=6, column=0, sticky="ew", padx=10, pady=(0, 8))
        wait_box.columnconfigure(0, weight=1)
        wait_box.rowconfigure(0, weight=1)

        # Campo de resposta AMPLO (multilinha) para escrever respostas grandes ao Manus.
        self.reply_text = ScrolledText(wait_box, height=6, wrap="word")
        self.reply_text.grid(row=0, column=0, columnspan=3, sticky="nsew", pady=(0, 6))

        botoes_resp = ttk.Frame(wait_box)
        botoes_resp.grid(row=1, column=0, columnspan=3, sticky="ew")
        ttk.Button(botoes_resp, text="Enviar resposta ao Manus", command=self.enviar_resposta_manus).pack(side="left", padx=(0, 6))
        ttk.Button(botoes_resp, text="Confirmar ação pendente", command=self.confirmar_acao_pendente).pack(side="left", padx=6)
        ttk.Label(botoes_resp, text="(Ctrl+Enter envia  •  Ctrl+Shift+V cola imagem)", style="Status.TLabel").pack(side="left", padx=10)

        # Linha de anexos: permite responder ao Manus anexando arquivos junto com o texto.
        anexos_resposta = ttk.Frame(wait_box)
        anexos_resposta.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        anexos_resposta.columnconfigure(0, weight=1)

        self.reply_files_label = ttk.Label(anexos_resposta, text="Nenhum arquivo anexado à resposta.")
        self.reply_files_label.grid(row=0, column=0, sticky="w", padx=(0, 8))

        btn_anexar_resp = ttk.Button(anexos_resposta, text="Anexar arquivos à resposta", command=self.anexar_arquivos_resposta)
        btn_anexar_resp.grid(row=0, column=1, padx=4)

        btn_colar_resp = ttk.Button(anexos_resposta, text="Colar imagem", command=self.colar_imagem_resposta)
        btn_colar_resp.grid(row=0, column=2, padx=4)

        btn_limpar_resp = ttk.Button(anexos_resposta, text="Limpar anexos", command=self.limpar_anexos_resposta)
        btn_limpar_resp.grid(row=0, column=3, padx=4)

        self.criar_tooltip(btn_anexar_resp, "Selecione um ou mais arquivos para enviar ao Manus junto com a resposta.")
        self.criar_tooltip(btn_colar_resp, "Cola uma imagem da área de transferência e anexa à resposta enviada ao Manus.")
        self.criar_tooltip(btn_limpar_resp, "Remove todos os arquivos anexados à resposta.")

        # Atalhos do campo de resposta: Ctrl+Enter envia; Ctrl+Shift+V cola imagem.
        try:
            self.reply_text.bind("<Control-Return>", lambda e: (self.enviar_resposta_manus(), "break")[1])
            self.reply_text.bind("<Control-Shift-v>", self.colar_imagem_resposta)
            self.reply_text.bind("<Control-Shift-V>", self.colar_imagem_resposta)
        except Exception:
            pass

        baixo = ttk.PanedWindow(self.main_content, orient="horizontal", height=330)
        baixo.grid(row=7, column=0, sticky="nsew", padx=10, pady=(0, 10))

        realtime_box = ttk.LabelFrame(baixo, text="Resposta em tempo real", padding=10)
        realtime_box.columnconfigure(0, weight=1)
        realtime_box.rowconfigure(0, weight=1)

        self.realtime_text = ScrolledText(realtime_box, height=16, wrap="word")
        self.realtime_text.grid(row=0, column=0, sticky="nsew")

        direita = ttk.PanedWindow(baixo, orient="vertical")

        downloads_box = ttk.LabelFrame(direita, text="Arquivos baixados do Manus", padding=10)
        downloads_box.columnconfigure(0, weight=1)
        downloads_box.rowconfigure(0, weight=1)

        self.downloads_list = tk.Listbox(downloads_box, height=8)
        self.downloads_list.grid(row=0, column=0, sticky="nsew")

        dl_buttons = ttk.Frame(downloads_box)
        dl_buttons.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(dl_buttons, text="Abrir arquivo", command=self.abrir_arquivo_baixado).pack(side="left", padx=(0, 6))
        ttk.Button(dl_buttons, text="Abrir pasta do arquivo", command=self.abrir_pasta_arquivo_baixado).pack(side="left", padx=6)

        log_box = ttk.LabelFrame(direita, text="Logs técnicos", padding=10)
        log_box.columnconfigure(0, weight=1)
        log_box.rowconfigure(0, weight=1)

        self.log_text = ScrolledText(log_box, height=10, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        direita.add(downloads_box, weight=1)
        direita.add(log_box, weight=1)

        baixo.add(realtime_box, weight=3)
        baixo.add(direita, weight=2)

        rodape = ttk.Frame(self.main_content, padding=(10, 0, 10, 10))
        rodape.grid(row=8, column=0, sticky="ew")
        ttk.Label(
            rodape,
            text="Use INICIAR TAREFA para criar, enviar arquivos, acompanhar até terminar e baixar anexos.",
        ).pack(side="left")



    def aplicar_tema_profissional(self):
        """Aplica tema visual moderno usando apenas ttk/Tkinter nativo."""
        try:
            style = ttk.Style(self)
            try:
                style.theme_use("clam")
            except Exception:
                pass

            # ===== Paleta dinâmica: tema claro ou escuro (futurista) =====
            modo = getattr(self, "tema_atual", "claro")
            if modo == "escuro":
                bg = "#0B1220"
                panel = "#111827"
                dark = "#E5E7EB"
                soft = "#1F2937"
                accent = "#38BDF8"
                btn_hover = "#1E3A8A"
                btn_press = "#1E40AF"
                tab_active = "#1E293B"
                accent_active = "#0EA5E9"
                accent_press = "#0284C7"
                status_bg = "#020617"
                self._tema_text_bg = "#0F172A"
                self._tema_text_fg = "#E5E7EB"
                self._tema_sel = "#1D4ED8"
            else:
                bg = "#F3F4F6"
                panel = "#FFFFFF"
                dark = "#111827"
                soft = "#E5E7EB"
                accent = "#2563EB"
                btn_hover = "#DBEAFE"
                btn_press = "#BFDBFE"
                tab_active = "#EEF2FF"
                accent_active = "#1D4ED8"
                accent_press = "#1E40AF"
                status_bg = "#0F172A"
                self._tema_text_bg = "#FFFFFF"
                self._tema_text_fg = "#111827"
                self._tema_sel = "#2563EB"

            self.configure(bg=bg)

            style.configure(".", font=("Segoe UI", 9))
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=dark)
            style.configure("TLabelframe", background=bg, foreground=dark)
            style.configure("TLabelframe.Label", background=bg, foreground=dark, font=("Segoe UI", 9, "bold"))
            style.configure("TNotebook", background=bg, borderwidth=0)
            style.configure("TNotebook.Tab", padding=(14, 8), font=("Segoe UI", 9, "bold"))
            style.configure("TButton", padding=(9, 5), font=("Segoe UI", 9), background=soft, foreground=dark)
            style.configure("TCheckbutton", background=bg, foreground=dark)
            style.configure("TRadiobutton", background=bg, foreground=dark)
            style.configure("TEntry", fieldbackground=panel, foreground=dark)
            style.configure("TCombobox", fieldbackground=panel, foreground=dark)
            style.configure("Accent.TButton", padding=(12, 7), font=("Segoe UI", 10, "bold"))
            style.configure("Status.TLabel", background=panel, foreground=dark, font=("Segoe UI", 9))
            style.configure("Success.TLabel", background=panel, foreground="#10B981" if modo == "escuro" else "#047857", font=("Segoe UI", 9, "bold"))
            style.configure("Warn.TLabel", background=panel, foreground="#F59E0B" if modo == "escuro" else "#B45309", font=("Segoe UI", 9, "bold"))
            style.configure("Danger.TLabel", background=panel, foreground="#F87171" if modo == "escuro" else "#B91C1C", font=("Segoe UI", 9, "bold"))
            style.configure("Horizontal.TProgressbar", thickness=14, background=accent)

            # ===== Polimento visual: efeitos de hover/pressionado e cores vivas =====
            try:
                style.map(
                    "TButton",
                    background=[("pressed", btn_press), ("active", btn_hover)],
                    foreground=[("disabled", "#9CA3AF")],
                    relief=[("pressed", "sunken"), ("!pressed", "flat")],
                )
                style.configure("Accent.TButton", background=accent, foreground="#FFFFFF")
                style.map(
                    "Accent.TButton",
                    background=[("pressed", accent_press), ("active", accent_active)],
                    foreground=[("disabled", "#E5E7EB"), ("active", "#FFFFFF")],
                )

                # Abas mais modernas, com destaque na aba selecionada.
                style.configure("TNotebook.Tab", background=soft, foreground=dark)
                style.map(
                    "TNotebook.Tab",
                    background=[("selected", panel), ("active", tab_active)],
                    foreground=[("selected", accent)],
                )

                # Tabelas (Treeview) mais legíveis e com seleção destacada.
                style.configure("Treeview", rowheight=24, background=panel, fieldbackground=panel, foreground=dark)
                style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background=soft, foreground=dark)
                style.map(
                    "Treeview",
                    background=[("selected", accent)],
                    foreground=[("selected", "#FFFFFF")],
                )

                # Barra de status inferior (visual futurista escuro em ambos os temas).
                style.configure("StatusBar.TFrame", background=status_bg)
                style.configure("StatusBar.TLabel", background=status_bg, foreground="#CBD5E1", font=("Segoe UI", 9))
                style.configure("StatusBarAccent.TLabel", background=status_bg, foreground="#38BDF8", font=("Consolas", 10, "bold"))
                style.configure("StatusBarOk.TLabel", background=status_bg, foreground="#34D399", font=("Segoe UI", 9, "bold"))
            except Exception:
                pass

            self.option_add("*Font", "{Segoe UI} 9")
        except Exception:
            pass

    def criar_tooltip(self, widget, texto: str):
        try:
            ToolTip(widget, texto)
        except Exception:
            pass
        return widget

    def _recolorir_widgets_tk(self, widget=None):
        """
        Recolore os widgets nativos do Tkinter (Text, Listbox, Canvas) conforme
        o tema atual. Os widgets ttk são tratados pelo Style; estes não, então
        precisam ser percorridos manualmente. Totalmente protegido por try.
        """
        if widget is None:
            widget = self
        try:
            cls = widget.winfo_class()
        except Exception:
            cls = ""
        try:
            if cls in ("Text", "TText"):
                widget.configure(
                    background=self._tema_text_bg,
                    foreground=self._tema_text_fg,
                    insertbackground=self._tema_text_fg,
                    selectbackground=self._tema_sel,
                    selectforeground="#FFFFFF",
                )
            elif cls == "Listbox":
                widget.configure(
                    background=self._tema_text_bg,
                    foreground=self._tema_text_fg,
                    selectbackground=self._tema_sel,
                    selectforeground="#FFFFFF",
                )
            elif cls == "Canvas":
                widget.configure(background=self._tema_text_bg)
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._recolorir_widgets_tk(child)
        except Exception:
            pass

    def alternar_tema(self, event=None):
        """Alterna entre tema claro e escuro, aplicando e persistindo a escolha."""
        try:
            self.tema_atual = "claro" if getattr(self, "tema_atual", "claro") == "escuro" else "escuro"
            self.aplicar_tema_profissional()
            self._recolorir_widgets_tk()
            try:
                self.salvar_preferencias_locais()
            except Exception:
                pass
            self.definir_status(f"Tema alterado para: {self.tema_atual.upper()}.")
            try:
                self.log(f"[TEMA] Tema alterado para {self.tema_atual}.\n")
            except Exception:
                pass
        except Exception as e:
            try:
                self.log(f"[TEMA/ERRO] {e}\n")
            except Exception:
                pass
        return "break"

    def configurar_atalhos_profissionais(self):
        """Atalhos para uso rápido e comercial."""
        try:
            self.bind_all("<Control-Return>", lambda e: self.criar_tarefa())
            self.bind_all("<Control-o>", lambda e: self.adicionar_arquivos())
            self.bind_all("<Control-O>", lambda e: self.adicionar_arquivos())
            self.bind_all("<F5>", lambda e: self.testar_conexao())
            self.bind_all("<F6>", lambda e: self.abrir_tarefas_concluidas())
            self.bind_all("<F7>", lambda e: self.continuar_tarefa_atual())
            self.bind_all("<F8>", lambda e: self.exportar_sessao_atual())
            self.bind_all("<F9>", lambda e: self.consultar_creditos())
            self.bind_all("<F10>", lambda e: self.notebook.select(self.other_ai_tab))
            self.bind_all("<F11>", lambda e: self.carregar_ultimo_checkpoint())
            self.bind_all("<Control-s>", lambda e: self.salvar_rascunho_prompt())
            self.bind_all("<Control-S>", lambda e: self.salvar_rascunho_prompt())
            self.bind_all("<F1>", lambda e: self.mostrar_ajuda())
            self.bind_all("<Control-t>", self.alternar_tema)
            self.bind_all("<Control-T>", self.alternar_tema)
            self.bind_all("<Escape>", lambda e: self.parar_acompanhamento())
        except Exception:
            pass

    def carregar_preferencias_locais(self):
        """Carrega preferências locais sem mexer na API key."""
        prefs = ler_json_seguro(PREFERENCES_FILE, {})
        try:
            if "agent_profile" in prefs:
                self.agent_var.set(str(prefs.get("agent_profile") or self.agent_var.get()))
            if "poll_interval" in prefs:
                self.poll_interval_var.set(str(prefs.get("poll_interval") or self.poll_interval_var.get()))
            if "auto_log" in prefs:
                self.auto_log_var.set(bool(prefs.get("auto_log")))
            if "auto_follow" in prefs:
                self.auto_follow_var.set(bool(prefs.get("auto_follow")))
            if "auto_download" in prefs:
                self.auto_download_var.set(bool(prefs.get("auto_download")))
            if "professional_mode" in prefs:
                self.professional_mode_var.set(bool(prefs.get("professional_mode")))
            if "autosave_prompt" in prefs:
                self.autosave_prompt_var.set(bool(prefs.get("autosave_prompt")))
        except Exception:
            pass

    def salvar_preferencias_locais(self):
        """Salva preferências não sensíveis."""
        prefs = {
            "agent_profile": self.agent_var.get(),
            "poll_interval": self.poll_interval_var.get(),
            "auto_log": bool(self.auto_log_var.get()),
            "auto_follow": bool(self.auto_follow_var.get()),
            "auto_download": bool(self.auto_download_var.get()),
            "professional_mode": bool(self.professional_mode_var.get()),
            "autosave_prompt": bool(self.autosave_prompt_var.get()),
            "tema": getattr(self, "tema_atual", "claro"),
            "updated_at": agora_iso(),
        }
        ok = salvar_json_seguro(PREFERENCES_FILE, prefs)
        if ok:
            self.session_status_var.set(f"Sessão: preferências salvas em {agora_iso()}")
            try:
                self.log("[PREFERÊNCIAS] Preferências locais salvas.\n")
            except Exception:
                pass
        return ok

    def salvar_rascunho_prompt(self, event=None):
        """Salva o prompt atual localmente, sem enviar ao servidor."""
        try:
            texto = self.prompt_text.get("1.0", "end").strip()
            DRAFT_FILE.write_text(texto, encoding="utf-8")
            self.session_status_var.set(f"Sessão: rascunho salvo em {agora_iso()}")
            self.log("[RASCUNHO] Prompt salvo localmente.\n")
        except Exception as e:
            try:
                self.log(f"[RASCUNHO] Falha ao salvar: {e}\n")
            except Exception:
                pass

    def carregar_rascunho_prompt(self):
        """Restaura rascunho de prompt se existir e não estiver vazio."""
        try:
            if DRAFT_FILE.exists():
                texto = DRAFT_FILE.read_text(encoding="utf-8").strip()
                if texto and hasattr(self, "prompt_text"):
                    atual = self.prompt_text.get("1.0", "end").strip()
                    if atual:
                        self.prompt_text.delete("1.0", "end")
                    self.prompt_text.insert("1.0", texto)
                    self.session_status_var.set("Sessão: rascunho de prompt restaurado")
        except Exception:
            pass

    def verificar_integridade_local(self):
        """Diagnóstico leve do ambiente local e pastas necessárias."""
        try:
            LOG_DIR.mkdir(exist_ok=True)
            DOWNLOAD_DIR.mkdir(exist_ok=True)
            SESSION_EXPORT_DIR.mkdir(exist_ok=True)

            problemas = []
            if not self.chaves_disponiveis():
                problemas.append("APIKEY ausente")
            try:
                poll = int(str(self.poll_interval_var.get()).strip())
                if poll < 1:
                    problemas.append("polling menor que 1")
            except Exception:
                problemas.append("polling inválido")

            if problemas:
                self.integrity_status_var.set("Integridade: atenção - " + ", ".join(problemas))
            else:
                self.integrity_status_var.set("Integridade: OK")

            self.security_status_var.set(f"Segurança: APIKEY mascarada; {len(getattr(self, 'api_keys', []))} chave(s) no cofre local; logs opcionais")
        except Exception as e:
            self.integrity_status_var.set(f"Integridade: erro no diagnóstico - {e}")

    def exportar_sessao_atual(self, event=None):
        """Exporta um pacote de sessão em JSON + TXT para auditoria/backup local."""
        try:
            SESSION_EXPORT_DIR.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            base = SESSION_EXPORT_DIR / f"sessao_manus_{ts}"
            prompt = self.prompt_text.get("1.0", "end").strip() if hasattr(self, "prompt_text") else ""
            resposta = self.realtime_text.get("1.0", "end").strip() if hasattr(self, "realtime_text") else ""
            logs = self.log_text.get("1.0", "end").strip() if hasattr(self, "log_text") else ""

            data = {
                "exported_at": agora_iso(),
                "task_id": self.task_id_var.get(),
                "task_url": self.task_url_var.get(),
                "title": self.title_var.get(),
                "agent_profile": self.agent_var.get(),
                "server_status": self.server_status_var.get(),
                "task_status": self.task_status_var.get(),
                "task_phase": self.task_phase_var.get(),
                "task_clue": self.task_clue_var.get(),
                "task_activity": self.task_activity_var.get(),
                "credit_status": self.credit_status_var.get(),
                "credit_detail": self.credit_detail_var.get(),
                "other_ai_status": self.other_ai_status_var.get(),
                "other_ai_provider": self.other_ai_name_var.get(),
                "other_ai_model": self.other_ai_model_var.get(),
                "checkpoint_status": self.task_checkpoint_status_var.get(),
                "checkpoint_file": str(TASK_STATE_CURRENT_FILE),
                "prompt_preview": resumo_texto(prompt, 300),
                "downloads": [str(p) for p in getattr(self, "downloaded_files", [])],
                "selected_files": [str(p) for p in getattr(self, "selected_files", [])],
            }

            json_path = base.with_suffix(".json")
            txt_path = base.with_suffix(".txt")
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            txt_path.write_text(
                "=== SESSÃO MANUS EXPORTADA ===\n"
                f"Exportado em: {agora_iso()}\n"
                f"Task ID: {self.task_id_var.get()}\n"
                f"URL: {self.task_url_var.get()}\n"
                f"Título: {self.title_var.get()}\n"
                f"Modelo: {self.agent_var.get()}\n\n"
                "=== PROMPT ===\n"
                f"{prompt}\n\n"
                "=== RESPOSTA ===\n"
                f"{resposta}\n\n"
                "=== LOGS ===\n"
                f"{logs}\n",
                encoding="utf-8",
            )
            self.session_status_var.set(f"Sessão: exportada em {json_path.name}")
            self.msg("download", str(txt_path))
            self.log(f"[EXPORTAÇÃO] Sessão exportada: {json_path} / {txt_path}\n")
            self.enfileirar_backup(json_path)
            self.enfileirar_backup(txt_path)
            messagebox.showinfo("Exportação concluída", f"Sessão exportada em:\n{SESSION_EXPORT_DIR}")
        except Exception as e:
            messagebox.showerror("Erro ao exportar sessão", str(e))

    def alternar_modo_foco(self):
        """Modo foco: amplia área principal e prompt/anexos."""
        try:
            self.compact_mode_var.set(not self.compact_mode_var.get())
            if self.compact_mode_var.get():
                self.geometry("1400x1040")
                if hasattr(self, "main_content"):
                    self.main_content.rowconfigure(2, weight=5, minsize=460)
                    self.main_content.rowconfigure(7, weight=1, minsize=240)
                self.session_status_var.set("Sessão: modo foco ativado")
            else:
                try:
                    self.state("zoomed")
                except Exception:
                    self.geometry("1380x920")
                self.session_status_var.set("Sessão: modo foco desativado")
            self.log("[LAYOUT] Modo foco alternado.\n")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def fechar_app_salvando(self):
        """Salva chaves, provedores e preferências antes de fechar."""
        try:
            self.salvar_chaves_multiplas_silencioso()
        except Exception:
            pass
        try:
            self.salvar_outros_provedores_ia_silencioso()
        except Exception:
            pass
        try:
            self.salvar_preferencias_locais()
        except Exception:
            pass
        try:
            self.salvar_checkpoint_tarefa("fechamento do aplicativo")
        except Exception:
            pass
        try:
            if hasattr(self, "prompt_text") and self.autosave_prompt_var.get():
                self.salvar_rascunho_prompt()
        except Exception:
            pass
        self.destroy()

    def mostrar_ajuda(self):
        """Janela de Ajuda / Atalhos / Sobre, profissional e completa."""
        try:
            janela = tk.Toplevel(self)
            janela.title("Ajuda, Atalhos e Sobre - Manus API Pro FULL")
            janela.geometry("760x620")
            janela.minsize(640, 480)
            janela.transient(self)
            try:
                janela.grab_set()
            except Exception:
                pass
            janela.columnconfigure(0, weight=1)
            janela.rowconfigure(1, weight=1)

            cabecalho = ttk.Frame(janela, padding=(14, 12))
            cabecalho.grid(row=0, column=0, sticky="ew")
            ttk.Label(cabecalho, text="Manus API Pro FULL", style="Success.TLabel").pack(anchor="w")
            ttk.Label(
                cabecalho,
                text="Profissional, seguro, robusto, animado e comercial. Tudo em um único aplicativo.",
                style="Status.TLabel",
            ).pack(anchor="w")

            corpo = ScrolledText(janela, wrap="word", height=24)
            corpo.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))

            texto_ajuda = (
                "===== ATALHOS DE TECLADO =====\n"
                "Ctrl+Enter ....... Iniciar tarefa\n"
                "Ctrl+O ........... Anexar arquivo(s)\n"
                "Ctrl+V ........... Colar imagem (com a lista de arquivos em foco)\n"
                "Ctrl+Shift+V ..... Colar imagem como anexo da resposta\n"
                "Ctrl+S ........... Salvar rascunho do prompt\n"
                "F1 ............... Abrir esta ajuda\n"
                "F5 ............... Testar conexão\n"
                "F6 ............... Tarefas concluídas\n"
                "F7 ............... Continuar tarefa atual\n"
                "F8 ............... Exportar sessão\n"
                "F9 ............... Ver créditos\n"
                "F10 .............. Aba Outras IAs / APIs\n"
                "F11 .............. Carregar último checkpoint\n"
                "Esc .............. Parar acompanhamento\n\n"

                "===== RECURSOS PRINCIPAIS =====\n"
                "- Criar tarefas no Manus, anexar arquivos de qualquer extensão e acompanhar em tempo real.\n"
                "- Responder ao Manus quando ele aguardar, podendo anexar arquivos na resposta.\n"
                "- Colar imagens direto da área de transferência (tarefa e resposta).\n"
                "- Download automático de anexos e links gerados pela tarefa.\n"
                "- Múltiplas APIKEYs com persistência local e troca de chave.\n"
                "- Integração com outras IAs / APIs compatíveis.\n\n"

                "===== SEGURANÇA E ROBUSTEZ =====\n"
                "- Conexão com tentativas automáticas em falhas transitórias de rede/servidor.\n"
                "- Chaves armazenadas localmente com permissão restrita e exibição mascarada.\n"
                "- Modo privacidade limpa os dados locais ao fechar.\n\n"

                "===== SALVAMENTO CONTÍNUO (NUNCA PERDE NADA) =====\n"
                "- O app salva o estado completo da tarefa em disco o tempo todo (autosave).\n"
                "- Ao fechar, tudo é salvo automaticamente (chaves, preferências, checkpoint e rascunho).\n"
                "- Use 'Carregar checkpoint' para retomar exatamente de onde parou.\n\n"

                "===== QUANDO A CHAVE FICA SEM CRÉDITO OU É INATIVADA =====\n"
                "- O app detecta crédito esgotado (429) ou chave inválida/inativada (401/403).\n"
                "- Pergunta se você deseja continuar e permite escolher outra chave cadastrada ou nova.\n"
                "- A tarefa é retomada de onde parou. Se a nova chave for de outra conta, o app cria\n"
                "  uma nova tarefa de continuação reenviando o contexto e os arquivos salvos localmente.\n\n"

                "===== DICA =====\n"
                "A barra inferior mostra o relógio, o status do servidor e um indicador animado quando há\n"
                "trabalho em andamento. Tudo funciona em Python 32 bits.\n"
            )
            corpo.insert("1.0", texto_ajuda)
            corpo.configure(state="disabled")

            rodape = ttk.Frame(janela, padding=(14, 0, 14, 12))
            rodape.grid(row=2, column=0, sticky="ew")
            ttk.Button(rodape, text="Abrir pasta de logs", command=self.abrir_pasta_logs).pack(side="left")
            ttk.Button(rodape, text="Abrir pasta de downloads", command=self.abrir_pasta_downloads).pack(side="left", padx=8)
            ttk.Button(rodape, text="Fechar", command=janela.destroy).pack(side="right")
        except Exception as e:
            try:
                messagebox.showinfo("Ajuda", f"Não foi possível abrir a janela de ajuda: {e}")
            except Exception:
                pass

    def diagnostico_visual(self):
        """Mostra diagnóstico local simplificado."""
        try:
            self.verificar_integridade_local()
            msg = (
                f"{self.integrity_status_var.get()}\n"
                f"{self.security_status_var.get()}\n"
                f"{self.server_status_var.get()}\n"
                f"{self.task_status_var.get()}\n"
                f"{self.task_phase_var.get()}\n"
                f"{self.credit_status_var.get()}\n"
                f"{self.credit_detail_var.get()}\n"
                f"{self.task_checkpoint_status_var.get()}\n"
                f"Checkpoint atual: {TASK_STATE_CURRENT_FILE.resolve()}\n\n"
                f"Python: {sys.version.split()[0]}\n"
                f"Plataforma: {sys.platform}\n"
                f"Logs: {LOG_DIR.resolve()}\n"
                f"Downloads: {DOWNLOAD_DIR.resolve()}\n"
                f"Preferências: {PREFERENCES_FILE.resolve()}\n"
            )
            messagebox.showinfo("Diagnóstico local", msg)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def gerar_titulo_agora(self):
        """Atualiza o campo título para data/hora atual + Nova Tarefa."""
        novo = titulo_nova_tarefa()
        self.title_var.set(novo)
        try:
            self.log(f"[TÍTULO] Novo título automático gerado: {novo}\n")
        except Exception:
            pass

    def aplicar_privacidade(self):
        if self.privacy_var.get():
            self.show_key_var.set(False)
            self.toggle_key_visibility()
            self.save_key_button.configure(state="disabled")
            self.log("[PRIVACIDADE] Ativado.\n")
        else:
            self.save_key_button.configure(state="normal")
            self.log("[PRIVACIDADE] Desativado.\n")
        self.atualizar_lista_arquivos()

    def aplicar_logs(self):
        self.logger.enabled = bool(self.auto_log_var.get())
        if self.logger.enabled and not self.logger.log_path:
            self.logger.prepare_paths(self.task_id_var.get().strip() or "gui")
        self.log(f"[LOG] Logs: {'ativado' if self.logger.enabled else 'desativado'}.\n")

    def carregar_outros_provedores_ia(self) -> List[Dict[str, Any]]:
        """Carrega provedores de outras IAs salvos localmente."""
        data = ler_json_seguro(OTHER_AI_PROVIDERS_FILE, {})
        providers = []
        try:
            raw = data.get("providers", []) if isinstance(data, dict) else data
            if isinstance(raw, list):
                for p in raw:
                    if isinstance(p, dict) and p.get("base_url") and p.get("api_key") and p.get("model"):
                        providers.append(p)
        except Exception:
            pass
        return providers

    def salvar_outros_provedores_ia(self):
        """Salva provedores de outras IAs em arquivo local sensível com persistência."""
        ok = self.salvar_outros_provedores_ia_silencioso()
        if ok:
            self.other_ai_status_var.set(
                f"Outras IAs: {len(self.other_ai_providers)} provedor(es) salvo(s) e persistido(s)"
            )
        return ok

    def atualizar_lista_outros_provedores_ia(self):
        """Atualiza a lista visual de provedores de outras IAs."""
        try:
            if not hasattr(self, "other_ai_listbox"):
                return
            self.other_ai_listbox.delete(0, "end")
            for i, p in enumerate(self.other_ai_providers):
                nome = p.get("name") or f"Provedor {i+1}"
                modelo = p.get("model") or "--"
                base = p.get("base_url") or "--"
                key = mascarar_chave_api(p.get("api_key"))
                self.other_ai_listbox.insert("end", f"#{i+1} {nome} | {modelo} | {base} | {key}")
            self.other_ai_status_var.set(f"Outras IAs: {len(self.other_ai_providers)} provedor(es) cadastrado(s)")
        except Exception as e:
            self.other_ai_status_var.set(f"Erro ao atualizar provedores: {e}")

    def _ao_escolher_provedor_nome(self, event=None):
        """Ao escolher um provedor conhecido pelo nome, autopreenche os campos."""
        try:
            nome = self.other_ai_name_var.get().strip()
            preset = PROVEDORES_IA_POR_NOME.get(nome)
            if not preset:
                return
            self.other_ai_base_url_var.set(preset.get("base_url", ""))
            self.other_ai_endpoint_var.set(preset.get("endpoint", "/chat/completions"))
            self.other_ai_model_var.set(preset.get("model", ""))
            self.other_ai_auth_var.set(preset.get("auth_mode", "bearer"))
            self.other_ai_type_var.set(preset.get("provider_type", "openai_compatible"))
            try:
                self.other_ai_status_var.set(f"Provedor '{nome}' carregado. Informe a APIKEY e salve.")
            except Exception:
                pass
        except Exception:
            pass

    def autodetectar_provedor_chave(self, silencioso: bool = True, online: bool = False):
        """
        Identifica o provedor pela APIKEY e preenche TODO o cadastro
        (Nome, Base URL, Endpoint, Modelo, Auth, Tipo). Se online=True, ainda
        valida a chave consultando os modelos reais da conta.
        """
        try:
            key = self.other_ai_key_var.get().strip()
        except Exception:
            key = ""
        if not key:
            if not silencioso:
                messagebox.showinfo("Detectar pela APIKEY", "Cole a APIKEY no campo APIKEY primeiro.")
            return

        preset = detectar_provedor_por_chave(key)
        if preset:
            self.other_ai_name_var.set(preset.get("name", "Outra IA"))
            self.other_ai_base_url_var.set(preset.get("base_url", ""))
            self.other_ai_endpoint_var.set(preset.get("endpoint", "/chat/completions"))
            self.other_ai_auth_var.set(preset.get("auth_mode", "bearer"))
            self.other_ai_type_var.set(preset.get("provider_type", "openai_compatible"))
            if preset.get("model"):
                self.other_ai_model_var.set(preset["model"])
            try:
                self.other_ai_status_var.set(f"Detectado pela chave: {preset.get('name')}. Cadastro preenchido.")
            except Exception:
                pass
        else:
            if not silencioso:
                self.other_ai_status_var.set("Não reconheci o provedor pelo prefixo da chave. Verificando online...")

        if online:
            self._buscar_modelos_provedor()

    def _buscar_modelos_provedor(self):
        """Consulta {base_url}/models para validar a chave e listar os modelos reais."""
        try:
            base = self.other_ai_base_url_var.get().strip().rstrip("/")
            key = self.other_ai_key_var.get().strip()
            auth = (self.other_ai_auth_var.get() or "bearer").strip().lower()
        except Exception:
            return
        if not base or not key:
            return

        def worker():
            try:
                headers = {"Accept": "application/json"}
                if auth in ("x-api-key", "x_api_key", "apikey"):
                    headers["x-api-key"] = key
                else:
                    headers["Authorization"] = "Bearer " + key
                resp = HTTP_SESSION.get(base + "/models", headers=headers, timeout=30)
                data = resp.json()
                arr = data.get("data") if isinstance(data, dict) else data
                ids = []
                if isinstance(arr, list):
                    for it in arr:
                        mid = it.get("id") if isinstance(it, dict) else str(it)
                        if mid:
                            ids.append(str(mid))
                self.msg("ai_models_detected", ids, base)
            except Exception as e:
                self.msg("ai_models_detected", [], f"erro: {e}")

        self.executar_thread(worker)

    def _dica_erro_outra_ia(self, erro: str) -> str:
        """Gera uma dica amigável a partir do texto de erro da outra IA/API."""
        e = str(erro or "").lower()
        conexao_recusada = any(t in e for t in [
            "10061", "connection refused", "recusou", "max retries exceeded",
            "failed to establish a new connection", "connectionerror", "actively refused",
        ])
        if conexao_recusada and ("localhost" in e or "127.0.0.1" in e):
            return (
                ">> DICA: nenhum servidor local esta rodando nesse endereco/porta.\n"
                ">> Para 'Kiro (gateway local)': inicie o gateway (ex.: kiro-openai-gateway) ANTES, "
                "e use como APIKEY a senha do proxy (PROXY_API_KEY) definida nele. Ele sobe em http://localhost:8000/v1.\n"
                ">> Para 'Ollama (local)': abra o Ollama e rode 'ollama serve' (porta 11434). Para 'LM Studio': ligue o servidor local (porta 1234).\n"
                ">> Confirme a porta na Base URL. Se o Kiro for empresarial com endpoint proprio, troque a Base URL pelo endereco correto."
            )
        if "401" in e or "403" in e or "unauthorized" in e or "forbidden" in e:
            return ">> DICA: a APIKEY parece invalida ou sem permissao para esse provedor. Confira a chave e o tipo de Auth (bearer / x-api-key)."
        if "404" in e or "not found" in e:
            return ">> DICA: endpoint nao encontrado (404). Verifique a Base URL e o Endpoint (ex.: /chat/completions)."
        if "timed out" in e or "timeout" in e:
            return ">> DICA: tempo esgotado. O servidor pode estar lento, offline, ou bloqueado por firewall/rede."
        return ""

    def dados_provedor_outra_ia_atual(self) -> Dict[str, Any]:
        """Lê os campos da aba Outras IAs."""
        return {
            "name": self.other_ai_name_var.get().strip() or "Outra IA",
            "provider_type": self.other_ai_type_var.get().strip() or "openai_compatible",
            "base_url": self.other_ai_base_url_var.get().strip(),
            "endpoint": self.other_ai_endpoint_var.get().strip() or "/chat/completions",
            "model": self.other_ai_model_var.get().strip(),
            "api_key": self.other_ai_key_var.get().strip(),
            "auth_mode": self.other_ai_auth_var.get().strip() or "bearer",
            "temperature": self.other_ai_temp_var.get().strip() or "0.4",
            "max_tokens": self.other_ai_max_tokens_var.get().strip() or "2048",
        }

    def carregar_provedor_outra_ia_nos_campos(self, p: Dict[str, Any]):
        """Carrega um provedor salvo para os campos de edição."""
        self.other_ai_name_var.set(str(p.get("name") or "Outra IA"))
        self.other_ai_type_var.set(str(p.get("provider_type") or "openai_compatible"))
        self.other_ai_base_url_var.set(str(p.get("base_url") or ""))
        self.other_ai_endpoint_var.set(str(p.get("endpoint") or "/chat/completions"))
        self.other_ai_model_var.set(str(p.get("model") or ""))
        self.other_ai_key_var.set(str(p.get("api_key") or ""))
        self.other_ai_auth_var.set(str(p.get("auth_mode") or "bearer"))
        self.other_ai_temp_var.set(str(p.get("temperature") or "0.4"))
        self.other_ai_max_tokens_var.set(str(p.get("max_tokens") or "2048"))

    def salvar_provedor_outra_ia_atual(self):
        """Adiciona ou atualiza um provedor de outra IA."""
        p = self.dados_provedor_outra_ia_atual()
        if not p["base_url"] or not p["api_key"] or not p["model"]:
            messagebox.showerror("Erro", "Preencha Base URL, APIKEY e Modelo da outra IA.")
            return

        # Atualiza se nome+base_url já existirem.
        atualizou = False
        for i, existente in enumerate(self.other_ai_providers):
            if (
                str(existente.get("name", "")).strip().lower() == p["name"].lower()
                and str(existente.get("base_url", "")).strip().lower() == p["base_url"].lower()
            ):
                self.other_ai_providers[i] = p
                atualizou = True
                break

        if not atualizou:
            self.other_ai_providers.append(p)

        self.salvar_outros_provedores_ia()
        self.atualizar_lista_outros_provedores_ia()
        self.other_ai_status_var.set(f"Provedor salvo e persistido: {p['name']} / {p['model']}")
        self.log(f"[OUTRA IA] Provedor salvo: {p['name']} {p['base_url']} {p['model']}\n")

    def usar_provedor_outra_ia_selecionado(self):
        """Usa o provedor selecionado na lista."""
        if not hasattr(self, "other_ai_listbox"):
            return
        sel = self.other_ai_listbox.curselection()
        if not sel:
            messagebox.showinfo("Informação", "Selecione um provedor de outra IA.")
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.other_ai_providers):
            p = self.other_ai_providers[idx]
            self.carregar_provedor_outra_ia_nos_campos(p)
            self.other_ai_status_var.set(f"Provedor ativo: {p.get('name')} / {p.get('model')}")
            try:
                self.notebook.select(self.other_ai_tab)
            except Exception:
                pass

    def remover_provedor_outra_ia(self):
        """Remove o provedor selecionado."""
        if not hasattr(self, "other_ai_listbox"):
            return
        sel = self.other_ai_listbox.curselection()
        if not sel:
            messagebox.showinfo("Informação", "Selecione um provedor para remover.")
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.other_ai_providers):
            removido = self.other_ai_providers.pop(idx)
            self.salvar_outros_provedores_ia()
            self.atualizar_lista_outros_provedores_ia()
            self.other_ai_status_var.set(f"Provedor removido: {removido.get('name')}")
            self.log(f"[OUTRA IA] Provedor removido: {removido.get('name')}\n")

    def toggle_other_ai_key(self):
        """Mostra/oculta a chave da outra IA."""
        try:
            atual = self.other_ai_key_entry.cget("show")
            self.other_ai_key_entry.configure(show="" if atual == "*" else "*")
        except Exception:
            pass

    def cliente_outra_ia_atual(self) -> OtherAIClient:
        """Cria cliente da outra IA a partir dos campos atuais."""
        p = self.dados_provedor_outra_ia_atual()
        return OtherAIClient(
            name=p["name"],
            base_url=p["base_url"],
            api_key=p["api_key"],
            model=p["model"],
            endpoint=p["endpoint"],
            auth_mode=p["auth_mode"],
            provider_type=p["provider_type"],
        )

    def testar_outra_ia(self):
        """Envia uma pergunta curta para testar a outra IA."""
        self.other_ai_status_var.set("Outra IA: testando conexão...")
        try:
            client = self.cliente_outra_ia_atual()
            temp = float(self.other_ai_temp_var.get() or "0.2")
            max_tokens = min(256, int(float(self.other_ai_max_tokens_var.get() or "256")))

            def worker():
                try:
                    data = client.chat(
                        "Responda apenas: OK",
                        system_prompt="Você é um teste de conectividade de API.",
                        temperature=temp,
                        max_tokens=max_tokens,
                        timeout=90,
                    )
                    texto = OtherAIClient.extrair_texto(data)
                    self.msg("other_ai_result", True, client.name, texto, data)
                except Exception as e:
                    self.msg("other_ai_result", False, client.name, str(e), {})

            self.executar_thread(worker)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def enviar_prompt_para_outra_ia(self):
        """Envia o prompt atual para a outra IA/API selecionada."""
        try:
            prompt = self.prompt_text.get("1.0", "end").strip()
            if not prompt:
                messagebox.showerror("Erro", "O prompt está vazio.")
                return

            client = self.cliente_outra_ia_atual()
            temp = float(self.other_ai_temp_var.get() or "0.4")
            max_tokens = int(float(self.other_ai_max_tokens_var.get() or "2048"))

            aviso = (
                "Você vai enviar o prompt atual para outra API de IA, independente da Manus.\n\n"
                f"Provedor: {client.name}\n"
                f"Modelo: {client.model}\n"
                f"URL: {client.url()}\n\n"
                "Arquivos anexados na Manus NÃO serão enviados automaticamente.\n"
                "Continuar?"
            )
            if not messagebox.askyesno("Enviar para outra IA", aviso):
                return

            self.other_ai_status_var.set(f"Enviando prompt para {client.name}...")
            try:
                self.notebook.select(self.other_ai_tab)
            except Exception:
                pass

            def worker():
                try:
                    data = client.chat(
                        prompt,
                        system_prompt="Você é uma IA auxiliar dentro de um aplicativo profissional. Responda de forma clara, útil e objetiva.",
                        temperature=temp,
                        max_tokens=max_tokens,
                        timeout=240,
                    )
                    texto = OtherAIClient.extrair_texto(data)
                    self.msg("other_ai_result", True, client.name, texto, data)
                    if self.auto_log_var.get():
                        self.logger.log("other_ai_response", texto, provider=client.name, model=client.model)
                except Exception as e:
                    self.msg("other_ai_result", False, client.name, str(e), {})

            self.executar_thread(worker)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def consultar_creditos(self):
        """Consulta e exibe o saldo de créditos da chave atual."""
        try:
            key = self.api_key_var.get().strip()
            if not key:
                keys = self.chaves_disponiveis()
                key = keys[0] if keys else ""
            if not key:
                messagebox.showerror("Erro", "Informe uma APIKEY antes de consultar créditos.")
                return

            self.credit_status_var.set("Créditos: consultando...")
            self.credit_key_var.set(f"Chave consultada: {mascarar_chave_api(key)}")
            self.credit_last_update_var.set("Créditos atualizados em: consultando...")
            self.log("[CRÉDITOS] Consultando saldo disponível da chave atual...\n")

            def worker():
                try:
                    api = ManusAPI(key)
                    data = api.available_credits()
                    self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | usage.availableCredits OK")
                    self.msg("credit_status", True, key, data)
                except Exception as e:
                    if erro_credito_esgotado(e):
                        self.definir_creditos_esgotados(f"Consulta de créditos retornou limite/crédito: {agora_iso()} | {e}")
                    self.msg("credit_status", False, key, str(e))

            self.executar_thread(worker)
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def consultar_creditos_todas_chaves(self):
        """Consulta créditos de todas as chaves cadastradas, uma por uma."""
        keys = self.chaves_disponiveis()
        if not keys:
            messagebox.showerror("Erro", "Nenhuma APIKEY cadastrada.")
            return

        self.credit_status_var.set("Créditos: consultando todas as chaves...")
        self.log(f"[CRÉDITOS] Consultando créditos de {len(keys)} chave(s).\n")

        def worker():
            linhas = []
            for idx, key in enumerate(keys, start=1):
                try:
                    api = ManusAPI(key)
                    data = api.available_credits()
                    total = total_creditos_manus(data)

                    # Busca o MODELO em uso DIRETAMENTE do servidor do Manus
                    # (tarefa mais recente da conta via task.list). Nada local.
                    try:
                        modelo = api.current_model()
                    except Exception as me:
                        modelo = f"erro: {resumo_texto(str(me), 40)}"

                    linhas.append({
                        "idx": idx,
                        "key": key,
                        "ok": True,
                        "total": total,
                        "model": modelo,
                        "detail": formatar_creditos_manus(data),
                        "raw": data,
                    })
                    self.msg("credit_status", True, key, data)
                except Exception as e:
                    linhas.append({
                        "idx": idx,
                        "key": key,
                        "ok": False,
                        "total": "--",
                        "model": "--",
                        "detail": str(e),
                        "raw": str(e),
                    })
            self.msg("credit_all_result", linhas)

        self.executar_thread(worker)

    def construir_aba_api_manus(self):
        """
        Central da API Manus: permite executar QUALQUER endpoint da API v2
        (leitura GET e escrita POST) diretamente no servidor do Manus.

        Fluxo:
        1) Escolha o endpoint na lista.
        2) Edite os parâmetros (GET) ou o corpo (POST) em JSON.
        3) Clique em EXECUTAR. A resposta bruta do servidor aparece abaixo.

        Endpoints POST alteram dados REAIS na conta (criar/alterar/apagar).
        """
        self.api_console_status_var = tk.StringVar(value="Pronto. Escolha um endpoint.")

        outer = self.api_tab
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

        topo = ttk.LabelFrame(outer, text="Endpoint da API do Manus (GET = leitura, POST = escrita)", padding=10)
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        topo.columnconfigure(1, weight=1)

        ttk.Label(topo, text="Endpoint:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.api_endpoint_var = tk.StringVar()
        valores = [f"{e['method']:4s} {e['path']}" for e in MANUS_API_ENDPOINTS]
        self.api_endpoint_combo = ttk.Combobox(
            topo, textvariable=self.api_endpoint_var, values=valores, state="readonly"
        )
        self.api_endpoint_combo.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        self.api_endpoint_combo.bind("<<ComboboxSelected>>", self._api_ao_selecionar_endpoint)

        self.api_desc_var = tk.StringVar(
            value="Selecione um endpoint. GET apenas lê; POST altera dados reais no servidor."
        )
        ttk.Label(topo, textvariable=self.api_desc_var, style="Status.TLabel", wraplength=1150, justify="left").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

        params_box = ttk.LabelFrame(
            outer, text="Parâmetros (GET) / Corpo (POST) em JSON — edite conforme necessário", padding=10
        )
        params_box.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        params_box.columnconfigure(0, weight=1)
        self.api_params_text = ScrolledText(params_box, height=10, wrap="word")
        self.api_params_text.grid(row=0, column=0, sticky="ew")

        acoes = ttk.Frame(outer)
        acoes.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(acoes, text="Carregar modelo de parâmetros", command=self._api_carregar_template).pack(side="left", padx=(0, 6))
        ttk.Button(acoes, text="EXECUTAR no servidor", command=self._api_executar, style="Accent.TButton").pack(side="left", padx=6)
        ttk.Button(acoes, text="Copiar resposta", command=self._api_copiar_resposta).pack(side="left", padx=6)
        ttk.Button(acoes, text="Limpar resposta", command=lambda: self.api_response_text.delete("1.0", "end")).pack(side="left", padx=6)
        ttk.Label(acoes, textvariable=self.api_console_status_var, style="Status.TLabel").pack(side="left", padx=12)

        resp_box = ttk.LabelFrame(outer, text="Resposta do servidor (JSON)", padding=10)
        resp_box.grid(row=3, column=0, sticky="nsew")
        resp_box.columnconfigure(0, weight=1)
        resp_box.rowconfigure(0, weight=1)
        self.api_response_text = ScrolledText(resp_box, height=16, wrap="word")
        self.api_response_text.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            outer,
            text=("Atenção: endpoints POST executam ações REAIS na sua conta (criar/alterar/apagar). "
                  "GET apenas lê. A chave usada é a ativa (com failover), definida na aba Configuração / IDs."),
            style="Warn.TLabel",
            wraplength=1200,
            justify="left",
        ).grid(row=4, column=0, sticky="w", pady=(6, 0))

    def _api_endpoint_atual(self) -> Optional[Dict[str, Any]]:
        try:
            idx = self.api_endpoint_combo.current()
        except Exception:
            idx = -1
        if idx is None or idx < 0 or idx >= len(MANUS_API_ENDPOINTS):
            return None
        return MANUS_API_ENDPOINTS[idx]

    def _api_ao_selecionar_endpoint(self, event=None):
        e = self._api_endpoint_atual()
        if not e:
            return
        tipo = "LEITURA (GET)" if e["method"] == "GET" else "ESCRITA (POST) — altera dados reais no servidor"
        self.api_desc_var.set(f"[{tipo}]  {e['path']}  —  {e.get('desc', '')}")
        self._api_carregar_template()

    def _api_carregar_template(self):
        e = self._api_endpoint_atual()
        if not e:
            messagebox.showinfo("API Manus", "Selecione um endpoint primeiro.")
            return
        try:
            txt = json.dumps(e.get("template", {}), ensure_ascii=False, indent=2)
        except Exception:
            txt = "{}"
        self.api_params_text.delete("1.0", "end")
        self.api_params_text.insert("1.0", txt)

    def _api_copiar_resposta(self):
        try:
            texto = self.api_response_text.get("1.0", "end").strip()
            if texto:
                self.clipboard_clear()
                self.clipboard_append(texto)
                self.api_console_status_var.set("Resposta copiada.")
        except Exception:
            pass

    def _api_executar(self):
        e = self._api_endpoint_atual()
        if not e:
            messagebox.showinfo("API Manus", "Selecione um endpoint primeiro.")
            return

        raw = self.api_params_text.get("1.0", "end").strip() or "{}"
        try:
            dados = json.loads(raw)
            if not isinstance(dados, dict):
                raise ValueError("O JSON precisa ser um objeto no formato { ... }.")
        except Exception as ex:
            messagebox.showerror("JSON inválido", f"Não foi possível ler os parâmetros JSON:\n\n{ex}")
            return

        metodo = e["method"]
        caminho = e["path"]

        if metodo == "POST":
            if not messagebox.askyesno(
                "Confirmar ação de ESCRITA no servidor",
                "Você vai EXECUTAR uma ação de ESCRITA diretamente no servidor do Manus:\n\n"
                f"{metodo} {caminho}\n\n"
                "Isso altera dados reais da conta (criar/alterar/apagar). Continuar?",
            ):
                return

        self.api_console_status_var.set(f"Executando {metodo} {caminho}...")
        self.log(f"[API] Executando {metodo} {caminho}\n")

        def worker():
            try:
                api = self.pegar_api()
                if metodo == "GET":
                    params = {k: v for k, v in dados.items() if v not in (None, "")}
                    resp = api.request("GET", caminho, params=params)
                else:
                    resp = api.request("POST", caminho, body=dados)
                try:
                    texto = json.dumps(resp, ensure_ascii=False, indent=2)
                except Exception:
                    texto = str(resp)
                self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | {caminho} OK")
                self.msg("api_console_result", True, f"{metodo} {caminho}", texto)
            except Exception as ex:
                self.msg("api_console_result", False, f"{metodo} {caminho}", str(ex))

        self.executar_thread(worker)

    def _carregar_creditos_editados(self) -> Dict[str, Any]:
        """
        Lê o arquivo local com as edições dos campos de créditos
        (refresh, créditos, quota mensal, próximo refresh, intervalo, etc.).

        Estrutura:
        {
          "por_chave": { "<apikey_mascarada>": {ok,total,detail} },
          "extras":    [ {idx,key,ok,total,detail}, ... ]  # linhas adicionadas à mão
        }
        """
        data = ler_json_seguro(CREDITOS_EDITADOS_FILE, {})
        if not isinstance(data, dict):
            data = {}
        if not isinstance(data.get("por_chave"), dict):
            data["por_chave"] = {}
        if not isinstance(data.get("extras"), list):
            data["extras"] = []
        return data

    def _salvar_creditos_editados(self, data: Dict[str, Any]) -> bool:
        """Grava (de forma atômica) as edições locais dos campos de créditos."""
        try:
            payload = {
                "updated_at": agora_iso(),
                "nota": "Edições LOCAIS dos campos de créditos. Não refletem o saldo real da conta no servidor do Manus.",
                "por_chave": data.get("por_chave", {}) if isinstance(data, dict) else {},
                "extras": data.get("extras", []) if isinstance(data, dict) else [],
            }
            ok = escrever_json_atomico(CREDITOS_EDITADOS_FILE, payload)
            if ok:
                try:
                    self.enfileirar_backup(CREDITOS_EDITADOS_FILE)
                except Exception:
                    pass
            return ok
        except Exception:
            return False

    def abrir_janela_creditos_todas_chaves(self, linhas: List[Dict[str, Any]]):
        """
        Mostra uma janela com o saldo de crédito de todas as chaves consultadas.

        Os campos da tabela são EDITÁVEIS: dê um duplo clique (ou tecle F2/Enter)
        sobre qualquer célula da linha para alterar o valor.
        - Enter confirma a edição.
        - Esc cancela.
        - Ao sair do campo (clicar fora), a alteração também é confirmada.

        PERSISTÊNCIA LOCAL: cada alteração é gravada automaticamente em
        manus_creditos_editados.local.json e recarregada ao reabrir a janela
        (ou reiniciar o app). Assim as edições NÃO se perdem. Importante: esses
        valores são apenas locais/visuais e não alteram o saldo real no servidor
        do Manus, que é somente leitura.
        """
        janela = tk.Toplevel(self)
        janela.title("Créditos de todas as APIKEYs")
        janela.geometry("1340x560")
        janela.minsize(980, 400)
        janela.columnconfigure(0, weight=1)
        janela.rowconfigure(1, weight=1)

        ttk.Label(
            janela,
            text=("Dica: dê um duplo clique (ou tecle F2 / Enter) em um campo para editá-lo. "
                  "Enter confirma, Esc cancela. As edições são salvas automaticamente e "
                  "recarregadas ao reabrir (valores locais, não alteram o saldo real do servidor). "
                  "A coluna 'Modelo em uso' é lida direto do servidor do Manus e não é editável."),
            style="Status.TLabel",
            wraplength=1280,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))

        cols = ("idx", "key", "ok", "total", "model", "detail")
        tree = ttk.Treeview(janela, columns=cols, show="headings", height=16)
        tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        cfg = {
            "idx": ("#", 50),
            "key": ("APIKEY", 170),
            "ok": ("OK", 70),
            "total": ("Créditos disponíveis", 140),
            "model": ("Modelo em uso (servidor)", 190),
            "detail": ("Detalhes", 560),
        }
        for col, (name, width) in cfg.items():
            tree.heading(col, text=name)
            tree.column(col, width=width, anchor="w")

        # Coluna do modelo: destaque visual para deixar claro que vem do servidor.
        try:
            tree.tag_configure("temmodelo", foreground="#1D4ED8")
        except Exception:
            pass

        scroll_y = ttk.Scrollbar(janela, orient="vertical", command=tree.yview)
        scroll_y.grid(row=1, column=1, sticky="ns", pady=10)
        tree.configure(yscrollcommand=scroll_y.set)

        # Carrega as edições locais persistidas e prepara para reaplicá-las.
        persistidos = self._carregar_creditos_editados()
        edicoes_por_chave = persistidos.get("por_chave", {}) or {}
        edicoes_extras = persistidos.get("extras", []) or []
        chaves_api_mascaradas = set()
        # Mapa: APIKEY mascarada (exibida) -> APIKEY real. Necessário para poder
        # aplicar a troca de modelo no servidor usando a chave correta.
        mapa_chave_real: Dict[str, str] = {}

        for row in linhas:
            mk = mascarar_chave_api(row.get("key"))
            chaves_api_mascaradas.add(mk)
            try:
                if row.get("key"):
                    mapa_chave_real[mk] = str(row.get("key"))
            except Exception:
                pass

            ok_val = "SIM" if row.get("ok") else "NÃO"
            total_val = row.get("total")
            detail_val = row.get("detail")
            # O modelo vem SEMPRE do servidor (nunca de edição local).
            model_val = row.get("model") or "--"

            # Se houver edição local salva para esta chave, aplica por cima da API.
            # (a coluna 'modelo' é intencionalmente ignorada aqui, pois é do servidor)
            editado = edicoes_por_chave.get(mk)
            if isinstance(editado, dict):
                if "ok" in editado:
                    ok_val = editado.get("ok")
                if "total" in editado:
                    total_val = editado.get("total")
                if "detail" in editado:
                    detail_val = editado.get("detail")

            tree.insert(
                "",
                "end",
                values=(row.get("idx"), mk, ok_val, total_val, model_val, detail_val),
                tags=("temmodelo",),
            )

        # Reinsere as linhas adicionadas manualmente (não vinculadas a uma chave da API).
        for reg in edicoes_extras:
            if not isinstance(reg, dict):
                continue
            tree.insert(
                "",
                "end",
                values=(
                    reg.get("idx", ""),
                    reg.get("key", ""),
                    reg.get("ok", ""),
                    reg.get("total", ""),
                    "--",  # modelo não se aplica a linhas locais adicionadas à mão
                    reg.get("detail", ""),
                ),
            )

        rodape = ttk.Frame(janela, padding=(10, 0, 10, 10))
        rodape.grid(row=3, column=0, columnspan=2, sticky="ew")

        resumo_var = tk.StringVar()

        def recalcular_resumo():
            filhos = tree.get_children()
            total_ok = 0
            soma = 0
            for iid in filhos:
                vals = tree.item(iid, "values")
                try:
                    if str(vals[2]).strip().upper() in ("SIM", "YES", "OK", "TRUE", "1"):
                        total_ok += 1
                except Exception:
                    pass
                try:
                    soma += int(float(str(vals[3]).strip()))
                except Exception:
                    pass
            resumo_var.set(
                f"Consulta finalizada: {total_ok}/{len(filhos)} chave(s) OK. "
                f"Soma dos saldos consultados: {soma} crédito(s)."
            )

        def persistir_estado_tabela(silencioso: bool = True) -> bool:
            """
            Grava o estado atual da tabela no arquivo local, separando linhas
            vinculadas a uma chave da API (por_chave) das linhas adicionadas
            manualmente (extras). Chamado automaticamente após cada alteração.
            """
            por_chave: Dict[str, Any] = {}
            extras: List[Dict[str, Any]] = []
            for iid in tree.get_children():
                vals = list(tree.item(iid, "values"))
                # Colunas: idx(0), key(1), ok(2), total(3), model(4), detail(5).
                # A coluna 'model' NÃO é persistida: ela é lida do servidor a cada consulta.
                idx_v = vals[0] if len(vals) > 0 else ""
                key_v = str(vals[1]).strip() if len(vals) > 1 else ""
                ok_v = vals[2] if len(vals) > 2 else ""
                total_v = vals[3] if len(vals) > 3 else ""
                detail_v = vals[5] if len(vals) > 5 else ""
                registro = {"idx": idx_v, "key": key_v, "ok": ok_v, "total": total_v, "detail": detail_v}
                if key_v and key_v in chaves_api_mascaradas:
                    por_chave[key_v] = {"ok": ok_v, "total": total_v, "detail": detail_v}
                else:
                    extras.append(registro)
            ok = self._salvar_creditos_editados({"por_chave": por_chave, "extras": extras})
            if ok and not silencioso:
                self.log(f"[CRÉDITOS] Edições salvas em: {CREDITOS_EDITADOS_FILE}\n")
            return ok

        recalcular_resumo()

        # ===== Editor inline: um Entry sobreposto à célula selecionada =====
        editor: Dict[str, Any] = {"entry": None, "iid": None, "col": None}

        def cancelar_editor(event=None):
            e = editor.get("entry")
            if e is not None:
                try:
                    e.destroy()
                except Exception:
                    pass
            editor["entry"] = None
            editor["iid"] = None
            editor["col"] = None

        def confirmar_editor(event=None):
            e = editor.get("entry")
            iid = editor.get("iid")
            col = editor.get("col")
            if e is None or not iid or not col:
                cancelar_editor()
                return
            try:
                novo_valor = e.get()
            except Exception:
                cancelar_editor()
                return
            try:
                idx_col = int(str(col).replace("#", "")) - 1
                vals = list(tree.item(iid, "values"))
                if 0 <= idx_col < len(vals):
                    vals[idx_col] = novo_valor
                    tree.item(iid, values=vals)
            except Exception:
                pass
            cancelar_editor()
            recalcular_resumo()
            # Persiste automaticamente a edição para não se perder ao reabrir/reiniciar.
            persistir_estado_tabela(silencioso=True)

        def iniciar_edicao(iid, col):
            cancelar_editor()
            if not iid or not col:
                return
            # A coluna "Modelo em uso" (#5) é somente leitura: vem do servidor.
            if str(col) == "#5":
                self.definir_status("A coluna 'Modelo em uso' vem do servidor e não pode ser editada.")
                return
            try:
                bbox = tree.bbox(iid, col)
            except Exception:
                bbox = None
            if not bbox:
                return
            x, y, w, h = bbox
            if not w:
                return
            try:
                idx_col = int(str(col).replace("#", "")) - 1
                vals = tree.item(iid, "values")
                valor_atual = vals[idx_col] if 0 <= idx_col < len(vals) else ""
            except Exception:
                valor_atual = ""
            e = ttk.Entry(tree)
            e.place(x=x, y=y, width=w, height=h)
            e.insert(0, str(valor_atual))
            e.select_range(0, "end")
            e.focus_set()
            e.bind("<Return>", confirmar_editor)
            e.bind("<KP_Enter>", confirmar_editor)
            e.bind("<Escape>", cancelar_editor)
            e.bind("<FocusOut>", confirmar_editor)
            editor["entry"] = e
            editor["iid"] = iid
            editor["col"] = col

        def ao_duplo_clique(event):
            try:
                if tree.identify_region(event.x, event.y) != "cell":
                    return
                iid = tree.identify_row(event.y)
                col = tree.identify_column(event.x)
            except Exception:
                return
            iniciar_edicao(iid, col)

        def editar_selecionada(event=None):
            iid = tree.focus()
            if not iid:
                sel = tree.selection()
                iid = sel[0] if sel else ""
            if iid:
                # Por padrão edita a coluna "Detalhes" (a mais usada).
                iniciar_edicao(iid, "#6")
            return "break"

        tree.bind("<Double-1>", ao_duplo_clique)
        tree.bind("<F2>", editar_selecionada)
        tree.bind("<Return>", editar_selecionada)

        # ===== Ações auxiliares de edição da tabela =====
        def adicionar_linha():
            cancelar_editor()
            novo = tree.insert("", "end", values=(len(tree.get_children()) + 1, "", "NÃO", 0, "--", ""))
            tree.selection_set(novo)
            tree.focus(novo)
            tree.see(novo)
            recalcular_resumo()
            persistir_estado_tabela(silencioso=True)

        def remover_selecionada():
            cancelar_editor()
            selecionados = tree.selection()
            if not selecionados:
                messagebox.showinfo("Informação", "Selecione uma linha para remover.", parent=janela)
                return
            for iid in selecionados:
                tree.delete(iid)
            recalcular_resumo()
            persistir_estado_tabela(silencioso=True)

        def salvar_alteracoes():
            confirmar_editor()
            # 1) Persistência principal: grava no arquivo local que é recarregado
            #    ao reabrir a janela / reiniciar o app.
            ok = persistir_estado_tabela(silencioso=False)

            # 2) Cópia extra com carimbo de data/hora para histórico/backup.
            try:
                dados = []
                for iid in tree.get_children():
                    vals = tree.item(iid, "values")
                    dados.append({
                        "idx": vals[0] if len(vals) > 0 else "",
                        "key_mascarada": vals[1] if len(vals) > 1 else "",
                        "ok": vals[2] if len(vals) > 2 else "",
                        "total": vals[3] if len(vals) > 3 else "",
                        "model_servidor": vals[4] if len(vals) > 4 else "",
                        "detail": vals[5] if len(vals) > 5 else "",
                    })
                SESSION_EXPORT_DIR.mkdir(exist_ok=True)
                destino = SESSION_EXPORT_DIR / ("creditos_editados_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
                escrever_json_atomico(destino, {"salvo_em": agora_iso(), "linhas": dados})
                try:
                    self.enfileirar_backup(destino)
                except Exception:
                    pass
            except Exception:
                pass

            if ok:
                messagebox.showinfo(
                    "Salvo",
                    "Alterações salvas localmente.\n\n"
                    f"Arquivo: {CREDITOS_EDITADOS_FILE.name}\n\n"
                    "Elas serão recarregadas automaticamente ao reabrir esta janela "
                    "ou reiniciar o aplicativo.",
                    parent=janela,
                )
            else:
                messagebox.showerror("Erro", "Não foi possível salvar as alterações localmente.", parent=janela)

        def descartar_edicoes():
            if not messagebox.askyesno(
                "Descartar edições",
                "Isto apaga TODAS as edições locais salvas e volta a mostrar apenas os "
                "valores reais consultados da API na próxima consulta.\n\nConfirmar?",
                parent=janela,
            ):
                return
            try:
                if CREDITOS_EDITADOS_FILE.exists():
                    CREDITOS_EDITADOS_FILE.unlink()
            except Exception:
                pass
            # Zera o arquivo em memória também.
            self._salvar_creditos_editados({"por_chave": {}, "extras": []})
            try:
                if CREDITOS_EDITADOS_FILE.exists():
                    CREDITOS_EDITADOS_FILE.unlink()
            except Exception:
                pass
            self.log("[CRÉDITOS] Edições locais descartadas.\n")
            messagebox.showinfo(
                "Edições descartadas",
                "Edições locais apagadas. Consulte os créditos novamente para ver os valores reais.",
                parent=janela,
            )
            janela.destroy()

        # ===== Alterar o MODELO diretamente NO SERVIDOR do Manus =====
        # Na API oficial, o modelo (agent_profile) é definido por TAREFA em
        # task.create. Não há endpoint para trocar o modelo de uma tarefa
        # existente nem um "modelo padrão da conta". Portanto, a forma real de
        # mudar o modelo no servidor é criar uma nova tarefa com o modelo
        # escolhido — o que faz a coluna "Modelo em uso" passar a refleti-lo.
        modelo_frame = ttk.LabelFrame(
            janela,
            text="Alterar modelo diretamente no servidor do Manus (aplica na conta da chave selecionada)",
            padding=(10, 6),
        )
        modelo_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))

        ttk.Label(modelo_frame, text="Modelo:").pack(side="left", padx=(0, 6))
        modelo_var = tk.StringVar(value="manus-1.6-lite")
        ttk.Combobox(
            modelo_frame,
            textvariable=modelo_var,
            values=["manus-1.6-lite", "manus-1.6", "manus-1.6-max"],
            state="readonly",
            width=18,
        ).pack(side="left", padx=(0, 10))

        def alterar_modelo_no_servidor():
            confirmar_editor()
            sel = tree.selection()
            if not sel:
                messagebox.showinfo(
                    "Informação",
                    "Selecione a linha da APIKEY cujo modelo você quer alterar no servidor.",
                    parent=janela,
                )
                return
            iid = sel[0]
            vals = tree.item(iid, "values")
            mk = str(vals[1]).strip() if len(vals) > 1 else ""
            real_key = mapa_chave_real.get(mk, "")
            if not real_key:
                messagebox.showerror(
                    "APIKEY não identificada",
                    "Não foi possível obter a APIKEY real desta linha.\n\n"
                    "Só é possível alterar o modelo no servidor de linhas vindas de uma "
                    "chave consultada (não de linhas adicionadas manualmente).",
                    parent=janela,
                )
                return
            novo_modelo = (modelo_var.get() or "").strip()
            if not novo_modelo:
                messagebox.showinfo("Informação", "Escolha um modelo.", parent=janela)
                return

            if not messagebox.askyesno(
                "Alterar modelo no servidor do Manus",
                "Isto aplica o modelo escolhido DIRETAMENTE no servidor do Manus, "
                "criando uma nova tarefa na conta dessa APIKEY com o modelo:\n\n"
                f"    {novo_modelo}\n\n"
                "Depois disso, a coluna 'Modelo em uso' passará a refletir esse modelo "
                "(pois ela lê a tarefa mais recente da conta no servidor).\n\n"
                "OBS.: a API do Manus só permite definir o modelo ao criar uma tarefa; "
                "criar essa tarefa pode consumir créditos da conta.\n\nContinuar?",
                parent=janela,
            ):
                return

            self.definir_status(f"Alterando modelo no servidor para {novo_modelo}...")
            self.log(f"[MODELO] Solicitando troca de modelo no servidor para {novo_modelo} (chave {mk}).\n")

            def worker():
                try:
                    api = ManusAPI(real_key)

                    # 1) Tenta aplicar o modelo na TAREFA EXISTENTE mais recente,
                    #    usando o override oficial de agent_profile em sendMessage.
                    recente = {}
                    try:
                        recente = api.most_recent_task()
                    except Exception:
                        recente = {}

                    task_id_alvo = str(recente.get("id") or "").strip()

                    if task_id_alvo:
                        api.send_message(
                            task_id_alvo,
                            "Ajuste de modelo do aplicativo. Responda apenas com 'OK'.",
                            agent_profile=novo_modelo,
                        )
                        novo_id = task_id_alvo
                    else:
                        # 2) Sem tarefas na conta: cria uma nova já no modelo pedido.
                        titulo = titulo_nova_tarefa()
                        prompt = (
                            "Definição do modelo da conta pelo aplicativo. "
                            "Responda apenas com 'OK' e não execute nenhuma outra ação."
                        )
                        data = api.create_task(prompt, novo_modelo, titulo)
                        novo_id = data.get("task_id") or ""

                    # 3) POLLING: o servidor aplica o modelo no próximo turno, então
                    #    o valor não muda instantaneamente. Consultamos a tarefa
                    #    específica (task.detail) repetidamente até o servidor
                    #    confirmar o modelo pedido (ou esgotar ~30s).
                    modelo_conf = ""
                    alvo = str(novo_modelo).strip()
                    tentativas = 15  # 15 x 2s = ~30s
                    for i in range(tentativas):
                        try:
                            if novo_id:
                                m = api.model_of_task(novo_id)
                            else:
                                m = api.current_model()
                        except Exception:
                            m = ""
                        if m:
                            modelo_conf = m
                            if str(m).strip() == alvo:
                                break
                        self.msg("log", f"[MODELO] Aguardando o servidor aplicar '{alvo}'... (leitura atual: '{m or '--'}', tentativa {i + 1}/{tentativas})\n")
                        time.sleep(2)

                    if not modelo_conf:
                        modelo_conf = novo_modelo

                    self.msg(
                        "modelo_alterado_servidor",
                        janela, tree, iid,
                        modelo_conf,
                        novo_id,
                        novo_modelo,
                    )
                except Exception as e:
                    self.msg("modelo_alterado_erro", str(e))

            self.executar_thread(worker)

        ttk.Button(modelo_frame, text="Aplicar modelo no servidor", command=alterar_modelo_no_servidor).pack(side="left")
        ttk.Label(
            modelo_frame,
            text="(cria uma nova tarefa na conta com o modelo escolhido - pode consumir créditos)",
            style="Status.TLabel",
        ).pack(side="left", padx=10)

        ttk.Label(rodape, textvariable=resumo_var).pack(side="left")

        ttk.Button(rodape, text="Fechar", command=janela.destroy).pack(side="right")
        ttk.Button(rodape, text="Salvar alterações", command=salvar_alteracoes).pack(side="right", padx=6)
        ttk.Button(rodape, text="Descartar edições", command=descartar_edicoes).pack(side="right", padx=6)
        ttk.Button(rodape, text="Remover linha", command=remover_selecionada).pack(side="right", padx=6)
        ttk.Button(rodape, text="Adicionar linha", command=adicionar_linha).pack(side="right", padx=6)

    def estado_atual_para_checkpoint(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monta o estado completo local da tarefa atual.

        Este estado é usado para:
        - continuar de onde parou se uma chave cair;
        - retomar depois de fechar/reabrir o app;
        - manter histórico local de prompt, arquivos, eventos e downloads.
        """
        task_id = self.task_id_var.get().strip() if hasattr(self, "task_id_var") else ""
        prompt = ""
        resposta = ""
        logs = ""

        try:
            if hasattr(self, "prompt_text"):
                prompt = self.prompt_text.get("1.0", "end").strip()
        except Exception:
            pass

        try:
            if hasattr(self, "realtime_text"):
                resposta = self.realtime_text.get("1.0", "end").strip()
        except Exception:
            pass

        try:
            if hasattr(self, "log_text"):
                logs = self.log_text.get("1.0", "end").strip()
        except Exception:
            pass

        state = {
            "schema": "manus_gui_task_checkpoint_v1",
            "saved_at": agora_iso(),
            "task_id": task_id,
            "task_url": self.task_url_var.get().strip() if hasattr(self, "task_url_var") else "",
            "title": self.title_var.get().strip() if hasattr(self, "title_var") else "",
            "agent_profile": self.agent_var.get().strip() if hasattr(self, "agent_var") else "",
            "prompt": prompt,
            "selected_files": lista_str_segura(getattr(self, "selected_files", [])),
            "downloaded_files": lista_str_segura(getattr(self, "downloaded_files", [])),
            "eventos_vistos": lista_str_segura(getattr(self, "eventos_vistos", [])),
            "urls_baixadas": lista_str_segura(getattr(self, "urls_baixadas", [])),
            "api_key_active_masked": mascarar_chave_api(self.api_key_var.get().strip()) if hasattr(self, "api_key_var") else "",
            "api_key_count": len(getattr(self, "api_keys", [])),
            "server_status": self.server_status_var.get() if hasattr(self, "server_status_var") else "",
            "server_last_seen": self.server_last_seen_var.get() if hasattr(self, "server_last_seen_var") else "",
            "task_status": self.task_status_var.get() if hasattr(self, "task_status_var") else "",
            "task_phase": self.task_phase_var.get() if hasattr(self, "task_phase_var") else "",
            "task_clue": self.task_clue_var.get() if hasattr(self, "task_clue_var") else "",
            "task_activity": self.task_activity_var.get() if hasattr(self, "task_activity_var") else "",
            "credit_status": self.credit_status_var.get() if hasattr(self, "credit_status_var") else "",
            "upload_percent": float(self.upload_percent_var.get()) if hasattr(self, "upload_percent_var") else 0.0,
            "upload_status": self.upload_status_var.get() if hasattr(self, "upload_status_var") else "",
            "last_response_text": resposta[-12000:],
            "last_log_text": logs[-12000:],
            "ultimas_mensagens": list(getattr(self, "ultimas_mensagens", []) or []),
            "message_count": len(getattr(self, "ultimas_mensagens", []) or []),
            "reply_files": lista_str_segura(getattr(self, "reply_files", [])),
        }

        if extra:
            try:
                state.update(extra)
            except Exception:
                pass

        return state

    def salvar_checkpoint_tarefa(self, reason: str = "", extra: Optional[Dict[str, Any]] = None) -> bool:
        """
        Salva checkpoint local da tarefa atual.

        Salva sempre em:
        - manus_estados_tarefas/tarefa_atual_estado.json
        - manus_estados_tarefas/<task_id>.estado.json, quando há Task ID
        """
        try:
            if hasattr(self, "checkpoint_enabled_var") and not self.checkpoint_enabled_var.get():
                return False

            TASK_STATE_DIR.mkdir(exist_ok=True)

            extra = dict(extra or {})
            if reason:
                extra["checkpoint_reason"] = reason

            state = self.estado_atual_para_checkpoint(extra=extra)
            self.current_task_state = state

            escrever_json_atomico(TASK_STATE_CURRENT_FILE, state)

            task_id = state.get("task_id") or ""
            if task_id:
                escrever_json_atomico(caminho_estado_tarefa(task_id), state)

            self.task_checkpoint_status_var.set(
                f"Checkpoint: salvo em {agora_iso()}" + (f" | {reason}" if reason else "")
            )
            return True

        except Exception as e:
            try:
                self.task_checkpoint_status_var.set(f"Checkpoint: erro ao salvar - {e}")
                self.log(f"[CHECKPOINT/ERRO] {e}\n")
            except Exception:
                pass
            return False

    def carregar_checkpoint_arquivo(self, path: Path) -> Dict[str, Any]:
        """Lê um checkpoint local."""
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            raise RuntimeError(f"Não foi possível ler checkpoint: {e}")

    def aplicar_checkpoint_tarefa(self, state: Dict[str, Any], acompanhar: bool = True):
        """
        Aplica um checkpoint salvo na interface e, opcionalmente,
        volta a acompanhar o mesmo Task ID.
        """
        if not isinstance(state, dict):
            raise RuntimeError("Checkpoint inválido.")

        task_id = str(state.get("task_id") or "").strip()
        task_url = str(state.get("task_url") or "").strip()
        title = str(state.get("title") or "").strip()
        agent = str(state.get("agent_profile") or "").strip()
        prompt = str(state.get("prompt") or "")

        if task_id:
            self.task_id_var.set(task_id)
        if task_url:
            self.task_url_var.set(task_url)
        elif task_id:
            self.task_url_var.set(f"https://manus.im/app/{task_id}")
        if title:
            self.title_var.set(title)
        if agent:
            self.agent_var.set(agent)

        try:
            if prompt and hasattr(self, "prompt_text"):
                self.prompt_text.delete("1.0", "end")
                self.prompt_text.insert("1.0", prompt)
        except Exception:
            pass

        try:
            self.selected_files = [Path(p) for p in state.get("selected_files", []) if p]
            if hasattr(self, "files_list"):
                self.files_list.delete(0, "end")
                for p in self.selected_files:
                    self.files_list.insert("end", str(p))
                self.atualizar_info_arquivos()
        except Exception:
            pass

        try:
            self.downloaded_files = [Path(p) for p in state.get("downloaded_files", []) if p]
            if hasattr(self, "downloads_list"):
                self.downloads_list.delete(0, "end")
                for p in self.downloaded_files:
                    self.downloads_list.insert("end", str(p))
        except Exception:
            pass

        try:
            self.eventos_vistos = set(state.get("eventos_vistos", []) or [])
            self.urls_baixadas = set(state.get("urls_baixadas", []) or [])
        except Exception:
            pass

        try:
            self.ultimas_mensagens = list(state.get("ultimas_mensagens", []) or [])
        except Exception:
            pass

        try:
            self.reply_files = [Path(p) for p in state.get("reply_files", []) if p]
            self.atualizar_label_anexos_resposta()
        except Exception:
            pass

        try:
            self.task_status_var.set(str(state.get("task_status") or "Tarefa: retomada de checkpoint"))
            self.task_phase_var.set(str(state.get("task_phase") or "Fase atual: retomada local"))
            self.task_clue_var.set(str(state.get("task_clue") or "Pistas: checkpoint local carregado"))
            self.task_activity_var.set(str(state.get("task_activity") or f"Atividade: checkpoint carregado em {agora_iso()}"))
            self.credit_status_var.set(str(state.get("credit_status") or self.credit_status_var.get()))
            self.upload_percent_var.set(float(state.get("upload_percent") or 0.0))
            self.upload_status_var.set(str(state.get("upload_status") or self.upload_status_var.get()))
        except Exception:
            pass

        try:
            texto = str(state.get("last_response_text") or "")
            if texto and hasattr(self, "realtime_text"):
                self.realtime_text.insert("end", "\n[CHECKPOINT LOCAL RESTAURADO]\n")
                self.realtime_text.insert("end", texto + "\n")
                self.realtime_text.see("end")
        except Exception:
            pass

        self.current_task_state = state
        self.task_checkpoint_status_var.set(f"Checkpoint: carregado em {agora_iso()}")

        try:
            self.notebook.select(self.main_tab)
        except Exception:
            pass

        if acompanhar and task_id:
            self.msg("live", "\n[RETOMANDO PELO CHECKPOINT LOCAL]\n")
            self.msg("live", f"Task ID: {task_id}\n")
            self.msg("live", "O app restaurou o estado local e voltará a consultar a API com a chave ativa/failover.\n")
            self.stop_polling.clear()
            self.executar_thread(lambda: self.acompanhar_tarefa(task_id))

    def carregar_ultimo_checkpoint(self):
        """Carrega o checkpoint da tarefa atual salvo localmente."""
        try:
            if not TASK_STATE_CURRENT_FILE.exists():
                messagebox.showinfo("Checkpoint", "Nenhum checkpoint local encontrado.")
                return
            state = self.carregar_checkpoint_arquivo(TASK_STATE_CURRENT_FILE)
            self.aplicar_checkpoint_tarefa(state, acompanhar=True)
        except Exception as e:
            messagebox.showerror("Erro ao carregar checkpoint", str(e))

    def abrir_pasta_checkpoints(self):
        """Abre a pasta de checkpoints locais."""
        try:
            TASK_STATE_DIR.mkdir(exist_ok=True)
            os.startfile(str(TASK_STATE_DIR.resolve()))
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def salvar_checkpoint_manual(self):
        """Botão manual para salvar checkpoint local."""
        ok = self.salvar_checkpoint_tarefa("salvo manualmente")
        if ok:
            messagebox.showinfo("Checkpoint", "Checkpoint local salvo com sucesso.")

    def autosave_periodico(self):
        """
        Salvamento contínuo: enquanto o app está aberto, grava em disco todos os
        dados da tarefa (prompt, arquivos, eventos, downloads, mensagens completas
        e respostas) de tempos em tempos. Assim, se a chave cair, a energia faltar
        ou o app fechar, nada é perdido e a tarefa pode ser retomada de onde parou.
        """
        try:
            if getattr(self, "checkpoint_enabled_var", None) and self.checkpoint_enabled_var.get():
                tem_tarefa = bool(self.task_id_var.get().strip()) if hasattr(self, "task_id_var") else False
                tem_prompt = False
                try:
                    tem_prompt = bool(self.prompt_text.get("1.0", "end").strip())
                except Exception:
                    pass
                if tem_tarefa or tem_prompt:
                    self.salvar_checkpoint_tarefa("autosave periódico")
                    # Backup automático para o FTP (com limites de frequência).
                    try:
                        agora = time.time()
                        if getattr(self, "ftp_enabled_var", None) and self.ftp_enabled_var.get():
                            if agora - getattr(self, "_ultimo_backup_checkpoint", 0) >= 60:
                                self._ultimo_backup_checkpoint = agora
                                self.enfileirar_backup(TASK_STATE_CURRENT_FILE)
                                tid = self.task_id_var.get().strip()
                                if tid:
                                    self.enfileirar_backup(caminho_estado_tarefa(tid))
                            if agora - getattr(self, "_ultimo_backup_full", 0) >= 300:
                                self.executar_thread(self.sincronizar_tudo_ftp)
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            try:
                self.after(self.autosave_intervalo_ms, self.autosave_periodico)
            except Exception:
                pass

    def salvar_chaves_multiplas_silencioso(self) -> bool:
        """
        Salva a lista de APIKEYs da Manus automaticamente, sem abrir pop-up.

        Persistência:
        - arquivo: manus_api_keys.local.json
        - fica na mesma pasta do .py/.exe
        - ao reiniciar o app ou o Windows, as chaves são recarregadas
        """
        try:
            # Garante que a chave atual também esteja na lista.
            atual = self.api_key_var.get().strip()
            if atual and atual not in self.api_keys:
                self.api_keys.insert(0, atual)

            # Remove vazias e duplicadas preservando ordem.
            limpas = []
            vistos = set()
            for key in self.api_keys:
                key = str(key or "").strip()
                if key and key not in vistos:
                    limpas.append(key)
                    vistos.add(key)
            self.api_keys = limpas

            data = {
                "updated_at": agora_iso(),
                "keys": self.api_keys,
                "active_key": atual,
                "note": "Arquivo local sensível. Não compartilhe. Contém APIKEYs salvas para persistência.",
            }
            KEY_RING_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            try:
                os.chmod(KEY_RING_FILE, 0o600)
            except Exception:
                pass

            self.atualizar_lista_chaves()
            self.keyring_status_var.set(f"Chaves cadastradas: {len(self.api_keys)} | persistidas em disco")
            return True
        except Exception as e:
            try:
                self.failover_status_var.set(f"Falha ao salvar chaves: {e}")
                self.log(f"[APIKEY/ERRO] Falha ao salvar chaves automaticamente: {e}\n")
            except Exception:
                pass
            return False

    def salvar_outros_provedores_ia_silencioso(self) -> bool:
        """
        Salva automaticamente os provedores/chaves da aba Outras IAs / APIs.

        Persistência:
        - arquivo: outras_ias_provedores.local.json
        - fica na mesma pasta do .py/.exe
        """
        try:
            # Remove registros vazios e duplicados simples.
            limpos = []
            vistos = set()
            for p in self.other_ai_providers:
                if not isinstance(p, dict):
                    continue
                base = str(p.get("base_url") or "").strip()
                key = str(p.get("api_key") or "").strip()
                model = str(p.get("model") or "").strip()
                name = str(p.get("name") or "Outra IA").strip()
                if not base or not key or not model:
                    continue
                ident = (name.lower(), base.lower(), model.lower(), mascarar_chave_api(key))
                if ident in vistos:
                    continue
                vistos.add(ident)
                limpos.append(p)

            self.other_ai_providers = limpos

            data = {
                "updated_at": agora_iso(),
                "providers": self.other_ai_providers,
                "note": "Arquivo local sensível. Contém chaves de APIs de outras IAs para persistência.",
            }
            OTHER_AI_PROVIDERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            try:
                os.chmod(OTHER_AI_PROVIDERS_FILE, 0o600)
            except Exception:
                pass

            self.atualizar_lista_outros_provedores_ia()
            self.other_ai_status_var.set(f"Outras IAs: {len(self.other_ai_providers)} provedor(es) persistido(s)")
            return True
        except Exception as e:
            try:
                self.other_ai_status_var.set(f"Falha ao salvar provedores: {e}")
                self.log(f"[OUTRA IA/ERRO] Falha ao salvar provedores automaticamente: {e}\n")
            except Exception:
                pass
            return False

    def aplicar_chave_ativa_persistida(self):
        """Restaura a chave ativa salva no arquivo de múltiplas chaves."""
        try:
            if KEY_RING_FILE.exists():
                data = json.loads(KEY_RING_FILE.read_text(encoding="utf-8"))
                active = str(data.get("active_key") or "").strip() if isinstance(data, dict) else ""
                if active:
                    if active not in self.api_keys:
                        self.api_keys.insert(0, active)
                    self.api_key_var.set(active)
                    self.keyring_status_var.set(f"Chave ativa restaurada: {mascarar_chave_api(active)}")
                    return

            # Se não tiver active_key, usa a primeira da lista.
            if self.api_keys and not self.api_key_var.get().strip():
                self.api_key_var.set(self.api_keys[0])
                self.keyring_status_var.set(f"Chave ativa restaurada: {mascarar_chave_api(self.api_keys[0])}")
        except Exception as e:
            try:
                self.log(f"[APIKEY] Não foi possível restaurar chave ativa: {e}\n")
            except Exception:
                pass

    def carregar_chaves_multiplas(self) -> List[str]:
        """Carrega múltiplas APIKEYs locais. As chaves são mantidas mascaradas na interface."""
        chaves: List[str] = []

        def add(k):
            k = str(k or "").strip()
            if k and k not in chaves:
                chaves.append(k)

        # 1) arquivo com várias chaves
        try:
            if KEY_RING_FILE.exists():
                data = json.loads(KEY_RING_FILE.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for k in data.get("keys", []):
                        if isinstance(k, dict):
                            add(k.get("key"))
                        else:
                            add(k)
                elif isinstance(data, list):
                    for k in data:
                        add(k.get("key") if isinstance(k, dict) else k)
        except Exception:
            pass

        # 2) chave local antiga
        try:
            if KEY_FILE.exists():
                add(KEY_FILE.read_text(encoding="utf-8").strip())
        except Exception:
            pass

        # 3) variável de ambiente
        add(os.environ.get("MANUS_API_KEY", ""))

        return chaves

    def chaves_disponiveis(self) -> List[str]:
        """Retorna chaves em ordem de uso, sempre começando pela chave do campo atual."""
        chaves: List[str] = []

        def add(k):
            k = str(k or "").strip()
            if k and k not in chaves:
                chaves.append(k)

        add(self.api_key_var.get())
        for k in getattr(self, "api_keys", []):
            add(k)

        if not self.privacy_var.get():
            try:
                if KEY_FILE.exists():
                    add(KEY_FILE.read_text(encoding="utf-8").strip())
            except Exception:
                pass

        add(os.environ.get("MANUS_API_KEY", ""))
        return chaves

    def salvar_chaves_multiplas(self):
        """Salva a lista de múltiplas chaves em arquivo local com persistência."""
        ok = self.salvar_chaves_multiplas_silencioso()
        if ok:
            self.log(f"[APIKEY] Lista de chaves salva em: {KEY_RING_FILE}\n")
            messagebox.showinfo(
                "OK",
                "Lista de chaves salva com sucesso.\n\n"
                "Ela será recarregada automaticamente ao reiniciar o app ou o Windows."
            )
        else:
            messagebox.showerror("Erro", "Não foi possível salvar a lista de chaves.")

    def atualizar_lista_chaves(self, selecionar_key: str = ""):
        """Atualiza a listbox de chaves mascaradas."""
        try:
            if not hasattr(self, "keys_listbox"):
                return

            self.keys_listbox.delete(0, "end")
            atual = self.api_key_var.get().strip()
            selecionar_key = str(selecionar_key or atual or "").strip()

            for i, key in enumerate(self.api_keys):
                ativo = "  [ATIVA]" if key == atual else ""
                self.keys_listbox.insert("end", f"#{i + 1}  {mascarar_chave_api(key)}{ativo}")

            if selecionar_key and selecionar_key in self.api_keys:
                idx = self.api_keys.index(selecionar_key)
                self.keys_listbox.selection_clear(0, "end")
                self.keys_listbox.selection_set(idx)
                self.keys_listbox.see(idx)

            total = len(self.api_keys)
            atual_txt = mascarar_chave_api(atual) if atual else "nenhuma"
            self.keyring_status_var.set(f"Chaves cadastradas: {total} | chave ativa: {atual_txt}")
            try:
                self.atualizar_lista_fusao()
            except Exception:
                pass
        except Exception as e:
            try:
                self.log(f"[APIKEY] Falha ao atualizar lista: {e}\n")
            except Exception:
                pass

    def adicionar_chave_do_campo(self):
        """Adiciona a chave digitada no campo APIKEY à lista de failover."""
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showerror("Erro", "Digite uma APIKEY no campo APIKEY antes de adicionar.")
            return
        if key in self.api_keys:
            messagebox.showinfo("Informação", "Essa chave já está cadastrada.")
            self.atualizar_lista_chaves(selecionar_key=key)
            return
        self.api_keys.append(key)
        self.atualizar_lista_chaves(selecionar_key=key)
        self.keyring_status_var.set(f"Chave adicionada e salva: {mascarar_chave_api(key)}")
        self.log(f"[APIKEY] Chave adicionada à lista: {mascarar_chave_api(key)}\n")

    def usar_chave_selecionada(self):
        """Coloca a chave selecionada como chave ativa no campo APIKEY."""
        if not hasattr(self, "keys_listbox"):
            return
        sel = self.keys_listbox.curselection()
        if not sel:
            messagebox.showinfo("Informação", "Selecione uma chave na lista.")
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.api_keys):
            self.api_key_var.set(self.api_keys[idx])
            self.atualizar_lista_chaves(selecionar_key=self.api_keys[idx])
            self.salvar_chaves_multiplas_silencioso()
            self.failover_status_var.set(f"Chave ativa alterada manualmente para #{idx + 1} e persistida.")
            self.log(f"[APIKEY] Chave ativa alterada manualmente para #{idx + 1} {mascarar_chave_api(self.api_keys[idx])}\n")

    def usar_proxima_chave_manual(self):
        """Pula manualmente para a próxima chave cadastrada."""
        if not self.api_keys:
            messagebox.showinfo("Informação", "Nenhuma chave cadastrada na lista.")
            return

        atual = self.api_key_var.get().strip()
        if atual in self.api_keys:
            idx = (self.api_keys.index(atual) + 1) % len(self.api_keys)
        else:
            idx = 0

        self.api_key_var.set(self.api_keys[idx])
        self.atualizar_lista_chaves(selecionar_key=self.api_keys[idx])
        self.salvar_chaves_multiplas_silencioso()
        self.failover_status_var.set(f"Chave ativa alterada manualmente para #{idx + 1} e persistida.")
        self.log(f"[APIKEY] Próxima chave selecionada manualmente: #{idx + 1} {mascarar_chave_api(self.api_keys[idx])}\n")

    def remover_chave_selecionada(self):
        """Remove uma chave da lista local."""
        if not hasattr(self, "keys_listbox"):
            return
        sel = self.keys_listbox.curselection()
        if not sel:
            messagebox.showinfo("Informação", "Selecione uma chave para remover.")
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.api_keys):
            removida = self.api_keys.pop(idx)
            if self.api_key_var.get().strip() == removida:
                self.api_key_var.set(self.api_keys[0] if self.api_keys else "")
            self.atualizar_lista_chaves()
            self.log(f"[APIKEY] Chave removida: {mascarar_chave_api(removida)}\n")

    def apagar_lista_chaves(self):
        """Apaga a lista de múltiplas chaves do disco e da memória."""
        if not messagebox.askyesno("Confirmar", "Apagar a lista de múltiplas chaves cadastradas?"):
            return
        self.api_keys.clear()
        if KEY_RING_FILE.exists():
            try:
                KEY_RING_FILE.unlink()
            except Exception:
                pass
        self.atualizar_lista_chaves()
        self.failover_status_var.set("Failover: lista de chaves apagada.")
        self.log("[APIKEY] Lista de múltiplas chaves apagada.\n")

    def callback_troca_chave_api(self, index: int, key: str, reason: str):
        """Callback chamado pelo wrapper de API quando há failover."""
        self.msg("key_active", int(index), str(key), str(reason))

    def callback_problema_chave_api(self, index: int, key: str, error: str):
        """Callback chamado pelo wrapper de API quando uma chave falha."""
        self.msg("key_problem", int(index), str(key), str(error))

    def toggle_key_visibility(self):
        self.key_entry.configure(show="" if self.show_key_var.get() else "*")

    def carregar_chave_local(self) -> str:
        if KEY_FILE.exists():
            return KEY_FILE.read_text(encoding="utf-8").strip()
        return ""

    def salvar_chave(self):
        if self.privacy_var.get():
            messagebox.showwarning("Privacidade local", "Desative o Modo Privacidade Local para salvar a chave.")
            return
        key = self.api_key_var.get().strip()
        if not key:
            messagebox.showerror("Erro", "A chave está vazia.")
            return
        KEY_FILE.write_text(key, encoding="utf-8")
        try:
            os.chmod(KEY_FILE, 0o600)
        except Exception:
            pass
        if key not in self.api_keys:
            self.api_keys.insert(0, key)
            self.atualizar_lista_chaves(selecionar_key=key)
        self.salvar_chaves_multiplas_silencioso()
        self.log(f"[OK] Chave salva em: {KEY_FILE} e persistida no cofre de múltiplas chaves\n")
        messagebox.showinfo("OK", "Chave salva com sucesso.")

    def apagar_chave(self):
        if KEY_FILE.exists():
            KEY_FILE.unlink()
        self.api_key_var.set("")
        self.atualizar_lista_chaves()
        self.log("[OK] Chave local apagada. A lista de múltiplas chaves não foi apagada.\n")

    def pegar_api(self) -> ManusAPI:
        keys = self.chaves_disponiveis()
        if not keys:
            raise RuntimeError("Informe pelo menos uma API Key da Manus primeiro.")

        # ===== Fusão de chaves ativa: usa o pool como UMA só chave, com
        # encadeamento automático quando uma esgota o crédito (créditos somados). =====
        try:
            if self.fusion_enabled_var.get():
                fused = []
                vistos = set()
                for k in self.fused_keys:
                    k = str(k or "").strip()
                    if k and k in self.api_keys and k not in vistos:
                        fused.append(k)
                        vistos.add(k)
                if len(fused) >= 2:
                    self.api_key_var.set(fused[0])
                    self.atualizar_lista_chaves(selecionar_key=fused[0])
                    return ManusAPIFailover(
                        fused,
                        on_key_change=self.callback_troca_chave_api,
                        on_key_problem=self.callback_problema_chave_api,
                        allow_credit_failover=True,
                    )
        except Exception:
            pass

        # Mantém a chave ativa no campo para o usuário saber qual é a primeira usada.
        self.api_key_var.set(keys[0])
        self.atualizar_lista_chaves(selecionar_key=keys[0])

        return ManusAPIFailover(
            keys,
            on_key_change=self.callback_troca_chave_api,
            on_key_problem=self.callback_problema_chave_api,
            allow_credit_failover=False,
        )

    def log(self, texto: str):
        self.log_text.insert("end", texto)
        if getattr(self, "autoscroll_var", None) is None or self.autoscroll_var.get():
            self.log_text.see("end")
        self.update_idletasks()
        if getattr(self, "logger", None) and self.auto_log_var.get():
            self.logger.log("gui_log", texto.strip())

    def resposta_live(self, texto: str):
        self.realtime_text.insert("end", texto)
        if getattr(self, "autoscroll_var", None) is None or self.autoscroll_var.get():
            self.realtime_text.see("end")
        self.update_idletasks()
        if getattr(self, "logger", None) and self.auto_log_var.get():
            self.logger.log("gui_realtime", texto.strip())

    def msg(self, kind: str, *args):
        self.msg_queue.put((kind, *args))

    def processar_fila(self):
        try:
            while True:
                item = self.msg_queue.get_nowait()
                kind = item[0]
                if kind == "log":
                    self.log(item[1])
                elif kind == "live":
                    self.resposta_live(item[1])
                elif kind == "reply_files_cleared":
                    self.atualizar_label_anexos_resposta()
                elif kind == "task":
                    _, task_id, url = item
                    self.current_task_id = task_id
                    self.current_task_url = url
                    self.task_id_var.set(task_id)
                    self.task_url_var.set(url)
                    if task_id and self.auto_log_var.get():
                        self.logger.update_task_id(task_id)
                elif kind == "upload_progress":
                    _, percent, sent, total, filename = item
                    self.upload_percent_var.set(float(percent))
                    self.upload_status_var.set(f"Upload: {filename} - {percent:.2f}%")
                    self.upload_detail_var.set(f"{tamanho_legivel(sent)} enviados de {tamanho_legivel(total)}")
                    try:
                        self.upload_progressbar.update_idletasks()
                    except Exception:
                        pass

                elif kind == "server_status":
                    _, online, detail = item
                    if online:
                        self.server_status_var.set("Servidor: ONLINE")
                    else:
                        self.server_status_var.set("Servidor: OFFLINE / sem resposta")
                    self.server_last_seen_var.set(str(detail))

                elif kind == "key_active":
                    _, index, key, reason = item
                    self.api_key_var.set(str(key or ""))
                    self.keyring_status_var.set(f"Chave ativa: #{int(index) + 1} {mascarar_chave_api(key)}")
                    self.failover_status_var.set(str(reason))
                    self.atualizar_lista_chaves(selecionar_key=key)
                    self.salvar_chaves_multiplas_silencioso()
                    self.salvar_checkpoint_tarefa("troca automática de chave", {"active_key_changed_to": mascarar_chave_api(key), "key_change_reason": str(reason)})
                    self.log(f"[APIKEY] {reason}\n")

                elif kind == "key_problem":
                    _, index, key, error = item
                    self.failover_status_var.set(
                        f"Problema na chave #{int(index) + 1} {mascarar_chave_api(key)}: {resumo_texto(error, 180)}"
                    )
                    self.log(f"[APIKEY] Problema na chave #{int(index) + 1} {mascarar_chave_api(key)}: {error}\n")

                elif kind == "credit_need_key":
                    _, task_id, error = item
                    if erro_chave_invalida(error) and not erro_credito_esgotado(error):
                        self.definir_chave_inativada(error)
                    else:
                        self.definir_creditos_esgotados(error)
                    self.tratar_interrupcao_chave(task_id, error)

                elif kind == "credit_status":
                    _, ok, key, data_or_error = item
                    if ok:
                        total = total_creditos_manus(data_or_error)
                        total_txt = "--" if total is None else str(total)
                        self.credit_status_var.set(f"Créditos disponíveis: {total_txt}")
                        self.credit_detail_var.set(formatar_creditos_manus(data_or_error))
                        self.credit_key_var.set(f"Chave consultada: {mascarar_chave_api(key)}")
                        self.credit_last_update_var.set(f"Créditos atualizados em: {agora_iso()}")
                        self.log(f"[CRÉDITOS] {formatar_creditos_manus(data_or_error)}\n")
                    else:
                        self.credit_status_var.set("Créditos: falha ao consultar")
                        self.credit_detail_var.set(f"Erro: {resumo_texto(data_or_error, 260)}")
                        self.credit_key_var.set(f"Chave consultada: {mascarar_chave_api(key)}")
                        self.credit_last_update_var.set(f"Falha em: {agora_iso()}")
                        self.log(f"[CRÉDITOS/ERRO] {data_or_error}\n")

                elif kind == "credit_all_result":
                    _, linhas = item
                    self.abrir_janela_creditos_todas_chaves(linhas)

                elif kind == "modelo_alterado_servidor":
                    _, janela_ref, tree_ref, iid, modelo_conf, novo_id, modelo_pedido = item
                    try:
                        if tree_ref.winfo_exists() and tree_ref.exists(iid):
                            vals = list(tree_ref.item(iid, "values"))
                            if len(vals) >= 5:
                                vals[4] = modelo_conf
                                tree_ref.item(iid, values=vals)
                    except Exception:
                        pass
                    self.log(f"[MODELO] Pedido: '{modelo_pedido}' | confirmado no servidor: '{modelo_conf}' (tarefa: {novo_id}).\n")
                    self.definir_status(f"Modelo no servidor agora: {modelo_conf}")
                    try:
                        rebaixou = (
                            str(modelo_conf).strip()
                            and str(modelo_pedido).strip()
                            and str(modelo_conf).strip() != str(modelo_pedido).strip()
                        )
                        if rebaixou:
                            messagebox.showwarning(
                                "Modelo ainda não confirmado como o pedido",
                                f"Você pediu: {modelo_pedido}\n"
                                f"O servidor ainda reporta: {modelo_conf}\n\n"
                                "Possíveis causas:\n"
                                "1) PROPAGAÇÃO: o override entra em vigor no próximo turno da tarefa. "
                                "Pode levar alguns segundos até o servidor refletir. Feche e reabra "
                                "'Créditos de todas as chaves' (ou clique de novo em 'Aplicar modelo') "
                                "para reconsultar.\n\n"
                                "2) PLANO/CHAVE: confirme que ESTA APIKEY pertence à conta com plano pago. "
                                "Contas gratuitas são rebaixadas para manus-1.6-lite pelo servidor.\n\n"
                                "3) A tarefa usada como base pode estar finalizada; nesse caso o override "
                                "só aparece após um novo turno processar.\n\n"
                                "Se você tem plano pago nesta chave e o valor não muda mesmo após reabrir, "
                                "me avise que eu ajusto a estratégia (ex.: criar uma tarefa nova já no modelo).",
                            )
                        else:
                            messagebox.showinfo(
                                "Modelo alterado no servidor",
                                f"Modelo aplicado no servidor do Manus: {modelo_conf}\n"
                                f"Tarefa: {novo_id}\n\n"
                                "A coluna 'Modelo em uso' foi atualizada com o valor real do servidor.",
                            )
                    except Exception:
                        pass

                elif kind == "modelo_alterado_erro":
                    _, erro = item
                    self.log(f"[MODELO/ERRO] {erro}\n")
                    self.definir_status("Falha ao alterar modelo no servidor.")
                    if erro_credito_esgotado(erro):
                        messagebox.showerror(
                            "Sem crédito",
                            "Não foi possível alterar o modelo: a conta está sem crédito/limite "
                            "para criar a tarefa que aplica o modelo no servidor.\n\n" + resumo_texto(erro, 300),
                        )
                    else:
                        messagebox.showerror("Erro ao alterar modelo", str(erro))

                elif kind == "api_console_result":
                    _, ok, titulo, texto = item
                    try:
                        cabecalho = ("OK" if ok else "ERRO") + f" | {titulo} | {agora_iso()}"
                        self.api_response_text.insert("end", f"\n===== {cabecalho} =====\n{texto}\n")
                        self.api_response_text.see("end")
                    except Exception:
                        pass
                    try:
                        self.api_console_status_var.set(("OK: " if ok else "ERRO: ") + titulo)
                    except Exception:
                        pass
                    self.log(f"[API] {'OK' if ok else 'ERRO'} {titulo}\n")

                elif kind == "other_ai_result":
                    _, ok, provider_name, text_or_error, raw = item
                    if ok:
                        self.other_ai_status_var.set(f"Outra IA OK: {provider_name} respondeu em {agora_iso()}")
                        try:
                            self.other_ai_response_text.insert("end", f"\n===== {provider_name} / {agora_iso()} =====\n")
                            self.other_ai_response_text.insert("end", str(text_or_error) + "\n")
                            self.other_ai_response_text.see("end")
                        except Exception:
                            pass
                        self.log(f"[OUTRA IA] {provider_name} respondeu com sucesso.\n")
                    else:
                        dica = self._dica_erro_outra_ia(text_or_error)
                        self.other_ai_status_var.set(f"Erro na outra IA {provider_name}: {resumo_texto(text_or_error, 160)}")
                        try:
                            self.other_ai_response_text.insert("end", f"\n[ERRO / {provider_name}]\n{text_or_error}\n")
                            if dica:
                                self.other_ai_response_text.insert("end", dica + "\n")
                            self.other_ai_response_text.see("end")
                        except Exception:
                            pass
                        self.log(f"[OUTRA IA/ERRO] {provider_name}: {text_or_error}\n")

                elif kind == "task_status":
                    _, status, phase, clue, activity = item
                    self.task_status_var.set(str(status))
                    self.task_phase_var.set(str(phase))
                    self.task_clue_var.set(str(clue))
                    self.task_activity_var.set(str(activity))
                    self.salvar_checkpoint_tarefa("status atualizado")

                elif kind == "unfinished_tasks_result":
                    _, janela_ref, tree, cache, tasks, status_lbl = item
                    try:
                        if not janela_ref.winfo_exists():
                            continue
                        tree.delete(*tree.get_children())
                        cache.clear()
                        for t in tasks:
                            tid, titulo, status, updated, credit, url = self.extrair_id_url_titulo_status_tarefa(t)
                            iid = tid or f"sem_id_{len(cache)}"
                            cache[iid] = t
                            tree.insert(
                                "",
                                "end",
                                iid=iid,
                                values=(
                                    status,
                                    formatar_timestamp(updated),
                                    titulo,
                                    tid,
                                    credit,
                                    url,
                                ),
                            )
                        status_lbl.config(text=f"Tarefas não terminadas encontradas: {len(tasks)}")
                    except Exception as e:
                        try:
                            status_lbl.config(text=f"Erro ao preencher lista: {e}")
                        except Exception:
                            pass

                elif kind == "unfinished_tasks_error":
                    _, status_lbl, error = item
                    try:
                        status_lbl.config(text=f"Erro ao carregar tarefas não terminadas: {error}")
                    except Exception:
                        pass

                elif kind == "download":
                    _, path = item
                    p = Path(path)
                    if p not in self.downloaded_files:
                        self.downloaded_files.append(p)
                        self.downloads_list.insert("end", str(p))
                        self.session_status_var.set(f"Sessão: arquivo baixado {p.name}")
                        self.salvar_checkpoint_tarefa("arquivo baixado", {"last_download": str(p)})
                elif kind == "waiting":
                    _, detail = item
                    self.last_waiting_detail = detail or {}
                elif kind == "erro":
                    erro_txt = str(item[1])
                    if erro_credito_esgotado(erro_txt):
                        self.definir_creditos_esgotados(erro_txt)
                        tid_atual = self.task_id_var.get().strip() if hasattr(self, "task_id_var") else ""
                        if tid_atual:
                            self.salvar_checkpoint_tarefa("erro de crédito capturado pela fila", {"credit_error": erro_txt})
                            self.escolher_chave_credito_e_continuar(tid_atual, erro_txt)
                        else:
                            messagebox.showerror("Erro", erro_txt)
                    else:
                        messagebox.showerror("Erro", erro_txt)
                    self.log(f"\n[ERRO] {erro_txt}\n")
                elif kind == "info":
                    messagebox.showinfo("Informação", item[1])
                elif kind == "notify_done":
                    self.notificar_conclusao()
                elif kind == "ftp_status":
                    _, ok, rel = item
                    if ok:
                        self.ftp_status_var.set(f"Backup FTP: {rel} | {agora_iso()}")
                    else:
                        self.ftp_status_var.set(f"Backup FTP: FALHA em {rel}")
                        self.log(f"[FTP] Falha ao enviar: {rel}\n")
                elif kind == "mysql_status":
                    _, ok, detail = item
                    if ok:
                        self.mysql_status_var.set(f"MySQL: {detail} | {agora_iso()}")
                    else:
                        self.mysql_status_var.set(f"MySQL: indisponível ({resumo_texto(detail, 80)})")
                elif kind == "ai_models_detected":
                    _, ids, info = item
                    if ids:
                        try:
                            self.other_ai_model_combo.configure(values=ids)
                        except Exception:
                            pass
                        try:
                            if hasattr(self, "estudio_model_combo"):
                                self.estudio_model_combo.configure(values=ids)
                        except Exception:
                            pass
                        cur = self.other_ai_model_var.get().strip()
                        if cur not in ids:
                            self.other_ai_model_var.set(ids[0])
                        self.other_ai_status_var.set(f"Chave válida! {len(ids)} modelo(s) disponíveis carregados da conta.")
                        try:
                            self.estudio_status_var.set(f"Modelos atualizados: {len(ids)} disponíveis.")
                        except Exception:
                            pass
                    else:
                        self.other_ai_status_var.set(
                            f"Cadastro preenchido. Não foi possível listar modelos online ({resumo_texto(str(info), 60)})."
                        )

                elif kind == "estudio_resposta":
                    _, texto, provedor = item
                    try:
                        if self.estudio_tarefa_atual:
                            self.estudio_tarefa_atual.setdefault("messages", []).append({"role": "assistant", "content": texto})
                            self._estudio_salvar_tarefas()
                        self.estudio_ultima_resposta = texto
                        self.estudio_render_transcript()
                        self.estudio_status_var.set(f"{provedor} respondeu em {agora_iso()}.")
                        # auto-baixa arquivos citados na resposta, se houver.
                        self.estudio_baixar_arquivos_resposta(silencioso=True)
                    except Exception:
                        pass

                elif kind == "estudio_resposta_erro":
                    _, erro, provedor = item
                    dica = self._dica_erro_outra_ia(erro)
                    self.estudio_status_var.set(f"Erro em {provedor}: {resumo_texto(erro, 120)}")
                    try:
                        self.estudio_resposta_text.insert("end", f"\n[ERRO / {provedor}]\n{erro}\n")
                        if dica:
                            self.estudio_resposta_text.insert("end", dica + "\n")
                        self.estudio_resposta_text.see("end")
                    except Exception:
                        pass

                elif kind == "estudio_status":
                    _, detalhe = item
                    try:
                        self.estudio_status_var.set(str(detalhe))
                    except Exception:
                        pass

                elif kind == "estudio_download":
                    _, caminho = item
                    try:
                        p = Path(caminho)
                        if p not in self.estudio_downloads:
                            self.estudio_downloads.append(p)
                            self.estudio_downloads_list.insert("end", str(p))
                        self.estudio_status_var.set(f"Arquivo baixado: {p.name}")
                        self.enfileirar_backup(p)
                    except Exception:
                        pass
                elif kind == "fused_credits":
                    _, soma, ok_count, total_chaves, detalhes = item
                    self.fused_credits_var.set(
                        f"Créditos somados: {soma} (de {ok_count}/{total_chaves} chaves do pool)"
                    )
                    self.credit_status_var.set(f"Créditos (pool fundido): {soma}")
                    self.log("[FUSÃO] Créditos somados do pool: " + str(soma) + "\n")
                    for d in detalhes:
                        self.log(f"   - {d}\n")
        except queue.Empty:
            pass
        self.after(getattr(self, "fila_intervalo_ms", 100), self.processar_fila)

    def executar_thread(self, alvo):
        def _wrap():
            try:
                self._threads_ativas += 1
            except Exception:
                pass
            try:
                alvo()
            finally:
                try:
                    self._threads_ativas = max(0, self._threads_ativas - 1)
                except Exception:
                    pass
        threading.Thread(target=_wrap, daemon=True).start()

    def definir_status(self, texto: str):
        """Atualiza o texto principal da barra de status inferior."""
        try:
            self.statusbar_var.set(str(texto))
        except Exception:
            pass

    def _heartbeat_ui(self):
        """
        Mantém a barra de status viva: relógio em tempo real e um spinner
        animado quando há trabalho em andamento. Puramente visual e seguro.
        """
        try:
            self.clock_var.set(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
            if getattr(self, "_threads_ativas", 0) > 0:
                self._spinner_idx = (self._spinner_idx + 1) % len(self._spinner_frames)
                self.spinner_var.set(self._spinner_frames[self._spinner_idx])
                self.statusbar_var.set(
                    f"Trabalhando... {self._threads_ativas} processo(s) em andamento"
                )
            else:
                self.spinner_var.set("[ ok ]")
        except Exception:
            pass
        finally:
            try:
                self.after(450, self._heartbeat_ui)
            except Exception:
                pass

    # ===================================================================
    # ============ CENTRAL AVANÇADA: TURBO / IA / INJEÇÃO ===============
    # ===================================================================

    def _carregar_injecoes(self) -> List[Dict[str, Any]]:
        data = ler_json_seguro(INJECTIONS_FILE, [])
        if isinstance(data, dict):
            data = data.get("itens") or []
        out: List[Dict[str, Any]] = []
        if isinstance(data, list):
            for it in data:
                if isinstance(it, dict) and it.get("texto"):
                    out.append({"nome": str(it.get("nome") or "Injeção"), "texto": str(it.get("texto"))})
        return out

    def _salvar_injecoes(self) -> bool:
        return escrever_json_atomico(INJECTIONS_FILE, {"updated_at": agora_iso(), "itens": self.injecoes})

    def _carregar_prompt_presets(self) -> List[Dict[str, Any]]:
        data = ler_json_seguro(PROMPT_PRESETS_FILE, [])
        if isinstance(data, dict):
            data = data.get("itens") or []
        out: List[Dict[str, Any]] = []
        if isinstance(data, list):
            for it in data:
                if isinstance(it, dict) and it.get("texto"):
                    out.append({"nome": str(it.get("nome") or "Preset"), "texto": str(it.get("texto"))})
        return out

    def _salvar_prompt_presets(self) -> bool:
        return escrever_json_atomico(PROMPT_PRESETS_FILE, {"updated_at": agora_iso(), "itens": self.prompt_presets})

    def aplicar_turbo(self):
        """Liga/desliga o modo tempo real: fila de UI mais rápida e polling de 1s."""
        try:
            on = bool(self.turbo_var.get())
            if on:
                self.fila_intervalo_ms = 25
                try:
                    self._poll_interval_anterior = self.poll_interval_var.get()
                except Exception:
                    self._poll_interval_anterior = ""
                try:
                    self.poll_interval_var.set("1")
                except Exception:
                    pass
                self.turbo_status_var.set("Turbo: LIGADO (tempo real, polling 1s, UI instantânea)")
            else:
                self.fila_intervalo_ms = 100
                try:
                    if self._poll_interval_anterior:
                        self.poll_interval_var.set(self._poll_interval_anterior)
                except Exception:
                    pass
                self.turbo_status_var.set("Turbo: desligado")
            self.definir_status(self.turbo_status_var.get())
            self.log(f"[TURBO] {self.turbo_status_var.get()}\n")
        except Exception as e:
            self.log(f"[TURBO/ERRO] {e}\n")

    def aplicar_modo_furtivo(self):
        """Modo furtivo (stealth): privacidade total e sem logs em arquivo."""
        try:
            on = bool(self.stealth_var.get())
            if on:
                try:
                    self.privacy_var.set(True)
                    self.aplicar_privacidade()
                except Exception:
                    pass
                try:
                    self.auto_log_var.set(False)
                    self.aplicar_logs()
                except Exception:
                    pass
                self.stealth_status_var.set("Furtivo: LIGADO (privacidade total, sem logs em arquivo)")
            else:
                try:
                    self.privacy_var.set(False)
                    self.aplicar_privacidade()
                except Exception:
                    pass
                try:
                    self.auto_log_var.set(True)
                    self.aplicar_logs()
                except Exception:
                    pass
                self.stealth_status_var.set("Furtivo: desligado")
            self.definir_status(self.stealth_status_var.get())
            self.log(f"[FURTIVO] {self.stealth_status_var.get()}\n")
        except Exception as e:
            self.log(f"[FURTIVO/ERRO] {e}\n")

    def aplicar_injecao_no_prompt(self, prompt: str) -> str:
        """Se a injeção estiver ativada, antepõe o preâmbulo de sistema ao prompt."""
        try:
            if self.injection_enabled_var.get() and hasattr(self, "injection_text"):
                preambulo = self.injection_text.get("1.0", "end").strip()
                if preambulo:
                    self.log("[INJEÇÃO] Preâmbulo de contexto injetado no prompt.\n")
                    return preambulo + "\n\n" + prompt
        except Exception:
            pass
        return prompt

    def atualizar_lista_injecoes(self):
        if not hasattr(self, "lista_injecoes"):
            return
        try:
            self.lista_injecoes.delete(0, "end")
            for it in self.injecoes:
                self.lista_injecoes.insert("end", it.get("nome") or "Injeção")
            self.injection_presets_status_var.set(f"Injeções salvas: {len(self.injecoes)}")
        except Exception:
            pass

    def salvar_injecao_atual(self):
        nome = (self.injection_name_var.get().strip() or "Injeção")
        texto = self.injection_text.get("1.0", "end").strip() if hasattr(self, "injection_text") else ""
        if not texto:
            messagebox.showinfo("Injeção", "Escreva o texto da injeção/preâmbulo antes de salvar.")
            return
        for it in self.injecoes:
            if str(it.get("nome", "")).strip().lower() == nome.lower():
                it["texto"] = texto
                break
        else:
            self.injecoes.append({"nome": nome, "texto": texto})
        self._salvar_injecoes()
        self.atualizar_lista_injecoes()
        self.log(f"[INJEÇÃO] Salva: {nome}\n")

    def aplicar_injecao_selecionada(self):
        try:
            sel = list(self.lista_injecoes.curselection())
            if not sel:
                return
            it = self.injecoes[sel[0]]
            self.injection_text.delete("1.0", "end")
            self.injection_text.insert("1.0", it.get("texto", ""))
            self.injection_name_var.set(it.get("nome", ""))
        except Exception as e:
            self.log(f"[INJEÇÃO/ERRO] {e}\n")

    def remover_injecao_selecionada(self):
        try:
            sel = list(self.lista_injecoes.curselection())
            if not sel:
                return
            del self.injecoes[sel[0]]
            self._salvar_injecoes()
            self.atualizar_lista_injecoes()
        except Exception as e:
            self.log(f"[INJEÇÃO/ERRO] {e}\n")

    def atualizar_lista_prompt_presets(self):
        if not hasattr(self, "lista_prompt_presets"):
            return
        try:
            self.lista_prompt_presets.delete(0, "end")
            for it in self.prompt_presets:
                self.lista_prompt_presets.insert("end", it.get("nome") or "Preset")
            self.prompt_presets_status_var.set(f"Presets de prompt: {len(self.prompt_presets)}")
        except Exception:
            pass

    def salvar_prompt_preset(self):
        nome = (self.prompt_preset_name_var.get().strip() or "Preset")
        try:
            texto = self.prompt_text.get("1.0", "end").strip()
        except Exception:
            texto = ""
        if not texto:
            messagebox.showinfo("Preset", "O prompt está vazio. Escreva algo na aba Principal antes de salvar.")
            return
        for it in self.prompt_presets:
            if str(it.get("nome", "")).strip().lower() == nome.lower():
                it["texto"] = texto
                break
        else:
            self.prompt_presets.append({"nome": nome, "texto": texto})
        self._salvar_prompt_presets()
        self.atualizar_lista_prompt_presets()
        self.log(f"[PRESET] Prompt salvo como preset: {nome}\n")

    def aplicar_prompt_preset(self):
        try:
            sel = list(self.lista_prompt_presets.curselection())
            if not sel:
                return
            it = self.prompt_presets[sel[0]]
            self.prompt_text.delete("1.0", "end")
            self.prompt_text.insert("1.0", it.get("texto", ""))
            self.prompt_preset_name_var.set(it.get("nome", ""))
            self.contar_metricas_prompt()
            try:
                self.notebook.select(self.main_tab)
            except Exception:
                pass
        except Exception as e:
            self.log(f"[PRESET/ERRO] {e}\n")

    def remover_prompt_preset(self):
        try:
            sel = list(self.lista_prompt_presets.curselection())
            if not sel:
                return
            del self.prompt_presets[sel[0]]
            self._salvar_prompt_presets()
            self.atualizar_lista_prompt_presets()
        except Exception as e:
            self.log(f"[PRESET/ERRO] {e}\n")

    def contar_metricas_prompt(self):
        try:
            t = self.prompt_text.get("1.0", "end")
        except Exception:
            t = ""
        self.prompt_metrics_var.set(
            f"Prompt: {contar_palavras(t)} palavras / ~{estimar_tokens(t)} tokens / {len(t.strip())} caracteres"
        )

    def _transformar_prompt(self, modo: str):
        try:
            t = self.prompt_text.get("1.0", "end").rstrip("\n")
        except Exception:
            return
        if modo == "maiusc":
            t = t.upper()
        elif modo == "minusc":
            t = t.lower()
        elif modo == "limpar":
            t = "\n".join(" ".join(linha.split()) for linha in t.splitlines())
        try:
            self.prompt_text.delete("1.0", "end")
            self.prompt_text.insert("1.0", t)
            self.contar_metricas_prompt()
        except Exception:
            pass

    def preencher_provedor_preset(self, preset: Dict[str, Any]):
        try:
            self.other_ai_name_var.set(preset.get("name", "Outra IA"))
            self.other_ai_type_var.set("openai_compatible")
            self.other_ai_base_url_var.set(preset.get("base_url", ""))
            self.other_ai_endpoint_var.set(preset.get("endpoint", "/chat/completions"))
            self.other_ai_model_var.set(preset.get("model", ""))
            self.other_ai_auth_var.set(preset.get("auth_mode", "bearer"))
            try:
                self.notebook.select(self.other_ai_tab)
            except Exception:
                pass
            self.other_ai_status_var.set(
                f"Preset '{preset.get('name')}' carregado. Informe a APIKEY e clique em salvar provedor."
            )
            self.log(f"[PRESET IA] Provedor preenchido: {preset.get('name')}\n")
        except Exception as e:
            self.log(f"[PRESET IA/ERRO] {e}\n")

    def enviar_para_manus_preferencial(self):
        """Atalho explícito reforçando que a Manus é a IA preferencial."""
        try:
            self.notebook.select(self.main_tab)
        except Exception:
            pass
        self.criar_tarefa()

    def comparar_em_varias_ias(self):
        """Envia o mesmo prompt para todas as outras IAs cadastradas (comparação)."""
        try:
            prompt = self.prompt_text.get("1.0", "end").strip()
        except Exception:
            prompt = ""
        if not prompt:
            messagebox.showinfo("Multi-IA", "Escreva um prompt na aba Principal primeiro.")
            return
        provs = [
            p for p in getattr(self, "other_ai_providers", [])
            if isinstance(p, dict) and p.get("base_url") and p.get("api_key") and p.get("model")
        ]
        if not provs:
            messagebox.showinfo(
                "Multi-IA",
                "Nenhuma outra IA cadastrada.\n\n"
                "Cadastre provedores na aba 'Outras IAs / APIs' (use os presets desta central).\n\n"
                "Lembrete: a Manus continua sendo a IA preferencial.",
            )
            return
        if not messagebox.askyesno(
            "Comparar em várias IAs",
            f"Enviar o mesmo prompt para {len(provs)} IA(s) cadastrada(s)?\n\n"
            "Isto é apenas comparação; a Manus permanece a IA preferencial do app.",
        ):
            return
        try:
            self.notebook.select(self.other_ai_tab)
        except Exception:
            pass
        self.multi_ia_status_var.set(f"Multi-IA: enviando para {len(provs)} provedor(es)...")
        try:
            temp = float(self.other_ai_temp_var.get() or "0.4")
        except Exception:
            temp = 0.4
        try:
            maxt = int(float(self.other_ai_max_tokens_var.get() or "1024"))
        except Exception:
            maxt = 1024

        def worker(p):
            try:
                c = OtherAIClient(
                    name=p.get("name"),
                    base_url=p.get("base_url"),
                    api_key=p.get("api_key"),
                    model=p.get("model"),
                    endpoint=p.get("endpoint", "/chat/completions"),
                    auth_mode=p.get("auth_mode", "bearer"),
                    provider_type=p.get("provider_type", "openai_compatible"),
                )
                data = c.chat(
                    prompt,
                    system_prompt="Comparação multi-IA dentro de um app profissional. Responda de forma clara e objetiva.",
                    temperature=temp,
                    max_tokens=maxt,
                    timeout=240,
                )
                self.msg("other_ai_result", True, c.name, OtherAIClient.extrair_texto(data), data)
            except Exception as e:
                self.msg("other_ai_result", False, str(p.get("name") or "Outra IA"), str(e), {})

        for p in provs:
            self.executar_thread(lambda p=p: worker(p))

    def notificar_conclusao(self):
        try:
            if self.bip_var.get():
                self.bell()
        except Exception:
            pass
        try:
            self.definir_status("Tarefa concluida! (clique para ver a resposta final)")
        except Exception:
            pass

    # ---------- Fusão de chaves Manus (créditos somados / cadeia automática) ----------

    def _salvar_fusao(self) -> bool:
        ok = escrever_json_atomico(
            FUSION_FILE,
            {
                "updated_at": agora_iso(),
                "enabled": bool(self.fusion_enabled_var.get()),
                "keys": list(self.fused_keys),
                "note": "Arquivo local sensível. Contém APIKEYs fundidas para uso em cadeia.",
            },
        )
        try:
            os.chmod(FUSION_FILE, 0o600)
        except Exception:
            pass
        return ok

    def atualizar_status_fusao(self):
        try:
            if self.fusion_enabled_var.get() and len(self.fused_keys) >= 2:
                self.fusion_status_var.set(
                    f"Fusão: ATIVADA com {len(self.fused_keys)} chaves (créditos somados, cadeia automática)"
                )
            elif self.fused_keys:
                self.fusion_status_var.set(
                    f"Fusão: {len(self.fused_keys)} chave(s) selecionada(s), mas DESATIVADA"
                )
            else:
                self.fusion_status_var.set("Fusão: desativada")
        except Exception:
            pass

    def atualizar_lista_fusao(self):
        """Lista as chaves cadastradas (mascaradas) e marca as que já estão no pool."""
        if not hasattr(self, "lista_fusao"):
            return
        try:
            self.lista_fusao.delete(0, "end")
            for k in getattr(self, "api_keys", []):
                marca = "  [NO POOL]" if k in self.fused_keys else ""
                self.lista_fusao.insert("end", f"{mascarar_chave_api(k)}{marca}")
            # Reseleciona visualmente as que estão no pool.
            for i, k in enumerate(getattr(self, "api_keys", [])):
                if k in self.fused_keys:
                    try:
                        self.lista_fusao.selection_set(i)
                    except Exception:
                        pass
            self.atualizar_status_fusao()
        except Exception:
            pass

    def fundir_chaves_selecionadas(self):
        """Funde as chaves selecionadas em um único pool (créditos somados)."""
        try:
            sel = list(self.lista_fusao.curselection())
            chaves = [self.api_keys[i] for i in sel if 0 <= i < len(getattr(self, "api_keys", []))]
            # Remove duplicadas preservando ordem.
            limpas = []
            vistos = set()
            for k in chaves:
                k = str(k or "").strip()
                if k and k not in vistos:
                    limpas.append(k)
                    vistos.add(k)
            if len(limpas) < 2:
                messagebox.showinfo(
                    "Fusão de chaves",
                    "Selecione 2 ou mais chaves cadastradas para fundir.\n\n"
                    "Dica: segure Ctrl ou Shift para selecionar várias na lista.",
                )
                return
            self.fused_keys = limpas
            self.fusion_enabled_var.set(True)
            self._salvar_fusao()
            self.atualizar_lista_fusao()
            self.fused_credits_var.set("Créditos somados: -- (clique em 'Consultar créditos somados')")
            self.log(f"[FUSÃO] {len(self.fused_keys)} chaves fundidas. Agora funcionam como uma só, em cadeia automática.\n")
            self.definir_status(f"Fusão ativada com {len(self.fused_keys)} chaves.")
            try:
                self.consultar_creditos_fundidos()
            except Exception:
                pass
        except Exception as e:
            self.log(f"[FUSÃO/ERRO] {e}\n")

    def desfazer_fusao(self):
        """Desfaz a fusão e volta ao comportamento normal de chave única/manual."""
        self.fused_keys = []
        self.fusion_enabled_var.set(False)
        self._salvar_fusao()
        self.atualizar_lista_fusao()
        self.fused_credits_var.set("Créditos somados: --")
        self.log("[FUSÃO] Fusão desfeita. Voltou ao uso normal de chaves.\n")
        self.definir_status("Fusão desfeita.")

    def aplicar_fusao(self):
        """Liga/desliga a fusão pelo checkbox (exige 2+ chaves no pool)."""
        try:
            if self.fusion_enabled_var.get() and len(self.fused_keys) < 2:
                self.fusion_enabled_var.set(False)
                messagebox.showinfo(
                    "Fusão de chaves",
                    "Para ativar a fusão, selecione 2 ou mais chaves na lista e clique em 'Fundir selecionadas'.",
                )
                return
            self._salvar_fusao()
            self.atualizar_status_fusao()
            self.definir_status(self.fusion_status_var.get())
            self.log(f"[FUSÃO] {self.fusion_status_var.get()}\n")
        except Exception as e:
            self.log(f"[FUSÃO/ERRO] {e}\n")

    def consultar_creditos_fundidos(self):
        """Consulta o crédito de cada chave do pool e mostra a SOMA (crédito unificado)."""
        chaves = [k for k in self.fused_keys if k]
        if len(chaves) < 2:
            messagebox.showinfo("Fusão de chaves", "Funda 2 ou mais chaves antes de somar os créditos.")
            return
        self.fused_credits_var.set(f"Créditos somados: consultando {len(chaves)} chave(s)...")
        self.log(f"[FUSÃO] Somando créditos de {len(chaves)} chave(s) do pool...\n")

        def worker():
            soma = 0
            ok_count = 0
            detalhes = []
            for idx, key in enumerate(chaves, start=1):
                try:
                    data = ManusAPI(key).available_credits()
                    total = total_creditos_manus(data)
                    if total is not None:
                        try:
                            soma += int(total)
                        except Exception:
                            pass
                    ok_count += 1
                    detalhes.append(f"#{idx} {mascarar_chave_api(key)}: {total if total is not None else '--'}")
                except Exception as e:
                    detalhes.append(f"#{idx} {mascarar_chave_api(key)}: erro ({resumo_texto(str(e), 60)})")
            self.msg("fused_credits", soma, ok_count, len(chaves), detalhes)

        self.executar_thread(worker)

    # ---------- Backup automático via FTPS ----------

    def _remote_rel_de(self, local_path) -> str:
        """Calcula o caminho remoto preservando a estrutura relativa à pasta do app."""
        try:
            p = Path(local_path).resolve()
        except Exception:
            p = Path(local_path)
        try:
            return p.relative_to(APP_DIR).as_posix()
        except Exception:
            return "externos/" + p.name

    def enfileirar_backup(self, local_path, remote_rel: str = ""):
        """Coloca um arquivo na fila de envio para o FTP (não bloqueia a interface)."""
        try:
            if not getattr(self, "ftp_enabled_var", None) or not self.ftp_enabled_var.get():
                return
            p = Path(local_path)
            if not p.exists() or not p.is_file():
                return
            rel = remote_rel or self._remote_rel_de(p)
            self.ftp_queue.put((str(p), rel))
        except Exception:
            pass

    def enfileirar_pasta(self, pasta):
        """Enfileira recursivamente todos os arquivos de uma pasta."""
        try:
            base = Path(pasta)
            if not base.exists():
                return
            for f in base.rglob("*"):
                try:
                    if f.is_file():
                        self.enfileirar_backup(f)
                except Exception:
                    pass
        except Exception:
            pass

    def _backup_inicial_automatico(self):
        try:
            if getattr(self, "ftp_enabled_var", None) and self.ftp_enabled_var.get():
                self.executar_thread(self.sincronizar_tudo_ftp)
        except Exception:
            pass

    def sincronizar_tudo_ftp(self):
        """
        Enfileira TUDO que foi usado/feito para o FTP: o próprio aplicativo,
        as pastas de trabalho (logs, downloads, checkpoints, sessões, imagens),
        os arquivos de configuração e os arquivos selecionados/baixados.
        """
        try:
            if not getattr(self, "ftp_enabled_var", None) or not self.ftp_enabled_var.get():
                return
            self.msg("ftp_status", True, "enfileirando tudo para envio...")
            for d in (LOG_DIR, DOWNLOAD_DIR, TASK_STATE_DIR, SESSION_EXPORT_DIR, CLIPBOARD_DIR):
                self.enfileirar_pasta(d)
            for a in (
                DRAFT_FILE, INJECTIONS_FILE, PROMPT_PRESETS_FILE, COMPLETED_HISTORY_FILE,
                PREFERENCES_FILE, FUSION_FILE, OTHER_AI_PROVIDERS_FILE, Path(__file__),
            ):
                try:
                    if Path(a).exists():
                        self.enfileirar_backup(a)
                except Exception:
                    pass
            for p in (
                list(getattr(self, "selected_files", []))
                + list(getattr(self, "downloaded_files", []))
                + list(getattr(self, "reply_files", []))
            ):
                self.enfileirar_backup(p)
            self._ultimo_backup_full = time.time()
            self.msg("log", "[FTP] Sincronização completa enfileirada para o servidor.\n")
        except Exception as e:
            self.msg("log", f"[FTP/ERRO] {e}\n")

    def testar_ftp(self):
        """Testa a conexão com o servidor FTP/FTPS."""
        def worker():
            try:
                fb = FTPBackup()
                fb.conectar()
                fb.fechar()
                self.msg("ftp_status", True, "conexão testada com sucesso")
                self.msg("log", f"[FTP] Conexão OK com {FTP_HOST} (pasta /{FTP_REMOTE_BASE}).\n")
            except Exception as e:
                self.msg("ftp_status", False, f"falha no teste: {resumo_texto(str(e), 80)}")
                self.msg("log", f"[FTP/ERRO] Não foi possível conectar: {e}\n")
        self.executar_thread(worker)

    def _ftp_worker(self):
        """Thread em segundo plano que envia os arquivos enfileirados para o FTP."""
        while True:
            try:
                job = self.ftp_queue.get()
            except Exception:
                return
            if not job:
                continue
            local, rel = job
            enviado = False
            ultimo_erro = None
            for _tentativa in range(2):
                try:
                    if self._ftp_backup is None:
                        self._ftp_backup = FTPBackup()
                        self._ftp_backup.conectar()
                    self._ftp_backup.enviar(local, rel)
                    enviado = True
                    break
                except Exception as e:
                    ultimo_erro = e
                    try:
                        if self._ftp_backup:
                            self._ftp_backup.fechar()
                    except Exception:
                        pass
                    self._ftp_backup = None
                    time.sleep(1.0)
            if enviado:
                self.msg("ftp_status", True, rel)
            else:
                self.msg("ftp_status", False, f"{rel} ({resumo_texto(str(ultimo_erro), 60)})")
            try:
                self.ftp_queue.task_done()
            except Exception:
                pass

    # ---------- Cache/persistência MySQL ----------

    def mysql_ativo(self) -> bool:
        try:
            return MYSQL_DISPONIVEL and bool(self.mysql_enabled_var.get())
        except Exception:
            return False

    def inicializar_mysql_bg(self):
        """Cria/verifica tabelas em segundo plano ao abrir o app."""
        if not MYSQL_DISPONIVEL:
            return
        def worker():
            try:
                self._mysql.inicializar()
                self.msg("mysql_status", True, "tabelas verificadas/criadas")
                self.msg("log", f"[MYSQL] Conectado a {MYSQL_HOST}/{MYSQL_DB}. Tabelas prontas.\n")
            except Exception as e:
                self.msg("mysql_status", False, str(e))
        self.executar_thread(worker)

    def testar_mysql(self):
        """Testa a conexão MySQL e garante as tabelas/colunas."""
        if not MYSQL_DISPONIVEL:
            messagebox.showinfo(
                "MySQL",
                "O driver PyMySQL não está instalado.\n\n"
                "Instale com:\npython -m pip install PyMySQL\n\n"
                "(ou rode 01_instalar_dependencias.bat)",
            )
            return
        def worker():
            try:
                self._mysql.inicializar()
                self.msg("mysql_status", True, "conexão OK e tabelas prontas")
                self.msg("log", f"[MYSQL] Conexão OK com {MYSQL_HOST}/{MYSQL_DB}.\n")
            except Exception as e:
                self.msg("mysql_status", False, str(e))
                self.msg("log", f"[MYSQL/ERRO] {e}\n")
        self.executar_thread(worker)

    def mysql_buscar(self, agent_profile: str, prompt: str) -> Optional[str]:
        try:
            if self.mysql_ativo() and bool(self.mysql_lookup_var.get()):
                return self._mysql.buscar_resposta(agent_profile, prompt)
        except Exception as e:
            try:
                self.msg("log", f"[MYSQL] Falha ao buscar no cache: {e}\n")
            except Exception:
                pass
        return None

    def mysql_salvar(self, agent_profile: str, prompt: str, response: str, source: str = "manus_api"):
        try:
            if self.mysql_ativo():
                self._mysql.salvar_resposta(agent_profile, prompt, response, source)
        except Exception:
            pass

    def mysql_conversa(self, task_id: str, role: str, content: str):
        try:
            if self.mysql_ativo():
                self._mysql.registrar_conversa(task_id, role, content)
        except Exception:
            pass

    def construir_aba_turbo(self):
        """Monta a Central Avançada. Isolada: não interfere nas demais abas."""
        # A aba é ROLÁVEL: um Canvas + barra de rolagem garantem que todas as
        # seções e botões fiquem acessíveis em qualquer tamanho de tela/resolução.
        outer = self.turbo_tab
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        canvas = tk.Canvas(outer, highlightthickness=0, borderwidth=0)
        canvas.configure(background=getattr(self, "_tema_text_bg", "#FFFFFF"))
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        tab = ttk.Frame(canvas, padding=(0, 0, 10, 0))
        _janela_inner = canvas.create_window((0, 0), window=tab, anchor="nw")

        def _ajustar_scrollregion(_e=None):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
            except Exception:
                pass

        def _ajustar_largura(e):
            try:
                canvas.itemconfigure(_janela_inner, width=e.width)
            except Exception:
                pass

        tab.bind("<Configure>", _ajustar_scrollregion)
        canvas.bind("<Configure>", _ajustar_largura)

        def _scroll_mouse(e):
            try:
                num = getattr(e, "num", None)
                if num == 4:
                    canvas.yview_scroll(-3, "units")
                elif num == 5:
                    canvas.yview_scroll(3, "units")
                else:
                    canvas.yview_scroll(int(-1 * (e.delta / 120)) * 3, "units")
            except Exception:
                pass

        def _ativar_scroll(_e=None):
            try:
                canvas.bind_all("<MouseWheel>", _scroll_mouse)
                canvas.bind_all("<Button-4>", _scroll_mouse)
                canvas.bind_all("<Button-5>", _scroll_mouse)
            except Exception:
                pass

        def _desativar_scroll(_e=None):
            try:
                canvas.unbind_all("<MouseWheel>")
                canvas.unbind_all("<Button-4>")
                canvas.unbind_all("<Button-5>")
            except Exception:
                pass

        canvas.bind("<Enter>", _ativar_scroll)
        canvas.bind("<Leave>", _desativar_scroll)
        tab.bind("<Enter>", _ativar_scroll)

        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=1)

        # --- Modos avançados ---
        modos = ttk.LabelFrame(tab, text="Modos avançados (tempo real, furtivo, IA preferencial)", padding=10)
        modos.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Checkbutton(modos, text="Modo Turbo (tempo real / atualizações instantâneas)", variable=self.turbo_var, command=self.aplicar_turbo).grid(row=0, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(modos, textvariable=self.turbo_status_var, style="Status.TLabel").grid(row=0, column=1, sticky="w", padx=10)
        ttk.Checkbutton(modos, text="Modo Furtivo (privacidade total, sem logs em arquivo)", variable=self.stealth_var, command=self.aplicar_modo_furtivo).grid(row=1, column=0, sticky="w", padx=4, pady=2)
        ttk.Label(modos, textvariable=self.stealth_status_var, style="Status.TLabel").grid(row=1, column=1, sticky="w", padx=10)
        ttk.Checkbutton(modos, text="Manter Manus como IA preferencial", variable=self.prefer_manus_var).grid(row=2, column=0, sticky="w", padx=4, pady=2)
        ttk.Checkbutton(modos, text="Usar sempre o MELHOR modelo da IA (manus-1.6-max)", variable=self.best_model_var).grid(row=2, column=1, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(modos, text="Bip sonoro ao concluir a tarefa", variable=self.bip_var).grid(row=3, column=0, sticky="w", padx=4, pady=2)
        ttk.Checkbutton(modos, text="Auto-rolagem das respostas/logs em tempo real", variable=self.autoscroll_var).grid(row=4, column=0, sticky="w", padx=4, pady=2)

        # --- Injeção ---
        inj = ttk.LabelFrame(tab, text="Modos de Injeção (preâmbulo de sistema / contexto no prompt)", padding=10)
        inj.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))
        inj.columnconfigure(0, weight=1)
        inj.rowconfigure(2, weight=1)
        ttk.Checkbutton(
            inj,
            text="Ativar injeção do preâmbulo ao INICIAR TAREFA",
            variable=self.injection_enabled_var,
            command=lambda: self.injection_status_var.set("Injeção: ATIVADA" if self.injection_enabled_var.get() else "Injeção: desativada"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(inj, textvariable=self.injection_status_var, style="Status.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 6))
        self.injection_text = ScrolledText(inj, height=7, wrap="word")
        self.injection_text.grid(row=2, column=0, sticky="nsew")
        linha_inj = ttk.Frame(inj)
        linha_inj.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        linha_inj.columnconfigure(1, weight=1)
        ttk.Label(linha_inj, text="Nome:").grid(row=0, column=0)
        ttk.Entry(linha_inj, textvariable=self.injection_name_var).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(linha_inj, text="Salvar injeção", command=self.salvar_injecao_atual).grid(row=0, column=2, padx=2)
        self.lista_injecoes = tk.Listbox(inj, height=5)
        self.lista_injecoes.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        botoes_inj = ttk.Frame(inj)
        botoes_inj.grid(row=5, column=0, sticky="ew", pady=(4, 0))
        ttk.Button(botoes_inj, text="Aplicar selecionada", command=self.aplicar_injecao_selecionada).pack(side="left")
        ttk.Button(botoes_inj, text="Remover", command=self.remover_injecao_selecionada).pack(side="left", padx=6)
        ttk.Label(inj, textvariable=self.injection_presets_status_var, style="Status.TLabel").grid(row=6, column=0, sticky="w", pady=(4, 0))

        # --- Outras IAs / Multi-IA ---
        ia = ttk.LabelFrame(tab, text="Outras IAs (a Manus é a preferencial) - presets e comparação", padding=10)
        ia.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(0, 8))
        ia.columnconfigure(0, weight=1)
        ttk.Label(ia, text="Preencher rapidamente um provedor compatível com OpenAI:", style="Status.TLabel").grid(row=0, column=0, sticky="w")
        presets_frame = ttk.Frame(ia)
        presets_frame.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        col = 0
        rowp = 0
        for preset in PROVEDORES_IA_PRESETS:
            ttk.Button(presets_frame, text=preset["name"], command=lambda p=preset: self.preencher_provedor_preset(p)).grid(row=rowp, column=col, sticky="ew", padx=3, pady=3)
            col += 1
            if col >= 3:
                col = 0
                rowp += 1
        ttk.Button(ia, text="Enviar para Manus (IA preferencial)", command=self.enviar_para_manus_preferencial).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(ia, text="Enviar prompt para a outra IA selecionada", command=self.enviar_prompt_para_outra_ia).grid(row=3, column=0, sticky="ew", pady=2)
        ttk.Button(ia, text="Comparar prompt em VÁRIAS IAs", command=self.comparar_em_varias_ias).grid(row=4, column=0, sticky="ew", pady=2)
        ttk.Label(ia, textvariable=self.multi_ia_status_var, style="Status.TLabel").grid(row=5, column=0, sticky="w", pady=(6, 0))

        # --- Ferramentas de prompt e presets ---
        fer = ttk.LabelFrame(tab, text="Ferramentas de prompt e presets", padding=10)
        fer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        fer.columnconfigure(6, weight=1)
        ttk.Button(fer, text="Contar palavras/tokens", command=self.contar_metricas_prompt).grid(row=0, column=0, padx=2)
        ttk.Button(fer, text="MAIÚSCULAS", command=lambda: self._transformar_prompt("maiusc")).grid(row=0, column=1, padx=2)
        ttk.Button(fer, text="minúsculas", command=lambda: self._transformar_prompt("minusc")).grid(row=0, column=2, padx=2)
        ttk.Button(fer, text="Limpar espaços", command=lambda: self._transformar_prompt("limpar")).grid(row=0, column=3, padx=2)
        ttk.Label(fer, textvariable=self.prompt_metrics_var, style="Status.TLabel").grid(row=0, column=6, sticky="e")
        linha_pp = ttk.Frame(fer)
        linha_pp.grid(row=1, column=0, columnspan=7, sticky="ew", pady=(8, 0))
        linha_pp.columnconfigure(1, weight=1)
        ttk.Label(linha_pp, text="Preset:").grid(row=0, column=0)
        ttk.Entry(linha_pp, textvariable=self.prompt_preset_name_var).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(linha_pp, text="Salvar prompt como preset", command=self.salvar_prompt_preset).grid(row=0, column=2, padx=2)
        self.lista_prompt_presets = tk.Listbox(fer, height=5)
        self.lista_prompt_presets.grid(row=2, column=0, columnspan=7, sticky="ew", pady=(6, 0))
        botoes_pp = ttk.Frame(fer)
        botoes_pp.grid(row=3, column=0, columnspan=7, sticky="ew", pady=(4, 0))
        ttk.Button(botoes_pp, text="Aplicar preset no prompt", command=self.aplicar_prompt_preset).pack(side="left")
        ttk.Button(botoes_pp, text="Remover preset", command=self.remover_prompt_preset).pack(side="left", padx=6)
        ttk.Label(fer, textvariable=self.prompt_presets_status_var, style="Status.TLabel").grid(row=4, column=0, columnspan=7, sticky="w", pady=(4, 0))

        # --- Fusão de chaves Manus ---
        fus = ttk.LabelFrame(tab, text="Fusão de chaves Manus (créditos somados + uso em cadeia automática)", padding=10)
        fus.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        fus.columnconfigure(0, weight=1)
        ttk.Label(
            fus,
            text=("Selecione 2 ou mais chaves cadastradas e clique em 'Fundir selecionadas'. Elas passam a funcionar como UMA só: "
                  "o crédito é somado e, quando uma esgota, o app usa a próxima automaticamente, sem parar por 'crédito acabou'. "
                  "Só quando TODAS do pool acabarem é que ele pede uma nova chave."),
            style="Status.TLabel",
            wraplength=920,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        self.lista_fusao = tk.Listbox(fus, height=5, selectmode="extended", exportselection=False)
        self.lista_fusao.grid(row=1, column=0, sticky="ew", pady=(6, 4))
        ttk.Checkbutton(
            fus,
            text="Ativar chave fundida (usar o pool em cadeia, sem parar por crédito)",
            variable=self.fusion_enabled_var,
            command=self.aplicar_fusao,
        ).grid(row=2, column=0, sticky="w")
        linha_fus = ttk.Frame(fus)
        linha_fus.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(linha_fus, text="Fundir selecionadas", command=self.fundir_chaves_selecionadas).pack(side="left")
        ttk.Button(linha_fus, text="Atualizar lista", command=self.atualizar_lista_fusao).pack(side="left", padx=6)
        ttk.Button(linha_fus, text="Consultar créditos somados", command=self.consultar_creditos_fundidos).pack(side="left", padx=6)
        ttk.Button(linha_fus, text="Desfazer fusão", command=self.desfazer_fusao).pack(side="left", padx=6)
        ttk.Label(fus, textvariable=self.fusion_status_var, style="Status.TLabel").grid(row=4, column=0, sticky="w", pady=(6, 0))
        ttk.Label(fus, textvariable=self.fused_credits_var, style="Success.TLabel").grid(row=5, column=0, sticky="w")

        # --- Backup automático FTP (FTPS) ---
        ftpf = ttk.LabelFrame(tab, text="Backup automático FTP (FTPS) - envia tudo para o seu servidor", padding=10)
        ftpf.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ftpf.columnconfigure(0, weight=1)
        ttk.Label(
            ftpf,
            text=f"Servidor: {FTP_HOST}   |   Usuário: {FTP_USER}   |   Senha: ******   |   Pasta remota: /{FTP_REMOTE_BASE}",
            style="Status.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            ftpf,
            text=("Envia automaticamente: o próprio aplicativo, downloads, checkpoints, sessões exportadas, "
                  "imagens coladas, presets, injeções e arquivos usados. Funciona em segundo plano."),
            style="Status.TLabel",
            wraplength=920,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(2, 4))
        ttk.Checkbutton(
            ftpf,
            text="Backup automático ativado",
            variable=self.ftp_enabled_var,
            command=lambda: self.ftp_status_var.set("Backup FTP: ativado" if self.ftp_enabled_var.get() else "Backup FTP: desativado"),
        ).grid(row=2, column=0, sticky="w")
        linha_ftp = ttk.Frame(ftpf)
        linha_ftp.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(linha_ftp, text="Enviar TUDO agora para o FTP", command=lambda: self.executar_thread(self.sincronizar_tudo_ftp)).pack(side="left")
        ttk.Button(linha_ftp, text="Testar conexão FTP", command=self.testar_ftp).pack(side="left", padx=6)
        ttk.Label(ftpf, textvariable=self.ftp_status_var, style="Status.TLabel").grid(row=4, column=0, sticky="w", pady=(6, 0))

        # --- Cache / persistência MySQL ---
        myf = ttk.LabelFrame(tab, text="Cache MySQL (busca a resposta no banco antes de usar a API)", padding=10)
        myf.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        myf.columnconfigure(0, weight=1)
        ttk.Label(
            myf,
            text=f"Servidor: {MYSQL_HOST}   |   Banco/Usuário: {MYSQL_DB}   |   Senha: ******",
            style="Status.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            myf,
            text=("Salva automaticamente tudo (prompt, conversas e respostas). Antes de chamar a API, procura a "
                  "solução no MySQL; se já existir, responde do banco sem gastar API. Tabelas e colunas são criadas "
                  "automaticamente."),
            style="Status.TLabel",
            wraplength=920,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(2, 4))
        ttk.Checkbutton(myf, text="Salvar/persistir no MySQL automaticamente", variable=self.mysql_enabled_var).grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(myf, text="Responder do MySQL quando já existir (antes da API)", variable=self.mysql_lookup_var).grid(row=3, column=0, sticky="w")
        linha_my = ttk.Frame(myf)
        linha_my.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(linha_my, text="Testar conexão / criar tabelas", command=self.testar_mysql).pack(side="left")
        ttk.Label(myf, textvariable=self.mysql_status_var, style="Status.TLabel").grid(row=5, column=0, sticky="w", pady=(6, 0))

        # --- Sobre ---
        info = ttk.LabelFrame(tab, text="Sobre esta central", padding=10)
        info.grid(row=6, column=0, columnspan=2, sticky="nsew")
        ttk.Label(
            info,
            text="Tudo aqui é adicional e não interfere nas funções nativas. A Manus permanece como a IA principal do app.",
            style="Status.TLabel",
        ).pack(anchor="w")

        try:
            self.atualizar_lista_injecoes()
            self.atualizar_lista_prompt_presets()
            self.atualizar_lista_fusao()
        except Exception:
            pass

    # ===================================================================
    # ===================== ESTÚDIO DE OUTRAS IAs =======================
    # ===================================================================

    def _estudio_carregar_tarefas_disco(self) -> List[Dict[str, Any]]:
        data = ler_json_seguro(ESTUDIO_TAREFAS_FILE, [])
        if isinstance(data, dict):
            data = data.get("tarefas") or []
        return data if isinstance(data, list) else []

    def _estudio_salvar_tarefas(self):
        try:
            escrever_json_atomico(ESTUDIO_TAREFAS_FILE, {"updated_at": agora_iso(), "tarefas": self.estudio_tarefas[-200:]})
        except Exception:
            pass

    def _estudio_eh_anthropic(self) -> bool:
        try:
            tipo = str(self.other_ai_type_var.get() or "").lower()
            base = str(self.other_ai_base_url_var.get() or "").lower()
            return ("anthropic" in tipo) or ("anthropic.com" in base)
        except Exception:
            return False

    def estudio_atualizar_info(self):
        try:
            self.estudio_info_var.set(
                f"Provedor: {self.other_ai_name_var.get()}  |  Modelo: {self.other_ai_model_var.get()}  |  {self.other_ai_base_url_var.get()}"
            )
        except Exception:
            pass

    def estudio_atualizar_label_anexos(self):
        try:
            if not self.estudio_anexos:
                self.estudio_anexos_var.set("Nenhum anexo.")
                return
            nomes = ", ".join(p.name for p in self.estudio_anexos)
            self.estudio_anexos_var.set(f"{len(self.estudio_anexos)} anexo(s): {resumo_texto(nomes, 90)}")
        except Exception:
            pass

    def estudio_anexar_arquivos(self):
        paths = filedialog.askopenfilenames(title="Anexar arquivos para enviar à IA", filetypes=[("Todos os arquivos", "*.*")])
        if not paths:
            return
        existentes = {str(p.resolve()).lower() for p in self.estudio_anexos}
        for item in paths:
            p = Path(item)
            if str(p.resolve()).lower() not in existentes:
                self.estudio_anexos.append(p)
                existentes.add(str(p.resolve()).lower())
        self.estudio_atualizar_label_anexos()

    def estudio_colar_imagem(self):
        try:
            novos = self.capturar_imagens_clipboard()
        except RuntimeError as e:
            messagebox.showinfo("Colar imagem", str(e))
            return
        for p in novos:
            self.estudio_anexos.append(p)
        self.estudio_atualizar_label_anexos()
        self.estudio_status_var.set(f"{len(novos)} imagem(ns) colada(s) como anexo.")

    def estudio_colar_texto(self):
        try:
            txt = self.clipboard_get()
        except Exception:
            txt = ""
        if not txt:
            messagebox.showinfo("Colar texto", "Não há texto na área de transferência.")
            return
        try:
            self.estudio_prompt_text.insert("end", txt)
        except Exception:
            pass

    def estudio_limpar_anexos(self):
        self.estudio_anexos = []
        self.estudio_atualizar_label_anexos()

    def _estudio_montar_conteudo_usuario(self, prompt: str):
        partes_texto = [prompt] if prompt else []
        imagens = []
        for p in self.estudio_anexos:
            try:
                ext = p.suffix.lower()
                if ext in IMAGE_EXTS:
                    b = p.read_bytes()
                    mime = mimetypes.guess_type(str(p))[0] or "image/png"
                    data_url = f"data:{mime};base64," + base64.b64encode(b).decode("ascii")
                    imagens.append(data_url)
                else:
                    try:
                        txt = p.read_text(encoding="utf-8", errors="ignore")[:100000]
                        partes_texto.append(f"\n[ARQUIVO ANEXADO: {p.name}]\n{txt}")
                    except Exception:
                        partes_texto.append(f"\n[ARQUIVO ANEXADO: {p.name}] (binário não incluído como texto)")
            except Exception:
                pass
        texto_final = "\n".join(partes_texto).strip()
        if imagens and not self._estudio_eh_anthropic():
            content = [{"type": "text", "text": texto_final}]
            for du in imagens:
                content.append({"type": "image_url", "image_url": {"url": du}})
            return content
        if imagens and self._estudio_eh_anthropic():
            self.estudio_status_var.set("Aviso: imagens não são enviadas no modo Anthropic deste app; enviando só o texto.")
        return texto_final

    def estudio_iniciar_tarefa(self):
        self._estudio_enviar(continuar=False)

    def estudio_continuar_conversa(self):
        if not self.estudio_tarefa_atual:
            messagebox.showinfo("Continuar", "Não há tarefa atual. Use 'Iniciar tarefa' ou carregue uma tarefa existente.")
            return
        self._estudio_enviar(continuar=True)

    def estudio_nova_conversa(self):
        self.estudio_tarefa_atual = {}
        self.estudio_ultima_resposta = ""
        try:
            self.estudio_resposta_text.delete("1.0", "end")
        except Exception:
            pass
        self.estudio_status_var.set("Nova conversa iniciada (vazia).")

    def _estudio_enviar(self, continuar: bool = False):
        try:
            prompt = self.estudio_prompt_text.get("1.0", "end").strip()
        except Exception:
            prompt = ""
        if not prompt and not self.estudio_anexos:
            messagebox.showinfo("Estúdio", "Escreva um prompt ou anexe um arquivo antes de enviar.")
            return
        try:
            cliente = self.cliente_outra_ia_atual()
        except Exception as e:
            messagebox.showerror(
                "Provedor não configurado",
                "Configure o provedor e a APIKEY na aba 'Outras IAs / APIs' primeiro.\n\n" + str(e),
            )
            return

        self.estudio_atualizar_info()
        conteudo = self._estudio_montar_conteudo_usuario(prompt)

        if not continuar or not self.estudio_tarefa_atual:
            tid = f"tarefa_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.estudio_tarefas) + 1}"
            self.estudio_tarefa_atual = {
                "id": tid,
                "criado_em": agora_iso(),
                "provider": cliente.name,
                "model": cliente.model,
                "titulo": resumo_texto(prompt, 50) or "Tarefa IA",
                "messages": [{"role": "system", "content": "Você é uma IA auxiliar dentro de um app profissional. Responda de forma clara, útil e objetiva."}],
            }
            self.estudio_tarefas.append(self.estudio_tarefa_atual)

        self.estudio_tarefa_atual.setdefault("messages", []).append({"role": "user", "content": conteudo})
        self._estudio_salvar_tarefas()

        msgs = list(self.estudio_tarefa_atual["messages"])
        try:
            temp = float(self.other_ai_temp_var.get() or "0.4")
        except Exception:
            temp = 0.4
        try:
            maxt = int(float(self.other_ai_max_tokens_var.get() or "2048"))
        except Exception:
            maxt = 2048

        # Consome anexos e limpa o prompt da caixa (a conversa já guarda tudo).
        self.estudio_anexos = []
        self.estudio_atualizar_label_anexos()
        try:
            self.estudio_prompt_text.delete("1.0", "end")
        except Exception:
            pass
        self.estudio_render_transcript()
        self.estudio_status_var.set(f"Enviando para {cliente.name} ({cliente.model})...")

        def worker():
            try:
                data = cliente.chat_mensagens(msgs, temperature=temp, max_tokens=maxt, timeout=300)
                texto = OtherAIClient.extrair_texto(data)
                self.msg("estudio_resposta", texto, cliente.name)
            except Exception as e:
                self.msg("estudio_resposta_erro", str(e), cliente.name)

        self.executar_thread(worker)

    def estudio_render_transcript(self):
        try:
            self.estudio_resposta_text.delete("1.0", "end")
            for m in (self.estudio_tarefa_atual.get("messages", []) if self.estudio_tarefa_atual else []):
                role = m.get("role")
                if role == "system":
                    continue
                cont = m.get("content")
                if isinstance(cont, list):
                    textos = []
                    for b in cont:
                        if isinstance(b, dict):
                            if b.get("type") == "text":
                                textos.append(str(b.get("text") or ""))
                            elif b.get("type") == "image_url":
                                textos.append("[imagem anexada]")
                    cont = "\n".join(textos)
                etiqueta = "VOCÊ" if role == "user" else "IA"
                self.estudio_resposta_text.insert("end", f"\n===== {etiqueta} =====\n{cont}\n")
            self.estudio_resposta_text.see("end")
        except Exception:
            pass

    def estudio_salvar_resposta(self):
        if not self.estudio_ultima_resposta.strip():
            messagebox.showinfo("Salvar resposta", "Não há resposta para salvar ainda.")
            return
        try:
            ESTUDIO_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            destino = caminho_unico(ESTUDIO_DOWNLOAD_DIR / ("resposta_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"))
            destino.write_text(self.estudio_ultima_resposta, encoding="utf-8")
            self.estudio_status_var.set(f"Resposta salva em: {destino}")
            self.enfileirar_backup(destino)
            messagebox.showinfo("Salvar resposta", f"Resposta salva em:\n{destino}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def estudio_baixar_arquivos_resposta(self, silencioso: bool = False):
        texto = self.estudio_ultima_resposta or ""
        urls = extrair_urls_baixaveis(texto)
        if not urls:
            if not silencioso:
                messagebox.showinfo("Baixar arquivos", "Nenhum link de arquivo encontrado na última resposta.")
            return

        def worker():
            ESTUDIO_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            for url in urls:
                try:
                    fname = nome_seguro(filename_from_url(url), 160)
                    destino = baixar_url(url, ESTUDIO_DOWNLOAD_DIR / fname, cb=lambda m: self.msg("log", f"[ESTÚDIO/DOWNLOAD] {m}\n"))
                    self.msg("estudio_download", str(destino))
                except Exception as e:
                    self.msg("log", f"[ESTÚDIO/DOWNLOAD ERRO] {url}: {e}\n")

        self.executar_thread(worker)

    def estudio_abrir_downloads(self):
        try:
            ESTUDIO_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            os.startfile(str(ESTUDIO_DOWNLOAD_DIR.resolve()))
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def estudio_ver_creditos(self):
        try:
            cliente = self.cliente_outra_ia_atual()
        except Exception as e:
            messagebox.showerror("Provedor", "Configure o provedor/chave na aba 'Outras IAs / APIs'.\n\n" + str(e))
            return
        base = cliente.base_url
        self.estudio_status_var.set("Consultando créditos/uso...")

        def worker():
            try:
                if "openrouter.ai" in base.lower():
                    r = HTTP_SESSION.get(base.rstrip("/") + "/auth/key", headers={"Authorization": "Bearer " + cliente.api_key}, timeout=30)
                    d = r.json()
                    info = d.get("data") if isinstance(d, dict) else d
                    self.msg("estudio_status", f"Créditos OpenRouter: {json.dumps(info, ensure_ascii=False)[:300]}")
                else:
                    # Sem endpoint padrão de créditos: valida a chave listando modelos.
                    self._buscar_modelos_provedor()
                    self.msg("estudio_status", "Este provedor não expõe créditos de forma padrão. Validei a chave listando os modelos.")
            except Exception as e:
                self.msg("estudio_status", f"Não foi possível consultar créditos: {resumo_texto(str(e), 100)}")

        self.executar_thread(worker)

    def estudio_carregar_tarefas(self):
        janela = tk.Toplevel(self)
        janela.title("Tarefas já feitas (Estúdio de Outras IAs)")
        janela.geometry("760x460")
        janela.transient(self)
        janela.columnconfigure(0, weight=1)
        janela.rowconfigure(0, weight=1)

        lb = tk.Listbox(janela)
        lb.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        sb = ttk.Scrollbar(janela, orient="vertical", command=lb.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=10)
        lb.configure(yscrollcommand=sb.set)

        ordenadas = list(reversed(self.estudio_tarefas))
        for t in ordenadas:
            lb.insert("end", f"{t.get('criado_em','')} | {t.get('provider','')} | {t.get('titulo','(sem título)')}")

        def continuar():
            sel = list(lb.curselection())
            if not sel:
                return
            self.estudio_tarefa_atual = ordenadas[sel[0]]
            self.estudio_ultima_resposta = ""
            for m in reversed(self.estudio_tarefa_atual.get("messages", [])):
                if m.get("role") == "assistant" and isinstance(m.get("content"), str):
                    self.estudio_ultima_resposta = m["content"]
                    break
            self.estudio_render_transcript()
            self.estudio_status_var.set(f"Tarefa carregada: {self.estudio_tarefa_atual.get('titulo','')}. Use 'Continuar conversa'.")
            janela.destroy()

        botoes = ttk.Frame(janela, padding=(10, 0, 10, 10))
        botoes.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Button(botoes, text="Continuar nesta tarefa", command=continuar).pack(side="left")
        ttk.Button(botoes, text="Fechar", command=janela.destroy).pack(side="right")

    def construir_aba_estudio_ia(self):
        """Estúdio completo das outras IAs: prompt, anexos, histórico, downloads, etc."""
        outer = self.estudio_tab
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        canvas = tk.Canvas(outer, highlightthickness=0, borderwidth=0)
        canvas.configure(background=getattr(self, "_tema_text_bg", "#FFFFFF"))
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tab = ttk.Frame(canvas, padding=(0, 0, 10, 0))
        _jin = canvas.create_window((0, 0), window=tab, anchor="nw")
        tab.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(_jin, width=e.width))

        def _wheel(e):
            try:
                canvas.yview_scroll(int(-1 * (e.delta / 120)) * 3, "units")
            except Exception:
                pass
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        tab.columnconfigure(0, weight=1)

        # Barra superior: provedor/modelo + ações
        topo = ttk.LabelFrame(tab, text="Provedor / Modelo (configure a chave na aba 'Outras IAs / APIs')", padding=10)
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        topo.columnconfigure(0, weight=1)
        ttk.Label(topo, textvariable=self.estudio_info_var, style="Status.TLabel").grid(row=0, column=0, columnspan=6, sticky="w")
        ttk.Label(topo, text="Modelo:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.estudio_model_combo = ttk.Combobox(topo, textvariable=self.other_ai_model_var, values=OUTRAS_IA_MODELOS, state="normal", width=40)
        self.estudio_model_combo.grid(row=1, column=1, sticky="w", padx=6, pady=(6, 0))
        ttk.Button(topo, text="Mudar/atualizar modelos da API", command=self._buscar_modelos_provedor).grid(row=1, column=2, padx=4, pady=(6, 0))
        ttk.Button(topo, text="Ver créditos", command=self.estudio_ver_creditos).grid(row=1, column=3, padx=4, pady=(6, 0))
        ttk.Button(topo, text="Config. do provedor", command=lambda: self.notebook.select(self.other_ai_tab)).grid(row=1, column=4, padx=4, pady=(6, 0))

        # Prompt + anexos
        prompt_box = ttk.LabelFrame(tab, text="Prompt para a outra IA", padding=10)
        prompt_box.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        prompt_box.columnconfigure(0, weight=1)
        self.estudio_prompt_text = ScrolledText(prompt_box, height=8, wrap="word")
        self.estudio_prompt_text.grid(row=0, column=0, sticky="nsew")
        anexos_linha = ttk.Frame(prompt_box)
        anexos_linha.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(anexos_linha, text="Anexar arquivos", command=self.estudio_anexar_arquivos).pack(side="left", padx=(0, 6))
        ttk.Button(anexos_linha, text="Colar imagem", command=self.estudio_colar_imagem).pack(side="left", padx=6)
        ttk.Button(anexos_linha, text="Colar texto", command=self.estudio_colar_texto).pack(side="left", padx=6)
        ttk.Button(anexos_linha, text="Limpar anexos", command=self.estudio_limpar_anexos).pack(side="left", padx=6)
        ttk.Label(prompt_box, textvariable=self.estudio_anexos_var, style="Status.TLabel").grid(row=2, column=0, sticky="w", pady=(4, 0))

        # Ações principais
        acoes = ttk.Frame(tab)
        acoes.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(acoes, text="INICIAR TAREFA", command=self.estudio_iniciar_tarefa).pack(side="left", padx=(0, 6))
        ttk.Button(acoes, text="Continuar conversa", command=self.estudio_continuar_conversa).pack(side="left", padx=6)
        ttk.Button(acoes, text="Nova conversa", command=self.estudio_nova_conversa).pack(side="left", padx=6)
        ttk.Button(acoes, text="Carregar tarefas feitas", command=self.estudio_carregar_tarefas).pack(side="left", padx=6)
        ttk.Button(acoes, text="Logs", command=self.abrir_pasta_logs).pack(side="left", padx=6)
        ttk.Button(acoes, text="Abrir pasta de downloads", command=self.estudio_abrir_downloads).pack(side="left", padx=6)

        # Resposta
        resp_box = ttk.LabelFrame(tab, text="Resposta / Conversa", padding=10)
        resp_box.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        resp_box.columnconfigure(0, weight=1)
        self.estudio_resposta_text = ScrolledText(resp_box, height=14, wrap="word")
        self.estudio_resposta_text.grid(row=0, column=0, sticky="nsew")
        resp_linha = ttk.Frame(resp_box)
        resp_linha.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(resp_linha, text="Salvar resposta", command=self.estudio_salvar_resposta).pack(side="left", padx=(0, 6))
        ttk.Button(resp_linha, text="Baixar arquivos da resposta", command=lambda: self.estudio_baixar_arquivos_resposta(silencioso=False)).pack(side="left", padx=6)

        # Downloads recebidos
        dl_box = ttk.LabelFrame(tab, text="Arquivos baixados (do que a IA pediu/entregou)", padding=10)
        dl_box.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        dl_box.columnconfigure(0, weight=1)
        self.estudio_downloads_list = tk.Listbox(dl_box, height=5)
        self.estudio_downloads_list.grid(row=0, column=0, sticky="ew")
        dl_botoes = ttk.Frame(dl_box)
        dl_botoes.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(dl_botoes, text="Abrir arquivo", command=self.estudio_abrir_arquivo_baixado).pack(side="left", padx=(0, 6))
        ttk.Button(dl_botoes, text="Abrir pasta", command=self.estudio_abrir_downloads).pack(side="left", padx=6)

        ttk.Label(tab, textvariable=self.estudio_status_var, style="Status.TLabel").grid(row=5, column=0, sticky="w", pady=(2, 0))

        self.estudio_atualizar_info()
        self.estudio_atualizar_label_anexos()

    def estudio_abrir_arquivo_baixado(self):
        try:
            sel = list(self.estudio_downloads_list.curselection())
            if not sel:
                return
            p = self.estudio_downloads[sel[0]]
            if Path(p).exists():
                os.startfile(str(p))
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def atualizar_lista_arquivos(self):
        self.files_list.delete(0, "end")
        total = 0
        for p in self.selected_files:
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            total += size
            exibicao = f"{p.name} | {tamanho_legivel(size)}" if self.privacy_var.get() else f"{p.name} | {tamanho_legivel(size)} | {p}"
            self.files_list.insert("end", exibicao)
        self.files_info_label.configure(text=f"{len(self.selected_files)} arquivo(s). Total: {tamanho_legivel(total)}" if self.selected_files else "Nenhum arquivo selecionado.")

    def adicionar_arquivos(self):
        paths = filedialog.askopenfilenames(title="Selecione qualquer arquivo para enviar ao Manus", filetypes=[("Todos os arquivos", "*.*")])
        if not paths:
            return
        existentes = {str(p.resolve()).lower() for p in self.selected_files}
        for item in paths:
            p = Path(item)
            chave = str(p.resolve()).lower()
            if chave not in existentes:
                self.selected_files.append(p)
                existentes.add(chave)
        self.atualizar_lista_arquivos()

    def remover_arquivo(self):
        for idx in reversed(list(self.files_list.curselection())):
            if 0 <= idx < len(self.selected_files):
                del self.selected_files[idx]
        self.atualizar_lista_arquivos()

    def limpar_arquivos(self):
        self.selected_files.clear()
        self.atualizar_lista_arquivos()

    def capturar_imagens_clipboard(self) -> List[Path]:
        """
        Lê a área de transferência e devolve uma lista de caminhos de imagem.

        Suporta dois casos:
        1) Uma imagem "bruta" (ex.: Print Screen / copiar imagem do navegador):
           salva como PNG em manus_imagens_coladas/.
        2) Arquivos de imagem copiados no explorador: usa os próprios caminhos.

        Levanta RuntimeError com mensagem amigável quando não há imagem.
        """
        if not PIL_DISPONIVEL:
            raise RuntimeError(
                "Para colar imagens da área de transferência é necessária a biblioteca Pillow.\n\n"
                "Instale com:\n"
                "python -m pip install Pillow\n\n"
                "(ou rode novamente o 01_instalar_dependencias.bat)"
            )

        try:
            conteudo = ImageGrab.grabclipboard()
        except Exception as e:
            raise RuntimeError(
                "Não foi possível ler a área de transferência.\n"
                f"Detalhe: {e}"
            )

        if conteudo is None:
            raise RuntimeError(
                "Não há imagem na área de transferência.\n\n"
                "Copie uma imagem (Print Screen, 'Copiar imagem' no navegador, "
                "ou copie um arquivo de imagem) e tente novamente."
            )

        CLIPBOARD_DIR.mkdir(exist_ok=True)
        salvos: List[Path] = []

        # Caso 2: lista de caminhos de arquivos copiados.
        if isinstance(conteudo, list):
            for item in conteudo:
                try:
                    p = Path(str(item))
                except Exception:
                    continue
                if p.exists() and p.suffix.lower() in IMAGE_EXTS:
                    salvos.append(p)
            if not salvos:
                raise RuntimeError(
                    "A área de transferência contém arquivos, mas nenhum é uma imagem reconhecida.\n"
                    f"Extensões aceitas: {', '.join(sorted(IMAGE_EXTS))}"
                )
            return salvos

        # Caso 1: imagem bruta (objeto PIL.Image) -> salva como PNG.
        nome = "colado_" + datetime.now().strftime("%d-%m-%Y_%H-%M-%S") + ".png"
        destino = caminho_unico(CLIPBOARD_DIR / nome)
        try:
            conteudo.save(destino, "PNG")
        except Exception as e:
            raise RuntimeError(f"Não foi possível salvar a imagem colada: {e}")
        salvos.append(destino)
        return salvos

    def colar_imagem_arquivos(self, event=None):
        """Cola imagem(ns) da área de transferência como anexo(s) da TAREFA."""
        try:
            novos = self.capturar_imagens_clipboard()
        except RuntimeError as e:
            messagebox.showinfo("Colar imagem", str(e))
            return
        existentes = {str(p.resolve()).lower() for p in self.selected_files}
        adicionados = 0
        for p in novos:
            chave = str(p.resolve()).lower()
            if chave not in existentes:
                self.selected_files.append(p)
                existentes.add(chave)
                adicionados += 1
        self.atualizar_lista_arquivos()
        self.log(f"[CLIPBOARD] {adicionados} imagem(ns) colada(s) e anexada(s) à tarefa.\n")
        try:
            for p in novos:
                self.enfileirar_backup(p)
        except Exception:
            pass
        try:
            self.salvar_checkpoint_tarefa("imagem colada anexada à tarefa")
        except Exception:
            pass
        return "break"

    def colar_imagem_resposta(self, event=None):
        """Cola imagem(ns) da área de transferência como anexo(s) da RESPOSTA ao Manus."""
        try:
            novos = self.capturar_imagens_clipboard()
        except RuntimeError as e:
            messagebox.showinfo("Colar imagem", str(e))
            return
        existentes = {str(p.resolve()).lower() for p in self.reply_files}
        adicionados = 0
        for p in novos:
            chave = str(p.resolve()).lower()
            if chave not in existentes:
                self.reply_files.append(p)
                existentes.add(chave)
                adicionados += 1
        self.atualizar_label_anexos_resposta()
        self.log(f"[CLIPBOARD] {adicionados} imagem(ns) colada(s) na resposta ao Manus.\n")
        return "break"

    def abrir_pasta_arquivo(self):
        sel = list(self.files_list.curselection())
        if not sel:
            return
        p = self.selected_files[sel[0]]
        os.startfile(str(p.parent))

    def abrir_pasta_logs(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(LOG_DIR))

    def abrir_pasta_downloads(self):
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(DOWNLOAD_DIR))

    def abrir_arquivo_baixado(self):
        sel = list(self.downloads_list.curselection())
        if not sel:
            return
        p = self.downloaded_files[sel[0]]
        if p.exists():
            os.startfile(str(p))

    def abrir_pasta_arquivo_baixado(self):
        sel = list(self.downloads_list.curselection())
        if not sel:
            return
        p = self.downloaded_files[sel[0]]
        os.startfile(str(p.parent))

    def solicitar_chave_por_credito(self, task_id: str = "", erro: str = ""):
        """
        Chamado quando a Manus retorna HTTP 429 / crédito ou limite.

        Fluxo seguro:
        1. Salva checkpoint local completo.
        2. Abre janela para o usuário escolher outra chave cadastrada.
        3. Troca a chave ativa.
        4. Restaura o checkpoint local.
        5. Continua acompanhando a mesma tarefa/Task ID do ponto atual.

        Não troca automaticamente em 429: o usuário escolhe manualmente.
        """
        try:
            task_id = str(task_id or self.task_id_var.get().strip() or "").strip()
            self.salvar_checkpoint_tarefa(
                "crédito/limite esgotado - aguardando escolha manual de chave",
                {
                    "credit_error": str(erro),
                    "manual_key_selection_required": True,
                    "task_id_for_resume": task_id,
                },
            )
        except Exception:
            pass

        self.msg("credit_need_key", task_id, str(erro))

    def escolher_chave_credito_e_continuar(self, task_id: str = "", erro: str = ""):
        """
        Janela principal para escolher outra chave quando a chave atual fica sem crédito.
        """
        task_id = str(task_id or self.task_id_var.get().strip() or "").strip()
        if not task_id:
            messagebox.showerror(
                "Crédito/limite esgotado",
                "A Manus informou crédito/limite esgotado, mas não há Task ID carregado para continuar.",
            )
            return

        # Garante checkpoint antes de trocar a chave.
        self.salvar_checkpoint_tarefa(
            "antes de escolher nova chave por crédito",
            {"credit_error": str(erro), "task_id_for_resume": task_id},
        )

        chaves = []
        atual = self.api_key_var.get().strip()

        def add(k):
            k = str(k or "").strip()
            if k and k not in chaves:
                chaves.append(k)

        # Preferir lista persistida e também a chave atual.
        for k in getattr(self, "api_keys", []):
            add(k)
        add(atual)
        try:
            for k in self.chaves_disponiveis():
                add(k)
        except Exception:
            pass

        if not chaves:
            messagebox.showerror(
                "Sem chaves cadastradas",
                "Não existe outra APIKEY cadastrada para continuar.\n\n"
                "Cadastre uma chave na aba Configuração / IDs e tente novamente.",
            )
            return

        janela = tk.Toplevel(self)
        janela.title("Crédito esgotado - escolher chave para continuar")
        janela.geometry("880x560")
        janela.minsize(760, 440)
        janela.transient(self)
        janela.grab_set()
        janela.columnconfigure(0, weight=1)
        janela.rowconfigure(2, weight=1)

        info = ttk.LabelFrame(janela, text="A tarefa foi salva em checkpoint local", padding=12)
        info.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        info.columnconfigure(1, weight=1)

        ttk.Label(info, text="Task ID:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Label(info, text=task_id).grid(row=0, column=1, sticky="w")

        ttk.Label(info, text="Motivo:").grid(row=1, column=0, sticky="nw", padx=(0, 8), pady=(6, 0))
        ttk.Label(
            info,
            text="A chave atual ficou sem crédito/limite. Escolha outra chave cadastrada para continuar a mesma tarefa.",
            wraplength=720,
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))

        ttk.Label(
            info,
            text="Checkpoint:",
        ).grid(row=2, column=0, sticky="nw", padx=(0, 8), pady=(6, 0))
        ttk.Label(
            info,
            text=str(TASK_STATE_CURRENT_FILE),
            wraplength=720,
        ).grid(row=2, column=1, sticky="w", pady=(6, 0))

        erro_box = ttk.LabelFrame(janela, text="Resumo do erro", padding=8)
        erro_box.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        ttk.Label(erro_box, text=resumo_texto(erro, 420), wraplength=820).pack(anchor="w")

        lista_box = ttk.LabelFrame(janela, text="Escolha a chave que vai assumir a continuação", padding=10)
        lista_box.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        lista_box.columnconfigure(0, weight=1)
        lista_box.rowconfigure(0, weight=1)

        lb = tk.Listbox(lista_box, height=10)
        lb.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(lista_box, orient="vertical", command=lb.yview)
        sb.grid(row=0, column=1, sticky="ns")
        lb.configure(yscrollcommand=sb.set)

        for i, key in enumerate(chaves):
            marca = " [ATUAL/SEM CRÉDITO]" if key == atual else ""
            lb.insert("end", f"#{i+1} {mascarar_chave_api(key)}{marca}")

        # Seleciona automaticamente a primeira chave diferente da atual.
        selecionado = 0
        for i, key in enumerate(chaves):
            if key != atual:
                selecionado = i
                break
        try:
            lb.selection_set(selecionado)
            lb.see(selecionado)
        except Exception:
            pass

        status_var = tk.StringVar(value="Selecione uma chave e clique em Continuar com esta chave.")

        ttk.Label(lista_box, textvariable=status_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        botoes = ttk.Frame(janela, padding=(10, 0, 10, 10))
        botoes.grid(row=3, column=0, sticky="ew")

        def continuar():
            sel = lb.curselection()
            if not sel:
                messagebox.showinfo("Informação", "Selecione uma chave.", parent=janela)
                return
            idx = int(sel[0])
            if idx < 0 or idx >= len(chaves):
                return

            nova = chaves[idx]
            if nova == atual:
                if not messagebox.askyesno(
                    "Mesma chave",
                    "Você selecionou a mesma chave que retornou crédito/limite esgotado.\n\n"
                    "Deseja tentar mesmo assim?",
                    parent=janela,
                ):
                    return

            try:
                # Troca chave ativa e salva persistência.
                self.api_key_var.set(nova)
                if nova not in self.api_keys:
                    self.api_keys.insert(0, nova)
                self.atualizar_lista_chaves(selecionar_key=nova)
                self.salvar_chaves_multiplas_silencioso()

                self.failover_status_var.set(
                    f"Crédito/limite: usuário escolheu continuar com {mascarar_chave_api(nova)}"
                )
                self.keyring_status_var.set(f"Chave ativa para continuação: {mascarar_chave_api(nova)}")

                self.salvar_checkpoint_tarefa(
                    "usuário escolheu nova chave para continuar após crédito/limite",
                    {
                        "chosen_key_masked": mascarar_chave_api(nova),
                        "previous_key_masked": mascarar_chave_api(atual),
                        "resume_task_id": task_id,
                    },
                )

                janela.destroy()

                # Restaura checkpoint salvo para garantir que nada se perca.
                state_continuacao = None
                try:
                    path_task = caminho_estado_tarefa(task_id)
                    if path_task.exists():
                        state_continuacao = self.carregar_checkpoint_arquivo(path_task)
                    elif TASK_STATE_CURRENT_FILE.exists():
                        state_continuacao = self.carregar_checkpoint_arquivo(TASK_STATE_CURRENT_FILE)

                    if state_continuacao:
                        self.aplicar_checkpoint_tarefa(state_continuacao, acompanhar=False)
                except Exception as e:
                    self.log(f"[CHECKPOINT] Não foi possível reaplicar checkpoint antes de continuar: {e}\n")

                self.msg("live", "\n[CHAVE ALTERADA PELO USUÁRIO]\n")
                self.msg("live", f"Nova chave ativa: {mascarar_chave_api(nova)}\n")
                self.msg("live", "Vou retomar a tarefa de onde parou, usando os dados salvos localmente.\n")
                self.msg(
                    "task_status",
                    "Tarefa: CONTINUANDO COM OUTRA CHAVE",
                    "Fase atual: retomando após crédito/limite/chave inativada",
                    "Pistas do servidor: usuário escolheu outra APIKEY cadastrada",
                    f"Atividade: retomada manual em {agora_iso()}",
                )

                self.stop_polling.clear()
                self.executar_thread(lambda: self.retomar_tarefa_apos_troca_chave(task_id, state_continuacao))

            except Exception as e:
                messagebox.showerror("Erro ao continuar com a chave escolhida", str(e), parent=janela)

        def cadastrar():
            janela.destroy()
            try:
                self.notebook.select(self.config_tab)
            except Exception:
                pass
            messagebox.showinfo(
                "Cadastrar chave",
                "Cadastre uma nova APIKEY na aba Configuração / IDs, clique em 'Adicionar chave do campo' e depois retome pelo checkpoint.",
            )

        ttk.Button(botoes, text="Continuar com esta chave", command=continuar).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Cadastrar nova chave", command=cadastrar).pack(side="left", padx=8)
        ttk.Button(botoes, text="Cancelar", command=janela.destroy).pack(side="left", padx=8)

    def continuar_checkpoint_com_chave_atual(self):
        """
        Recarrega o checkpoint e continua usando a chave atualmente selecionada.
        Útil depois de cadastrar manualmente uma nova chave.
        """
        try:
            if not TASK_STATE_CURRENT_FILE.exists():
                messagebox.showinfo("Checkpoint", "Nenhum checkpoint local encontrado.")
                return
            state = self.carregar_checkpoint_arquivo(TASK_STATE_CURRENT_FILE)
            task_id = str(state.get("task_id") or self.task_id_var.get().strip() or "").strip()
            if not task_id:
                messagebox.showerror("Checkpoint", "Checkpoint não possui Task ID.")
                return
            self.aplicar_checkpoint_tarefa(state, acompanhar=False)
            self.salvar_checkpoint_tarefa("continuar checkpoint com chave atual")
            self.stop_polling.clear()
            # Retomada inteligente: continua a MESMA tarefa se a chave atual tiver
            # acesso; senão, cria automaticamente uma nova tarefa de continuação
            # com todo o contexto salvo (resolve o caso de chave antiga desativada).
            self.executar_thread(lambda: self.retomar_tarefa_apos_troca_chave(task_id, state))
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def retomar_tarefa_apos_troca_chave(self, task_id: str, state: Optional[Dict[str, Any]] = None):
        """
        Retoma a tarefa depois que o usuário escolheu uma nova chave.

        Estratégia:
        1. Tenta acessar a MESMA tarefa (mesmo task_id) com a nova chave.
           Funciona quando a chave é da mesma conta (ex.: só faltava crédito).
        2. Se a nova chave não tiver acesso à tarefa (ex.: é de outra conta),
           cria uma NOVA tarefa enviando todo o contexto salvo localmente,
           para a nova chave entender que já existe uma tarefa em andamento e
           continuar de onde parou.
        """
        task_id = str(task_id or "").strip()

        # Garante que temos o state mais completo possível.
        if not state:
            try:
                path_task = caminho_estado_tarefa(task_id) if task_id else None
                if path_task and path_task.exists():
                    state = self.carregar_checkpoint_arquivo(path_task)
                elif TASK_STATE_CURRENT_FILE.exists():
                    state = self.carregar_checkpoint_arquivo(TASK_STATE_CURRENT_FILE)
            except Exception:
                state = None

        try:
            api = self.pegar_api()
        except Exception as e:
            self.msg("erro", str(e))
            return

        # 1) Tenta continuar a MESMA tarefa.
        if task_id:
            try:
                self.msg("log", f"[CONTINUAR] Verificando se a nova chave acessa a tarefa {task_id}...\n")
                api.list_messages(task_id, limit=1)
                self.msg("live", "\n[OK] A nova chave tem acesso à mesma tarefa. Continuando o mesmo Task ID.\n")
                self.acompanhar_tarefa(task_id)
                return
            except Exception as e:
                # IMPORTANTE: um erro de permissão/403 aqui normalmente significa apenas
                # que a NOVA chave (outra conta) não tem acesso à tarefa ANTIGA - e NÃO
                # que a nova chave está inválida. Por isso, validamos a saúde da nova
                # chave com uma chamada leve (list_skills) antes de decidir.
                chave_saudavel = False
                erro_chave = None
                try:
                    api.list_skills()
                    chave_saudavel = True
                except Exception as e2:
                    erro_chave = e2
                    # Só consideramos a chave "morta" se for crédito/inválida de fato.
                    chave_saudavel = not (erro_credito_esgotado(e2) or erro_chave_invalida(e2))

                if not chave_saudavel:
                    self.msg("log", f"[CONTINUAR] A NOVA chave também está sem crédito/inválida: {erro_chave or e}\n")
                    self.msg("credit_need_key", task_id, str(erro_chave or e))
                    return

                self.msg("live", "\n[INFO] A nova chave é válida, mas não acessa a tarefa original (provavelmente outra conta).\n")
                self.msg("live", "[INFO] Criando nova tarefa de continuação com o contexto salvo, para continuar de onde parou.\n")
                self.msg("log", f"[CONTINUAR] Sem acesso ao task original ({resumo_texto(str(e), 80)}). Continuando em nova tarefa.\n")

        # 2) Cria nova tarefa de continuação com todo o contexto salvo.
        self.continuar_em_nova_tarefa(api, state, task_id_antigo=task_id)

    def montar_prompt_continuacao(self, state: Optional[Dict[str, Any]]) -> str:
        """
        Monta um prompt de continuação a partir do checkpoint local, para que uma
        nova chave/conta entenda a tarefa e continue de onde parou.
        """
        state = state or {}
        titulo = str(state.get("title") or "").strip()
        prompt_orig = str(state.get("prompt") or "").strip()
        ultima_resp = str(state.get("last_response_text") or "").strip()
        msgs = state.get("ultimas_mensagens") or []

        historico: List[str] = []
        try:
            for m in list(msgs)[-25:]:
                if not isinstance(m, dict):
                    continue
                texto = ""
                try:
                    texto = extrair_texto_assistente(m.get("assistant_message"))
                except Exception:
                    texto = ""
                if texto:
                    historico.append("- " + resumo_texto(texto, 600))
        except Exception:
            pass

        arquivos_ctx = []
        for s in (state.get("selected_files") or []):
            try:
                arquivos_ctx.append(Path(str(s)).name)
            except Exception:
                pass
        for s in (state.get("downloaded_files") or []):
            try:
                arquivos_ctx.append(Path(str(s)).name)
            except Exception:
                pass

        partes: List[str] = []
        partes.append("CONTINUAÇÃO DE UMA TAREFA ANTERIOR DA MANUS.")
        partes.append(
            "Esta tarefa já estava em andamento em outra chave/conta e foi interrompida "
            "(sem crédito ou chave inativada). Use TODO o contexto salvo abaixo e CONTINUE "
            "exatamente de onde parou, SEM recomeçar do zero."
        )
        if titulo:
            partes.append(f"\nTítulo original: {titulo}")
        if prompt_orig:
            partes.append("\n=== PEDIDO / PROMPT ORIGINAL ===\n" + prompt_orig)
        if historico:
            partes.append(
                "\n=== RESUMO DO QUE JÁ FOI FEITO (mensagens anteriores do Manus) ===\n"
                + "\n".join(historico)
            )
        if ultima_resp:
            partes.append("\n=== ÚLTIMO ESTADO / RESPOSTA REGISTRADO ===\n" + resumo_texto(ultima_resp, 4000))
        if arquivos_ctx:
            partes.append("\n=== ARQUIVOS DA TAREFA (reenviados em anexo) ===\n- " + "\n- ".join(arquivos_ctx[:30]))
        partes.append(
            "\n=== INSTRUÇÃO ===\nRetome a execução a partir deste ponto e conclua o que falta. "
            "Os arquivos relevantes seguem anexados a esta nova tarefa."
        )
        return "\n".join(partes)

    def continuar_em_nova_tarefa(self, api: "ManusAPI", state: Optional[Dict[str, Any]], task_id_antigo: str = ""):
        """
        Cria uma nova tarefa na nova chave reenviando o contexto e os arquivos
        salvos localmente, para a nova conta continuar a tarefa de onde parou.
        """
        state = state or {}
        prompt_cont = self.montar_prompt_continuacao(state)
        agent = str(state.get("agent_profile") or (self.agent_var.get().strip() if hasattr(self, "agent_var") else "") or "manus-1.6-lite")
        base_titulo = str(state.get("title") or "").strip() or titulo_nova_tarefa()
        titulo = ("CONTINUAÇÃO - " + base_titulo)[:120]

        # Reúne arquivos salvos localmente (anexados + baixados) para reenviar.
        arquivos: List[Path] = []
        vistos = set()
        for grupo in (state.get("selected_files") or [], state.get("downloaded_files") or []):
            for s in grupo:
                try:
                    p = Path(str(s))
                except Exception:
                    continue
                chave = str(p).lower()
                if p.exists() and chave not in vistos:
                    arquivos.append(p)
                    vistos.add(chave)

        usar_logger = getattr(self, "logger", None) and self.auto_log_var.get()

        uploaded: List[Dict[str, str]] = []
        if arquivos:
            self.msg("log", f"[CONTINUAR] Reenviando {len(arquivos)} arquivo(s) salvos para a nova chave...\n")
            self.msg("upload_progress", 0.0, 0, 0, "reenviando arquivos da continuação")
        for i, fp in enumerate(arquivos, start=1):
            try:
                self.msg("log", f"[CONTINUAR][UPLOAD {i}/{len(arquivos)}] {fp.name}\n")
                info = api.upload_local_file(
                    fp,
                    logger=self.logger if usar_logger else None,
                    cb=lambda m: self.msg("log", f"[UPLOAD] {m}\n"),
                    progress_cb=lambda percent, sent, total, filename: self.enviar_progresso_upload(percent, sent, total, filename),
                )
                uploaded.append(info)
            except Exception as e:
                self.msg("log", f"[CONTINUAR][UPLOAD/ERRO] {fp.name}: {e}\n")

        self.msg("live", "\n[CRIANDO NOVA TAREFA DE CONTINUAÇÃO COM A NOVA CHAVE]\n")
        try:
            data = api.create_task(prompt_cont, agent, titulo, uploaded_files=uploaded)
        except Exception as e:
            if erro_credito_esgotado(e) or erro_chave_invalida(e):
                self.msg("log", f"[CONTINUAR] A nova chave falhou ao criar a tarefa: {e}\n")
                self.msg("credit_need_key", task_id_antigo, str(e))
                return
            self.msg("erro", str(e))
            return

        novo_id = data.get("task_id") or ""
        novo_url = data.get("task_url") or ""
        novo_titulo = data.get("task_title") or titulo

        self.msg("task", novo_id, novo_url)
        self.msg("live", f"[OK] Nova tarefa de continuação criada: {novo_id}\n")
        self.msg("live", f"Título: {novo_titulo}\n")
        self.msg("live", f"URL: {novo_url}\n")
        if uploaded:
            self.msg("upload_progress", 100.0, 100, 100, "arquivos da continuação reenviados")

        if getattr(self, "logger", None):
            try:
                self.logger.update_task_id(novo_id)
                if self.auto_log_var.get():
                    self.logger.log(
                        "task_continued_new_key",
                        "Tarefa continuada em nova tarefa com nova chave",
                        new_task_id=novo_id,
                        continuation_of=task_id_antigo,
                    )
            except Exception:
                pass

        self.salvar_checkpoint_tarefa(
            "continuação criada em nova tarefa com nova chave",
            {"continuation_of": task_id_antigo, "new_task_id": novo_id, "new_task_url": novo_url},
        )

        if novo_id:
            self.acompanhar_tarefa(novo_id)

    def definir_creditos_esgotados(self, detalhe: str = ""):
        """
        O servidor respondeu, portanto está online.
        Mas a conta/chave não tem crédito/limite para continuar.
        """
        detalhe_final = detalhe or f"HTTP 429 / credit limit exceeded em {agora_iso()}"
        self.msg("server_status", True, f"Servidor ONLINE, mas com limite/crédito bloqueando | {detalhe_final}")
        self.msg(
            "task_status",
            "Tarefa: BLOQUEADA POR CRÉDITOS",
            "Fase atual: aguardando escolha de outra chave para continuar",
            "Pistas do servidor: HTTP 429 | resource_exhausted | credit limit exceeded",
            f"Atividade: checkpoint salvo; aguardando escolha de outra API key desde {agora_iso()}",
        )

    def definir_chave_inativada(self, detalhe: str = ""):
        """
        O servidor respondeu (está ONLINE), mas a chave foi inativada/expirada
        ou não tem permissão para continuar.
        """
        detalhe_final = detalhe or f"Chave inválida/sem permissão em {agora_iso()}"
        self.msg("server_status", True, f"Servidor ONLINE, mas a chave está inativada/sem permissão | {detalhe_final}")
        self.msg(
            "task_status",
            "Tarefa: PAUSADA (chave inativada)",
            "Fase atual: aguardando escolha de outra chave para continuar",
            "Pistas do servidor: chave inválida/expirada/sem permissão (HTTP 401/403)",
            f"Atividade: checkpoint salvo; aguardando nova API key desde {agora_iso()}",
        )

    def tratar_interrupcao_chave(self, task_id: str = "", erro: str = ""):
        """
        Pergunta ao usuário se deseja continuar a tarefa depois que a chave ficou
        sem crédito ou foi inativada. Se sim, abre a janela para escolher/cadastrar
        outra chave e retomar a tarefa de onde parou.
        """
        task_id = str(task_id or self.task_id_var.get().strip() or "").strip()

        if erro_chave_invalida(erro) and not erro_credito_esgotado(erro):
            motivo = "foi inativada, expirou ou está sem permissão"
        else:
            motivo = "ficou sem crédito/limite"

        continuar = messagebox.askyesno(
            "Tarefa interrompida - deseja continuar?",
            f"A chave atual {motivo}.\n\n"
            "Todos os dados da tarefa foram salvos localmente (checkpoint).\n\n"
            "Deseja CONTINUAR esta tarefa agora com outra chave "
            "(cadastrada ou nova)?\n\n"
            "Se escolher Não, você pode retomar mais tarde pelo botão "
            "'Carregar checkpoint' / 'Continuar checkpoint c/ chave atual'.",
        )

        if not continuar:
            self.failover_status_var.set(
                f"Interrompido em {agora_iso()}: usuário optou por não continuar agora. Checkpoint salvo."
            )
            self.log("[CHAVE] Usuário optou por NÃO continuar agora. Tarefa salva no checkpoint para retomar depois.\n")
            return

        self.escolher_chave_credito_e_continuar(task_id, erro)

    def definir_servidor_online(self, detalhe: str = ""):
        """Atualiza indicação de servidor online."""
        texto = detalhe or f"Última resposta do servidor: {agora_iso()}"
        self.msg("server_status", True, texto)

    def definir_servidor_offline(self, detalhe: str = ""):
        """Atualiza indicação de servidor offline/sem resposta."""
        texto = detalhe or f"Última tentativa sem resposta: {agora_iso()}"
        self.msg("server_status", False, texto)

    def interpretar_status_tarefa(self, status: str, status_raw: dict, messages: list):
        """
        Interpreta tudo que o servidor fornece como pista:
        - agent_status: running/stopped/waiting/error
        - brief
        - description
        - status_detail.waiting_description
        - quantidade de mensagens/eventos
        """
        status_limpo = (status or "").lower().strip()
        raw = status_raw or {}

        brief = str(raw.get("brief") or "").strip()
        description = str(raw.get("description") or "").strip()
        detail = raw.get("status_detail") or {}
        waiting_description = str(detail.get("waiting_description") or "").strip()
        waiting_type = str(detail.get("waiting_for_event_type") or "").strip()

        total_msgs = len(messages or [])
        assistant_count = 0
        attachment_count = 0
        error_count = 0

        for msg in messages or []:
            if extrair_texto_assistente(msg.get("assistant_message")):
                assistant_count += 1
            attachment_count += len(extrair_anexos_assistente(msg))
            if msg.get("error_message"):
                error_count += 1

        if status_limpo == "running":
            status_text = "Tarefa: EM EXECUÇÃO"
            phase = "Fase atual: sendo feita agora"
        elif status_limpo == "stopped":
            status_text = "Tarefa: FINALIZADA"
            phase = "Fase atual: terminou"
        elif status_limpo == "waiting":
            status_text = "Tarefa: AGUARDANDO VOCÊ"
            phase = "Fase atual: precisa de resposta/confirmação"
        elif status_limpo == "error":
            status_text = "Tarefa: ERRO"
            phase = "Fase atual: falhou"
        elif status_limpo:
            status_text = f"Tarefa: {status_limpo}"
            phase = "Fase atual: informada pelo servidor"
        else:
            status_text = "Tarefa: sem status ainda"
            phase = "Fase atual: aguardando primeiro status"

        pistas = []
        if brief:
            pistas.append(f"brief: {brief}")
        if description:
            pistas.append(f"description: {description}")
        if waiting_description:
            pistas.append(f"waiting: {waiting_description}")
        if waiting_type:
            pistas.append(f"tipo: {waiting_type}")

        if not pistas:
            pistas.append("sem pistas textuais além do status")

        clue = "Pistas do servidor: " + " | ".join(pistas[:4])
        activity = (
            f"Atividade: mensagens={total_msgs}, respostas={assistant_count}, "
            f"anexos={attachment_count}, erros={error_count}, atualizado={agora_iso()}"
        )

        self.msg("task_status", status_text, phase, clue, activity)

    def widget_tem_rolagem_interna(self, widget):
        """
        Retorna True quando o widget sob o mouse pertence a uma área que
        deve rolar internamente, e não a barra principal do formulário.
        """
        try:
            internos = {
                getattr(self, "prompt_text", None),
                getattr(self, "files_list", None),
                getattr(self, "realtime_text", None),
                getattr(self, "downloads_list", None),
                getattr(self, "log_text", None),
            }

            w = widget
            while w is not None:
                if w in internos:
                    return True

                try:
                    classe = str(w.winfo_class())
                except Exception:
                    classe = ""

                if classe in {"Text", "Listbox", "Treeview"}:
                    return True

                if classe in {"Scrollbar", "TScrollbar"}:
                    return True

                if w == self:
                    break

                try:
                    w = w.master
                except Exception:
                    break

            return False
        except Exception:
            return False

    def expandir_prompt_arquivos(self):
        """Aumenta temporariamente a área de prompt e anexos."""
        try:
            try:
                self.state("zoomed")
            except Exception:
                self.geometry("1380x1040")

            if hasattr(self, "main_content"):
                self.main_content.rowconfigure(1, weight=4, minsize=430)
                self.main_content.rowconfigure(7, weight=2, minsize=260)
                self.notebook.select(self.main_tab)
                try:
                    self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
                    self.main_canvas.yview_moveto(0)
                except Exception:
                    pass
            elif hasattr(self, "main_tab"):
                self.main_tab.rowconfigure(1, weight=4, minsize=380)
                self.main_tab.rowconfigure(5, weight=2, minsize=240)
                self.notebook.select(self.main_tab)
            else:
                self.rowconfigure(3, weight=4, minsize=360)
                self.rowconfigure(7, weight=2, minsize=240)
            self.log("[LAYOUT] Área de prompt/anexos expandida.\n")
        except Exception as e:
            messagebox.showerror("Erro", str(e))


    def enviar_progresso_upload(self, percent: float, sent: int, total: int, filename: str):
        """Envia progresso real de upload para a interface e logs."""
        try:
            self.msg("upload_progress", float(percent), int(sent), int(total), str(filename))
            if getattr(self, "logger", None) and self.auto_log_var.get():
                # Grava somente alguns pontos para não gerar JSONL gigante.
                percent_int = int(percent)
                if percent_int in (0, 25, 50, 75, 100) or percent_int % 10 == 0:
                    self.logger.log(
                        "upload_progress",
                        f"{filename}: {percent:.2f}% ({tamanho_legivel(sent)} / {tamanho_legivel(total)})",
                        filename=filename,
                        percent=round(float(percent), 2),
                        sent=int(sent),
                        total=int(total),
                    )
        except Exception:
            pass

    def testar_conexao(self):
        def worker():
            try:
                api = self.pegar_api()
                self.msg("log", "\n=== TESTANDO CONEXÃO ===\n")
                skills = api.list_skills().get("data", [])
                self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | skill.list OK")
                try:
                    credit_data = api.available_credits()
                    self.msg("credit_status", True, self.api_key_var.get().strip(), credit_data)
                except Exception as credit_err:
                    self.msg("log", f"[CRÉDITOS] Não foi possível consultar créditos no teste: {credit_err}\n")
                self.msg("log", f"OK: autenticação funcionando. Skills encontradas: {len(skills)}\n")
                for skill in skills[:10]:
                    self.msg("log", f"- {skill.get('id')} | {skill.get('name')}\n")
            except Exception as e:
                if erro_credito_esgotado(e):
                    self.definir_creditos_esgotados(f"Falha ao testar limite/crédito: {agora_iso()} | {e}")
                else:
                    self.definir_servidor_offline(f"Falha ao testar servidor: {agora_iso()} | {e}")
                self.msg("erro", str(e))
        self.executar_thread(worker)

    def criar_tarefa(self):
        def worker():
            try:
                api = self.pegar_api()
                prompt = self.prompt_text.get("1.0", "end").strip()
                if not prompt:
                    raise RuntimeError("Digite um prompt primeiro.")
                # Modo de injeção: antepõe o preâmbulo de contexto, se ativado.
                prompt = self.aplicar_injecao_no_prompt(prompt)
                agent_profile = self.agent_var.get().strip()

                # Opção: usar sempre o melhor modelo disponível da IA.
                if getattr(self, "best_model_var", None) and self.best_model_var.get():
                    agent_profile = "manus-1.6-max"
                    try:
                        self.agent_var.set(agent_profile)
                    except Exception:
                        pass
                    self.msg("log", "[MODELO] Usando o melhor modelo: manus-1.6-max\n")

                # ===== Cache MySQL: busca a resposta no banco ANTES de usar a API. =====
                cached = self.mysql_buscar(agent_profile, prompt)
                if cached:
                    self.msg("live", "\n[RESPOSTA OBTIDA DO BANCO MYSQL - cache | API não foi necessária]\n")
                    self.msg("live", cached + "\n")
                    self.msg("log", "[MYSQL] Resposta encontrada no cache do banco. A API da Manus NÃO foi chamada.\n")
                    self.msg(
                        "task_status",
                        "Tarefa: RESPONDIDA DO CACHE (MySQL)",
                        "Fase atual: resposta servida do banco",
                        "Pistas: cache hit no MySQL",
                        f"Atividade: resposta do banco em {agora_iso()}",
                    )
                    try:
                        self.mysql_conversa("", "user", prompt)
                        self.mysql_conversa("", "assistant_cache", cached)
                    except Exception:
                        pass
                    self.msg("notify_done")
                    return

                self._ultimo_prompt_enviado = prompt
                self._ultimo_agent_enviado = agent_profile
                self.mysql_conversa("", "user", prompt)

                # Título automático obrigatório de cada nova tarefa:
                # DATA HORA - Nova Tarefa
                title = titulo_nova_tarefa()
                self.title_var.set(title)

                self.stop_polling.clear()
                self.textos_mostrados.clear()
                self.eventos_vistos.clear()
                self.urls_baixadas.clear()
                self.last_waiting_detail = {}
                self.downloaded_files.clear()
                self.salvar_preferencias_locais()
                if self.autosave_prompt_var.get():
                    self.salvar_rascunho_prompt()

                self.verificar_integridade_local()
                try:
                    credit_data = self.pegar_api().available_credits()
                    self.msg("credit_status", True, self.api_key_var.get().strip(), credit_data)
                except Exception as credit_err:
                    self.msg("log", f"[CRÉDITOS] Não foi possível consultar antes de iniciar: {credit_err}\n")

                self.msg("log", "\n=== PREPARANDO TAREFA ===\n")
                self.msg("live", "\n--- Nova tarefa iniciada ---\n")
                self.msg("upload_progress", 0.0, 0, 0, "aguardando upload")
                self.session_status_var.set(f"Sessão: tarefa iniciada em {agora_iso()}")
                self.salvar_checkpoint_tarefa("antes de criar/enviar tarefa")

                self.logger = AutoLogger(enabled=self.auto_log_var.get(), prefix=title)
                self.logger.log("task_prepare", "Preparando tarefa", title=title, agent_profile=agent_profile)

                uploaded_files = []
                if self.selected_files:
                    self.msg("log", f"[ARQUIVOS] {len(self.selected_files)} arquivo(s) selecionado(s) para envio.\n")
                else:
                    self.msg("log", "[ARQUIVOS] Nenhum arquivo selecionado. A tarefa será criada somente com o prompt.\n")

                for i, file_path in enumerate(self.selected_files, start=1):
                    self.msg("log", f"\n[UPLOAD {i}/{len(self.selected_files)}] {file_path.name}\n")
                    info = api.upload_local_file(
                        file_path,
                        logger=self.logger if self.auto_log_var.get() else None,
                        cb=lambda m: self.msg("log", f"[UPLOAD] {m}\n"),
                        progress_cb=lambda percent, sent, total, filename: self.enviar_progresso_upload(percent, sent, total, filename),
                    )
                    uploaded_files.append(info)
                    self.msg("log", f"[OK] Upload concluído: {info['filename']}\n")

                if self.selected_files:
                    self.msg("upload_progress", 100.0, 100, 100, "todos os uploads concluídos")
                else:
                    self.msg("upload_progress", 0.0, 0, 0, "sem arquivos para upload")

                self.msg("log", "\n=== CRIANDO TAREFA ===\n")
                data = api.create_task(prompt, agent_profile, title, uploaded_files=uploaded_files)
                task_id = data.get("task_id") or ""
                task_title = data.get("task_title") or title
                task_url = data.get("task_url") or ""

                self.msg("task", task_id, task_url)
                if task_id:
                    self.logger.update_task_id(task_id)

                self.logger.log("task_created", "Tarefa criada", task_id=task_id, task_url=task_url, title=task_title)
                self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | task.create OK")
                self.msg("task_status", "Tarefa: CRIADA", "Fase atual: iniciando acompanhamento", "Pistas do servidor: task.create retornou task_id e URL", f"Atividade: criada em {agora_iso()}")
                self.salvar_checkpoint_tarefa("tarefa criada", {"created_task_id": task_id, "created_task_url": task_url})
                self.msg("log", "Tarefa criada com sucesso.\n")
                self.msg("log", f"task_id: {task_id}\n")
                self.msg("log", f"título: {task_title}\n")
                self.msg("log", f"url: {task_url}\n")

                if task_id and self.auto_follow_var.get():
                    self.acompanhar_tarefa(task_id)
            except Exception as e:
                if erro_credito_esgotado(e):
                    self.definir_creditos_esgotados(f"Falha ao criar/executar por limite/crédito: {agora_iso()} | {e}")
                self.msg("erro", str(e))
        self.executar_thread(worker)

    def acompanhar_tarefa_atual(self):
        task_id = self.task_id_var.get().strip()
        if not task_id:
            messagebox.showerror("Erro", "Nenhum Task ID informado.")
            return
        self.stop_polling.clear()
        self.textos_mostrados.clear()
        self.eventos_vistos.clear()
        self.urls_baixadas.clear()
        self.executar_thread(lambda: self._acompanhar_safe(task_id))

    def _acompanhar_safe(self, task_id):
        try:
            self.acompanhar_tarefa(task_id)
        except Exception as e:
            self.msg("erro", str(e))

    def abrir_tarefa_no_app(self, task_id: str, titulo: str = "", url: str = ""):
        """Carrega uma tarefa existente dentro da própria interface, sem abrir navegador."""
        task_id = str(task_id or "").strip()
        if not task_id:
            messagebox.showerror("Erro", "Task ID vazio.")
            return

        self.stop_polling.clear()
        self.eventos_vistos.clear()
        self.urls_baixadas.clear()

        def worker():
            try:
                self._abrir_tarefa_no_app_worker(task_id, titulo=titulo, url=url)
            except Exception as e:
                self.msg("erro", str(e))

        self.executar_thread(worker)

    def _abrir_tarefa_no_app_worker(self, task_id: str, titulo: str = "", url: str = ""):
        """Busca mensagens de uma tarefa concluída e mostra tudo na área de tempo real."""
        api = self.pegar_api()
        task_url = url or f"https://manus.im/app/{task_id}"

        self.msg("task", task_id, task_url)
        self.msg("live", "\n================ TAREFA ABERTA NO APP ================\n")
        if titulo:
            self.msg("live", f"Título: {titulo}\n")
        self.msg("live", f"Task ID: {task_id}\n")
        self.msg("live", f"URL: {task_url}\n")
        self.msg("live", "=======================================================\n")
        self.msg("log", f"[TAREFA] Abrindo dentro do app: {task_id}\n")

        data = api.list_messages(task_id, limit=200, slides_format="pptx")
        messages = data.get("messages", [])
        status, status_raw = status_mais_recente(messages)
        if status:
            self.msg("log", f"[STATUS] {status}\n")
            self.msg("live", f"\n[STATUS] {status}\n")

        ultima_resposta = ""
        achou_conteudo = False

        for ev in eventos_da_tarefa(messages):
            kind = ev["kind"]
            text = ev["text"]

            if kind == "assistant":
                achou_conteudo = True
                ultima_resposta = text
                self.msg("live", "\n[MENSAGEM DO MANUS]\n")
                self.msg("live", text + "\n")
                if self.auto_log_var.get():
                    self.logger.log("opened_task_assistant_message", text, task_id=task_id)

                if self.auto_download_var.get():
                    for link in extrair_urls_baixaveis(text):
                        self.baixar_e_registrar(link, task_id)

            elif kind == "attachment":
                achou_conteudo = True
                anexo = ev["raw"]
                link = anexo.get("url")
                filename = anexo.get("filename") or anexo.get("file_name") or ""
                self.msg("live", f"\n[ANEXO DETECTADO]\n{filename or link}\n")
                if self.auto_download_var.get() and link:
                    self.baixar_e_registrar(link, task_id, filename)

            elif kind == "waiting_detail":
                self.last_waiting_detail = ev["raw"] or {}
                self.msg("waiting", self.last_waiting_detail)
                self.msg("live", "\n[MANUS AGUARDANDO]\n" + text + "\n")

            elif kind == "error":
                achou_conteudo = True
                self.msg("live", "\n[ERRO NA TAREFA]\n" + text + "\n")
                self.msg("log", "[ERRO NA TAREFA ABERTA]\n" + text + "\n")

        if not achou_conteudo:
            self.msg("live", "\n[INFO] Nenhuma mensagem/anexo foi retornado para esta tarefa.\n")

        if ultima_resposta and self.auto_log_var.get():
            final_path = self.logger.save_final(ultima_resposta)
            if final_path:
                self.msg("log", f"[OK] Resposta da tarefa aberta salva em: {final_path}\n")
                self.enfileirar_backup(final_path)

        self.msg("live", "\n[OK] Tarefa carregada dentro do aplicativo.\n")
        self.msg("log", f"[DOWNLOAD] Arquivos baixados em: {DOWNLOAD_DIR / nome_seguro(task_id)}\n")

    def baixar_e_registrar(self, url: str, task_id: str, filename: str = ""):
        if url in self.urls_baixadas:
            return
        self.urls_baixadas.add(url)
        fname = nome_seguro(filename or filename_from_url(url), 160)
        try:
            path = baixar_url(url, DOWNLOAD_DIR / nome_seguro(task_id) / fname, logger=self.logger if self.auto_log_var.get() else None, cb=lambda m: self.msg("log", f"[DOWNLOAD] {m}\n"))
            self.msg("download", str(path))
            self.msg("live", f"\n[ARQUIVO BAIXADO]\n{path}\n")
            self.enfileirar_backup(path)
        except Exception as e:
            self.msg("log", f"[ERRO DOWNLOAD] {url}\n{e}\n")

    def acompanhar_tarefa(self, task_id: str):
        api = self.pegar_api()
        try:
            poll_interval = max(1, int(float(self.poll_interval_var.get().strip() or "3")))
        except ValueError:
            poll_interval = 3

        self.msg("log", "\n=== ACOMPANHANDO ATÉ TERMINAR ===\n")
        self.msg("log", "Sem timeout automático. O app só para em stopped/error/waiting ou botão Parar.\n")
        self.msg("live", "\n[Acompanhamento iniciado: aguardando finalizar]\n")

        ultima_resposta = ""

        while True:
            if self.stop_polling.is_set():
                self.msg("log", "\n[INFO] Acompanhamento parado pelo usuário.\n")
                self.msg("live", "\n[Acompanhamento parado]\n")
                return

            try:
                data = api.list_messages(task_id, limit=200, slides_format="pptx")
                self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | task.listMessages OK")
            except Exception as e:
                if erro_credito_esgotado(e):
                    self.definir_creditos_esgotados(f"task.listMessages bloqueado: {agora_iso()} | {e}")
                    self.salvar_checkpoint_tarefa(
                        "crédito/limite esgotado durante acompanhamento",
                        {"credit_error": str(e), "resume_task_id": task_id},
                    )
                    self.msg("log", f"[CRÉDITO ESGOTADO] {e}\n")
                    self.msg("live", "\n[PAUSADO] A Manus respondeu HTTP 429: crédito/limite esgotado.\n")
                    self.msg("live", "[AÇÃO NECESSÁRIA] Escolha outra chave cadastrada para continuar a mesma tarefa do checkpoint.\n")
                    if self.auto_log_var.get():
                        self.logger.log("credit_limit_exceeded_need_key", str(e), task_id=task_id)
                    self.msg("credit_need_key", task_id, str(e))
                    return

                if erro_chave_invalida(e):
                    self.salvar_checkpoint_tarefa(
                        "chave inativada/inválida durante acompanhamento",
                        {"key_error": str(e), "resume_task_id": task_id},
                    )
                    self.msg("log", f"[CHAVE INATIVADA/INVÁLIDA] {e}\n")
                    self.msg("live", "\n[PAUSADO] A chave atual parece inativada, expirada ou sem permissão.\n")
                    self.msg("live", "[AÇÃO NECESSÁRIA] Escolha outra chave cadastrada (ou cadastre uma nova) para continuar a tarefa.\n")
                    if self.auto_log_var.get():
                        self.logger.log("api_key_invalid_need_key", str(e), task_id=task_id)
                    self.msg("credit_need_key", task_id, str(e))
                    return

                self.definir_servidor_offline(f"Falha em task.listMessages: {agora_iso()} | {e}")
                self.salvar_checkpoint_tarefa("falha listMessages antes de tentar novamente", {"last_error": str(e)})
                self.msg("log", f"[SERVIDOR OFFLINE/SEM RESPOSTA] {e}\n")
                time.sleep(poll_interval)
                continue

            messages = data.get("messages", [])
            self.ultimas_mensagens = messages
            status, status_raw = status_mais_recente(messages)

            self.interpretar_status_tarefa(status, status_raw, messages)
            self.salvar_checkpoint_tarefa("poll/listMessages", {"last_server_status": status, "message_count": len(messages)})

            if status:
                self.msg("log", f"[STATUS] {status}\n")
                if self.auto_log_var.get():
                    self.logger.log("status", status, raw=status_raw)

            for ev in eventos_da_tarefa(messages):
                if ev["id"] in self.eventos_vistos:
                    continue
                self.eventos_vistos.add(ev["id"])

                kind = ev["kind"]
                text = ev["text"]

                if kind == "assistant":
                    ultima_resposta = text
                    self.msg("live", "\n[MENSAGEM DO MANUS]\n")
                    self.msg("live", text + "\n")
                    if self.auto_log_var.get():
                        self.logger.log("assistant_message", text)
                    self.mysql_conversa(task_id, "assistant", text)

                    if self.auto_download_var.get():
                        for url in extrair_urls_baixaveis(text):
                            self.baixar_e_registrar(url, task_id)

                elif kind == "attachment":
                    anexo = ev["raw"]
                    url = anexo.get("url")
                    filename = anexo.get("filename") or anexo.get("file_name") or ""
                    self.msg("live", f"\n[ANEXO DETECTADO]\n{filename or url}\n")
                    if self.auto_download_var.get() and url:
                        self.baixar_e_registrar(url, task_id, filename)

                elif kind == "waiting_detail":
                    self.last_waiting_detail = ev["raw"] or {}
                    self.msg("waiting", self.last_waiting_detail)
                    self.msg("live", "\n[MANUS AGUARDANDO]\n" + text + "\n")
                    self.msg("log", "[AGUARDANDO] A tarefa precisa de resposta/confirmação. Use o campo 'Enviar resposta' ou 'Confirmar ação pendente'.\n")
                    return

                elif kind == "error":
                    self.msg("log", "\n[ERRO NA TAREFA]\n" + text + "\n")
                    self.msg("live", "\n[ERRO NA TAREFA]\n" + text + "\n")
                    return

            if status == "stopped":
                self.msg("log", "\n[OK] Tarefa finalizada.\n")
                self.msg("live", "\n[OK] Tarefa finalizada.\n")
                self.msg("notify_done")
                salvar_tarefa_concluida_local({
                    "id": task_id,
                    "title": self.title_var.get().strip() or "Tarefa Manus completa",
                    "task_url": self.task_url_var.get().strip(),
                    "status": "stopped",
                    "updated_at": int(time.time()),
                    "source": "gui_local",
                })

                if ultima_resposta:
                    self.mysql_salvar(
                        getattr(self, "_ultimo_agent_enviado", "") or self.agent_var.get().strip(),
                        getattr(self, "_ultimo_prompt_enviado", "") or "",
                        ultima_resposta,
                        "manus_api",
                    )
                    if self.auto_log_var.get():
                        final_path = self.logger.save_final(ultima_resposta)
                        if final_path:
                            self.msg("log", f"[OK] Resposta final salva em: {final_path}\n")
                            self.enfileirar_backup(final_path)
                    self.msg("live", "\n================ RESPOSTA FINAL ================\n")
                    self.msg("live", ultima_resposta + "\n")
                    self.msg("live", "================================================\n")

                self.msg("log", f"[DOWNLOAD] Arquivos baixados em: {DOWNLOAD_DIR / nome_seguro(task_id)}\n")
                return

            if status == "error":
                self.msg("log", "\n[ERRO] A tarefa terminou com erro.\n")
                self.msg("live", "\n[ERRO] A tarefa terminou com erro.\n")
                return

            if status == "waiting":
                self.msg("waiting", status_raw.get("status_detail") or {})
                desc = (status_raw.get("status_detail") or {}).get("waiting_description") or status_raw.get("description") or status_raw.get("brief") or "Aguardando ação."
                self.msg("live", "\n[MANUS AGUARDANDO]\n" + str(desc) + "\n")
                self.msg("log", "[AGUARDANDO] Use o campo de resposta ou confirme a ação pendente.\n")
                return

            time.sleep(poll_interval)

    def pedir_texto_continuacao_tarefa(self, task_id: str, titulo: str = "", parent=None) -> str:
        """
        Abre uma pequena janela para o usuário escrever o que deseja continuar
        na mesma tarefa já existente.
        """
        resultado = {"texto": ""}

        janela = tk.Toplevel(parent or self)
        janela.title("Continuar mesma tarefa")
        janela.geometry("760x420")
        janela.minsize(640, 360)
        janela.transient(parent or self)
        janela.grab_set()
        janela.columnconfigure(0, weight=1)
        janela.rowconfigure(2, weight=1)

        info = ttk.LabelFrame(janela, text="Tarefa selecionada", padding=10)
        info.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 8))
        info.columnconfigure(1, weight=1)

        ttk.Label(info, text="Task ID:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Label(info, text=task_id).grid(row=0, column=1, sticky="w")

        ttk.Label(info, text="Título:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(4, 0))
        ttk.Label(info, text=titulo or "Sem título").grid(row=1, column=1, sticky="w", pady=(4, 0))

        ttk.Label(
            janela,
            text="Digite abaixo o que o Manus deve continuar fazendo nessa mesma tarefa:",
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 6))

        texto_box = ScrolledText(janela, height=10, wrap="word")
        texto_box.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        texto_box.insert(
            "1.0",
            "Continue esta mesma tarefa a partir do ponto em que parou. "
            "Use o contexto anterior da própria tarefa e prossiga com o que falta."
        )
        texto_box.focus_set()

        botoes = ttk.Frame(janela, padding=(10, 0, 10, 10))
        botoes.grid(row=3, column=0, sticky="ew")

        def confirmar():
            texto = texto_box.get("1.0", "end").strip()
            if not texto:
                messagebox.showerror("Erro", "Digite o texto de continuação.", parent=janela)
                return
            resultado["texto"] = texto
            janela.destroy()

        def cancelar():
            resultado["texto"] = ""
            janela.destroy()

        ttk.Button(botoes, text="Enviar e continuar", command=confirmar).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Cancelar", command=cancelar).pack(side="left")

        janela.protocol("WM_DELETE_WINDOW", cancelar)
        self.wait_window(janela)
        return resultado["texto"]

    def continuar_mesma_tarefa(self, task_id: str, titulo: str = "", url: str = "", parent=None) -> bool:
        """
        Continua uma tarefa já existente usando task.sendMessage.

        A ideia é continuar a MESMA tarefa, com o mesmo Task ID.
        Se a API permitir continuação após stopped, o app envia a mensagem e volta a acompanhar.
        Se a API recusar tarefa finalizada, o erro será mostrado claramente.
        """
        task_id = str(task_id or "").strip()
        if not task_id:
            messagebox.showerror("Erro", "Task ID vazio.", parent=parent or self)
            return False

        texto = self.pedir_texto_continuacao_tarefa(task_id, titulo=titulo, parent=parent or self)
        if not texto:
            return False

        task_url = url or f"https://manus.im/app/{task_id}"
        self.task_id_var.set(task_id)
        self.task_url_var.set(task_url)
        try:
            self.notebook.select(self.main_tab)
        except Exception:
            pass

        self.msg("task", task_id, task_url)
        self.msg("live", "\n================ CONTINUANDO A MESMA TAREFA ================\n")
        if titulo:
            self.msg("live", f"Título: {titulo}\n")
        self.msg("live", f"Task ID: {task_id}\n")
        self.msg("live", "[PEDIDO DE CONTINUAÇÃO]\n" + texto + "\n")
        self.msg("live", "============================================================\n")
        self.msg("log", f"[CONTINUAR] Enviando continuação para a mesma tarefa: {task_id}\n")
        self.msg(
            "task_status",
            "Tarefa: CONTINUANDO",
            "Fase atual: enviando nova mensagem",
            "Pistas do servidor: continuação solicitada pelo usuário via task.sendMessage",
            f"Atividade: pedido enviado em {agora_iso()}",
        )

        def worker():
            try:
                api = self.pegar_api()

                # Marca eventos antigos como vistos para a continuação não repetir toda a tarefa antiga.
                try:
                    data_antiga = api.list_messages(task_id, limit=200, slides_format="pptx")
                    mensagens_antigas = data_antiga.get("messages", [])
                    for ev in eventos_da_tarefa(mensagens_antigas):
                        self.eventos_vistos.add(ev["id"])
                    self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | contexto antigo lido")
                except Exception as e:
                    self.msg("log", f"[CONTINUAR] Não foi possível pré-carregar eventos antigos: {e}\n")

                api.send_message(task_id, texto)
                self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | task.sendMessage OK")
                self.msg("live", "\n[CONTINUAÇÃO ENVIADA]\n")
                self.salvar_checkpoint_tarefa("continuação enviada para mesma tarefa", {"continuation_text": texto})
                self.msg("log", "[CONTINUAR] Mensagem enviada. Acompanhando novamente a mesma tarefa.\n")

                if self.auto_log_var.get():
                    self.logger.log("continue_same_task", texto, task_id=task_id, task_url=task_url, title=titulo)

                self.stop_polling.clear()
                self.urls_baixadas.clear()
                self.acompanhar_tarefa(task_id)

            except Exception as e:
                if erro_credito_esgotado(e):
                    self.definir_creditos_esgotados(f"Falha ao continuar por limite/crédito: {agora_iso()} | {e}")
                    self.salvar_checkpoint_tarefa(
                        "crédito/limite ao enviar continuação",
                        {"credit_error": str(e), "pending_continuation_text": texto, "resume_task_id": task_id},
                    )
                    self.msg("credit_need_key", task_id, str(e))
                else:
                    self.definir_servidor_offline(f"Falha ao continuar tarefa: {agora_iso()} | {e}")
                    self.msg("erro", str(e))

        self.executar_thread(worker)
        return True

    def extrair_id_url_titulo_status_tarefa(self, task: Dict[str, Any]):
        """Normaliza os principais campos de uma tarefa retornada pela API."""
        tid = str(task.get("id") or task.get("task_id") or task.get("taskId") or task.get("uuid") or "").strip()
        titulo = str(task.get("title") or task.get("task_title") or task.get("name") or task.get("summary") or "Sem título")
        status = str(task.get("status") or task.get("agent_status") or task.get("state") or "--")
        updated = str(task.get("updated_at") or task.get("updatedAt") or task.get("created_at") or task.get("createdAt") or "")
        credit = task.get("credit_usage") or task.get("creditUsage") or task.get("credits") or ""
        url = str(task.get("task_url") or task.get("url") or (f"https://manus.im/app/{tid}" if tid else ""))
        return tid, titulo, status, updated, credit, url

    def carregar_tarefa_nao_terminada_no_app(self, task_id: str, titulo: str = "", url: str = "", status_inicial: str = ""):
        """
        Carrega uma tarefa ainda não terminada, reconstrói o histórico dentro do app
        e continua acompanhando a partir do ponto atual.
        """
        task_id = str(task_id or "").strip()
        if not task_id:
            messagebox.showerror("Erro", "Task ID vazio.")
            return

        task_url = url or f"https://manus.im/app/{task_id}"
        self.task_id_var.set(task_id)
        self.task_url_var.set(task_url)

        try:
            self.notebook.select(self.main_tab)
        except Exception:
            pass

        self.msg("task", task_id, task_url)
        self.msg("live", "\n================ CARREGANDO TAREFA NÃO TERMINADA ================\n")
        self.msg("live", f"Task ID: {task_id}\n")
        if titulo:
            self.msg("live", f"Título: {titulo}\n")
        if status_inicial:
            self.msg("live", f"Status da lista: {status_inicial}\n")
        self.msg("live", "Lendo o histórico completo para o app voltar como se já estivesse acompanhando desde o começo...\n")
        self.msg("live", "==================================================================\n")
        self.msg(
            "task_status",
            "Tarefa: CARREGANDO HISTÓRICO",
            "Fase atual: lendo mensagens já existentes",
            "Pistas do servidor: task.listMessages reconstruindo o contexto da tarefa",
            f"Atividade: carregamento iniciado em {agora_iso()}",
        )

        def worker():
            try:
                api = self.pegar_api()

                data = api.list_messages(task_id, limit=200, slides_format="pptx")
                self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | histórico carregado")

                messages = data.get("messages", [])
                status, status_raw = status_mais_recente(messages)

                # Mostra o histórico completo uma vez e marca como visto para não duplicar na sequência.
                self.eventos_vistos.clear()
                self.urls_baixadas.clear()

                self.msg("live", "\n[HISTÓRICO COMPLETO DA TAREFA]\n")
                self.msg("log", f"[RETOMAR] Histórico carregado: {len(messages)} mensagem(ns).\n")

                achou_algo = False
                ultima_resposta = ""

                for ev in eventos_da_tarefa(messages):
                    self.eventos_vistos.add(ev["id"])
                    kind = ev.get("kind")
                    text = ev.get("text") or ""

                    if kind == "status":
                        self.msg("log", f"[HISTÓRICO/STATUS] {text}\n")

                    elif kind == "assistant":
                        achou_algo = True
                        ultima_resposta = text
                        self.msg("live", "\n[MANUS / HISTÓRICO]\n")
                        self.msg("live", text + "\n")
                        if self.auto_log_var.get():
                            self.logger.log("unfinished_history_assistant", text, task_id=task_id)
                        if self.auto_download_var.get():
                            for link in extrair_urls_baixaveis(text):
                                self.baixar_e_registrar(link, task_id)

                    elif kind == "attachment":
                        achou_algo = True
                        anexo = ev.get("raw") or {}
                        link = anexo.get("url")
                        filename = anexo.get("filename") or anexo.get("file_name") or ""
                        self.msg("live", f"\n[ANEXO JÁ EXISTENTE]\n{filename or link}\n")
                        if self.auto_download_var.get() and link:
                            self.baixar_e_registrar(link, task_id, filename)

                    elif kind == "waiting_detail":
                        self.last_waiting_detail = ev.get("raw") or {}
                        self.msg("waiting", self.last_waiting_detail)
                        self.msg("live", "\n[MANUS AGUARDANDO / HISTÓRICO]\n" + text + "\n")
                        self.msg("log", "[RETOMAR] A tarefa parece estar aguardando resposta/confirmação.\n")

                    elif kind == "error":
                        achou_algo = True
                        self.msg("live", "\n[ERRO NO HISTÓRICO]\n" + text + "\n")
                        self.msg("log", "[RETOMAR/ERRO] " + text + "\n")

                if not achou_algo:
                    self.msg("live", "\n[INFO] Nenhuma resposta/anexo antigo foi retornado ainda. Vou acompanhar a partir de agora.\n")

                self.interpretar_status_tarefa(status, status_raw, messages)

                if ultima_resposta and self.auto_log_var.get():
                    self.logger.log("unfinished_task_last_response", ultima_resposta, task_id=task_id)

                self.salvar_checkpoint_tarefa("tarefa não terminada carregada", {"loaded_unfinished": True, "message_count": len(messages)})
                self.msg("live", "\n[RETOMADA ATIVA]\n")
                self.msg("live", "A tarefa foi carregada no aplicativo e o acompanhamento continuará daqui em diante.\n")

                if self.auto_log_var.get():
                    self.logger.log(
                        "unfinished_task_loaded",
                        "Tarefa não terminada carregada e retomada no app",
                        task_id=task_id,
                        task_url=task_url,
                        title=titulo,
                        status=status,
                        message_count=len(messages),
                    )

                self.stop_polling.clear()
                self.acompanhar_tarefa(task_id)

            except Exception as e:
                if erro_credito_esgotado(e):
                    self.definir_creditos_esgotados(f"Falha ao carregar tarefa por limite/crédito: {agora_iso()} | {e}")
                else:
                    self.definir_servidor_offline(f"Falha ao carregar tarefa não terminada: {agora_iso()} | {e}")
                self.msg("erro", str(e))

        self.executar_thread(worker)

    def abrir_tarefas_nao_terminadas(self):
        """
        Lista tarefas que ainda não terminaram e permite carregá-las no app
        para continuar acompanhando de onde estão.
        """
        try:
            api = self.pegar_api()
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        janela = tk.Toplevel(self)
        janela.title("Tarefas não terminadas - Retomar no aplicativo")
        janela.geometry("1340x620")
        janela.minsize(1100, 480)
        janela.columnconfigure(0, weight=1)
        janela.rowconfigure(0, weight=1)

        cols = ("status", "updated", "title", "task_id", "credit", "url")
        tree = ttk.Treeview(janela, columns=cols, show="headings", height=18)
        tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        config_cols = {
            "status": ("Status", 110),
            "updated": ("Atualizado/Criado", 170),
            "title": ("Título", 350),
            "task_id": ("Task ID", 260),
            "credit": ("Crédito", 90),
            "url": ("URL", 320),
        }
        for col, (header, width) in config_cols.items():
            tree.heading(col, text=header)
            tree.column(col, width=width, anchor="w")

        scroll_y = ttk.Scrollbar(janela, orient="vertical", command=tree.yview)
        scroll_y.grid(row=0, column=1, sticky="ns", pady=10)
        tree.configure(yscrollcommand=scroll_y.set)

        scroll_x = ttk.Scrollbar(janela, orient="horizontal", command=tree.xview)
        scroll_x.grid(row=1, column=0, sticky="ew", padx=10)
        tree.configure(xscrollcommand=scroll_x.set)

        tarefas_cache: Dict[str, Dict[str, Any]] = {}

        rodape = ttk.Frame(janela, padding=(10, 0, 10, 10))
        rodape.grid(row=2, column=0, columnspan=2, sticky="ew")
        rodape.columnconfigure(6, weight=1)

        status_lbl = ttk.Label(rodape, text="Clique em Atualizar para buscar tarefas ainda não finalizadas.")
        status_lbl.grid(row=1, column=0, columnspan=7, sticky="w", pady=(8, 0))

        def tarefa_selecionada():
            sel = tree.selection()
            if not sel:
                return None
            return tarefas_cache.get(sel[0])

        def carregar():
            tree.delete(*tree.get_children())
            tarefas_cache.clear()
            status_lbl.config(text="Buscando tarefas não terminadas na Manus...")

            def worker():
                try:
                    tasks = api.list_unfinished_tasks(max_pages=5, scope="all")
                    self.definir_servidor_online(f"Última resposta do servidor: {agora_iso()} | task.list tarefas não terminadas OK")
                    self.msg("log", f"[TAREFAS NÃO TERMINADAS] Encontradas: {len(tasks)}\n")
                    self.msg_queue.put(("unfinished_tasks_result", janela, tree, tarefas_cache, tasks, status_lbl))
                except Exception as e:
                    if erro_credito_esgotado(e):
                        self.definir_creditos_esgotados(f"Falha ao listar tarefas não terminadas: {agora_iso()} | {e}")
                    else:
                        self.definir_servidor_offline(f"Falha ao listar tarefas não terminadas: {agora_iso()} | {e}")
                    self.msg("erro", str(e))
                    self.msg_queue.put(("unfinished_tasks_error", status_lbl, str(e)))

            self.executar_thread(worker)

        def carregar_no_app():
            t = tarefa_selecionada()
            if not t:
                messagebox.showinfo("Informação", "Selecione uma tarefa não terminada.", parent=janela)
                return
            tid, titulo, status, updated, credit, url = self.extrair_id_url_titulo_status_tarefa(t)
            if not tid:
                messagebox.showerror("Erro", "Task ID vazio.", parent=janela)
                return
            janela.destroy()
            self.carregar_tarefa_nao_terminada_no_app(tid, titulo=titulo, url=url, status_inicial=status)

        def abrir_url():
            t = tarefa_selecionada()
            if not t:
                messagebox.showinfo("Informação", "Selecione uma tarefa.", parent=janela)
                return
            tid, titulo, status, updated, credit, url = self.extrair_id_url_titulo_status_tarefa(t)
            if url:
                webbrowser.open(url)

        def copiar_id():
            t = tarefa_selecionada()
            if not t:
                return
            tid, titulo, status, updated, credit, url = self.extrair_id_url_titulo_status_tarefa(t)
            self.clipboard_clear()
            self.clipboard_append(tid)
            status_lbl.config(text="Task ID copiado.")

        def copiar_url():
            t = tarefa_selecionada()
            if not t:
                return
            tid, titulo, status, updated, credit, url = self.extrair_id_url_titulo_status_tarefa(t)
            self.clipboard_clear()
            self.clipboard_append(url)
            status_lbl.config(text="URL copiada.")

        ttk.Button(rodape, text="Atualizar", command=carregar).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(rodape, text="Carregar e retomar no app", command=carregar_no_app).grid(row=0, column=1, padx=6)
        ttk.Button(rodape, text="Abrir no Manus", command=abrir_url).grid(row=0, column=2, padx=6)
        ttk.Button(rodape, text="Copiar ID", command=copiar_id).grid(row=0, column=3, padx=6)
        ttk.Button(rodape, text="Copiar URL", command=copiar_url).grid(row=0, column=4, padx=6)
        ttk.Button(rodape, text="Fechar", command=janela.destroy).grid(row=0, column=5, padx=6)

        tree.bind("<Double-1>", lambda e: carregar_no_app())
        carregar()

    def abrir_tarefas_concluidas(self):
        janela = tk.Toplevel(self)
        janela.title("Tarefas concluídas - Manus")
        janela.geometry("1320x600")
        janela.minsize(1100, 460)
        janela.columnconfigure(0, weight=1)
        janela.rowconfigure(1, weight=1)

        topo = ttk.Frame(janela, padding=10)
        topo.grid(row=0, column=0, sticky="ew")
        topo.columnconfigure(5, weight=1)

        ttk.Label(topo, text="Fonte:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        fonte_var = tk.StringVar(value="API + Local")
        fonte_combo = ttk.Combobox(topo, textvariable=fonte_var, state="readonly", width=14, values=["API + Local", "Só API", "Só Local"])
        fonte_combo.grid(row=0, column=1, sticky="w", padx=(0, 10))

        ttk.Label(topo, text="Páginas API:").grid(row=0, column=2, sticky="w", padx=(0, 6))
        paginas_var = tk.StringVar(value="5")
        ttk.Entry(topo, textvariable=paginas_var, width=6).grid(row=0, column=3, sticky="w", padx=(0, 10))

        status_label = ttk.Label(topo, text="Clique em Atualizar para carregar.")
        status_label.grid(row=0, column=5, sticky="w", padx=(10, 0))

        cols = ("status", "atualizado", "titulo", "id", "creditos", "fonte")
        tree = ttk.Treeview(janela, columns=cols, show="headings", selectmode="browse")
        tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        tree.heading("status", text="Status")
        tree.heading("atualizado", text="Atualizado")
        tree.heading("titulo", text="Título")
        tree.heading("id", text="Task ID")
        tree.heading("creditos", text="Créditos")
        tree.heading("fonte", text="Fonte")

        tree.column("status", width=90, stretch=False)
        tree.column("atualizado", width=150, stretch=False)
        tree.column("titulo", width=360, stretch=True)
        tree.column("id", width=210, stretch=False)
        tree.column("creditos", width=80, stretch=False)
        tree.column("fonte", width=90, stretch=False)

        scroll = ttk.Scrollbar(janela, orient="vertical", command=tree.yview)
        scroll.grid(row=1, column=1, sticky="ns", pady=(0, 8))
        tree.configure(yscrollcommand=scroll.set)

        rodape = ttk.Frame(janela, padding=(10, 0, 10, 10))
        rodape.grid(row=2, column=0, sticky="ew")
        rodape.columnconfigure(7, weight=1)

        tarefas_por_iid: Dict[str, Dict[str, Any]] = {}

        def tarefa_selecionada() -> Optional[Dict[str, Any]]:
            sel = tree.selection()
            if not sel:
                return None
            return tarefas_por_iid.get(sel[0])

        def limpar_tree():
            tarefas_por_iid.clear()
            for iid in tree.get_children():
                tree.delete(iid)

        def inserir_tarefas(tarefas: List[Dict[str, Any]]):
            limpar_tree()
            dedupe: Dict[str, Dict[str, Any]] = {}
            for t in tarefas:
                tid = str(t.get("id") or t.get("task_id") or "").strip()
                if not tid:
                    continue
                if tid not in dedupe:
                    dedupe[tid] = t
                else:
                    # Prefere dados vindos da API quando houver duplicidade.
                    if t.get("source") == "api":
                        dedupe[tid].update(t)

            ordenadas = sorted(
                dedupe.values(),
                key=lambda x: str(x.get("updated_at") or x.get("finished_at_local") or x.get("created_at") or ""),
                reverse=True,
            )

            for i, t in enumerate(ordenadas, start=1):
                tid = str(t.get("id") or t.get("task_id") or "")
                status = str(t.get("status") or "stopped")
                atualizado = formatar_timestamp(t.get("updated_at") or t.get("finished_at_local") or t.get("created_at"))
                titulo = str(t.get("title") or t.get("task_title") or "Sem título")
                creditos = str(t.get("credit_usage") or "")
                fonte = str(t.get("source") or "local")
                iid = f"task_{i}"
                tarefas_por_iid[iid] = t
                tree.insert("", "end", iid=iid, values=(status, atualizado, titulo, tid, creditos, fonte))

            status_label.configure(text=f"{len(ordenadas)} tarefa(s) concluída(s) carregada(s).")

        def carregar():
            def worker():
                try:
                    self.msg("log", "[TAREFAS] Carregando lista de tarefas concluídas...\n")
                    fonte = fonte_var.get()
                    todas: List[Dict[str, Any]] = []

                    if fonte in ("API + Local", "Só API"):
                        try:
                            api = self.pegar_api()
                            try:
                                max_pages = max(1, int(paginas_var.get().strip() or "5"))
                            except ValueError:
                                max_pages = 5
                            api_tasks = api.list_completed_tasks(max_pages=max_pages, scope="all")
                            todas.extend(api_tasks)
                        except Exception as e:
                            self.msg("log", f"[TAREFAS] Erro ao buscar na API: {e}\n")
                            if fonte == "Só API":
                                raise

                    if fonte in ("API + Local", "Só Local"):
                        local_tasks = carregar_historico_concluidas()
                        for t in local_tasks:
                            t.setdefault("source", "local")
                            t.setdefault("status", "stopped")
                        todas.extend(local_tasks)

                    janela.after(0, lambda: inserir_tarefas(todas))
                except Exception as e:
                    janela.after(0, lambda: messagebox.showerror("Erro", str(e), parent=janela))

            status_label.configure(text="Carregando...")
            threading.Thread(target=worker, daemon=True).start()

        def abrir_no_app():
            t = tarefa_selecionada()
            if not t:
                messagebox.showinfo("Informação", "Selecione uma tarefa.", parent=janela)
                return
            tid = str(t.get("id") or t.get("task_id") or "").strip()
            if not tid:
                messagebox.showerror("Erro", "Task ID vazio.", parent=janela)
                return
            titulo = str(t.get("title") or t.get("task_title") or "")
            url = str(t.get("task_url") or f"https://manus.im/app/{tid}")
            self.abrir_tarefa_no_app(tid, titulo=titulo, url=url)
            janela.destroy()

        def continuar_mesma():
            t = tarefa_selecionada()
            if not t:
                messagebox.showinfo("Informação", "Selecione uma tarefa concluída.", parent=janela)
                return
            tid = str(t.get("id") or t.get("task_id") or "").strip()
            if not tid:
                messagebox.showerror("Erro", "Task ID vazio.", parent=janela)
                return
            titulo = str(t.get("title") or t.get("task_title") or "")
            url = str(t.get("task_url") or f"https://manus.im/app/{tid}")
            iniciado = self.continuar_mesma_tarefa(tid, titulo=titulo, url=url, parent=janela)
            if iniciado:
                janela.destroy()

        def abrir_url():
            t = tarefa_selecionada()
            if not t:
                messagebox.showinfo("Informação", "Selecione uma tarefa.", parent=janela)
                return
            url = t.get("task_url") or ""
            if not url:
                tid = t.get("id") or t.get("task_id") or ""
                url = f"https://manus.im/app/{tid}" if tid else ""
            if url:
                webbrowser.open(url)

        def acompanhar():
            t = tarefa_selecionada()
            if not t:
                messagebox.showinfo("Informação", "Selecione uma tarefa.", parent=janela)
                return
            tid = str(t.get("id") or t.get("task_id") or "").strip()
            if not tid:
                return
            self.task_id_var.set(tid)
            self.task_url_var.set(t.get("task_url") or f"https://manus.im/app/{tid}")
            self.acompanhar_tarefa_atual()
            janela.destroy()

        def copiar_id():
            t = tarefa_selecionada()
            if not t:
                return
            tid = str(t.get("id") or t.get("task_id") or "").strip()
            if tid:
                self.clipboard_clear()
                self.clipboard_append(tid)
                status_label.configure(text="Task ID copiado.")

        def copiar_url():
            t = tarefa_selecionada()
            if not t:
                return
            tid = str(t.get("id") or t.get("task_id") or "").strip()
            url = str(t.get("task_url") or (f"https://manus.im/app/{tid}" if tid else ""))
            if url:
                self.clipboard_clear()
                self.clipboard_append(url)
                status_label.configure(text="URL copiada.")

        def baixar_resultados():
            t = tarefa_selecionada()
            if not t:
                messagebox.showinfo("Informação", "Selecione uma tarefa.", parent=janela)
                return
            tid = str(t.get("id") or t.get("task_id") or "").strip()
            if not tid:
                return
            self.task_id_var.set(tid)
            self.task_url_var.set(t.get("task_url") or f"https://manus.im/app/{tid}")
            self.stop_polling.clear()
            self.eventos_vistos.clear()
            self.urls_baixadas.clear()
            self.executar_thread(lambda: self._acompanhar_safe(tid))
            janela.destroy()

        ttk.Button(rodape, text="Atualizar", command=carregar).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(rodape, text="Abrir no aplicativo", command=abrir_no_app).grid(row=0, column=1, padx=6)
        ttk.Button(rodape, text="Continuar mesma tarefa", command=continuar_mesma).grid(row=0, column=2, padx=6)
        ttk.Button(rodape, text="Abrir no Manus", command=abrir_url).grid(row=0, column=3, padx=6)
        ttk.Button(rodape, text="Acompanhar/baixar resultados", command=baixar_resultados).grid(row=0, column=4, padx=6)
        ttk.Button(rodape, text="Copiar ID", command=copiar_id).grid(row=0, column=5, padx=6)
        ttk.Button(rodape, text="Copiar URL", command=copiar_url).grid(row=0, column=6, padx=6)
        ttk.Button(rodape, text="Fechar", command=janela.destroy).grid(row=0, column=7, padx=6)

        tree.bind("<Double-1>", lambda _e: abrir_no_app())
        carregar()

    def continuar_tarefa_atual(self):
        """Continua a tarefa atualmente informada em Task ID."""
        task_id = self.task_id_var.get().strip()
        if not task_id:
            messagebox.showerror("Erro", "Nenhum Task ID informado.")
            return
        titulo = self.title_var.get().strip()
        url = self.task_url_var.get().strip() or f"https://manus.im/app/{task_id}"
        self.continuar_mesma_tarefa(task_id, titulo=titulo, url=url, parent=self)

    def atualizar_label_anexos_resposta(self):
        """Atualiza o texto que mostra quantos arquivos estão anexados à resposta."""
        if not hasattr(self, "reply_files_label"):
            return
        if not self.reply_files:
            self.reply_files_label.configure(text="Nenhum arquivo anexado à resposta.")
            return
        total = 0
        for p in self.reply_files:
            try:
                total += p.stat().st_size
            except OSError:
                pass
        nomes = ", ".join(p.name for p in self.reply_files)
        self.reply_files_label.configure(
            text=f"{len(self.reply_files)} anexo(s) | {tamanho_legivel(total)}: {resumo_texto(nomes, 90)}"
        )

    def anexar_arquivos_resposta(self):
        """Seleciona arquivos para enviar ao Manus junto com a resposta."""
        paths = filedialog.askopenfilenames(
            title="Selecione arquivos para anexar à resposta",
            filetypes=[("Todos os arquivos", "*.*")],
        )
        if not paths:
            return
        existentes = {str(p.resolve()).lower() for p in self.reply_files}
        for item in paths:
            p = Path(item)
            chave = str(p.resolve()).lower()
            if chave not in existentes:
                self.reply_files.append(p)
                existentes.add(chave)
        self.atualizar_label_anexos_resposta()
        self.log(f"[RESPOSTA] {len(self.reply_files)} arquivo(s) anexado(s) à resposta.\n")

    def limpar_anexos_resposta(self):
        """Remove todos os arquivos anexados à resposta."""
        self.reply_files.clear()
        self.atualizar_label_anexos_resposta()
        self.log("[RESPOSTA] Anexos da resposta limpos.\n")

    def enviar_resposta_manus(self):
        task_id = self.task_id_var.get().strip()
        texto = self.reply_text.get("1.0", "end").strip()
        anexos = list(self.reply_files)
        if not task_id:
            messagebox.showerror("Erro", "Nenhum Task ID.")
            return
        if not texto and not anexos:
            messagebox.showerror("Erro", "Digite a resposta ou anexe ao menos um arquivo para enviar ao Manus.")
            return

        def worker():
            try:
                api = self.pegar_api()

                uploaded_files = []
                if anexos:
                    self.msg("log", f"[RESPOSTA] Enviando {len(anexos)} anexo(s) com a resposta...\n")
                    self.msg("upload_progress", 0.0, 0, 0, "aguardando upload da resposta")
                    for i, file_path in enumerate(anexos, start=1):
                        self.msg("log", f"\n[UPLOAD RESPOSTA {i}/{len(anexos)}] {file_path.name}\n")
                        info = api.upload_local_file(
                            file_path,
                            logger=self.logger if (hasattr(self, "logger") and self.logger and self.auto_log_var.get()) else None,
                            cb=lambda m: self.msg("log", f"[UPLOAD] {m}\n"),
                            progress_cb=lambda percent, sent, total, filename: self.enviar_progresso_upload(percent, sent, total, filename),
                        )
                        uploaded_files.append(info)
                        self.msg("log", f"[OK] Upload concluído: {info['filename']}\n")
                    self.msg("upload_progress", 100.0, 100, 100, "anexos da resposta enviados")

                self.msg("log", "[ENVIO] Enviando resposta ao Manus...\n")
                api.send_message(task_id, texto, uploaded_files=uploaded_files)
                self.mysql_conversa(task_id, "user", texto)

                resumo_anexos = ""
                if uploaded_files:
                    resumo_anexos = "\n[ANEXOS ENVIADOS]\n" + "\n".join(f"- {u['filename']}" for u in uploaded_files) + "\n"
                self.msg("live", "\n[VOCÊ RESPONDEU]\n" + (texto or "(sem texto)") + "\n" + resumo_anexos)

                if hasattr(self, "logger") and self.logger and self.auto_log_var.get():
                    self.logger.log(
                        "user_reply",
                        texto,
                        task_id=task_id,
                        attachments=[u["filename"] for u in uploaded_files],
                    )

                self.reply_text.delete("1.0", "end")
                self.reply_files.clear()
                self.msg("reply_files_cleared")
                self.stop_polling.clear()
                self.acompanhar_tarefa(task_id)
            except Exception as e:
                if erro_credito_esgotado(e) or erro_chave_invalida(e):
                    self.salvar_checkpoint_tarefa(
                        "crédito/chave bloqueou o envio de resposta",
                        {"reply_error": str(e), "resume_task_id": task_id},
                    )
                    self.msg("log", f"[RESPOSTA BLOQUEADA] {e}\n")
                    self.msg("credit_need_key", task_id, str(e))
                    return
                self.msg("erro", str(e))
        self.executar_thread(worker)

    def confirmar_acao_pendente(self):
        task_id = self.task_id_var.get().strip()
        detail = self.last_waiting_detail or {}
        event_id = detail.get("waiting_for_event_id")
        event_type = detail.get("waiting_for_event_type") or ""

        if not task_id:
            messagebox.showerror("Erro", "Nenhum Task ID.")
            return
        if not event_id:
            messagebox.showerror("Erro", "Nenhum evento pendente para confirmar.")
            return

        if event_type == "messageAskUser":
            messagebox.showinfo("Informação", "Este tipo precisa de resposta de texto. Use 'Enviar resposta ao Manus'.")
            return

        if not messagebox.askyesno("Confirmar ação", f"Confirmar a ação pendente?\n\nTipo: {event_type}\nEvento: {event_id}"):
            return

        def worker():
            try:
                api = self.pegar_api()
                self.msg("log", f"[CONFIRM] Confirmando ação {event_type}...\n")
                api.confirm_action(task_id, event_id, {"accept": True})
                self.stop_polling.clear()
                self.acompanhar_tarefa(task_id)
            except Exception as e:
                self.msg("erro", str(e))
        self.executar_thread(worker)

    def parar_acompanhamento(self):
        self.stop_polling.set()
        self.log("[INFO] Solicitado parar acompanhamento.\n")

    def abrir_tarefa(self):
        url = self.task_url_var.get().strip()
        if not url:
            messagebox.showerror("Erro", "Nenhuma URL de tarefa disponível.")
            return
        webbrowser.open(url)

    def limpar_log(self):
        self.log_text.delete("1.0", "end")
        self.realtime_text.delete("1.0", "end")

    def limpar_dados_locais(self):
        self.stop_polling.set()
        self.log_text.delete("1.0", "end")
        self.realtime_text.delete("1.0", "end")
        self.prompt_text.delete("1.0", "end")
        self.reply_text.delete("1.0", "end")
        self.task_id_var.set("")
        self.task_url_var.set("")
        self.selected_files.clear()
        self.reply_files.clear()
        self.downloaded_files.clear()
        self.downloads_list.delete(0, "end")
        self.eventos_vistos.clear()
        self.urls_baixadas.clear()
        self.last_waiting_detail = {}
        self.atualizar_lista_arquivos()
        self.atualizar_label_anexos_resposta()
        try:
            self.clipboard_clear()
        except Exception:
            pass
        self.log("[OK] Dados locais da tela limpos.\n")

    def salvar_resposta_manual(self):
        texto = self.realtime_text.get("1.0", "end").strip()
        if not texto:
            messagebox.showinfo("Informação", "Não há resposta para salvar.")
            return
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        task = self.task_id_var.get().strip() or "sem_task"
        path = LOG_DIR / f"{stamp}_{nome_seguro(task)}_resposta_manual.txt"
        path.write_text(texto, encoding="utf-8")
        self.log(f"[OK] Resposta salva manualmente em: {path}\n")

    def copiar_task_id(self):
        task_id = self.task_id_var.get().strip()
        if task_id:
            self.clipboard_clear()
            self.clipboard_append(task_id)
            self.log("[OK] Task ID copiado.\n")

    def copiar_task_url(self):
        url = self.task_url_var.get().strip()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.log("[OK] URL copiada.\n")

    def ao_fechar(self):
        """
        Fechamento seguro do aplicativo.

        - Em modo privacidade: limpa os dados locais e fecha.
        - Caso contrário: salva tudo (chaves, provedores, preferências,
          checkpoint da tarefa e rascunho) antes de fechar, para nada se perder.
        """
        try:
            if self.privacy_var.get():
                self.limpar_dados_locais()
            else:
                try:
                    self.salvar_chaves_multiplas_silencioso()
                except Exception:
                    pass
                try:
                    self.salvar_outros_provedores_ia_silencioso()
                except Exception:
                    pass
                try:
                    self.salvar_preferencias_locais()
                except Exception:
                    pass
                try:
                    self.salvar_checkpoint_tarefa("fechamento do aplicativo")
                except Exception:
                    pass
                try:
                    if hasattr(self, "prompt_text") and self.autosave_prompt_var.get():
                        self.salvar_rascunho_prompt()
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self.destroy()


def run_gui():
    app = ManusGui()
    app.mainloop()


def parse_args():
    p = argparse.ArgumentParser(description="Manus API completa: GUI, tempo real, logs, downloads e automação.")
    p.add_argument("--auto", action="store_true", help="Executa sem interface.")
    p.add_argument("--api-key", default="", help="API key. Preferível MANUS_API_KEY ou manus_api_key.local.")
    p.add_argument("--prompt", default="", help="Prompt para enviar ao Manus.")
    p.add_argument("--prompt-file", default="", help="Arquivo TXT com prompt.")
    p.add_argument("--file", action="append", default=[], help="Arquivo para anexar. Pode repetir.")
    p.add_argument("--agent-profile", default="manus-1.6-lite", choices=["manus-1.6-lite", "manus-1.6", "manus-1.6-max"])
    p.add_argument("--title", default="Tarefa Manus automatizada", help="Título da tarefa.")
    p.add_argument("--poll-interval", type=int, default=3, help="Intervalo de polling em segundos.")
    p.add_argument("--no-log", action="store_true", help="Desativa logs em arquivo.")
    p.add_argument("--no-download", action="store_true", help="Desativa download automático de anexos/links.")
    p.add_argument("--list-completed", action="store_true", help="Lista tarefas concluídas no terminal e sai.")
    p.add_argument("--completed-pages", type=int, default=5, help="Quantidade de páginas da API para varrer ao listar concluídas.")
    return p.parse_args()


def main():
    args = parse_args()

    if args.list_completed:
        try:
            api_key = carregar_api_key(args.api_key)
            api = ManusAPI(api_key)
            tarefas = api.list_completed_tasks(max_pages=max(1, args.completed_pages), scope="all")
            locais = carregar_historico_concluidas()
            merged: Dict[str, Dict[str, Any]] = {}
            for t in locais + tarefas:
                tid = str(t.get("id") or t.get("task_id") or "").strip()
                if tid:
                    merged[tid] = t
            for t in sorted(merged.values(), key=lambda x: str(x.get("updated_at") or x.get("finished_at_local") or ""), reverse=True):
                tid = str(t.get("id") or t.get("task_id") or "")
                title = str(t.get("title") or t.get("task_title") or "Sem título")
                updated = formatar_timestamp(t.get("updated_at") or t.get("finished_at_local") or t.get("created_at"))
                url = str(t.get("task_url") or (f"https://manus.im/app/{tid}" if tid else ""))
                print(f"{updated} | stopped | {tid} | {title} | {url}")
            return 0
        except Exception as e:
            print(f"[ERRO] {e}", file=sys.stderr)
            return 1

    if not args.auto:
        run_gui()
        return 0

    prompt = args.prompt.strip()
    if args.prompt_file:
        pf = Path(args.prompt_file)
        if not pf.exists():
            print(f"[ERRO] prompt-file não encontrado: {pf}", file=sys.stderr)
            return 1
        prompt = pf.read_text(encoding="utf-8").strip()
    if not prompt:
        print("[ERRO] Informe --prompt ou --prompt-file no modo --auto.", file=sys.stderr)
        return 1

    try:
        api_key = carregar_api_key(args.api_key)
    except Exception as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        return 1

    # No modo automação, o título também segue o padrão:
    # DATA HORA - Nova Tarefa
    # Se quiser forçar um título manual no terminal, passe --title diferente do padrão.
    auto_title = titulo_nova_tarefa()
    final_title = auto_title if not args.title or args.title == "Tarefa Manus automatizada" else args.title

    return run_automation(
        api_key=api_key,
        prompt=prompt,
        files=args.file,
        agent_profile=args.agent_profile,
        title=final_title,
        poll_interval=max(1, args.poll_interval),
        log_enabled=not args.no_log,
        download_enabled=not args.no_download,
    )


if __name__ == "__main__":
    raise SystemExit(main())
