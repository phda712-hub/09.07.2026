#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lovable_chat_gui.py
===================

Chat com interface grafica (Tkinter) para o Lovable AI Gateway
(endpoint compativel com a API da OpenAI).

Basta executar:

    python lovable_chat_gui.py

A janela de chat abre pronta para conversar. A resposta chega
em streaming (token a token) dentro da janela.

------------------------------------------------------------------
CONFIGURACAO (edite os valores abaixo se precisar)
------------------------------------------------------------------
  - API_KEY   : a chave usada para autenticar.
  - BASE_URL  : endpoint da API (padrao: Lovable AI Gateway).
  - MODEL     : modelo de IA usado.

ATENCAO / SEGURANCA:
  A chave esta embutida no codigo conforme solicitado. Como uma
  chave "_live_" exposta e um risco, considere rotaciona-la depois.
  O Lovable AI Gateway espera chaves que comecam com "sk_"; se a
  sua chave for de outro servico, troque BASE_URL/MODEL de acordo.
------------------------------------------------------------------
"""

from __future__ import annotations

import json
import threading
import urllib.request
import urllib.error

import tkinter as tk
from tkinter import scrolledtext, messagebox

# ====================== CONFIGURACAO ==============================
# Chave embutida (conforme solicitado).
API_KEY = "21098106_live_vD6VqTsAMNjjWFOMljo20iNGqu9DX1dH"

# Endpoint compativel com OpenAI. Padrao: Lovable AI Gateway.
BASE_URL = "https://ai.gateway.lovable.dev/v1/chat/completions"

# Modelo de IA. Exemplos do Lovable:
#   google/gemini-2.5-flash   (rapido/barato - padrao)
#   google/gemini-2.5-pro     (raciocinio profundo)
#   openai/gpt-5              / openai/gpt-5-mini
MODEL = "google/gemini-2.5-flash"

# Mensagem de sistema que orienta o assistente.
SYSTEM_PROMPT = "Voce e um assistente util, direto e responde em portugues do Brasil."
# ==================================================================


class ChatApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Lovable AI - Chat")
        self.root.geometry("720x560")
        self.root.minsize(520, 400)

        # Historico da conversa (com a mensagem de sistema).
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

        self._build_ui()
        self._append_system_line(
            f"Conectado ao modelo: {MODEL}\n"
            "Digite sua mensagem abaixo e pressione Enter (ou clique em Enviar).\n"
            + "-" * 60 + "\n"
        )

    # ---------------------------- UI ----------------------------
    def _build_ui(self):
        # Area de conversa
        self.chat_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state=tk.DISABLED,
            font=("Segoe UI", 11), bg="#1e1e1e", fg="#e6e6e6",
            insertbackground="#e6e6e6", padx=10, pady=10,
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

        # Cores por tipo de remetente
        self.chat_area.tag_config("user", foreground="#4fc3f7", font=("Segoe UI", 11, "bold"))
        self.chat_area.tag_config("assistant", foreground="#a5d6a7", font=("Segoe UI", 11, "bold"))
        self.chat_area.tag_config("assistant_text", foreground="#e6e6e6")
        self.chat_area.tag_config("system", foreground="#9e9e9e", font=("Segoe UI", 9, "italic"))
        self.chat_area.tag_config("error", foreground="#ef9a9a")

        # Barra inferior: campo de texto + botao
        bottom = tk.Frame(self.root, bg="#2b2b2b")
        bottom.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.entry = tk.Text(bottom, height=3, wrap=tk.WORD, font=("Segoe UI", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6), pady=6)
        self.entry.focus_set()
        # Enter envia; Shift+Enter quebra linha
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)

        btns = tk.Frame(bottom, bg="#2b2b2b")
        btns.pack(side=tk.RIGHT, pady=6)

        self.send_btn = tk.Button(
            btns, text="Enviar", command=self.send_message,
            bg="#4caf50", fg="white", activebackground="#43a047",
            font=("Segoe UI", 10, "bold"), width=10, relief=tk.FLAT,
        )
        self.send_btn.pack(pady=(0, 4))

        self.clear_btn = tk.Button(
            btns, text="Limpar", command=self.clear_chat,
            bg="#616161", fg="white", activebackground="#525252",
            font=("Segoe UI", 10), width=10, relief=tk.FLAT,
        )
        self.clear_btn.pack()

    # ------------------------ Helpers UI ------------------------
    def _append(self, text: str, tag: str | None = None):
        self.chat_area.config(state=tk.NORMAL)
        if tag:
            self.chat_area.insert(tk.END, text, tag)
        else:
            self.chat_area.insert(tk.END, text)
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def _append_system_line(self, text: str):
        self._append(text, "system")

    def _on_enter(self, event):
        # Enter sem Shift -> envia (e nao insere quebra de linha)
        if not (event.state & 0x0001):  # 0x0001 = Shift
            self.send_message()
            return "break"
        return None

    # ------------------------ Acoes -----------------------------
    def clear_chat(self):
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state=tk.DISABLED)
        self._append_system_line("Conversa limpa.\n" + "-" * 60 + "\n")

    def send_message(self):
        user_msg = self.entry.get("1.0", tk.END).strip()
        if not user_msg:
            return
        self.entry.delete("1.0", tk.END)

        self._append("Voce: ", "user")
        self._append(user_msg + "\n")
        self.history.append({"role": "user", "content": user_msg})

        # Desabilita envio enquanto processa
        self._set_busy(True)
        self._append("IA: ", "assistant")

        # Chamada em thread para nao travar a interface
        threading.Thread(target=self._request_worker, daemon=True).start()

    def _set_busy(self, busy: bool):
        state = tk.DISABLED if busy else tk.NORMAL
        self.send_btn.config(state=state)
        self.entry.config(state=state)

    # -------------------- Chamada a API -------------------------
    def _request_worker(self):
        payload = {"model": MODEL, "messages": self.history, "stream": True}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            BASE_URL, data=data, method="POST",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
        )

        collected = ""
        try:
            with urllib.request.urlopen(req) as resp:
                for raw in resp:
                    line = raw.decode("utf-8").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    chunk_data = line[len("data:"):].strip()
                    if chunk_data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(chunk_data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    piece = delta.get("content")
                    if piece:
                        collected += piece
                        self.root.after(0, self._append, piece, "assistant_text")
        except urllib.error.HTTPError as e:
            self._handle_error(e)
            collected = ""
        except urllib.error.URLError as e:
            self.root.after(0, self._append, f"\n[Erro de conexao: {e.reason}]\n", "error")
            collected = ""
        finally:
            if collected:
                self.history.append({"role": "assistant", "content": collected})
            self.root.after(0, self._append, "\n")
            self.root.after(0, self._set_busy, False)
            self.root.after(0, self.entry.focus_set)

    def _handle_error(self, e: urllib.error.HTTPError):
        detail = ""
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            pass
        if e.code == 401:
            msg = "401 - Chave invalida ou de formato incorreto para este endpoint."
        elif e.code == 402:
            msg = "402 - Sem creditos disponiveis no workspace."
        elif e.code == 429:
            msg = "429 - Muitas requisicoes (limite de taxa). Tente novamente em instantes."
        else:
            msg = f"Erro HTTP {e.code}."
        self.root.after(0, self._append, f"\n[{msg}]\n", "error")
        if detail:
            self.root.after(0, self._append, f"{detail}\n", "error")


def main():
    root = tk.Tk()
    ChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
