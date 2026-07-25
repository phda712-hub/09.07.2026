# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
 REPARADOR DE ESTRUTURA DO BANCO  ·  Quantum / Farma Quantum PDV
 (Cria TABELAS e COLUNAS faltantes — corrige os erros ao cadastrar
  Fornecedor, Tamanho e Nota de Entrada: "faltando coluna ...")
═══════════════════════════════════════════════════════════════════════════════

POR QUE ESSES ERROS ACONTECEM
-----------------------------
As tabelas foram criadas por uma versao ANTIGA do sistema e nunca receberam as
colunas novas que o programa passou a usar. Exemplos reais encontrados no codigo:

  • fornecedores  -> faltavam as colunas `observacao` e `updated_at`
  • notas_entrada -> a tabela antiga tinha `numero` (o codigo usa `numero_nota`);
                     faltavam `fornecedor_nome`, `itens`, `usuario`, `updated_at`
  • tamanhos / tamanhos_produtos -> tabela/colunas podiam nao existir

Quando o programa tenta gravar/ler uma coluna que nao existe, o MySQL retorna
"Unknown column ..." (o famoso "faltando coluna nome").

O QUE ESTE SCRIPT FAZ
---------------------
  1. Conecta no MySQL do cliente (descobre credenciais em config.ini/config.json,
     ou voce informa por parametro / interativamente).
  2. Cria as TABELAS que estiverem faltando (CREATE TABLE IF NOT EXISTS).
  3. Adiciona as COLUNAS que estiverem faltando (ALTER TABLE ADD COLUMN), sem
     tocar nas colunas/dados que ja existem.
  4. Cria indices uteis (ignora se ja existirem).
  5. Mostra um relatorio do que foi criado/adicionado.

SEGURANCA
---------
  • NAO apaga dados. So CRIA o que falta (idempotente: pode rodar varias vezes).
  • Use --dry-run para apenas VER o que seria feito, sem alterar nada.

USO
---
  python reparar_estrutura_banco.py
  python reparar_estrutura_banco.py --dry-run
  python reparar_estrutura_banco.py --host 127.0.0.1 --user root --password SENHA --database farmacia
  python reparar_estrutura_banco.py --config-ini "C:\\Quantum\\config.ini"
  python reparar_estrutura_banco.py --config-json "config.json"
  python reparar_estrutura_banco.py --yes        (sem perguntas)

Requisitos: mysql-connector-python  (ou PyMySQL).
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import argparse
import configparser


# ══════════════════════════════════════════════════════════════════════════
# ESQUEMA ESPERADO (extraido de verificar_integridade_banco do Quantum)
# Cada tabela: (CREATE TABLE MySQL, { coluna: "DEFINICAO MYSQL PARA ADD COLUMN" })
# Tipos usados: INT / DOUBLE / VARCHAR(n) / TEXT / LONGTEXT / DATE / DATETIME /
#               TIMESTAMP. As colunas TIMESTAMP entram como NULL para nao exigir
#               valor default incompativel em tabelas ja populadas.
# ══════════════════════════════════════════════════════════════════════════
ENGINE = "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
TS = "TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP"
TS_UPD = "TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"

SCHEMA = {
    # ─────────────────────────── CATEGORIAS ───────────────────────────
    "categorias": (
        f"""CREATE TABLE IF NOT EXISTS categorias (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            descricao TEXT NULL,
            ativo TINYINT(1) DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(255) NOT NULL DEFAULT ''",
            "descricao": "TEXT NULL",
            "ativo": "TINYINT(1) DEFAULT 1",
            "created_at": TS,
            "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── PRODUTOS ───────────────────────────
    "produtos": (
        f"""CREATE TABLE IF NOT EXISTS produtos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            codigo_barras VARCHAR(500) DEFAULT '',
            categoria_id INT DEFAULT 1,
            preco DOUBLE DEFAULT 0.0,
            preco_atacado DOUBLE DEFAULT 0.0,
            atacado_qtd_minima DOUBLE DEFAULT 10.0,
            preco_promocional DOUBLE DEFAULT 0.0,
            promocao_ativa INT DEFAULT 0,
            promocao_inicio VARCHAR(500) DEFAULT '',
            promocao_fim VARCHAR(500) DEFAULT '',
            preco_compra DOUBLE DEFAULT 0.0,
            tipo VARCHAR(500) DEFAULT 'unidade',
            estoque DOUBLE DEFAULT 0.0,
            estoque_minimo DOUBLE DEFAULT 5.0,
            fidelidade_pontos INT DEFAULT 0,
            tamanho_id INT DEFAULT NULL,
            controlar_lote_validade INT DEFAULT 0,
            lote VARCHAR(500) DEFAULT '',
            validade VARCHAR(500) DEFAULT '',
            data_validade VARCHAR(500) DEFAULT '',
            imagem LONGTEXT NULL,
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''",
            "codigo_barras": "VARCHAR(500) DEFAULT ''",
            "codigo": "VARCHAR(120) DEFAULT ''",
            "categoria_id": "INT DEFAULT 1",
            "categoria": "VARCHAR(255) DEFAULT ''",
            "preco": "DOUBLE DEFAULT 0.0",
            "preco_venda": "DOUBLE DEFAULT 0.0",
            "preco_custo": "DOUBLE DEFAULT 0.0",
            "preco_atacado": "DOUBLE DEFAULT 0.0",
            "atacado_qtd_minima": "DOUBLE DEFAULT 10.0",
            "preco_promocional": "DOUBLE DEFAULT 0.0",
            "promocao_ativa": "INT DEFAULT 0",
            "promocao_inicio": "VARCHAR(500) DEFAULT ''",
            "promocao_fim": "VARCHAR(500) DEFAULT ''",
            "preco_compra": "DOUBLE DEFAULT 0.0",
            "tipo": "VARCHAR(500) DEFAULT 'unidade'",
            "unidade": "VARCHAR(40) DEFAULT 'unidade'",
            "estoque": "DOUBLE DEFAULT 0.0",
            "estoque_inicial": "DOUBLE DEFAULT 0.0",
            "estoque_minimo": "DOUBLE DEFAULT 5.0",
            "fidelidade_pontos": "INT DEFAULT 0",
            "tamanho_id": "INT DEFAULT NULL",
            "controlar_lote_validade": "INT DEFAULT 0",
            "lote": "VARCHAR(500) DEFAULT ''",
            "validade": "VARCHAR(500) DEFAULT ''",
            "data_validade": "VARCHAR(500) DEFAULT ''",
            "fornecedor_id": "INT NULL",
            "imagem": "LONGTEXT NULL",
            "descricao": "TEXT NULL",
            "ativo": "INT DEFAULT 1",
            "created_at": TS,
            "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── CLIENTES ───────────────────────────
    "clientes": (
        f"""CREATE TABLE IF NOT EXISTS clientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            cpf VARCHAR(500) DEFAULT '',
            telefone VARCHAR(500) DEFAULT '',
            endereco VARCHAR(500) DEFAULT '',
            bairro VARCHAR(500) DEFAULT '',
            observacao VARCHAR(500) DEFAULT '',
            saldo_fidelidade DOUBLE DEFAULT 0.0,
            saldo_credito DOUBLE DEFAULT 0.0,
            email VARCHAR(500) DEFAULT '',
            data_nascimento VARCHAR(500) DEFAULT '',
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''",
            "cpf": "VARCHAR(500) DEFAULT ''",
            "cpf_cnpj": "VARCHAR(32) DEFAULT ''",
            "telefone": "VARCHAR(500) DEFAULT ''",
            "whatsapp": "VARCHAR(60) DEFAULT ''",
            "endereco": "VARCHAR(500) DEFAULT ''",
            "numero": "VARCHAR(30) DEFAULT ''",
            "bairro": "VARCHAR(500) DEFAULT ''",
            "cidade": "VARCHAR(120) DEFAULT ''",
            "uf": "VARCHAR(5) DEFAULT ''",
            "cep": "VARCHAR(20) DEFAULT ''",
            "observacao": "VARCHAR(500) DEFAULT ''",
            "limite_credito": "DOUBLE DEFAULT 0.0",
            "saldo_fidelidade": "DOUBLE DEFAULT 0.0",
            "saldo_credito": "DOUBLE DEFAULT 0.0",
            "email": "VARCHAR(500) DEFAULT ''",
            "data_nascimento": "VARCHAR(500) DEFAULT ''",
            "ativo": "INT DEFAULT 1",
            "created_at": TS,
            "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── FORNECEDORES ───────────────────────────
    "fornecedores": (
        f"""CREATE TABLE IF NOT EXISTS fornecedores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            cnpj VARCHAR(500) DEFAULT '',
            contato VARCHAR(500) DEFAULT '',
            telefone VARCHAR(500) DEFAULT '',
            email VARCHAR(500) DEFAULT '',
            endereco VARCHAR(500) DEFAULT '',
            observacao VARCHAR(500) DEFAULT '',
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''",
            "cnpj": "VARCHAR(500) DEFAULT ''",
            "contato": "VARCHAR(500) DEFAULT ''",
            "telefone": "VARCHAR(500) DEFAULT ''",
            "email": "VARCHAR(500) DEFAULT ''",
            "endereco": "VARCHAR(500) DEFAULT ''",
            "observacao": "VARCHAR(500) DEFAULT ''",   # <- faltava (erro ao cadastrar fornecedor)
            "ativo": "INT DEFAULT 1",
            "created_at": TS,
            "updated_at": TS_UPD,                       # <- faltava
        },
    ),

    # ─────────────────────────── TAMANHOS ───────────────────────────
    "tamanhos": (
        f"""CREATE TABLE IF NOT EXISTS tamanhos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            sigla VARCHAR(500) DEFAULT '',
            ordem INT DEFAULT 0,
            tipo VARCHAR(500) DEFAULT 'Roupa',
            descricao VARCHAR(500) DEFAULT '',
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''",
            "sigla": "VARCHAR(500) DEFAULT ''",
            "ordem": "INT DEFAULT 0",
            "tipo": "VARCHAR(500) DEFAULT 'Roupa'",
            "descricao": "VARCHAR(500) DEFAULT ''",
            "ativo": "INT DEFAULT 1",
            "created_at": TS,
            "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────── TAMANHOS x PRODUTOS ───────────────────────
    "tamanhos_produtos": (
        f"""CREATE TABLE IF NOT EXISTS tamanhos_produtos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            produto_id INT,
            nome VARCHAR(120) DEFAULT '',
            tamanho VARCHAR(120) DEFAULT '',
            descricao VARCHAR(255) DEFAULT '',
            estoque DECIMAL(15,3) DEFAULT 0,
            preco DECIMAL(15,2) DEFAULT 0,
            preco_venda DECIMAL(15,2) DEFAULT 0,
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "produto_id": "INT NULL",
            "nome": "VARCHAR(120) DEFAULT ''",
            "tamanho": "VARCHAR(120) DEFAULT ''",
            "descricao": "VARCHAR(255) DEFAULT ''",
            "estoque": "DECIMAL(15,3) DEFAULT 0",
            "preco": "DECIMAL(15,2) DEFAULT 0",
            "preco_venda": "DECIMAL(15,2) DEFAULT 0",
            "ativo": "INT DEFAULT 1",
            "created_at": TS,
            "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── NOTAS DE ENTRADA ───────────────────────────
    "notas_entrada": (
        f"""CREATE TABLE IF NOT EXISTS notas_entrada (
            id INT AUTO_INCREMENT PRIMARY KEY,
            numero_nota VARCHAR(500) DEFAULT '',
            fornecedor_id INT NULL,
            fornecedor_nome VARCHAR(500) DEFAULT '',
            data_entrada VARCHAR(500) NULL,
            total DOUBLE DEFAULT 0.0,
            itens LONGTEXT NULL,
            usuario VARCHAR(500) DEFAULT '',
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "numero_nota": "VARCHAR(500) DEFAULT ''",    # <- codigo usa numero_nota (tabela antiga tinha 'numero')
            "fornecedor_id": "INT NULL",
            "fornecedor_nome": "VARCHAR(500) DEFAULT ''",  # <- faltava
            "data_emissao": "VARCHAR(500) NULL",
            "data_entrada": "VARCHAR(500) NULL",
            "total": "DOUBLE DEFAULT 0.0",
            "itens": "LONGTEXT NULL",                    # <- faltava (guarda os itens da nota em JSON)
            "usuario": "VARCHAR(500) DEFAULT ''",        # <- faltava
            "observacao": "TEXT NULL",
            "created_at": TS,
            "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── ENTREGADORES ───────────────────────────
    "entregadores": (
        f"""CREATE TABLE IF NOT EXISTS entregadores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            cpf VARCHAR(500) DEFAULT '',
            telefone VARCHAR(500) DEFAULT '',
            telefone2 VARCHAR(500) DEFAULT '',
            whatsapp VARCHAR(80) DEFAULT '',
            veiculo VARCHAR(500) DEFAULT 'Moto',
            placa VARCHAR(500) DEFAULT '',
            cnh VARCHAR(500) DEFAULT '',
            endereco VARCHAR(500) DEFAULT '',
            bairro VARCHAR(500) DEFAULT '',
            pix VARCHAR(500) DEFAULT '',
            valor_entrega DOUBLE DEFAULT 0.0,
            taxa_entrega DECIMAL(15,4) DEFAULT 0,
            status VARCHAR(500) DEFAULT 'Ativo',
            data_admissao VARCHAR(500) DEFAULT '',
            observacao VARCHAR(500) DEFAULT '',
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''", "cpf": "VARCHAR(500) DEFAULT ''",
            "telefone": "VARCHAR(500) DEFAULT ''", "telefone2": "VARCHAR(500) DEFAULT ''",
            "whatsapp": "VARCHAR(80) DEFAULT ''", "veiculo": "VARCHAR(500) DEFAULT 'Moto'",
            "placa": "VARCHAR(500) DEFAULT ''", "cnh": "VARCHAR(500) DEFAULT ''",
            "endereco": "VARCHAR(500) DEFAULT ''", "bairro": "VARCHAR(500) DEFAULT ''",
            "pix": "VARCHAR(500) DEFAULT ''", "valor_entrega": "DOUBLE DEFAULT 0.0",
            "taxa_entrega": "DECIMAL(15,4) DEFAULT 0", "status": "VARCHAR(500) DEFAULT 'Ativo'",
            "data_admissao": "VARCHAR(500) DEFAULT ''", "observacao": "VARCHAR(500) DEFAULT ''",
            "ativo": "INT DEFAULT 1", "created_at": TS, "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── VENDEDORES ───────────────────────────
    "vendedores": (
        f"""CREATE TABLE IF NOT EXISTS vendedores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            cpf VARCHAR(500) DEFAULT '',
            rg VARCHAR(500) DEFAULT '',
            telefone VARCHAR(500) DEFAULT '',
            telefone2 VARCHAR(500) DEFAULT '',
            email VARCHAR(500) DEFAULT '',
            endereco VARCHAR(500) DEFAULT '',
            bairro VARCHAR(500) DEFAULT '',
            cidade VARCHAR(500) DEFAULT '',
            comissao DOUBLE DEFAULT 0.0,
            meta_mensal DOUBLE DEFAULT 0.0,
            salario_base DOUBLE DEFAULT 0.0,
            pix VARCHAR(500) DEFAULT '',
            status VARCHAR(500) DEFAULT 'Ativo',
            data_admissao VARCHAR(500) DEFAULT '',
            data_demissao VARCHAR(500) DEFAULT '',
            observacao VARCHAR(500) DEFAULT '',
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''", "cpf": "VARCHAR(500) DEFAULT ''",
            "rg": "VARCHAR(500) DEFAULT ''", "telefone": "VARCHAR(500) DEFAULT ''",
            "telefone2": "VARCHAR(500) DEFAULT ''", "email": "VARCHAR(500) DEFAULT ''",
            "endereco": "VARCHAR(500) DEFAULT ''", "bairro": "VARCHAR(500) DEFAULT ''",
            "cidade": "VARCHAR(500) DEFAULT ''", "comissao": "DOUBLE DEFAULT 0.0",
            "meta_mensal": "DOUBLE DEFAULT 0.0", "salario_base": "DOUBLE DEFAULT 0.0",
            "pix": "VARCHAR(500) DEFAULT ''", "status": "VARCHAR(500) DEFAULT 'Ativo'",
            "data_admissao": "VARCHAR(500) DEFAULT ''", "data_demissao": "VARCHAR(500) DEFAULT ''",
            "observacao": "VARCHAR(500) DEFAULT ''", "ativo": "INT DEFAULT 1",
            "created_at": TS, "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── BAIRROS ───────────────────────────
    "bairros": (
        f"""CREATE TABLE IF NOT EXISTS bairros (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            cidade VARCHAR(500) DEFAULT '',
            valor_entrega DOUBLE DEFAULT 0.0,
            taxa_entrega DECIMAL(15,4) DEFAULT 0,
            tempo_estimado VARCHAR(500) DEFAULT '',
            observacao VARCHAR(500) DEFAULT '',
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''", "cidade": "VARCHAR(500) DEFAULT ''",
            "valor_entrega": "DOUBLE DEFAULT 0.0", "taxa_entrega": "DECIMAL(15,4) DEFAULT 0",
            "tempo_estimado": "VARCHAR(500) DEFAULT ''", "observacao": "VARCHAR(500) DEFAULT ''",
            "ativo": "INT DEFAULT 1", "created_at": TS, "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── CARTOES ───────────────────────────
    "cartoes": (
        f"""CREATE TABLE IF NOT EXISTS cartoes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            bandeira VARCHAR(500) DEFAULT '',
            tipo VARCHAR(500) DEFAULT 'Crédito',
            taxa_debito DOUBLE DEFAULT 0.0,
            taxa_credito DOUBLE DEFAULT 0.0,
            taxa_credito_parcelado DOUBLE DEFAULT 0.0,
            dias_recebimento INT DEFAULT 30,
            max_parcelas INT DEFAULT 1,
            operadora VARCHAR(500) DEFAULT '',
            codigo_operadora VARCHAR(500) DEFAULT '',
            ativo INT DEFAULT 1,
            observacao VARCHAR(500) DEFAULT '',
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''", "bandeira": "VARCHAR(500) DEFAULT ''",
            "tipo": "VARCHAR(500) DEFAULT 'Crédito'", "taxa_debito": "DOUBLE DEFAULT 0.0",
            "taxa_credito": "DOUBLE DEFAULT 0.0", "taxa_credito_parcelado": "DOUBLE DEFAULT 0.0",
            "dias_recebimento": "INT DEFAULT 30", "max_parcelas": "INT DEFAULT 1",
            "operadora": "VARCHAR(500) DEFAULT ''", "codigo_operadora": "VARCHAR(500) DEFAULT ''",
            "ativo": "INT DEFAULT 1", "observacao": "VARCHAR(500) DEFAULT ''",
            "created_at": TS, "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── SERVICOS ───────────────────────────
    "servicos": (
        f"""CREATE TABLE IF NOT EXISTS servicos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(500) NOT NULL,
            descricao VARCHAR(500) DEFAULT '',
            categoria VARCHAR(500) DEFAULT 'Outros',
            preco DOUBLE DEFAULT 0.0,
            duracao_estimada VARCHAR(500) DEFAULT 'A combinar',
            unidade_cobranca VARCHAR(500) DEFAULT 'Por serviço',
            status VARCHAR(500) DEFAULT 'Ativo',
            codigo VARCHAR(500) DEFAULT '',
            garantia VARCHAR(500) DEFAULT 'Sem garantia',
            observacao VARCHAR(500) DEFAULT '',
            ativo INT DEFAULT 1,
            created_at {TS},
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(500) NOT NULL DEFAULT ''", "descricao": "VARCHAR(500) DEFAULT ''",
            "categoria": "VARCHAR(500) DEFAULT 'Outros'", "preco": "DOUBLE DEFAULT 0.0",
            "duracao_estimada": "VARCHAR(500) DEFAULT 'A combinar'",
            "unidade_cobranca": "VARCHAR(500) DEFAULT 'Por serviço'",
            "status": "VARCHAR(500) DEFAULT 'Ativo'", "codigo": "VARCHAR(500) DEFAULT ''",
            "garantia": "VARCHAR(500) DEFAULT 'Sem garantia'", "observacao": "VARCHAR(500) DEFAULT ''",
            "ativo": "INT DEFAULT 1", "created_at": TS, "updated_at": TS_UPD,
        },
    ),

    # ─────────────────────────── CONTAS A PAGAR ───────────────────────────
    "contas_pagar": (
        f"""CREATE TABLE IF NOT EXISTS contas_pagar (
            id INT AUTO_INCREMENT PRIMARY KEY,
            descricao VARCHAR(500) NOT NULL,
            valor DOUBLE DEFAULT 0.0,
            data_vencimento VARCHAR(500) NULL,
            fornecedor_id INT NULL,
            status VARCHAR(500) DEFAULT 'Pendente',
            data_pagamento VARCHAR(500) DEFAULT '',
            forma_pagamento VARCHAR(500) DEFAULT '',
            observacao VARCHAR(500) DEFAULT '',
            created_at {TS}
        ) {ENGINE}""",
        {
            "descricao": "VARCHAR(500) NOT NULL DEFAULT ''", "valor": "DOUBLE DEFAULT 0.0",
            "data_vencimento": "VARCHAR(500) NULL", "fornecedor_id": "INT NULL",
            "status": "VARCHAR(500) DEFAULT 'Pendente'", "data_pagamento": "VARCHAR(500) DEFAULT ''",
            "forma_pagamento": "VARCHAR(500) DEFAULT ''", "observacao": "VARCHAR(500) DEFAULT ''",
            "created_at": TS,
        },
    ),

    # ─────────────────────────── CONTAS A RECEBER ───────────────────────────
    "contas_receber": (
        f"""CREATE TABLE IF NOT EXISTS contas_receber (
            id INT AUTO_INCREMENT PRIMARY KEY,
            descricao VARCHAR(500) NOT NULL,
            valor DOUBLE DEFAULT 0.0,
            data_vencimento VARCHAR(500) NULL,
            cliente_id INT NULL,
            status VARCHAR(500) DEFAULT 'Pendente',
            data_recebimento VARCHAR(500) DEFAULT '',
            forma_pagamento VARCHAR(500) DEFAULT '',
            observacao VARCHAR(500) DEFAULT '',
            venda_id INT NULL,
            created_at {TS}
        ) {ENGINE}""",
        {
            "descricao": "VARCHAR(500) NOT NULL DEFAULT ''", "valor": "DOUBLE DEFAULT 0.0",
            "data_vencimento": "VARCHAR(500) NULL", "cliente_id": "INT NULL",
            "status": "VARCHAR(500) DEFAULT 'Pendente'", "data_recebimento": "VARCHAR(500) DEFAULT ''",
            "forma_pagamento": "VARCHAR(500) DEFAULT ''", "observacao": "VARCHAR(500) DEFAULT ''",
            "venda_id": "INT NULL", "created_at": TS,
        },
    ),

    # ─────────────────────────── EMPRESA ───────────────────────────
    "empresa": (
        f"""CREATE TABLE IF NOT EXISTS empresa (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(255) DEFAULT 'Minha Empresa',
            razao_social VARCHAR(255) DEFAULT '',
            cnpj VARCHAR(32) DEFAULT '',
            telefone VARCHAR(60) DEFAULT '',
            email VARCHAR(120) DEFAULT '',
            endereco TEXT NULL,
            cidade VARCHAR(120) DEFAULT '',
            uf VARCHAR(5) DEFAULT '',
            cep VARCHAR(20) DEFAULT '',
            updated_at {TS_UPD}
        ) {ENGINE}""",
        {
            "nome": "VARCHAR(255) DEFAULT 'Minha Empresa'", "razao_social": "VARCHAR(255) DEFAULT ''",
            "cnpj": "VARCHAR(32) DEFAULT ''", "telefone": "VARCHAR(60) DEFAULT ''",
            "email": "VARCHAR(120) DEFAULT ''", "endereco": "TEXT NULL",
            "cidade": "VARCHAR(120) DEFAULT ''", "uf": "VARCHAR(5) DEFAULT ''",
            "cep": "VARCHAR(20) DEFAULT ''", "updated_at": TS_UPD,
        },
    ),
}

# Indices uteis (tabela, nome_indice, colunas). Criados se ainda nao existirem.
INDICES = [
    ("produtos", "idx_produtos_nome", "nome"),
    ("produtos", "idx_produtos_barras", "codigo_barras"),
    ("clientes", "idx_clientes_nome", "nome"),
    ("fornecedores", "idx_fornecedores_nome", "nome"),
    ("notas_entrada", "idx_notas_numero", "numero_nota"),
    ("tamanhos", "idx_tamanhos_nome", "nome"),
]


# ══════════════════════════════════════════════════════════════════════════
# Conexao MySQL
# ══════════════════════════════════════════════════════════════════════════
def conectar(cfg):
    host = cfg["host"]; port = int(cfg.get("port", 3306))
    user = cfg["user"]; password = cfg.get("password", ""); database = cfg["database"]
    erro = None
    try:
        import mysql.connector  # type: ignore
        return mysql.connector.connect(host=host, port=port, user=user,
                                       password=password, database=database,
                                       charset="utf8mb4", autocommit=False,
                                       connection_timeout=30), "mysql.connector"
    except Exception as e:
        erro = e
    try:
        import pymysql  # type: ignore
        return pymysql.connect(host=host, port=port, user=user, password=password,
                               database=database, charset="utf8mb4", autocommit=False,
                               connect_timeout=30,
                               cursorclass=pymysql.cursors.DictCursor), "pymysql"
    except Exception as e:
        erro = e
    raise RuntimeError(
        "Falha ao conectar no MySQL. Verifique host/usuario/senha/banco.\n"
        f"Ultimo erro: {erro}\n"
        "Instale o conector:  pip install mysql-connector-python"
    )


# ══════════════════════════════════════════════════════════════════════════
# Descoberta de credenciais (mesma logica do sistema)
# ══════════════════════════════════════════════════════════════════════════
def candidatos_ini():
    cands = [r"C:\Quantum\config.ini",
             os.path.join(os.getcwd(), "config.ini"),
             os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")]
    vis, out = set(), []
    for c in cands:
        cn = os.path.abspath(c)
        if cn not in vis and os.path.exists(cn):
            vis.add(cn); out.append(cn)
    return out


def ler_ini(caminho):
    cp = configparser.ConfigParser(); cp.read(caminho, encoding="utf-8")
    if not cp.has_section("mysql"):
        return None
    return {"host": cp.get("mysql", "host", fallback="127.0.0.1").strip() or "127.0.0.1",
            "port": cp.getint("mysql", "port", fallback=3306),
            "user": cp.get("mysql", "user", fallback="").strip(),
            "password": cp.get("mysql", "password", fallback=""),
            "database": cp.get("mysql", "database", fallback="").strip()}


def ler_json_externo(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        d = json.load(f)
    host = d.get("envio_mysql_externo_servidor", "").strip()
    if not host:
        return None
    return {"host": host, "port": int(d.get("envio_mysql_externo_porta", 3306) or 3306),
            "user": d.get("envio_mysql_externo_usuario", "").strip(),
            "password": d.get("envio_mysql_externo_senha", ""),
            "database": d.get("envio_mysql_externo_banco", "").strip()}


def perguntar(campo, atual, oculto=False):
    suf = f" [{atual}]" if atual not in (None, "") else ""
    if oculto and atual:
        suf = " [***definida***]"
    try:
        v = input(f"  {campo}{suf}: ").strip()
    except (EOFError, KeyboardInterrupt):
        v = ""
    return v or (atual if atual is not None else "")


def resolver_credenciais(args):
    cfg = {"host": "", "port": 3306, "user": "", "password": "", "database": ""}
    if args.config_json:
        try:
            j = ler_json_externo(args.config_json)
            if j:
                cfg.update({k: v for k, v in j.items() if v not in (None, "")})
                print(f"[i] Credenciais base de {args.config_json} (envio_mysql_externo_*).")
        except Exception as e:
            print(f"[!] Nao li {args.config_json}: {e}")
    for ini in ([args.config_ini] if args.config_ini else candidatos_ini()):
        if ini and os.path.exists(ini):
            try:
                d = ler_ini(ini)
                if d:
                    cfg.update({k: v for k, v in d.items() if v not in (None, "")})
                    print(f"[i] Credenciais de {ini} (secao [mysql]).")
                    break
            except Exception as e:
                print(f"[!] Falha ao ler {ini}: {e}")
    for k in ("host", "port", "user", "password", "database"):
        v = getattr(args, k, None)
        if v not in (None, ""):
            cfg[k] = v
    faltando = [k for k in ("host", "user", "database") if not cfg.get(k)]
    if faltando and not args.yes:
        print("\nInforme os dados de conexao MySQL (Enter mantem o valor entre colchetes):")
        cfg["host"] = perguntar("Host", cfg.get("host") or "127.0.0.1")
        cfg["port"] = perguntar("Porta", cfg.get("port") or 3306)
        cfg["user"] = perguntar("Usuario", cfg.get("user"))
        cfg["password"] = perguntar("Senha", cfg.get("password"), oculto=True)
        cfg["database"] = perguntar("Banco (database)", cfg.get("database"))
    try:
        cfg["port"] = int(cfg.get("port", 3306) or 3306)
    except Exception:
        cfg["port"] = 3306
    return cfg


# ══════════════════════════════════════════════════════════════════════════
# Reparo da estrutura
# ══════════════════════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser(
        description="Cria tabelas/colunas faltantes no MySQL do Quantum PDV.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host"); ap.add_argument("--port", type=int)
    ap.add_argument("--user"); ap.add_argument("--password"); ap.add_argument("--database")
    ap.add_argument("--config-ini"); ap.add_argument("--config-json")
    ap.add_argument("--dry-run", action="store_true", help="So mostra o que faria.")
    ap.add_argument("--yes", action="store_true", help="Nao pergunta nada.")
    args = ap.parse_args()

    print("╔" + "═" * 68 + "╗")
    print("║  REPARADOR DE ESTRUTURA DO BANCO — Quantum / Farma Quantum PDV     ║")
    print("║  Cria TABELAS e COLUNAS faltantes (fornecedor, tamanho, nota...)  ║")
    print("╚" + "═" * 68 + "╝")
    if args.dry_run:
        print(">>> MODO SIMULACAO (--dry-run): nada sera alterado. <<<")

    cfg = resolver_credenciais(args)
    if not (cfg.get("host") and cfg.get("user") and cfg.get("database")):
        print("[X] Dados de conexao incompletos (host/usuario/banco).")
        sys.exit(1)

    print(f"\n[i] Conectando em {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']} ...")
    conn, driver = conectar(cfg)
    print(f"[✓] Conectado ({driver}).")
    dbname = cfg["database"]

    def q(sql, params=None):
        cur = conn.cursor(dictionary=True) if driver == "mysql.connector" else conn.cursor()
        cur.execute(sql, params or ()); rows = cur.fetchall(); cur.close(); return rows

    def ex(sql, params=None):
        cur = conn.cursor(); cur.execute(sql, params or ()); cur.close()

    def tabela_existe(t):
        return bool(q("SELECT 1 FROM information_schema.tables "
                      "WHERE table_schema=%s AND table_name=%s", (dbname, t)))

    def colunas_de(t):
        rows = q("SELECT COLUMN_NAME AS c FROM information_schema.columns "
                 "WHERE table_schema=%s AND table_name=%s", (dbname, t))
        return {(r["c"] if isinstance(r, dict) else r[0]).lower() for r in rows}

    def indice_existe(t, idx):
        return bool(q("SELECT 1 FROM information_schema.statistics "
                      "WHERE table_schema=%s AND table_name=%s AND index_name=%s",
                      (dbname, t, idx)))

    tabelas_criadas, colunas_add, indices_add, avisos = [], [], [], []

    try:
        for tabela, (create_sql, colunas) in SCHEMA.items():
            novo = not tabela_existe(tabela)
            if novo:
                print(f"\n[+] Tabela FALTANDO: {tabela}  ->  criando...")
                if not args.dry_run:
                    ex(create_sql)
                tabelas_criadas.append(tabela)
            else:
                print(f"\n[i] Tabela existe: {tabela}  ->  conferindo colunas...")

            existentes = set() if (novo and args.dry_run) else colunas_de(tabela)
            for col, definicao in colunas.items():
                if col.lower() not in existentes:
                    print(f"    [+] coluna faltando: {tabela}.{col}  ->  ADD COLUMN {definicao}")
                    if not args.dry_run:
                        try:
                            ex(f"ALTER TABLE `{tabela}` ADD COLUMN `{col}` {definicao}")
                        except Exception as e:
                            avisos.append(f"{tabela}.{col}: {e}")
                            print(f"        [!] aviso: {e}")
                    colunas_add.append(f"{tabela}.{col}")

        # Indices
        for tabela, idx, cols in INDICES:
            if tabela_existe(tabela) and not indice_existe(tabela, idx):
                print(f"[+] indice faltando: {idx} em {tabela}({cols})")
                if not args.dry_run:
                    try:
                        ex(f"CREATE INDEX `{idx}` ON `{tabela}` (`{cols}`)")
                    except Exception as e:
                        avisos.append(f"indice {idx}: {e}")
                indices_add.append(idx)

        if not args.dry_run:
            conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Relatorio
    print("\n" + "=" * 70)
    print(" RESUMO DO REPARO" + (" (SIMULACAO)" if args.dry_run else ""))
    print("=" * 70)
    print(f"  Tabelas criadas .....: {len(tabelas_criadas)}" +
          (f"  -> {', '.join(tabelas_criadas)}" if tabelas_criadas else ""))
    print(f"  Colunas adicionadas .: {len(colunas_add)}")
    for c in colunas_add:
        print(f"      + {c}")
    print(f"  Indices criados .....: {len(indices_add)}" +
          (f"  -> {', '.join(indices_add)}" if indices_add else ""))
    if avisos:
        print(f"\n  Avisos ({len(avisos)}):")
        for a in avisos:
            print(f"      ! {a}")
    if not tabelas_criadas and not colunas_add and not indices_add:
        print("\n  [✓] Nada faltando: a estrutura do banco ja estava completa.")
    else:
        print("\n  [✓] Estrutura corrigida." if not args.dry_run
              else "\n  [i] Rode sem --dry-run para aplicar as mudancas acima.")
    print("=" * 70)
    print(" Reabra o sistema e teste cadastrar Fornecedor, Tamanho e Nota de Entrada.")
    print("=" * 70)


if __name__ == "__main__":
    main()
