#!/usr/bin/env bash
#
# liberar_portas_anydesk.sh
# ------------------------------------------------------------
# Libera no firewall do Ubuntu as portas usadas pelo AnyDesk.
# Compatível com UFW (padrão do Ubuntu) e iptables como fallback.
#
# Uso:
#   sudo ./liberar_portas_anydesk.sh
#
# Autor: gerado para uso em servidores/estações Ubuntu
# ------------------------------------------------------------

set -euo pipefail

# ---- Cores para saída ----
VERDE="\033[0;32m"
AMARELO="\033[1;33m"
VERMELHO="\033[0;31m"
SEM_COR="\033[0m"

info()    { echo -e "${VERDE}[INFO]${SEM_COR} $*"; }
aviso()   { echo -e "${AMARELO}[AVISO]${SEM_COR} $*"; }
erro()    { echo -e "${VERMELHO}[ERRO]${SEM_COR} $*" >&2; }

# ---- Portas do AnyDesk ----
# TCP: conexao direta / relay / fallback web
PORTAS_TCP=(7070 6568 80 443)
# UDP: descoberta na rede local (LAN)
PORTAS_UDP=(50001 50002 50003)

# ------------------------------------------------------------
# 1. Verifica se esta rodando como root
# ------------------------------------------------------------
if [[ "${EUID}" -ne 0 ]]; then
    erro "Este script precisa ser executado como root."
    erro "Execute:  sudo $0"
    exit 1
fi

# ------------------------------------------------------------
# 2. Detecta o firewall disponivel
# ------------------------------------------------------------
usar_ufw=false
usar_iptables=false

if command -v ufw >/dev/null 2>&1; then
    usar_ufw=true
    info "UFW detectado. Sera usado como firewall principal."
elif command -v iptables >/dev/null 2>&1; then
    usar_iptables=true
    aviso "UFW nao encontrado. Usando iptables diretamente."
else
    erro "Nem UFW nem iptables foram encontrados no sistema."
    erro "Instale o UFW com:  sudo apt install ufw"
    exit 1
fi

# ------------------------------------------------------------
# 3. Libera portas com UFW
# ------------------------------------------------------------
liberar_com_ufw() {
    # Garante que o UFW esteja habilitado
    if ! ufw status | grep -q "Status: active"; then
        aviso "UFW esta inativo. Habilitando..."
        # --force evita o prompt interativo (pode derrubar conexao SSH!)
        ufw --force enable
    fi

    info "Liberando portas TCP..."
    for porta in "${PORTAS_TCP[@]}"; do
        ufw allow "${porta}/tcp" comment "AnyDesk" >/dev/null
        info "  -> TCP ${porta} liberada"
    done

    info "Liberando portas UDP (descoberta LAN)..."
    for porta in "${PORTAS_UDP[@]}"; do
        ufw allow "${porta}/udp" comment "AnyDesk LAN" >/dev/null
        info "  -> UDP ${porta} liberada"
    done

    # Recarrega para aplicar
    ufw reload >/dev/null
    info "Regras aplicadas e UFW recarregado."
    echo
    info "Status atual do UFW:"
    ufw status verbose | grep -Ei "anydesk|7070|6568|443|80|5000" || ufw status
}

# ------------------------------------------------------------
# 4. Libera portas com iptables (fallback)
# ------------------------------------------------------------
liberar_com_iptables() {
    info "Liberando portas TCP via iptables..."
    for porta in "${PORTAS_TCP[@]}"; do
        # Evita duplicar a regra
        if ! iptables -C INPUT -p tcp --dport "${porta}" -j ACCEPT 2>/dev/null; then
            iptables -A INPUT -p tcp --dport "${porta}" -j ACCEPT
        fi
        info "  -> TCP ${porta} liberada"
    done

    info "Liberando portas UDP via iptables..."
    for porta in "${PORTAS_UDP[@]}"; do
        if ! iptables -C INPUT -p udp --dport "${porta}" -j ACCEPT 2>/dev/null; then
            iptables -A INPUT -p udp --dport "${porta}" -j ACCEPT
        fi
        info "  -> UDP ${porta} liberada"
    done

    # Tenta persistir as regras
    if command -v netfilter-persistent >/dev/null 2>&1; then
        netfilter-persistent save >/dev/null 2>&1 || true
        info "Regras salvas com netfilter-persistent."
    elif command -v iptables-save >/dev/null 2>&1; then
        mkdir -p /etc/iptables
        iptables-save > /etc/iptables/rules.v4
        info "Regras salvas em /etc/iptables/rules.v4"
    else
        aviso "Nao foi possivel persistir as regras automaticamente."
        aviso "As regras serao perdidas ao reiniciar. Instale: sudo apt install iptables-persistent"
    fi
}

# ------------------------------------------------------------
# 5. Execucao
# ------------------------------------------------------------
info "Iniciando liberacao das portas do AnyDesk..."
echo

if [[ "${usar_ufw}" == true ]]; then
    liberar_com_ufw
elif [[ "${usar_iptables}" == true ]]; then
    liberar_com_iptables
fi

echo
info "Concluido! As portas do AnyDesk foram liberadas."
aviso "Se o AnyDesk ainda nao conectar, verifique tambem o firewall do roteador/rede."
