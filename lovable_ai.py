#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lovable_ai.py
=============

Cliente simples para o Lovable AI Gateway (compatível com a API da OpenAI).

O Lovable AI Gateway usa a sua LOVABLE_API_KEY e expõe um endpoint
compatível com a OpenAI:

    https://ai.gateway.lovable.dev/v1/chat/completions

Este script permite:
  - Enviar um prompt de chat (com ou sem streaming)
  - Escolher o modelo (padrao: google/gemini-2.5-flash)
  - Usar a chave via variavel de ambiente (recomendado) ou --api-key

------------------------------------------------------------------
SEGURANCA
------------------------------------------------------------------
NUNCA deixe a API key escrita dentro do codigo ou em repositorios
publicos. Defina como variavel de ambiente antes de rodar:

    Linux / macOS:
        export LOVABLE_API_KEY="sua_chave_aqui"

    Windows (PowerShell):
        $env:LOVABLE_API_KEY="sua_chave_aqui"

Se a sua chave ja foi exposta, rotacione-a no Lovable
(Cloud -> Secrets -> Rotate) ou fale com support@lovable.dev.
------------------------------------------------------------------

USO
------------------------------------------------------------------
    # prompt unico
    python lovable_ai.py "Explique o que e um closure em JavaScript"

    # escolhendo modelo
    python lovable_ai.py -m openai/gpt-5 "Resuma este texto: ..."

    # com streaming (resposta token a token)
    python lovable_ai.py --stream "Escreva um haiku sobre o mar"

    # modo interativo (chat continuo)
    python lovable_ai.py --chat
------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# Endpoint do Lovable AI Gateway (compativel com OpenAI)
BASE_URL = "https://ai.gateway.lovable.dev/v1"
CHAT_ENDPOINT = f"{BASE_URL}/chat/completions"

# Modelo padrao. Outros exemplos:
#   google/gemini-2.5-flash        (rapido, barato - padrao)
#   google/gemini-2.5-pro          (raciocinio mais profundo)
#   openai/gpt-5                    (alta qualidade)
#   openai/gpt-5-mini               (equilibrio custo/velocidade)
DEFAULT_MODEL = "google/gemini-2.5-flash"


def get_api_key(cli_key: str | None) -> str:
    """Obtem a API key da linha de comando ou da variavel de ambiente."""
    key = cli_key or os.environ.get("LOVABLE_API_KEY")
    if not key:
        sys.exit(
            "ERRO: nenhuma API key encontrada.\n"
            "Defina a variavel de ambiente LOVABLE_API_KEY ou use --api-key.\n"
            '  export LOVABLE_API_KEY="sua_chave_aqui"'
        )
    return key


def build_request(api_key: str, payload: dict) -> urllib.request.Request:
    """Monta a requisicao HTTP para o gateway."""
    data = json.dumps(payload).encode("utf-8")
    return urllib.request.Request(
        CHAT_ENDPOINT,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )


def chat_once(api_key: str, model: str, messages: list[dict]) -> str:
    """Faz uma chamada nao-streaming e retorna o texto da resposta."""
    payload = {"model": model, "messages": messages, "stream": False}
    req = build_request(api_key, payload)
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        _handle_http_error(e)
    except urllib.error.URLError as e:
        sys.exit(f"ERRO de conexao: {e.reason}")

    return body["choices"][0]["message"]["content"]


def chat_stream(api_key: str, model: str, messages: list[dict]) -> str:
    """Faz uma chamada com streaming (SSE) e imprime token a token."""
    payload = {"model": model, "messages": messages, "stream": True}
    req = build_request(api_key, payload)
    full_text = ""
    try:
        with urllib.request.urlopen(req) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                piece = delta.get("content")
                if piece:
                    full_text += piece
                    print(piece, end="", flush=True)
        print()  # nova linha ao final
    except urllib.error.HTTPError as e:
        _handle_http_error(e)
    except urllib.error.URLError as e:
        sys.exit(f"ERRO de conexao: {e.reason}")

    return full_text


def _handle_http_error(e: urllib.error.HTTPError):
    """Traduz erros comuns do gateway."""
    detail = ""
    try:
        detail = e.read().decode("utf-8")
    except Exception:
        pass
    if e.code == 401:
        msg = "API key invalida ou ausente (401)."
    elif e.code == 402:
        msg = "Sem creditos disponiveis no workspace (402). Adicione creditos no Lovable."
    elif e.code == 429:
        msg = "Muitas requisicoes - limite de taxa atingido (429). Tente novamente em instantes."
    else:
        msg = f"Erro HTTP {e.code}."
    sys.exit(f"ERRO: {msg}\n{detail}")


def interactive_chat(api_key: str, model: str):
    """Loop de chat continuo no terminal."""
    print(f"Chat interativo com Lovable AI ({model}).")
    print("Digite 'sair' ou Ctrl+C para encerrar.\n")
    history: list[dict] = [
        {"role": "system", "content": "Voce e um assistente util e direto."}
    ]
    try:
        while True:
            user_msg = input("Voce: ").strip()
            if user_msg.lower() in {"sair", "exit", "quit"}:
                break
            if not user_msg:
                continue
            history.append({"role": "user", "content": user_msg})
            print("IA: ", end="", flush=True)
            answer = chat_stream(api_key, model, history)
            history.append({"role": "assistant", "content": answer})
    except (KeyboardInterrupt, EOFError):
        print("\nEncerrando.")


def main():
    parser = argparse.ArgumentParser(
        description="Cliente do Lovable AI Gateway (compativel com OpenAI)."
    )
    parser.add_argument("prompt", nargs="*", help="Texto do prompt.")
    parser.add_argument(
        "-m", "--model", default=DEFAULT_MODEL,
        help=f"Modelo a usar (padrao: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="API key (prefira a variavel de ambiente LOVABLE_API_KEY).",
    )
    parser.add_argument(
        "--stream", action="store_true",
        help="Recebe a resposta em streaming (token a token).",
    )
    parser.add_argument(
        "--chat", action="store_true",
        help="Inicia um chat interativo continuo.",
    )
    parser.add_argument(
        "--system", default="Voce e um assistente util e direto.",
        help="Mensagem de sistema para orientar o modelo.",
    )
    args = parser.parse_args()

    api_key = get_api_key(args.api_key)

    if args.chat:
        interactive_chat(api_key, args.model)
        return

    prompt_text = " ".join(args.prompt).strip()
    if not prompt_text:
        parser.error("informe um prompt ou use --chat para o modo interativo.")

    messages = [
        {"role": "system", "content": args.system},
        {"role": "user", "content": prompt_text},
    ]

    if args.stream:
        chat_stream(api_key, args.model, messages)
    else:
        print(chat_once(api_key, args.model, messages))


if __name__ == "__main__":
    main()
