#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat com IA via API.

Este script solicita a chave de API de uma IA (OpenAI, OpenRouter, Groq, etc.)
e em seguida inicia uma conversa interativa no terminal usando essa chave.

Uso:
    python chat_ia.py

Requisitos:
    pip install requests
"""

import os
import sys
import json
import getpass

try:
    import requests
except ImportError:
    print("Erro: a biblioteca 'requests' nao esta instalada.")
    print("Instale com: pip install requests")
    sys.exit(1)


# Provedores compativeis com o padrao OpenAI (endpoint /chat/completions)
PROVEDORES = {
    "1": {
        "nome": "OpenAI",
        "url": "https://api.openai.com/v1/chat/completions",
        "modelo_padrao": "gpt-4o-mini",
    },
    "2": {
        "nome": "OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "modelo_padrao": "openai/gpt-4o-mini",
    },
    "3": {
        "nome": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "modelo_padrao": "llama-3.3-70b-versatile",
    },
    "4": {
        "nome": "DeepSeek",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "modelo_padrao": "deepseek-chat",
    },
}


def escolher_provedor():
    """Mostra o menu de provedores e retorna o escolhido."""
    print("=" * 50)
    print("        CHAT COM IA - Selecione o provedor")
    print("=" * 50)
    for chave, info in PROVEDORES.items():
        print(f"  {chave}. {info['nome']}")
    print("=" * 50)

    while True:
        opcao = input("Escolha o provedor (numero): ").strip()
        if opcao in PROVEDORES:
            return PROVEDORES[opcao]
        print("Opcao invalida. Tente novamente.")


def solicitar_chave():
    """Solicita a chave de API do usuario de forma segura."""
    # Permite reutilizar a chave de uma variavel de ambiente, se existir.
    chave_env = os.environ.get("IA_API_KEY")
    if chave_env:
        usar = input("Foi encontrada a variavel IA_API_KEY. Usar? (s/n): ").strip().lower()
        if usar == "s":
            return chave_env

    while True:
        # getpass evita que a chave apareca na tela enquanto e digitada.
        chave = getpass.getpass("Digite sua chave de API da IA: ").strip()
        if chave:
            return chave
        print("A chave nao pode ser vazia. Tente novamente.")


def solicitar_modelo(modelo_padrao):
    """Permite escolher o modelo (ou usa o padrao)."""
    modelo = input(f"Modelo [{modelo_padrao}]: ").strip()
    return modelo or modelo_padrao


def enviar_mensagem(url, chave, modelo, historico):
    """Envia o historico de conversa para a API e retorna a resposta da IA."""
    headers = {
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": modelo,
        "messages": historico,
        "temperature": 0.7,
    }

    resposta = requests.post(url, headers=headers, json=payload, timeout=60)

    if resposta.status_code != 200:
        raise RuntimeError(
            f"Erro {resposta.status_code} da API: {resposta.text}"
        )

    dados = resposta.json()
    return dados["choices"][0]["message"]["content"]


def main():
    provedor = escolher_provedor()
    chave = solicitar_chave()
    modelo = solicitar_modelo(provedor["modelo_padrao"])

    print("\n" + "=" * 50)
    print(f"Conectado a {provedor['nome']} usando o modelo '{modelo}'.")
    print("Digite sua mensagem e pressione Enter para conversar.")
    print("Comandos: 'sair' para encerrar, 'limpar' para reiniciar a conversa.")
    print("=" * 50 + "\n")

    # Historico da conversa (contexto enviado a cada requisicao).
    historico = [
        {"role": "system", "content": "Voce e um assistente util e responde em portugues."}
    ]

    while True:
        try:
            entrada = input("Voce: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando. Ate logo!")
            break

        if not entrada:
            continue

        if entrada.lower() in ("sair", "exit", "quit"):
            print("Encerrando. Ate logo!")
            break

        if entrada.lower() == "limpar":
            historico = [historico[0]]
            print("Conversa reiniciada.\n")
            continue

        historico.append({"role": "user", "content": entrada})

        try:
            resposta = enviar_mensagem(provedor["url"], chave, modelo, historico)
        except Exception as erro:
            print(f"\n[Erro] {erro}\n")
            # Remove a ultima mensagem do usuario para nao poluir o historico.
            historico.pop()
            continue

        historico.append({"role": "assistant", "content": resposta})
        print(f"\nIA: {resposta}\n")


if __name__ == "__main__":
    main()
