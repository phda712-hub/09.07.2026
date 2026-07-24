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
COL_FIDELIDADE = "fidelidade_pontos"   # nome real da coluna na tabela produtos
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


def obter_colunas_tabela(con_my, tabela):
    """Retorna o conjunto de nomes de colunas existentes na tabela MySQL."""
    cur = con_my.cursor()
    cur.execute(f"SHOW COLUMNS FROM {tabela}")
    colunas = {row[0] for row in cur.fetchall()}
    cur.close()
    return colunas


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

        # Descobre quais colunas realmente existem na tabela 'produtos'.
        # Colunas do mapeamento que nao existirem sao ignoradas automaticamente,
        # evitando o erro "Unknown column".
        colunas_existentes = obter_colunas_tabela(con_my, "produtos")

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Mapeamento: nome_da_coluna_mysql -> funcao(produto) que retorna o valor.
        # (funcoes lambda para calcular o valor de cada linha)
        mapeamento = [
            (COL_ID,                 lambda p, i: i),
            (COL_NOME,               lambda p, i: p["nome"]),
            (COL_CODIGO_BARRAS,      lambda p, i: p["codigo_barras"]),
            (COL_CATEGORIA,          lambda p, i: p["categoria"]),
            (COL_PRECO,              lambda p, i: p["preco"]),
            (COL_PRECO_ATACADO,      lambda p, i: 0),
            (COL_ATACADO_QTD_MINIMA, lambda p, i: 0),
            (COL_PRECO_PROMOCIONAL,  lambda p, i: 0),
            (COL_PROMOCAO_INICIO,    lambda p, i: agora),
            (COL_PROMOCAO_FIM,       lambda p, i: agora),
            (COL_PRECO_COMPRA,       lambda p, i: p["preco_compra"]),
            (COL_TIPO,               lambda p, i: "unidade"),
            (COL_ESTOQUE,            lambda p, i: p["estoque"]),
            (COL_ESTOQUE_MINIMO,     lambda p, i: p["estoque_minimo"]),
            (COL_FIDELIDADE,         lambda p, i: 0),
            (COL_ATIVO,              lambda p, i: 1),
            (COL_CREATED_AT,         lambda p, i: agora),
            (COL_UPDATED_AT,         lambda p, i: agora),
            (COL_UNIDADE,            lambda p, i: "unid."),
        ]

        # Mantem apenas as colunas que existem na tabela.
        mapeamento_ativo = [(c, f) for (c, f) in mapeamento if c in colunas_existentes]
        ignoradas = [c for (c, _) in mapeamento if c not in colunas_existentes]
        if ignoradas:
            print(f"[AVISO] Colunas do mapeamento que NAO existem em 'produtos' "
                  f"e serao ignoradas: {', '.join(ignoradas)}")

        colunas = [c for (c, _) in mapeamento_ativo]
        funcoes = [f for (_, f) in mapeamento_ativo]
        placeholders = ", ".join(["%s"] * len(colunas))
        sql = (
            f"INSERT INTO produtos ({', '.join(colunas)}) "
            f"VALUES ({placeholders})"
        )

        cur = con_my.cursor()
        inseridos = 0
        id_atual = proximo_id
        for p in produtos:
            valores = tuple(f(p, id_atual) for f in funcoes)
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
