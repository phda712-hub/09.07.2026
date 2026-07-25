# -*- coding: utf-8 -*-
"""
Script UNICO de migracao Firebird -> MySQL.

Executa em sequencia, usando as mesmas conexoes:
    1) TGRUPOS_PRODUTOS (Firebird)  ->  categorias (MySQL 'quantum')
    2) TPRODUTOS        (Firebird)  ->  produtos   (MySQL 'quantum')
    3) THOSPEDES        (Firebird)  ->  clientes   (MySQL 'quantum')

Mapeamento clientes  (<- THOSPEDES):
    id         -> proximo id (ultimo + 1, ou 1) apenas em novos registros
                  (mesma logica de id usada em categorias e produtos)
    nome       -> NOME
    cpf        -> CPF
    telefone   -> TELEFONE ; se vazio, usa CELULAR
    endereco   -> ENDERECO + " " + ENDERECO_NUMERO
    bairro     -> BAIRRO
    ativo      -> 1
    created_at -> data/hora atual (so em novos)
    updated_at -> data/hora atual
    (chave de upsert: nome)

Comportamento UPSERT (nos dois casos):
    - Se o registro ja existir, ele e ATUALIZADO (id e created_at preservados).
    - Caso contrario, e inserido um novo registro.
    - Chave "ja existe":
        * categorias -> coluna 'descricao' (= ID_GRUPO_PRODUTO)
        * produtos   -> coluna 'codigo' (= CODIGO interno do Firebird, estavel).
          Como fallback, tambem procura por 'codigo_barras' para adotar registros
          de execucoes antigas que ainda nao tinham a coluna 'codigo' preenchida.

Mapeamento categorias  (<- TGRUPOS_PRODUTOS):
    id         -> proximo id (ultimo + 1, ou 1) apenas em novos registros
    nome       -> DESCRICAO
    descricao  -> ID_GRUPO_PRODUTO
    ativo      -> 1
    created_at -> data/hora atual (so em novos)
    updated_at -> data/hora atual

Mapeamento produtos  (<- TPRODUTOS):
    id                 -> proximo id (ultimo + 1, ou 1) apenas em novos registros
    nome               -> DESCRICAO
    codigo             -> CODIGO (codigo interno do Firebird - chave estavel)
    codigo_barras      -> CODIGO_BARRAS ; se vazio, usa CODIGO
    categoria          -> ID_GRUPO_PRODUTO (texto)
    categoria_id       -> id da categoria cujo 'descricao' == ID_GRUPO_PRODUTO
                          (se nao achar, usa CATEGORIA_ID_PADRAO)
    preco              -> PRECO_VENDA
    preco_atacado      -> 0
    atacado_qtd_minima -> 0
    preco_promocional  -> 0
    promocao_inicio    -> data/hora atual
    promocao_fim       -> data/hora atual
    preco_compra       -> PRECO_CUSTO
    tipo               -> "unidade"
    estoque            -> ESTOQUE
    estoque_minimo     -> ESTOQUE_MINIMO
    fidelidade_pontos  -> 0
    ativo              -> 1
    created_at         -> data/hora atual (so em novos)
    updated_at         -> data/hora atual
    unidade            -> "unid."

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
    "charset": "WIN1252",
}

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "quantum",
}

# Categoria usada quando o grupo do produto nao tem correspondente em categorias.
CATEGORIA_ID_PADRAO = 1                  # normalmente 1 = "Geral"
COL_CATEGORIAS_CHAVE = "descricao"       # coluna de 'categorias' que guarda o ID_GRUPO_PRODUTO

# Nomes das colunas na tabela MySQL 'produtos' (ajuste se algum for diferente).
COL_ID = "id"
COL_NOME = "nome"
COL_CODIGO = "codigo"                     # CODIGO interno do Firebird (chave estavel)
COL_CODIGO_BARRAS = "codigo_barras"
COL_CATEGORIA = "categoria"
COL_CATEGORIA_ID = "categoria_id"
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
COL_FIDELIDADE = "fidelidade_pontos"
COL_ATIVO = "ativo"
COL_CREATED_AT = "created_at"
COL_UPDATED_AT = "updated_at"
COL_UNIDADE = "unidade"


# ----------------------------------------------------------------------------
# Conexoes
# ----------------------------------------------------------------------------
def conectar_firebird():
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


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _texto(valor):
    if valor is None:
        return ""
    return valor.strip() if isinstance(valor, str) else str(valor).strip()


def _numero(valor, padrao=0):
    if valor is None:
        return padrao
    try:
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _chave_grupo(valor):
    """Normaliza o grupo p/ comparacao: 10, '10', '10.0' -> '10'."""
    if valor is None:
        return ""
    try:
        return str(int(float(valor)))
    except (TypeError, ValueError):
        return str(valor).strip()


def obter_ultimo_id(con_my, tabela):
    cur = con_my.cursor()
    cur.execute(f"SELECT MAX(id) FROM {tabela}")
    (max_id,) = cur.fetchone()
    cur.close()
    return int(max_id) if max_id is not None else 0


def obter_colunas_tabela(con_my, tabela):
    cur = con_my.cursor()
    cur.execute(f"SHOW COLUMNS FROM {tabela}")
    colunas = {row[0] for row in cur.fetchall()}
    cur.close()
    return colunas


# ----------------------------------------------------------------------------
# ETAPA 1 - Grupos -> categorias
# ----------------------------------------------------------------------------
def migrar_categorias(con_fb, con_my):
    print("\n=== ETAPA 1: TGRUPOS_PRODUTOS -> categorias ===")
    cur_fb = con_fb.cursor()
    cur_fb.execute("SELECT DESCRICAO, ID_GRUPO_PRODUTO FROM TGRUPOS_PRODUTOS")
    grupos = []
    for descricao, id_grupo in cur_fb.fetchall():
        nome = _texto(descricao)
        id_grupo_txt = _texto(id_grupo)
        if nome:
            grupos.append((nome, id_grupo_txt))
    cur_fb.close()
    print(f"[OK] {len(grupos)} registro(s) lido(s) de TGRUPOS_PRODUTOS.")

    if not grupos:
        print("[AVISO] Nenhum grupo encontrado. Nada a fazer na etapa 1.")
        return

    ultimo_id = obter_ultimo_id(con_my, "categorias")
    id_atual = ultimo_id + 1 if ultimo_id >= 1 else 1
    print(f"[INFO] Ultimo id em 'categorias': {ultimo_id}. "
          f"Novos registros a partir do id {id_atual}.")

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql_insert = (
        "INSERT INTO categorias (id, nome, descricao, ativo, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )
    sql_update = "UPDATE categorias SET nome = %s, ativo = 1, updated_at = %s WHERE id = %s"

    cur = con_my.cursor()
    inseridos = atualizados = 0
    for nome, id_grupo_produto in grupos:
        existente_id = None
        if id_grupo_produto:
            cur.execute("SELECT id FROM categorias WHERE descricao = %s LIMIT 1",
                        (id_grupo_produto,))
            linha = cur.fetchone()
            if linha:
                existente_id = int(linha[0])

        if existente_id is not None:
            cur.execute(sql_update, (nome, agora, existente_id))
            atualizados += 1
        else:
            cur.execute(sql_insert, (id_atual, nome, id_grupo_produto, 1, agora, agora))
            inseridos += 1
            id_atual += 1

    con_my.commit()
    cur.close()
    print(f"[OK] Categorias: {inseridos} inserida(s), {atualizados} atualizada(s).")


# ----------------------------------------------------------------------------
# ETAPA 2 - Produtos -> produtos
# ----------------------------------------------------------------------------
def obter_produtos_firebird(con_fb):
    cur = con_fb.cursor()
    cur.execute(
        "SELECT DESCRICAO, CODIGO_BARRAS, CODIGO, ID_GRUPO_PRODUTO, "
        "PRECO_VENDA, PRECO_CUSTO, ESTOQUE, ESTOQUE_MINIMO FROM TPRODUTOS"
    )
    produtos = []
    for row in cur.fetchall():
        (descricao, codigo_barras, codigo, id_grupo,
         preco_venda, preco_custo, estoque, estoque_minimo) = row
        cod = _texto(codigo)                 # CODIGO interno (estavel)
        cb = _texto(codigo_barras) or cod    # codigo_barras; se vazio, usa CODIGO
        produtos.append({
            "nome": _texto(descricao),
            "codigo": cod,
            "codigo_barras": cb,
            "categoria": _texto(id_grupo),
            "grupo_chave": _chave_grupo(id_grupo),
            "categoria_id": None,
            "preco": _numero(preco_venda),
            "preco_compra": _numero(preco_custo),
            "estoque": _numero(estoque),
            "estoque_minimo": _numero(estoque_minimo),
        })
    cur.close()
    print(f"[OK] {len(produtos)} registro(s) lido(s) de TPRODUTOS.")
    return produtos


def obter_mapa_categorias(con_my):
    cur = con_my.cursor()
    cur.execute(f"SELECT id, {COL_CATEGORIAS_CHAVE} FROM categorias")
    mapa = {}
    for cat_id, chave in cur.fetchall():
        mapa[_chave_grupo(chave)] = int(cat_id)
    cur.close()
    return mapa


def migrar_produtos(con_fb, con_my):
    print("\n=== ETAPA 2: TPRODUTOS -> produtos ===")
    produtos = obter_produtos_firebird(con_fb)
    if not produtos:
        print("[AVISO] Nenhum produto encontrado. Nada a fazer na etapa 2.")
        return

    # Resolve categoria_id via lookup em categorias (descricao == ID_GRUPO_PRODUTO).
    mapa_categorias = obter_mapa_categorias(con_my)
    print(f"[INFO] {len(mapa_categorias)} categoria(s) carregada(s) para vinculo.")

    nao_encontrados = set()
    for p in produtos:
        cat_id = mapa_categorias.get(p["grupo_chave"])
        if cat_id is None:
            cat_id = CATEGORIA_ID_PADRAO
            if p["grupo_chave"]:
                nao_encontrados.add(p["grupo_chave"])
        p["categoria_id"] = cat_id
    if nao_encontrados:
        print(f"[AVISO] Grupo(s) sem categoria correspondente (usando padrao "
              f"id={CATEGORIA_ID_PADRAO}): {', '.join(sorted(nao_encontrados))}")

    colunas_existentes = obter_colunas_tabela(con_my, "produtos")
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    mapeamento = [
        (COL_ID,                 lambda p, i: i),
        (COL_NOME,               lambda p, i: p["nome"]),
        (COL_CODIGO,             lambda p, i: p["codigo"]),
        (COL_CODIGO_BARRAS,      lambda p, i: p["codigo_barras"]),
        (COL_CATEGORIA,          lambda p, i: p["categoria"]),
        (COL_CATEGORIA_ID,       lambda p, i: p["categoria_id"]),
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

    mapeamento_ativo = [(c, f) for (c, f) in mapeamento if c in colunas_existentes]
    ignoradas = [c for (c, _) in mapeamento if c not in colunas_existentes]
    if ignoradas:
        print(f"[AVISO] Colunas inexistentes em 'produtos' (ignoradas): "
              f"{', '.join(ignoradas)}")

    colunas_ins = [c for (c, _) in mapeamento_ativo]
    funcoes_ins = [f for (_, f) in mapeamento_ativo]
    placeholders = ", ".join(["%s"] * len(colunas_ins))
    sql_insert = (
        f"INSERT INTO produtos ({', '.join(colunas_ins)}) VALUES ({placeholders})"
    )

    mapeamento_update = [(c, f) for (c, f) in mapeamento_ativo
                         if c not in (COL_ID, COL_CREATED_AT)]
    set_clause = ", ".join(f"{c} = %s" for (c, _) in mapeamento_update)
    sql_update = f"UPDATE produtos SET {set_clause} WHERE {COL_ID} = %s"

    ultimo_id = obter_ultimo_id(con_my, "produtos")
    id_atual = ultimo_id + 1 if ultimo_id >= 1 else 1
    print(f"[INFO] Ultimo id em 'produtos': {ultimo_id}. "
          f"Novos registros a partir do id {id_atual}.")

    def localizar_existente(cur, p):
        """Localiza o id de um produto ja existente usando chave estavel.

        Ordem de busca (a primeira que encontrar vence):
          1) codigo == CODIGO interno do Firebird  (chave estavel definitiva)
          2) codigo_barras == CODIGO_BARRAS         (registro que ja tem o codigo de barras)
          3) codigo_barras == CODIGO                (registro antigo, criado quando o
                                                      codigo de barras ainda estava vazio)
        As opcoes 2 e 3 servem para "adotar" registros de execucoes anteriores
        que ainda nao tinham a coluna 'codigo' preenchida.
        """
        cod = p["codigo"]
        cb = p["codigo_barras"]
        tentativas = []
        if cod:
            tentativas.append((COL_CODIGO, cod))
        if cb:
            tentativas.append((COL_CODIGO_BARRAS, cb))
        if cod:
            tentativas.append((COL_CODIGO_BARRAS, cod))
        for coluna, valor in tentativas:
            cur.execute(
                f"SELECT {COL_ID} FROM produtos WHERE {coluna} = %s ORDER BY {COL_ID} LIMIT 1",
                (valor,))
            linha = cur.fetchone()
            if linha:
                return int(linha[0])
        return None

    cur = con_my.cursor()
    inseridos = atualizados = 0
    for p in produtos:
        existente_id = localizar_existente(cur, p)

        if existente_id is not None:
            valores = [f(p, existente_id) for (_, f) in mapeamento_update]
            valores.append(existente_id)
            cur.execute(sql_update, tuple(valores))
            atualizados += 1
        else:
            valores = tuple(f(p, id_atual) for f in funcoes_ins)
            cur.execute(sql_insert, valores)
            inseridos += 1
            id_atual += 1

    con_my.commit()
    cur.close()
    print(f"[OK] Produtos: {inseridos} inserido(s), {atualizados} atualizado(s).")


# ----------------------------------------------------------------------------
# ETAPA 3 - Hospedes/clientes -> clientes
# ----------------------------------------------------------------------------
def obter_clientes_firebird(con_fb):
    cur = con_fb.cursor()
    cur.execute(
        "SELECT NOME, CPF, TELEFONE, CELULAR, ENDERECO, ENDERECO_NUMERO, BAIRRO "
        "FROM THOSPEDES"
    )
    clientes = []
    for nome, cpf, telefone, celular, endereco, numero, bairro in cur.fetchall():
        nm = _texto(nome)
        if not nm:
            continue
        tel = _texto(telefone) or _texto(celular)   # TELEFONE; se vazio, CELULAR
        # endereco = ENDERECO + espaco + ENDERECO_NUMERO (ignora partes vazias)
        end = " ".join(x for x in [_texto(endereco), _texto(numero)] if x)
        clientes.append({
            "nome": nm,
            "cpf": _texto(cpf),
            "telefone": tel,
            "endereco": end,
            "bairro": _texto(bairro),
        })
    cur.close()
    print(f"[OK] {len(clientes)} registro(s) lido(s) de THOSPEDES.")
    return clientes


def migrar_clientes(con_fb, con_my):
    print("\n=== ETAPA 3: THOSPEDES -> clientes ===")
    clientes = obter_clientes_firebird(con_fb)
    if not clientes:
        print("[AVISO] Nenhum cliente encontrado. Nada a fazer na etapa 3.")
        return

    colunas_existentes = obter_colunas_tabela(con_my, "clientes")
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # nome_da_coluna_mysql -> funcao(cliente, id)
    mapeamento = [
        ("id",         lambda c, i: i),
        ("nome",       lambda c, i: c["nome"]),
        ("cpf",        lambda c, i: c["cpf"]),
        ("telefone",   lambda c, i: c["telefone"]),
        ("endereco",   lambda c, i: c["endereco"]),
        ("bairro",     lambda c, i: c["bairro"]),
        ("ativo",      lambda c, i: 1),
        ("created_at", lambda c, i: agora),
        ("updated_at", lambda c, i: agora),
    ]
    mapeamento_ativo = [(col, f) for (col, f) in mapeamento if col in colunas_existentes]
    ignoradas = [col for (col, _) in mapeamento if col not in colunas_existentes]
    if ignoradas:
        print(f"[AVISO] Colunas inexistentes em 'clientes' (ignoradas): "
              f"{', '.join(ignoradas)}")

    colunas_ins = [col for (col, _) in mapeamento_ativo]
    funcoes_ins = [f for (_, f) in mapeamento_ativo]
    placeholders = ", ".join(["%s"] * len(colunas_ins))
    sql_insert = (
        f"INSERT INTO clientes ({', '.join(colunas_ins)}) VALUES ({placeholders})"
    )

    # No UPDATE nao mexemos em id nem created_at.
    mapeamento_update = [(col, f) for (col, f) in mapeamento_ativo
                         if col not in ("id", "created_at")]
    set_clause = ", ".join(f"{col} = %s" for (col, _) in mapeamento_update)
    sql_update = f"UPDATE clientes SET {set_clause} WHERE id = %s"

    ultimo_id = obter_ultimo_id(con_my, "clientes")
    id_atual = ultimo_id + 1 if ultimo_id >= 1 else 1
    print(f"[INFO] Ultimo id em 'clientes': {ultimo_id}. "
          f"Novos registros a partir do id {id_atual}.")

    cur = con_my.cursor()
    inseridos = atualizados = 0
    for c in clientes:
        # Chave de comparacao (upsert): nome.
        cur.execute("SELECT id FROM clientes WHERE nome = %s ORDER BY id LIMIT 1",
                    (c["nome"],))
        linha = cur.fetchone()
        existente_id = int(linha[0]) if linha else None

        if existente_id is not None:
            valores = [f(c, existente_id) for (_, f) in mapeamento_update]
            valores.append(existente_id)
            cur.execute(sql_update, tuple(valores))
            atualizados += 1
        else:
            valores = tuple(f(c, id_atual) for f in funcoes_ins)
            cur.execute(sql_insert, valores)
            inseridos += 1
            id_atual += 1

    con_my.commit()
    cur.close()
    print(f"[OK] Clientes: {inseridos} inserido(s), {atualizados} atualizado(s).")


# ----------------------------------------------------------------------------
# Fluxo principal
# ----------------------------------------------------------------------------
def main():
    con_fb = conectar_firebird()
    con_my = conectar_mysql()
    try:
        migrar_categorias(con_fb, con_my)   # 1) grupos -> categorias
        migrar_produtos(con_fb, con_my)     # 2) produtos -> produtos
        migrar_clientes(con_fb, con_my)     # 3) hospedes -> clientes
        print("\n[OK] Migracao concluida com sucesso.")
    except Exception as e:
        con_my.rollback()
        print(f"\nERRO durante a migracao: {e}")
        raise
    finally:
        con_fb.close()
        con_my.close()
        print("[OK] Conexoes encerradas.")


if __name__ == "__main__":
    main()
