# -*- coding: utf-8 -*-
"""
Script de migracao: copia a coluna DESCRICAO da tabela TGRUPOS_PRODUTOS
(banco Firebird 2.5) para a tabela 'categorias' (banco MySQL 'quantum').

Regras de preenchimento na tabela MySQL 'categorias':
    - id         -> proximo numero apos o ultimo id existente (ou 1 se vazia)
    - nome       -> valor de DESCRICAO (Firebird)
    - descricao  -> mesmo valor de DESCRICAO (Firebird)
    - ativo      -> sempre 1
    - created_at -> data/hora atual (yyyy-MM-dd HH:mm:ss)
    - updated_at -> data/hora atual (yyyy-MM-dd HH:mm:ss)

Dependencias (instale antes de rodar):
    pip install fdb mysql-connector-python

Obs.: 'fdb' precisa da client library do Firebird (fbclient.dll) instalada.
      Para Firebird 2.5 use a versao correta do cliente (32/64 bits) compativel
      com o seu Python.
"""

import sys
from datetime import datetime

# ----------------------------------------------------------------------------
# CONFIGURACOES DE CONEXAO  (ajuste se necessario)
# ----------------------------------------------------------------------------
FIREBIRD_CONFIG = {
    "dsn": r"localhost:C:\Topvendas\BD\TOPVENDAS.FDB",
    "user": "SYSDBA",
    "password": "masterkey",
    "charset": "WIN1252",   # charset comum em bases Firebird brasileiras
}

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "quantum",
}


def conectar_firebird():
    """Abre conexao com o banco Firebird."""
    try:
        import fdb
    except ImportError:
        print("ERRO: modulo 'fdb' nao encontrado. Instale com: pip install fdb")
        sys.exit(1)

    try:
        con = fdb.connect(
            dsn=FIREBIRD_CONFIG["dsn"],
            user=FIREBIRD_CONFIG["user"],
            password=FIREBIRD_CONFIG["password"],
            charset=FIREBIRD_CONFIG["charset"],
        )
        print("[OK] Conectado ao Firebird.")
        return con
    except Exception as e:
        print(f"ERRO ao conectar no Firebird: {e}")
        sys.exit(1)


def conectar_mysql():
    """Abre conexao com o banco MySQL."""
    try:
        import mysql.connector
    except ImportError:
        print("ERRO: modulo 'mysql-connector-python' nao encontrado. "
              "Instale com: pip install mysql-connector-python")
        sys.exit(1)

    try:
        con = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            database=MYSQL_CONFIG["database"],
        )
        print("[OK] Conectado ao MySQL.")
        return con
    except Exception as e:
        print(f"ERRO ao conectar no MySQL: {e}")
        sys.exit(1)


def obter_descricoes_firebird(con_fb):
    """Le todas as DESCRICAO da tabela TGRUPOS_PRODUTOS."""
    cur = con_fb.cursor()
    cur.execute("SELECT DESCRICAO FROM TGRUPOS_PRODUTOS")
    descricoes = []
    for (descricao,) in cur.fetchall():
        if descricao is None:
            continue
        texto = descricao.strip() if isinstance(descricao, str) else str(descricao).strip()
        if texto:
            descricoes.append(texto)
    cur.close()
    print(f"[OK] {len(descricoes)} registro(s) lido(s) de TGRUPOS_PRODUTOS.")
    return descricoes


def obter_ultimo_id(con_my):
    """Retorna o maior id existente na tabela categorias (0 se vazia)."""
    cur = con_my.cursor()
    cur.execute("SELECT MAX(id) FROM categorias")
    (max_id,) = cur.fetchone()
    cur.close()
    return int(max_id) if max_id is not None else 0


def migrar():
    con_fb = conectar_firebird()
    con_my = conectar_mysql()

    try:
        descricoes = obter_descricoes_firebird(con_fb)
        if not descricoes:
            print("Nenhuma descricao encontrada no Firebird. Nada a migrar.")
            return

        ultimo_id = obter_ultimo_id(con_my)
        proximo_id = ultimo_id + 1 if ultimo_id >= 1 else 1
        print(f"[INFO] Ultimo id em 'categorias': {ultimo_id}. "
              f"Iniciando insercao a partir do id {proximo_id}.")

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql = (
            "INSERT INTO categorias "
            "(id, nome, descricao, ativo, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )

        cur = con_my.cursor()
        inseridos = 0
        id_atual = proximo_id
        for descricao in descricoes:
            cur.execute(sql, (id_atual, descricao, descricao, 1, agora, agora))
            inseridos += 1
            id_atual += 1

        con_my.commit()
        cur.close()
        print(f"[OK] {inseridos} registro(s) inserido(s) em 'categorias' "
              f"(ids {proximo_id} ate {id_atual - 1}).")

    except Exception as e:
        con_my.rollback()
        print(f"ERRO durante a migracao (nenhuma alteracao foi salva): {e}")
        raise
    finally:
        con_fb.close()
        con_my.close()
        print("[OK] Conexoes encerradas.")


if __name__ == "__main__":
    migrar()
