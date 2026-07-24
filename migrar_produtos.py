# -*- coding: utf-8 -*-
"""
Script de migracao: copia dados da tabela TPRODUTOS
(banco Firebird 2.5) para a tabela 'produtos' (banco MySQL 'quantum').

Mapeamento de colunas (MySQL 'produtos'  <-  Firebird 'TPRODUTOS'):
    id                 -> sequencial: ultimo id existente + 1 (ou 1 se vazia)
                          (mesma logica usada na tabela 'categorias')
    nome               -> DESCRICAO
    codigo_barras      -> CODIGO_BARRAS ; se vazio, usa CODIGO
    categoria          -> ID_GRUPO_PRODUTO
    preco              -> PRECO_VENDA
    preco_atacado      -> sempre 0
    atacado_qtd_minima -> sempre 0
    preco_promocional  -> sempre 0
    promocao_inicio    -> data/hora atual (yyyy-MM-dd HH:mm:ss)
    promocao_fim       -> data/hora atual (yyyy-MM-dd HH:mm:ss)
    preco_compra       -> PRECO_CUSTO
    tipo               -> sempre "unidade"
    estoque            -> ESTOQUE
    estoque_minimo     -> ESTOQUE_MINIMO
    fidelidade         -> sempre 0
    ativo              -> sempre 1
    created_at         -> data/hora atual (yyyy-MM-dd HH:mm:ss)
    updated_at         -> data/hora atual (yyyy-MM-dd HH:mm:ss)
    unidade            -> sempre "unid."

Dependencias (instale antes de rodar):
    pip install fdb mysql-connector-python

Obs.: 'fdb' precisa da client library do Firebird (fbclient.dll) instalada,
      na mesma arquitetura do Python (32/64 bits).
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

# Nomes das colunas na tabela MySQL 'produtos'.
# Se algum nome for diferente no seu banco, ajuste aqui.
COL_ID = "id"
COL_NOME = "nome"
COL_CODIGO_BARRAS = "codigo_barras"
COL_CATEGORIA = "categoria"
COL_PRECO = "preco"
COL_PRECO_ATACADO = "preco_atacado"
COL_ATACADO_QTD_MINIMA = "atacado_qtd_minima"
COL_PRECO_PROMOCIONAL = "preco_promocional"
COL_PROMOCAO_INICIO = "promocao_inicio"
COL_PROMOCAO_FIM = "promocao_fim"
COL_PRECO_COMPRA = "preco_compra"
COL_TIPO = "tipo"
COL_ESTOQUE = "estoque"
COL_ESTOQUE_MINIMO = "estoque_minimo"
COL_FIDELIDADE = "fidelidade"
COL_ATIVO = "ativo"
COL_CREATED_AT = "created_at"
COL_UPDATED_AT = "updated_at"
COL_UNIDADE = "unidade"


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


def _texto(valor):
    """Converte para texto limpo; None vira string vazia."""
    if valor is None:
        return ""
    return valor.strip() if isinstance(valor, str) else str(valor).strip()


def _numero(valor, padrao=0):
    """Converte para numero; None ou invalido vira o padrao."""
    if valor is None:
        return padrao
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def obter_produtos_firebird(con_fb):
    """Le os campos necessarios da tabela TPRODUTOS."""
    cur = con_fb.cursor()
    cur.execute(
        "SELECT DESCRICAO, CODIGO_BARRAS, CODIGO, ID_GRUPO_PRODUTO, "
        "PRECO_VENDA, PRECO_CUSTO, ESTOQUE, ESTOQUE_MINIMO "
        "FROM TPRODUTOS"
    )
    produtos = []
    for row in cur.fetchall():
        (descricao, codigo_barras, codigo, id_grupo,
         preco_venda, preco_custo, estoque, estoque_minimo) = row

        nome = _texto(descricao)
        cb = _texto(codigo_barras)
        if not cb:                      # se CODIGO_BARRAS estiver vazio, usa CODIGO
            cb = _texto(codigo)

        produtos.append({
            "nome": nome,
            "codigo_barras": cb,
            "categoria": _texto(id_grupo),
            "preco": _numero(preco_venda),
            "preco_compra": _numero(preco_custo),
            "estoque": _numero(estoque),
            "estoque_minimo": _numero(estoque_minimo),
        })
    cur.close()
    print(f"[OK] {len(produtos)} registro(s) lido(s) de TPRODUTOS.")
    return produtos


def obter_ultimo_id(con_my, tabela, coluna_id):
    """Retorna o maior id existente na tabela (0 se vazia)."""
    cur = con_my.cursor()
    cur.execute(f"SELECT MAX({coluna_id}) FROM {tabela}")
    (max_id,) = cur.fetchone()
    cur.close()
    return int(max_id) if max_id is not None else 0


def migrar():
    con_fb = conectar_firebird()
    con_my = conectar_mysql()

    try:
        produtos = obter_produtos_firebird(con_fb)
        if not produtos:
            print("Nenhum produto encontrado no Firebird. Nada a migrar.")
            return

        ultimo_id = obter_ultimo_id(con_my, "produtos", COL_ID)
        proximo_id = ultimo_id + 1 if ultimo_id >= 1 else 1
        print(f"[INFO] Ultimo id em 'produtos': {ultimo_id}. "
              f"Iniciando insercao a partir do id {proximo_id}.")

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        colunas = [
            COL_ID, COL_NOME, COL_CODIGO_BARRAS, COL_CATEGORIA, COL_PRECO,
            COL_PRECO_ATACADO, COL_ATACADO_QTD_MINIMA, COL_PRECO_PROMOCIONAL,
            COL_PROMOCAO_INICIO, COL_PROMOCAO_FIM, COL_PRECO_COMPRA, COL_TIPO,
            COL_ESTOQUE, COL_ESTOQUE_MINIMO, COL_FIDELIDADE, COL_ATIVO,
            COL_CREATED_AT, COL_UPDATED_AT, COL_UNIDADE,
        ]
        placeholders = ", ".join(["%s"] * len(colunas))
        sql = (
            f"INSERT INTO produtos ({', '.join(colunas)}) "
            f"VALUES ({placeholders})"
        )

        cur = con_my.cursor()
        inseridos = 0
        id_atual = proximo_id
        for p in produtos:
            valores = (
                id_atual,               # id
                p["nome"],              # nome
                p["codigo_barras"],     # codigo_barras (ou CODIGO se vazio)
                p["categoria"],         # categoria = ID_GRUPO_PRODUTO
                p["preco"],             # preco = PRECO_VENDA
                0,                      # preco_atacado
                0,                      # atacado_qtd_minima
                0,                      # preco_promocional
                agora,                  # promocao_inicio
                agora,                  # promocao_fim
                p["preco_compra"],      # preco_compra = PRECO_CUSTO
                "unidade",              # tipo
                p["estoque"],           # estoque
                p["estoque_minimo"],    # estoque_minimo
                0,                      # fidelidade
                1,                      # ativo
                agora,                  # created_at
                agora,                  # updated_at
                "unid.",                # unidade
            )
            cur.execute(sql, valores)
            inseridos += 1
            id_atual += 1

        con_my.commit()
        cur.close()
        print(f"[OK] {inseridos} registro(s) inserido(s) em 'produtos' "
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
