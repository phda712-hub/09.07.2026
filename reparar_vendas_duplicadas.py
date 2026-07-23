# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
 REPARADOR DE VENDAS DUPLICADAS  ·  Quantum / Farma Quantum PDV
═══════════════════════════════════════════════════════════════════════════════

O QUE ELE RESOLVE
-----------------
O sistema gravava, na tabela MySQL `vendas`, MAIS DE UMA LINHA para o MESMO
número de cupom (coupon_number). Como a tabela não tinha índice UNIQUE em
coupon_number e a gravação não era atômica, o mesmo cupom se "propagava",
multiplicando itens, quantidade e valor no relatório de Produtos Vendidos
(foi o caso da venda 739 — e também de outras: 730, 733, 734, 735, 736, 737,
738, 740, 741, 742).

Este script:
  1. Conecta no MySQL do cliente (descobre as credenciais em config.ini,
     ou você informa por parâmetro / interativamente).
  2. Lista TODOS os cupons duplicados (não só o 739) e quantas cópias existem.
  3. Faz um BACKUP completo (JSON) das linhas afetadas antes de mexer.
  4. Remove as linhas duplicadas, mantendo APENAS 1 por cupom (a de maior id,
     que é o registro mais recente/completo).
  5. (Opcional) Cria um índice UNIQUE em coupon_number para o banco passar a
     REJEITAR duplicidade no futuro.
  6. Também limpa o arquivo local sales_log.json, se existir (instalações em
     modo JSON / fallback).

SEGURANÇA
---------
  • Sempre gera backup antes de apagar.
  • Modo simulação: use --dry-run para apenas VER o que seria feito.
  • Nenhuma venda legítima é perdida: mantemos 1 registro por cupom.

USO
---
  python reparar_vendas_duplicadas.py                # descobre config.ini e pergunta o que precisar
  python reparar_vendas_duplicadas.py --dry-run      # só mostra, não altera
  python reparar_vendas_duplicadas.py --host 127.0.0.1 --user root --password SENHA --database farmacia
  python reparar_vendas_duplicadas.py --config-ini "C:\\Quantum\\config.ini"
  python reparar_vendas_duplicadas.py --config-json "config.json"   # usa envio_mysql_externo_*
  python reparar_vendas_duplicadas.py --yes --add-unique-index      # sem perguntas, cria índice UNIQUE
  python reparar_vendas_duplicadas.py --sales-json "pdv_data\\sales_log.json"  # também limpa o JSON

Requisitos: mysql-connector-python  (ou PyMySQL).  pip install mysql-connector-python
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import argparse
import configparser
import datetime


# ──────────────────────────────────────────────────────────────────────────
# Conector MySQL (aceita mysql-connector-python OU PyMySQL)
# ──────────────────────────────────────────────────────────────────────────
def _conectar_mysql(cfg):
    host = cfg["host"]; port = int(cfg.get("port", 3306))
    user = cfg["user"]; password = cfg.get("password", "")
    database = cfg["database"]
    ultimo_erro = None

    # 1) mysql.connector
    try:
        import mysql.connector  # type: ignore
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password,
            database=database, charset="utf8mb4", autocommit=False,
            connection_timeout=30,
        )
        return conn, "mysql.connector"
    except Exception as e:
        ultimo_erro = e

    # 2) pymysql
    try:
        import pymysql  # type: ignore
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password,
            database=database, charset="utf8mb4", autocommit=False,
            connect_timeout=30, cursorclass=pymysql.cursors.DictCursor,
        )
        return conn, "pymysql"
    except Exception as e:
        ultimo_erro = e

    raise RuntimeError(
        "Não foi possível conectar ao MySQL. Verifique host/usuário/senha/banco.\n"
        f"Último erro: {ultimo_erro}\n"
        "Dica: instale o conector com  ->  pip install mysql-connector-python"
    )


def _dict_cursor(conn, driver):
    """Retorna um cursor que devolve linhas como dicionário."""
    if driver == "mysql.connector":
        return conn.cursor(dictionary=True)
    return conn.cursor()  # pymysql já está em DictCursor


# ──────────────────────────────────────────────────────────────────────────
# Descoberta de credenciais
# ──────────────────────────────────────────────────────────────────────────
def _candidatos_config_ini():
    caminhos = [
        r"C:\Quantum\config.ini",
        os.path.join(os.getcwd(), "config.ini"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.ini"),
    ]
    vistos, saida = set(), []
    for c in caminhos:
        cn = os.path.abspath(c)
        if cn not in vistos and os.path.exists(cn):
            vistos.add(cn); saida.append(cn)
    return saida


def _ler_config_ini(caminho):
    cp = configparser.ConfigParser()
    cp.read(caminho, encoding="utf-8")
    if not cp.has_section("mysql"):
        return None
    return {
        "host": cp.get("mysql", "host", fallback="127.0.0.1").strip() or "127.0.0.1",
        "port": cp.getint("mysql", "port", fallback=3306),
        "user": cp.get("mysql", "user", fallback="").strip(),
        "password": cp.get("mysql", "password", fallback=""),
        "database": cp.get("mysql", "database", fallback="").strip(),
    }


def _ler_config_json_externo(caminho):
    """Lê os campos envio_mysql_externo_* de um config.json (sincronização externa)."""
    with open(caminho, "r", encoding="utf-8") as f:
        d = json.load(f)
    host = d.get("envio_mysql_externo_servidor", "").strip()
    if not host:
        return None
    return {
        "host": host,
        "port": int(d.get("envio_mysql_externo_porta", 3306) or 3306),
        "user": d.get("envio_mysql_externo_usuario", "").strip(),
        "password": d.get("envio_mysql_externo_senha", ""),
        "database": d.get("envio_mysql_externo_banco", "").strip(),
    }


def _perguntar(campo, atual, oculto=False):
    sufixo = f" [{atual}]" if atual not in (None, "") else ""
    if oculto and atual:
        sufixo = " [***definida***]"
    try:
        val = input(f"  {campo}{sufixo}: ").strip()
    except (EOFError, KeyboardInterrupt):
        val = ""
    return val or (atual if atual not in (None,) else "")


def resolver_credenciais(args):
    cfg = {"host": "", "port": 3306, "user": "", "password": "", "database": ""}

    # 1) config.json externo (se pedido)
    if args.config_json:
        try:
            j = _ler_config_json_externo(args.config_json)
            if j:
                cfg.update({k: v for k, v in j.items() if v not in (None, "")})
                print(f"[i] Credenciais base lidas de {args.config_json} (envio_mysql_externo_*).")
        except Exception as e:
            print(f"[!] Não consegui ler {args.config_json}: {e}")

    # 2) config.ini (informado ou descoberto)
    inis = [args.config_ini] if args.config_ini else _candidatos_config_ini()
    for ini in inis:
        if ini and os.path.exists(ini):
            try:
                d = _ler_config_ini(ini)
                if d:
                    cfg.update({k: v for k, v in d.items() if v not in (None, "")})
                    print(f"[i] Credenciais lidas de {ini} (seção [mysql]).")
                    break
            except Exception as e:
                print(f"[!] Falha ao ler {ini}: {e}")

    # 3) Overrides por linha de comando
    for k in ("host", "port", "user", "password", "database"):
        v = getattr(args, k, None)
        if v not in (None, ""):
            cfg[k] = v

    # 4) Preenche o que faltar interativamente (a não ser que --yes)
    faltando = [k for k in ("host", "user", "database") if not cfg.get(k)] or \
               ([] if cfg.get("password") else ["password"])
    if faltando and not args.yes:
        print("\nInforme os dados de conexão MySQL (Enter mantém o valor entre colchetes):")
        cfg["host"] = _perguntar("Host", cfg.get("host") or "127.0.0.1")
        cfg["port"] = _perguntar("Porta", cfg.get("port") or 3306)
        cfg["user"] = _perguntar("Usuário", cfg.get("user"))
        cfg["password"] = _perguntar("Senha", cfg.get("password"), oculto=True)
        cfg["database"] = _perguntar("Banco (database)", cfg.get("database"))

    try:
        cfg["port"] = int(cfg.get("port", 3306) or 3306)
    except Exception:
        cfg["port"] = 3306
    return cfg


# ──────────────────────────────────────────────────────────────────────────
# Reparo no MySQL
# ──────────────────────────────────────────────────────────────────────────
def _fetchall(conn, driver, sql, params=None):
    cur = _dict_cursor(conn, driver)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    return rows


def _execute(conn, driver, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or ())
    afetadas = cur.rowcount
    cur.close()
    return afetadas


def reparar_mysql(args):
    print("\n" + "=" * 70)
    print(" REPARO NO BANCO MySQL (tabela `vendas`)")
    print("=" * 70)

    cfg = resolver_credenciais(args)
    if not (cfg.get("host") and cfg.get("user") and cfg.get("database")):
        print("[X] Dados de conexão incompletos (host/usuário/banco). Abortando etapa MySQL.")
        return False

    print(f"\n[i] Conectando em {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']} ...")
    conn, driver = _conectar_mysql(cfg)
    print(f"[✓] Conectado ({driver}).")

    try:
        # A tabela existe?
        existe = _fetchall(conn, driver, "SHOW TABLES LIKE 'vendas'")
        if not existe:
            print("[!] A tabela `vendas` não existe neste banco. Nada a fazer no MySQL.")
            return True

        total_linhas = _fetchall(conn, driver, "SELECT COUNT(*) AS n FROM vendas")[0]["n"]

        dups = _fetchall(conn, driver,
            "SELECT coupon_number, COUNT(*) AS copias, MIN(id) AS menor_id, MAX(id) AS maior_id "
            "FROM vendas WHERE coupon_number IS NOT NULL "
            "GROUP BY coupon_number HAVING COUNT(*) > 1 "
            "ORDER BY coupon_number")

        nulos = _fetchall(conn, driver,
            "SELECT COUNT(*) AS n FROM vendas WHERE coupon_number IS NULL")[0]["n"]

        print(f"\n[i] Total de linhas na tabela `vendas`: {total_linhas}")
        print(f"[i] Cupons distintos duplicados: {len(dups)}")
        if nulos:
            print(f"[i] Linhas com coupon_number NULO (não deduplicáveis por cupom): {nulos}")

        if not dups:
            print("\n[✓] Nenhuma venda duplicada encontrada. O banco já está saudável.")
        else:
            linhas_excedentes = sum(int(d["copias"]) - 1 for d in dups)
            print("\n--- CUPONS DUPLICADOS ENCONTRADOS ---")
            print(f"{'CUPOM':>8} | {'CÓPIAS':>6} | mantém id | remove ids (menores)")
            print("-" * 60)
            for d in dups:
                cup = d["coupon_number"]
                print(f"{cup:>8} | {int(d['copias']):>6} | {int(d['maior_id']):>8}  | < {int(d['maior_id'])}")
            print("-" * 60)
            print(f"Linhas duplicadas a remover (mantendo 1 por cupom): {linhas_excedentes}")
            tem_739 = any(str(d["coupon_number"]) == "739" for d in dups)
            print(f"O cupom 739 estava duplicado? {'SIM' if tem_739 else 'não'}")
            print("Conclusão: o erro NÃO foi exclusivo do 739 — vários cupons foram afetados."
                  if len(dups) > 1 else
                  "Conclusão: o único cupom afetado foi o listado acima.")

            # BACKUP das linhas afetadas
            cupons_afetados = [d["coupon_number"] for d in dups]
            placeholders = ",".join(["%s"] * len(cupons_afetados))
            afetadas = _fetchall(conn, driver,
                f"SELECT * FROM vendas WHERE coupon_number IN ({placeholders}) ORDER BY coupon_number, id",
                cupons_afetados)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.abspath(f"backup_vendas_duplicadas_{ts}.json")
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(afetadas, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n[✓] Backup das linhas afetadas salvo em:\n    {backup_path}")

            if args.dry_run:
                print("\n[DRY-RUN] Simulação: NADA foi alterado no banco.")
            else:
                if not args.yes:
                    resp = input(f"\nConfirma remover {linhas_excedentes} linha(s) duplicada(s)? (s/N): ").strip().lower()
                    if resp not in ("s", "sim", "y", "yes"):
                        print("[i] Operação cancelada pelo usuário. Nada foi alterado.")
                        conn.rollback()
                        return True

                total_removidas = 0
                for d in dups:
                    cup = d["coupon_number"]
                    afet = _execute(conn, driver,
                        "DELETE v FROM vendas v "
                        "JOIN (SELECT MAX(id) AS keep_id FROM vendas WHERE coupon_number = %s) k "
                        "ON v.coupon_number = %s AND v.id < k.keep_id",
                        (cup, cup))
                    total_removidas += max(0, afet)
                conn.commit()
                print(f"[✓] Removidas {total_removidas} linha(s) duplicada(s). Mantido 1 registro por cupom.")

                # Verificação pós-reparo
                rest = _fetchall(conn, driver,
                    "SELECT COUNT(*) AS n FROM (SELECT coupon_number FROM vendas "
                    "WHERE coupon_number IS NOT NULL GROUP BY coupon_number HAVING COUNT(*)>1) t")[0]["n"]
                print(f"[i] Cupons ainda duplicados após o reparo: {rest}")

        # Índice UNIQUE (prevenção futura)
        criar_indice = args.add_unique_index
        if not args.dry_run and not args.no_unique_index and not criar_indice and not args.yes:
            r = input("\nCriar índice UNIQUE em coupon_number para IMPEDIR duplicidade futura? (S/n): ").strip().lower()
            criar_indice = r in ("", "s", "sim", "y", "yes")
        if args.yes and not args.no_unique_index:
            criar_indice = True

        if criar_indice and not args.dry_run:
            try:
                _execute(conn, driver,
                    "ALTER TABLE vendas ADD UNIQUE INDEX uq_vendas_coupon_number (coupon_number)")
                conn.commit()
                print("[✓] Índice UNIQUE `uq_vendas_coupon_number` criado. Duplicidade futura será rejeitada pelo banco.")
            except Exception as e:
                print(f"[!] Não foi possível criar o índice UNIQUE (talvez já exista ou ainda haja duplicidade): {e}")
                conn.rollback()
        elif args.dry_run and criar_indice:
            print("[DRY-RUN] Índice UNIQUE seria criado (não executado em simulação).")

        return True
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────
# Reparo no arquivo local sales_log.json (fallback / modo JSON)
# ──────────────────────────────────────────────────────────────────────────
def _chave_cupom(v):
    if not isinstance(v, dict):
        return None
    for k in ("coupon_number", "numero_venda", "cupom", "numero_cupom", "numero"):
        val = v.get(k)
        if val not in (None, ""):
            return str(val).strip()
    return None


def reparar_sales_json(caminho, dry_run=False):
    print("\n" + "=" * 70)
    print(" REPARO NO ARQUIVO LOCAL sales_log.json")
    print("=" * 70)
    if not caminho or not os.path.exists(caminho):
        print(f"[i] Arquivo não encontrado ({caminho}). Etapa ignorada.")
        return True

    with open(caminho, "r", encoding="utf-8") as f:
        vendas = json.load(f)
    if not isinstance(vendas, list):
        print("[!] Formato inesperado (esperava uma lista de vendas). Etapa ignorada.")
        return True

    vistos, ordem, sem_cupom = {}, [], []
    contagem = {}
    for v in vendas:
        cup = _chave_cupom(v)
        if cup is None:
            sem_cupom.append(v)
            continue
        contagem[cup] = contagem.get(cup, 0) + 1
        if cup not in vistos:
            ordem.append(cup)
        vistos[cup] = v  # mantém a última ocorrência

    dup = {c: n for c, n in contagem.items() if n > 1}
    resultado = [vistos[c] for c in ordem] + sem_cupom
    removidas = len(vendas) - len(resultado)

    print(f"[i] Registros no arquivo: {len(vendas)}")
    print(f"[i] Cupons duplicados: {len(dup)}  |  registros duplicados a remover: {removidas}")
    if dup:
        for c in sorted(dup, key=lambda x: (len(x), x)):
            print(f"    cupom {c}: {dup[c]} cópias")

    if removidas <= 0:
        print("[✓] Arquivo já está sem duplicidades.")
        return True

    if dry_run:
        print("[DRY-RUN] Simulação: arquivo NÃO foi alterado.")
        return True

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = f"{caminho}.bak_{ts}"
    with open(bak, "w", encoding="utf-8") as f:
        json.dump(vendas, f, ensure_ascii=False, indent=2)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)
    print(f"[✓] Backup salvo em {bak}")
    print(f"[✓] Arquivo corrigido: {removidas} registro(s) duplicado(s) removido(s).")
    return True


def main():
    ap = argparse.ArgumentParser(
        description="Repara vendas duplicadas (mesmo cupom repetido) no MySQL e/ou no sales_log.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--host")
    ap.add_argument("--port", type=int)
    ap.add_argument("--user")
    ap.add_argument("--password")
    ap.add_argument("--database")
    ap.add_argument("--config-ini", help="Caminho de um config.ini com seção [mysql].")
    ap.add_argument("--config-json", help="config.json para ler envio_mysql_externo_* (sincronização externa).")
    ap.add_argument("--sales-json", help="Caminho do sales_log.json local para também limpar.")
    ap.add_argument("--dry-run", action="store_true", help="Só mostra o que faria, sem alterar nada.")
    ap.add_argument("--yes", action="store_true", help="Não pergunta nada (assume SIM). Cuidado.")
    ap.add_argument("--add-unique-index", action="store_true", help="Cria índice UNIQUE em coupon_number.")
    ap.add_argument("--no-unique-index", action="store_true", help="Nunca cria o índice UNIQUE.")
    ap.add_argument("--skip-mysql", action="store_true", help="Não mexe no MySQL (só no JSON).")
    args = ap.parse_args()

    print("╔" + "═" * 68 + "╗")
    print("║  REPARADOR DE VENDAS DUPLICADAS — Quantum / Farma Quantum PDV      ║")
    print("║  Corrige o cupom 739 e TODOS os demais cupons duplicados          ║")
    print("╚" + "═" * 68 + "╝")
    if args.dry_run:
        print(">>> MODO SIMULAÇÃO (--dry-run): nada será alterado. <<<")

    ok = True
    if not args.skip_mysql:
        try:
            ok = reparar_mysql(args) and ok
        except Exception as e:
            ok = False
            print(f"\n[X] Erro no reparo MySQL: {e}")

    # sales_log.json: usa o informado ou tenta locais padrão
    sales_json = args.sales_json
    if not sales_json:
        for cand in (
            os.path.join(os.getcwd(), "pdv_data", "sales_log.json"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdv_data", "sales_log.json"),
        ):
            if os.path.exists(cand):
                sales_json = cand
                break
    if sales_json:
        try:
            reparar_sales_json(sales_json, dry_run=args.dry_run)
        except Exception as e:
            print(f"[X] Erro no reparo do sales_log.json: {e}")

    print("\n" + "=" * 70)
    print(" CONCLUÍDO." if ok else " CONCLUÍDO COM AVISOS (veja as mensagens acima).")
    print(" Após o reparo, reabra o sistema e gere novamente o relatório de")
    print(" Produtos Vendidos para confirmar que os valores estão corretos.")
    print("=" * 70)


if __name__ == "__main__":
    main()
