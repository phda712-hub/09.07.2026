# PsiphonLinux - Guia de Uso

Instalador automático **single-file** do Psiphon VPN para **Linux** e **Raspberry Pi**.
Um único arquivo executável que já contém os binários embutidos (x86_64, arm64 e arm),
detecta sua arquitetura e faz tudo automaticamente.

---

## Compatibilidade

| Plataforma | Instala com este script? |
|---|---|
| **Linux (PC/servidor) x86_64** | ✅ Sim |
| **Raspberry Pi** (Zero/1/2/3/4/5) | ✅ Sim (arm64 ou arm 32-bit) |
| **Android (celular)** | ❌ Não (use o app oficial *Psiphon Pro* na Play Store) |

> O script detecta a arquitetura automaticamente (`uname -m`) e instala o binário correto:
> **x86_64/amd64** (PCs e servidores), **arm64/aarch64** (Raspberry Pi 64-bit) ou
> **arm 32-bit** (Raspberry Pi Zero/1/2 ou sistema 32-bit).

---

## 1. Baixar o instalador

No terminal do Linux ou Raspberry Pi:

```bash
wget https://github.com/phda712-hub/09.07.2026/raw/add-psiphon-installer/psiphon-linux-setup.sh
chmod +x psiphon-linux-setup.sh
```

---

## 2. Instalar

Escolha **uma** das opções:

**Opção A — Instalar e rodar como serviço (recomendado)** — inicia sozinho junto com o sistema:

```bash
sudo ./psiphon-linux-setup.sh --service
```

**Opção B — Só instalar** (você inicia manualmente quando quiser):

```bash
sudo ./psiphon-linux-setup.sh
```

---

## 3. Iniciar / Parar

```bash
sudo psiphon                          # inicia (fica na tela; Ctrl+C para sair)
sudo ./psiphon-linux-setup.sh stop    # para o Psiphon (serviço ou manual)
sudo ./psiphon-linux-setup.sh enable  # ativa o serviço (inicia com o sistema)
sudo ./psiphon-linux-setup.sh disable # desativa o serviço
```

---

## 4. Usar a conexão (passo mais importante)

O Psiphon **não** redireciona todo o tráfego automaticamente — ele cria **proxies locais**
que você precisa apontar no navegador ou nos aplicativos:

| Tipo | Endereço | Porta |
|---|---|---|
| HTTP/HTTPS | `127.0.0.1` | **8081** |
| SOCKS 4/5 | `127.0.0.1` | **1081** |

**Exemplo no Firefox:**
Configurações → Rede → *Configurar conexão* → **Configuração manual de proxy** →
Proxy HTTP `127.0.0.1` porta `8081` (marque *"usar este proxy também para HTTPS"*).

> ⏳ A **primeira conexão demora um pouco** (o Psiphon testa vários servidores).
> Aguarde a mensagem de que conectou.

---

## 5. Verificar e desinstalar

```bash
sudo ./psiphon-linux-setup.sh status          # verifica se está instalado/ativo
sudo ./psiphon-linux-setup.sh service-status  # status detalhado do serviço
sudo ./psiphon-linux-setup.sh uninstall       # para tudo e remove completamente
```

---

## Todos os comandos

```
install          instala (detecta a arquitetura)
--start          instala e inicia agora
--service        instala + serviço systemd
run              apenas inicia (foreground)
stop             para o serviço/processo
enable           ativa o serviço systemd
disable          desativa o serviço systemd
service-status   status do serviço
status           verifica a instalação
uninstall        para tudo e remove
help             mostra a ajuda
```

Ajuda a qualquer momento:

```bash
./psiphon-linux-setup.sh help
```

---

## Fluxo mais simples (copiar e colar)

```bash
wget https://github.com/phda712-hub/09.07.2026/raw/add-psiphon-installer/psiphon-linux-setup.sh
chmod +x psiphon-linux-setup.sh
sudo ./psiphon-linux-setup.sh --service
```

Depois é só configurar o proxy `127.0.0.1:8081` no navegador.

---

## Detalhes técnicos

- **Arquivo único (~29 MB):** contém os 3 binários comprimidos (`tar.gz` embutido em base64);
  na instalação, apenas o binário da arquitetura detectada é extraído.
- **Verificação de integridade:** o SHA256 do binário extraído é conferido automaticamente.
- **Serviço systemd:** unidade em `/etc/systemd/system/psiphon.service`, com
  `Restart=on-failure` e início após a rede (`network-online.target`).
- **Arquivos instalados:**
  - `/etc/psiphon/psiphon-tunnel-core-<arch>` — binário
  - `/etc/psiphon/psiphon.config` — configuração (portas dos proxies, região de saída, etc.)
  - `/usr/bin/psiphon` — comando de atalho para iniciar
- **Binários ARM:** compilados a partir do código-fonte oficial
  (`Psiphon-Labs/psiphon-tunnel-core`) com Go.

### Ver logs do serviço

```bash
sudo journalctl -u psiphon -f
```

### Mudar a região de saída

Edite `/etc/psiphon/psiphon.config` e altere o campo `"EgressRegion"`
(ex.: `"US"`, `"GB"`, `"DE"`, `"JP"`; deixe `""` para automático). Depois reinicie:

```bash
sudo ./psiphon-linux-setup.sh stop
sudo psiphon    # ou: sudo systemctl restart psiphon
```

---

*Baseado em [SpherionOS/PsiphonLinux](https://github.com/SpherionOS/PsiphonLinux) + build oficial do [Psiphon-Labs](https://github.com/Psiphon-Labs/psiphon-tunnel-core).*
