# -*- coding: utf-8 -*-
"""
===============================================================================
 LIMPEZA DE DADOS DE TESTE  ·  Quantum / Farma Quantum PDV
===============================================================================
 Percorre as tabelas de cadastro/movimento e, para CADA uma, mostra os
 registros e PERGUNTA o que voce quer excluir:

     [Enter]  Pular (nao exclui nada nesta tabela)
        T     Excluir TODOS os registros da tabela
        F     Excluir por FILTRO de texto (ex.: tudo que contem "teste")
        I     Excluir por IDs (ex.: 3,5,8)
        V     Ver mais registros desta tabela
        Q     Sair

 Ideal para remover os lancamentos criados durante os testes (fornecedor,
 tamanho, nota de entrada, contas a pagar/receber, vendedores, bairros, etc.)
 sem apagar o que voce quer manter.

 SEGURANCA:
   - Sempre faz BACKUP (JSON) das linhas antes de apagar.
   - Pede CONFIRMACAO antes de excluir (a menos que use --yes).
   - Use --dry-run para simular (nada e apagado).
   - NUNCA mexe em tabelas de sistema/configuracao por padrao.

 USO:
   python limpar_dados_teste.py
   python limpar_dados_teste.py --dry-run
   python limpar_dados_teste.py --host 127.0.0.1 --user root --password X --database farmacia
   python limpar_dados_teste.py --config-ini "C:\\Quantum\\config.ini"
   python limpar_dados_teste.py --tabelas fornecedores,tamanhos,notas_entrada
   python limpar_dados_teste.py --config-json "config.json"

 Requisitos: mysql-connector-python  (ou PyMySQL).
===============================================================================
"""

import os, sys, json, argparse, configparser, datetime


# Tabelas candidatas a conter dados de teste (cadastros e movimentos),
# com as colunas usadas para exibir/filtrar um "rotulo" legivel.
# A ordem tenta a 1a coluna que existir na tabela.
TABELAS = [
    ("fornecedores",   ["nome"]),
    ("clientes",       ["nome"]),
    ("produtos",       ["nome"]),
    ("categorias",     ["nome"]),
    ("tamanhos",       ["nome"]),
    ("tamanhos_produtos", ["nome", "tamanho"]),
    ("produto_tamanhos",  ["nome", "tamanho"]),
    ("vendedores",     ["nome"]),
    ("entregadores",   ["nome"]),
    ("bairros",        ["nome"]),
    ("cartoes",        ["nome"]),
    ("servicos",       ["nome"]),
    ("notas_entrada",  ["numero_nota", "numero", "fornecedor_nome"]),
    ("contas_pagar",   ["descricao"]),
    ("contas_receber", ["descricao"]),
    ("creditos_clientes", ["cliente_nome"]),
    ("devolucoes",     ["cliente_nome", "id"]),
    ("comandas",       ["numero", "cliente_nome"]),
    ("orcamentos",     ["numero", "cliente_nome"]),
    ("ordens_servico", ["numero", "cliente_nome"]),
    ("vendas",         ["coupon_number", "cliente_nome"]),
    ("vendas_itens",   ["produto_nome", "venda_id"]),
]

# Nunca oferecidas por padrao (config/sistema/licenca/usuarios).
PROTEGIDAS = {
    "configuracoes", "config", "empresa", "usuarios", "user_log", "schema_migrations",
    "sequencias", "quantum_backup_automatico_ftp", "quantum_envio_mysql_externo",
    "quantum_configuracoes_automaticas", "quantum_permissoes_revisoes_usuarios",
    "caixa", "caixas_pdv", "turnos", "vinculos_usuario_caixa_turno",
    "fechamentos_caixa", "sync_events",
}


# ══════════════════════════════════════════════════════════════════════════
# Conexao MySQL
# ══════════════════════════════════════════════════════════════════════════
def conectar(cfg):
    host = cfg["host"]; port = int(cfg.get("port", 3306)); user = cfg["user"]
    password = cfg.get("password", ""); database = cfg["database"]; erro = None
    try:
        import mysql.connector
        return mysql.connector.connect(host=host, port=port, user=user, password=password,
                database=database, charset="utf8mb4", autocommit=False, connection_timeout=30), "mysql.connector"
    except Exception as e:
        erro = e
    try:
        import pymysql
        return pymysql.connect(host=host, port=port, user=user, password=password, database=database,
                charset="utf8mb4", autocommit=False, connect_timeout=30,
                cursorclass=pymysql.cursors.DictCursor), "pymysql"
    except Exception as e:
        erro = e
    raise RuntimeError("Falha ao conectar no MySQL: %s\nInstale: pip install mysql-connector-python" % erro)


# ══════════════════════════════════════════════════════════════════════════
# Credenciais (mesma logica dos outros scripts)
# ══════════════════════════════════════════════════════════════════════════
def candidatos_ini():
    c = [r"C:\Quantum\config.ini", os.path.join(os.getcwd(), "config.ini"),
         os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")]
    vis = set(); out = []
    for x in c:
        xn = os.path.abspath(x)
        if xn not in vis and os.path.exists(xn):
            vis.add(xn); out.append(xn)
    return out

def ler_ini(p):
    cp = configparser.ConfigParser(); cp.read(p, encoding="utf-8")
    if not cp.has_section("mysql"):
        return None
    return {"host": cp.get("mysql", "host", fallback="127.0.0.1").strip() or "127.0.0.1",
            "port": cp.getint("mysql", "port", fallback=3306),
            "user": cp.get("mysql", "user", fallback="").strip(),
            "password": cp.get("mysql", "password", fallback=""),
            "database": cp.get("mysql", "database", fallback="").strip()}

def ler_json_externo(p):
    d = json.load(open(p, encoding="utf-8"))
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
                print(f"[i] Credenciais base de {args.config_json}.")
        except Exception as e:
            print(f"[!] Nao li {args.config_json}: {e}")
    for ini in ([args.config_ini] if args.config_ini else candidatos_ini()):
        if ini and os.path.exists(ini):
            try:
                d = ler_ini(ini)
                if d:
                    cfg.update({k: v for k, v in d.items() if v not in (None, "")})
                    print(f"[i] Credenciais de {ini}.")
                    break
            except Exception as e:
                print(f"[!] Falha ao ler {ini}: {e}")
    for k in ("host", "port", "user", "password", "database"):
        v = getattr(args, k, None)
        if v not in (None, ""):
            cfg[k] = v
    if [k for k in ("host", "user", "database") if not cfg.get(k)] and not args.yes:
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
# Limpeza interativa
# ══════════════════════════════════════════════════════════════════════════
def ask(msg):
    try:
        return input(msg).strip()
    except (EOFError, KeyboardInterrupt):
        return "Q"


def backup_rows(rows, tabela):
    if not rows:
        return None
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.abspath(f"backup_limpeza_{tabela}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2, default=str)
    return path


def main():
    ap = argparse.ArgumentParser(
        description="Limpeza interativa de dados de teste no MySQL do Quantum PDV.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host"); ap.add_argument("--port", type=int)
    ap.add_argument("--user"); ap.add_argument("--password"); ap.add_argument("--database")
    ap.add_argument("--config-ini"); ap.add_argument("--config-json")
    ap.add_argument("--tabelas", help="Lista de tabelas (separadas por virgula) para revisar. Padrao: todas as de cadastro.")
    ap.add_argument("--limite-preview", type=int, default=15, help="Quantos registros mostrar por vez (padrao 15).")
    ap.add_argument("--dry-run", action="store_true", help="Simula: nao apaga nada.")
    ap.add_argument("--yes", action="store_true", help="Nao pede confirmacao extra antes de cada exclusao.")
    args = ap.parse_args()

    print("+" + "=" * 68 + "+")
    print("|  LIMPEZA DE DADOS DE TESTE - Quantum / Farma Quantum PDV           |")
    print("+" + "=" * 68 + "+")
    if args.dry_run:
        print(">>> MODO SIMULACAO (--dry-run): nada sera apagado. <<<")

    cfg = resolver_credenciais(args)
    if not (cfg.get("host") and cfg.get("user") and cfg.get("database")):
        print("[X] Dados de conexao incompletos (host/usuario/banco).")
        sys.exit(1)

    print(f"\n[i] Conectando em {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']} ...")
    conn, driver = conectar(cfg)
    print(f"[OK] Conectado ({driver}).")
    dbname = cfg["database"]

    def q(sql, p=None):
        cur = conn.cursor(dictionary=True) if driver == "mysql.connector" else conn.cursor()
        cur.execute(sql, p or ()); r = cur.fetchall(); cur.close(); return r

    def ex(sql, p=None):
        cur = conn.cursor(); cur.execute(sql, p or ()); n = cur.rowcount; cur.close(); return n

    def tab_existe(t):
        return bool(q("SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s", (dbname, t)))

    def cols_de(t):
        rows = q("SELECT COLUMN_NAME c FROM information_schema.columns WHERE table_schema=%s AND table_name=%s", (dbname, t))
        return [(r["c"] if isinstance(r, dict) else r[0]) for r in rows]

    # define a lista de tabelas a revisar
    if args.tabelas:
        pedidas = [t.strip() for t in args.tabelas.split(",") if t.strip()]
        lista = [(t, next((lbl for tt, lbl in TABELAS if tt == t), ["nome"])) for t in pedidas]
    else:
        lista = TABELAS

    total_apagado = 0
    backups = []
    encerrar = False

    try:
        for tabela, label_cands in lista:
            if encerrar:
                break
            if tabela in PROTEGIDAS and not args.tabelas:
                continue
            if not tab_existe(tabela):
                continue

            colunas = set(cols_de(tabela))
            if "id" not in {c.lower() for c in colunas}:
                # sem PK id nao conseguimos excluir com seguranca por id
                continue
            label = next((c for c in label_cands if c in colunas), None)

            total = q(f"SELECT COUNT(*) n FROM `{tabela}`")[0]
            total = total["n"] if isinstance(total, dict) else total[0]

            print("\n" + "─" * 70)
            print(f" TABELA: {tabela}   ({total} registro(s))")
            print("─" * 70)
            if total == 0:
                print("   (vazia — nada a limpar)")
                continue

            def mostrar(offset=0):
                sel = f"id" + (f", `{label}`" if label else "")
                rows = q(f"SELECT {sel} FROM `{tabela}` ORDER BY id LIMIT %s OFFSET %s",
                         (args.limite_preview, offset))
                for r in rows:
                    rid = r["id"] if isinstance(r, dict) else r[0]
                    rlab = ""
                    if label:
                        rlab = (r[label] if isinstance(r, dict) else r[1])
                    print(f"    id={rid:<6} {label + '=' if label else ''}{rlab}")
                return len(rows)

            offset = 0
            mostrado = mostrar(offset)
            if mostrado < total:
                print(f"    ... ({total - mostrado} a mais — use 'V' para ver mais)")

            # loop de acao para esta tabela
            while True:
                op = ask("\n  Acao [Enter=pular | T=todos | F=filtro | I=ids | V=ver mais | Q=sair]: ").upper()

                if op in ("", "P"):
                    print("   -> Pulado.")
                    break
                if op == "Q":
                    encerrar = True
                    break
                if op == "V":
                    offset += mostrado
                    if offset >= total:
                        print("   (fim da lista)")
                        offset = 0
                    mostrado = mostrar(offset)
                    continue

                where = None; params = ()
                descricao_acao = ""
                if op == "T":
                    where = "1=1"; params = ()
                    descricao_acao = f"TODOS os {total} registros de {tabela}"
                elif op == "F":
                    if not label:
                        print("   [!] Esta tabela nao tem coluna de texto para filtrar. Use I (ids).")
                        continue
                    termo = ask(f"   Termo a procurar em '{label}' (ex.: teste): ")
                    if not termo:
                        print("   (cancelado)")
                        continue
                    where = f"`{label}` LIKE %s"; params = (f"%{termo}%",)
                    descricao_acao = f"registros de {tabela} onde {label} contem '{termo}'"
                elif op == "I":
                    ids_txt = ask("   IDs a excluir (separados por virgula, ex.: 3,5,8): ")
                    ids = [x.strip() for x in ids_txt.split(",") if x.strip().isdigit()]
                    if not ids:
                        print("   (nenhum id valido)")
                        continue
                    place = ",".join(["%s"] * len(ids))
                    where = f"id IN ({place})"; params = tuple(ids)
                    descricao_acao = f"registros de {tabela} com id em ({', '.join(ids)})"
                else:
                    print("   (opcao invalida)")
                    continue

                # pre-visualiza quantos serao afetados + backup
                afetadas = q(f"SELECT * FROM `{tabela}` WHERE {where}", params)
                n = len(afetadas)
                if n == 0:
                    print("   (nenhum registro corresponde — nada feito)")
                    continue
                print(f"   -> {n} registro(s) serao excluidos: {descricao_acao}")

                if args.dry_run:
                    print("   [DRY-RUN] Simulacao: nada foi apagado.")
                    continue

                if not args.yes:
                    conf = ask(f"   Confirmar exclusao de {n} registro(s)? (s/N): ").lower()
                    if conf not in ("s", "sim", "y", "yes"):
                        print("   (cancelado)")
                        continue

                bkp = backup_rows(afetadas, tabela)
                if bkp:
                    print(f"   [backup] {bkp}")
                    backups.append(bkp)
                apagadas = ex(f"DELETE FROM `{tabela}` WHERE {where}", params)
                conn.commit()
                total_apagado += apagadas
                print(f"   [OK] {apagadas} registro(s) excluido(s) de {tabela}.")

                # atualiza total e continua oferecendo acoes na mesma tabela
                total = q(f"SELECT COUNT(*) n FROM `{tabela}`")[0]
                total = total["n"] if isinstance(total, dict) else total[0]
                print(f"   (restam {total} em {tabela})")
                if total == 0:
                    break
    finally:
        try:
            conn.close()
        except Exception:
            pass

    print("\n" + "=" * 70)
    print(" RESUMO DA LIMPEZA" + (" (SIMULACAO)" if args.dry_run else ""))
    print("=" * 70)
    print(f"  Registros excluidos: {total_apagado}")
    if backups:
        print(f"  Backups gerados ({len(backups)}):")
        for b in backups:
            print(f"      {b}")
    print("  Dica: os arquivos backup_limpeza_*.json permitem reimportar se precisar.")
    print("=" * 70)


if __name__ == "__main__":
    main()
