#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat com IA via API.

Este script solicita a chave de API de uma IA (Manus, OpenAI, OpenRouter, Groq,
DeepSeek) e em seguida inicia uma conversa interativa no terminal usando essa chave.

Observacao sobre o Manus:
    O Manus NAO usa o padrao "chat/completions". Ele funciona com tarefas
    assincronas (task.create / task.sendMessage / task.listMessages). Por isso o
    script trata o Manus de forma separada: cria uma tarefa na primeira mensagem
    e continua a conversa na mesma tarefa, aguardando (polling) a resposta.

Uso:
    python chat_ia.py

Requisitos:
    pip install requests
"""

import os
import sys
import time
import getpass

try:
    import requests
except ImportError:
    print("Erro: a biblioteca 'requests' nao esta instalada.")
    print("Instale com: pip install requests")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Provedores compativeis com o padrao OpenAI (endpoint /chat/completions)
# ---------------------------------------------------------------------------
PROVEDORES_OPENAI = {
    "2": {
        "nome": "OpenAI",
        "url": "https://api.openai.com/v1/chat/completions",
        "modelo_padrao": "gpt-4o-mini",
    },
    "3": {
        "nome": "OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "modelo_padrao": "openai/gpt-4o-mini",
    },
    "4": {
        "nome": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "modelo_padrao": "llama-3.3-70b-versatile",
    },
    "5": {
        "nome": "DeepSeek",
        "url": "https://api.deepseek.com/v1/chat/completions",
        "modelo_padrao": "deepseek-chat",
    },
}

# ---------------------------------------------------------------------------
# Configuracao do Manus (API baseada em tarefas)
# ---------------------------------------------------------------------------
MANUS_BASE_URL = "https://api.manus.ai"
MANUS_MODELOS = ["manus-1.6-lite", "manus-1.6", "manus-1.6-max"]
MANUS_MODELO_PADRAO = "manus-1.6-lite"


def escolher_provedor():
    """Mostra o menu de provedores e retorna a opcao escolhida."""
    print("=" * 55)
    print("          CHAT COM IA - Selecione o provedor")
    print("=" * 55)
    print("  1. Manus")
    for chave, info in PROVEDORES_OPENAI.items():
        print(f"  {chave}. {info['nome']}")
    print("=" * 55)

    while True:
        opcao = input("Escolha o provedor (numero): ").strip()
        if opcao == "1":
            return "manus"
        if opcao in PROVEDORES_OPENAI:
            return PROVEDORES_OPENAI[opcao]
        print("Opcao invalida. Tente novamente.")


def solicitar_chave(nome_var="IA_API_KEY"):
    """Solicita a chave de API do usuario de forma segura."""
    # Permite reutilizar a chave de uma variavel de ambiente, se existir.
    chave_env = os.environ.get(nome_var)
    if chave_env:
        usar = input(f"Foi encontrada a variavel {nome_var}. Usar? (s/n): ").strip().lower()
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


def escolher_modelo_manus():
    """
    Menu numerado para escolher o tier do Manus.

    O valor retornado e enviado LITERALMENTE no campo 'agent_profile' da API,
    ou seja, e o que realmente define o modelo usado na tarefa.
    """
    print("\nEscolha o modelo (tier) do Manus:")
    for i, nome in enumerate(MANUS_MODELOS, start=1):
        marca = "  (padrao)" if nome == MANUS_MODELO_PADRAO else ""
        print(f"  {i}. {nome}{marca}")

    while True:
        escolha = input(f"Numero [1-{len(MANUS_MODELOS)}]: ").strip()
        if not escolha:
            return MANUS_MODELO_PADRAO
        if escolha.isdigit() and 1 <= int(escolha) <= len(MANUS_MODELOS):
            return MANUS_MODELOS[int(escolha) - 1]
        print("Opcao invalida. Tente novamente.")


# ===========================================================================
# Fluxo dos provedores compativeis com OpenAI
# ===========================================================================
def enviar_mensagem_openai(url, chave, modelo, historico):
    """Envia o historico de conversa para a API (padrao OpenAI) e retorna a resposta."""
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
        raise RuntimeError(f"Erro {resposta.status_code} da API: {resposta.text}")

    dados = resposta.json()
    return dados["choices"][0]["message"]["content"]


def chat_openai(provedor):
    """Loop de conversa para provedores compativeis com OpenAI."""
    chave = solicitar_chave()
    modelo = solicitar_modelo(provedor["modelo_padrao"])

    print("\n" + "=" * 55)
    print(f"Conectado a {provedor['nome']} usando o modelo '{modelo}'.")
    print("Digite sua mensagem e pressione Enter para conversar.")
    print("Comandos: 'sair' para encerrar, 'limpar' para reiniciar a conversa.")
    print("=" * 55 + "\n")

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
            resposta = enviar_mensagem_openai(provedor["url"], chave, modelo, historico)
        except Exception as erro:
            print(f"\n[Erro] {erro}\n")
            historico.pop()
            continue

        historico.append({"role": "assistant", "content": resposta})
        print(f"\nIA: {resposta}\n")


# ===========================================================================
# Fluxo do Manus (API baseada em tarefas)
# ===========================================================================
def manus_request(metodo, caminho, chave, params=None, body=None, timeout=120):
    """Faz uma requisicao para a API do Manus com o header de autenticacao correto."""
    url = MANUS_BASE_URL.rstrip("/") + caminho
    headers = {
        "x-manus-api-key": chave,
        "Content-Type": "application/json",
    }
    resposta = requests.request(
        metodo.upper(), url, headers=headers, params=params, json=body, timeout=timeout
    )
    try:
        dados = resposta.json()
    except ValueError:
        raise RuntimeError(f"Resposta nao veio em JSON (HTTP {resposta.status_code}): {resposta.text[:500]}")

    if not resposta.ok or dados.get("ok") is False:
        if resposta.status_code == 429:
            raise RuntimeError("Credito/limite da Manus esgotado (HTTP 429).")
        raise RuntimeError(f"Erro da API Manus (HTTP {resposta.status_code}): {dados}")

    return dados


def manus_criar_tarefa(chave, modelo, prompt):
    """Cria uma nova tarefa no Manus em modo interativo (chat)."""
    body = {
        "message": {"content": [{"type": "text", "text": prompt}]},
        "locale": "pt-BR",
        "interactive_mode": True,   # mantem a tarefa aberta para conversa
        "hide_in_task_list": False,
        "share_visibility": "private",
        "agent_profile": modelo,
        "title": "Conversa via chat_ia.py",
    }
    dados = manus_request("POST", "/v2/task.create", chave, body=body)
    return dados.get("task_id") or ""


def manus_enviar_mensagem(chave, task_id, texto):
    """Envia uma nova mensagem para uma tarefa Manus ja existente."""
    body = {
        "task_id": task_id,
        "message": {"content": [{"type": "text", "text": texto}]},
    }
    manus_request("POST", "/v2/task.sendMessage", chave, body=body)


def _extrair_texto_assistente(assistant_message):
    """Extrai o texto de uma mensagem do assistente do Manus."""
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


def manus_aguardar_resposta(chave, task_id, ids_ja_vistos, tempo_max=600):
    """
    Faz polling em task.listMessages ate aparecer uma nova resposta do assistente
    ou a tarefa ficar aguardando entrada do usuario.

    Retorna (texto_resposta, novos_ids_vistos).
    """
    inicio = time.time()
    espera = 3  # segundos entre consultas

    while time.time() - inicio < tempo_max:
        dados = manus_request(
            "GET",
            "/v2/task.listMessages",
            chave,
            params={"task_id": task_id, "order": "desc", "limit": 50, "verbose": "false"},
        )
        mensagens = dados.get("messages") or dados.get("data") or []

        # Procura a mensagem de assistente mais recente ainda nao exibida.
        respostas = []
        aguardando = False
        for msg in mensagens:
            msg_id = str(msg.get("id") or msg.get("timestamp") or "")

            status_update = msg.get("status_update")
            if status_update:
                st = str(status_update.get("agent_status") or "").strip().lower()
                if st in ("waiting", "idle", "stopped", "completed", "finished"):
                    aguardando = True

            assistant = msg.get("assistant_message")
            if assistant and msg_id and msg_id not in ids_ja_vistos:
                texto = _extrair_texto_assistente(assistant)
                if texto:
                    respostas.append((msg_id, texto))

        if respostas:
            # As mensagens vem em ordem decrescente; junta em ordem cronologica.
            respostas.reverse()
            texto_final = "\n".join(t for _, t in respostas)
            for mid, _ in respostas:
                ids_ja_vistos.add(mid)
            return texto_final, ids_ja_vistos

        if aguardando:
            # A tarefa parou sem nova resposta textual detectada.
            return "", ids_ja_vistos

        print("  (Manus processando... aguarde)")
        time.sleep(espera)

    raise RuntimeError("Tempo limite excedido aguardando a resposta do Manus.")


def chat_manus():
    """Loop de conversa para o Manus (baseado em tarefas)."""
    chave = solicitar_chave(nome_var="MANUS_API_KEY")
    modelo = escolher_modelo_manus()

    print("\n" + "=" * 55)
    print(f"Conectado ao Manus. Tier ATIVO (agent_profile): '{modelo}'")
    print("Este valor e enviado de verdade a API ao criar cada tarefa.")
    print("-" * 55)
    print("Comandos:")
    print("  /modelo  -> trocar o tier (inicia uma nova tarefa no novo tier)")
    print("  /tier    -> mostrar o tier ativo neste momento")
    print("  sair     -> encerrar")
    print("-" * 55)
    print("Obs.: o Manus processa tarefas; a resposta pode levar alguns segundos.")
    print("AVISO: se voce perguntar ao Manus 'qual modelo sou eu?', a resposta")
    print("dele nao e confiavel (ele nao tem introspecao real do proprio tier).")
    print("A fonte de verdade e o 'agent_profile' que este script envia (acima).")
    print("=" * 55 + "\n")

    task_id = ""
    ids_vistos = set()

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

        # Mostra o tier realmente ativo (valor enviado a API).
        if entrada.lower() in ("/tier", "/modelo?", "tier"):
            print(f"\n>> Tier ATIVO (agent_profile enviado a API): '{modelo}'\n")
            continue

        # Troca o tier. Como o agent_profile e definido na CRIACAO da tarefa,
        # trocar o tier obrigatoriamente inicia uma nova tarefa.
        if entrada.lower() in ("/modelo", "/trocar", "modelo"):
            novo = escolher_modelo_manus()
            if novo != modelo:
                modelo = novo
                task_id = ""          # forca criar nova tarefa no novo tier
                ids_vistos = set()
                print(f"\n>> Tier alterado para '{modelo}'. A proxima mensagem "
                      f"iniciara uma NOVA tarefa neste tier.\n")
            else:
                print(f"\n>> Tier mantido em '{modelo}'.\n")
            continue

        try:
            if not task_id:
                # Primeira mensagem (ou apos troca de tier): cria a tarefa.
                task_id = manus_criar_tarefa(chave, modelo, entrada)
                if not task_id:
                    print("\n[Erro] Nao foi possivel criar a tarefa no Manus.\n")
                    continue
                # PROVA REAL: mostramos o agent_profile que ENVIAMOS a API.
                print(f"  (tarefa criada: {task_id} | agent_profile enviado = '{modelo}')")
            else:
                # Continua a conversa na mesma tarefa (mesmo tier).
                manus_enviar_mensagem(chave, task_id, entrada)

            resposta, ids_vistos = manus_aguardar_resposta(chave, task_id, ids_vistos)
        except Exception as erro:
            print(f"\n[Erro] {erro}\n")
            continue

        if resposta:
            print(f"\nManus [{modelo}]: {resposta}\n")
        else:
            print("\nManus: (sem resposta textual; a tarefa pode estar aguardando ou concluida)\n")


def main():
    escolha = escolher_provedor()
    if escolha == "manus":
        chat_manus()
    else:
        chat_openai(escolha)


if __name__ == "__main__":
    main()
