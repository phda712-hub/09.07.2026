# -*- coding: utf-8 -*-
"""
Script de migracao: copia dados da tabela TGRUPOS_PRODUTOS
(banco Firebird 2.5) para a tabela 'categorias' (banco MySQL 'quantum').

Regras de preenchimento na tabela MySQL 'categorias':
    - id         -> proximo numero apos o ultimo id existente (ou 1 se vazia)
    - nome       -> valor de DESCRICAO (Firebird)
    - descricao  -> valor de ID_GRUPO_PRODUTO (Firebird)
    - ativo      -> sempre 1
    - created_at -> data/hora atual (yyyy-MM-dd HH:mm:ss)
    - updated_at -> data/hora atual (yyyy-MM-dd HH:mm:ss)

Comportamento UPSERT: se ja existir uma categoria cujo 'descricao' seja igual
ao ID_GRUPO_PRODUTO, o registro e ATUALIZADO (id e created_at preservados);
caso contrario, e inserida uma nova categoria.

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


def obter_grupos_firebird(con_fb):
    """Le DESCRICAO e ID_GRUPO_PRODUTO da tabela TGRUPOS_PRODUTOS.

    Retorna lista de tuplas (nome, id_grupo_produto), onde:
        - nome              -> DESCRICAO
        - id_grupo_produto  -> ID_GRUPO_PRODUTO (usado na coluna 'descricao')
    """
    cur = con_fb.cursor()
    cur.execute("SELECT DESCRICAO, ID_GRUPO_PRODUTO FROM TGRUPOS_PRODUTOS")
    grupos = []
    for descricao, id_grupo in cur.fetchall():
        nome = descricao.strip() if isinstance(descricao, str) else (
            str(descricao).strip() if descricao is not None else "")
        id_grupo_txt = str(id_grupo).strip() if id_grupo is not None else ""
        if nome:
            grupos.append((nome, id_grupo_txt))
    cur.close()
    print(f"[OK] {len(grupos)} registro(s) lido(s) de TGRUPOS_PRODUTOS.")
    return grupos


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
        grupos = obter_grupos_firebird(con_fb)
        if not grupos:
            print("Nenhum registro encontrado no Firebird. Nada a migrar.")
            return

        ultimo_id = obter_ultimo_id(con_my)
        proximo_id = ultimo_id + 1 if ultimo_id >= 1 else 1
        print(f"[INFO] Ultimo id em 'categorias': {ultimo_id}. "
              f"Iniciando insercao a partir do id {proximo_id}.")

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql_insert = (
            "INSERT INTO categorias "
            "(id, nome, descricao, ativo, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        # No UPDATE preservamos id, descricao (a chave) e created_at.
        sql_update = (
            "UPDATE categorias SET nome = %s, ativo = 1, updated_at = %s "
            "WHERE id = %s"
        )

        cur = con_my.cursor()
        inseridos = 0
        atualizados = 0
        id_atual = proximo_id
        for nome, id_grupo_produto in grupos:
            # nome -> DESCRICAO ; descricao -> ID_GRUPO_PRODUTO (chave de comparacao)
            # Verifica se ja existe uma categoria com esse ID_GRUPO_PRODUTO na descricao.
            existente_id = None
            if id_grupo_produto:
                cur.execute(
                    "SELECT id FROM categorias WHERE descricao = %s LIMIT 1",
                    (id_grupo_produto,),
                )
                linha = cur.fetchone()
                if linha:
                    existente_id = int(linha[0])

            if existente_id is not None:
                # Atualiza o nome da categoria ja existente.
                cur.execute(sql_update, (nome, agora, existente_id))
                atualizados += 1
            else:
                # Insere nova categoria.
                cur.execute(sql_insert, (id_atual, nome, id_grupo_produto, 1, agora, agora))
                inseridos += 1
                id_atual += 1

        con_my.commit()
        cur.close()
        print(f"[OK] Concluido em 'categorias': {inseridos} inserida(s), "
              f"{atualizados} atualizada(s).")

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
