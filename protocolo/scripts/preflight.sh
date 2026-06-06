#!/usr/bin/env bash
# protocolo/scripts/preflight.sh — Pre-flight check para kobra-sdk-demo.
#
# Qué hace:
#   1. Auto-activa hooks si no están configurados.
#   2. Fetch origin.
#   3. Verifica que main local esté alineada con origin/main.
#   4. Alerta si el working tree está sucio.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_ROOT" ]]; then
    echo "ERROR: no estás dentro de un repo git." >&2
    exit 1
fi
cd "$REPO_ROOT"

if [[ -t 1 ]]; then
    C_OK="\033[32m"; C_WARN="\033[33m"; C_ERR="\033[31m"; C_INFO="\033[36m"; C_END="\033[0m"
else
    C_OK=""; C_WARN=""; C_ERR=""; C_INFO=""; C_END=""
fi

ok()    { echo -e "${C_OK}✓${C_END} $*"; }
info()  { echo -e "${C_INFO}·${C_END} $*"; }
warn()  { echo -e "${C_WARN}⚠${C_END} $*"; ALERTAS=$((ALERTAS + 1)); }
action(){ echo -e "${C_OK}→${C_END} $*"; }

ALERTAS=0

echo "=== Pre-flight — kobra-sdk-demo ==="
echo

# 1. Auto-activar hooks
HOOKS_PATH=$(git config --get core.hooksPath 2>/dev/null || echo "")
if [[ -d protocolo/hooks && "$HOOKS_PATH" != "protocolo/hooks" ]]; then
    git config core.hooksPath protocolo/hooks
    action "Hooks activados (protocolo/hooks/)."
elif [[ -n "$HOOKS_PATH" ]]; then
    ok "Hooks activos: $HOOKS_PATH"
fi

# 2. Working tree
if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
    warn "Working tree sucio — commiteá o stasheá antes de seguir:"
    git status --short | sed 's/^/    /'
    echo
else
    ok "Working tree limpio."
fi

# 3. Fetch + verificar main (solo si hay remote configurado)
HAS_ORIGIN=0; git remote | grep -q "^origin$" 2>/dev/null && HAS_ORIGIN=1 || true
if [[ "$HAS_ORIGIN" -gt 0 ]]; then
    info "Fetching origin..."
    git fetch origin --prune 2>&1 | grep -v "^$" | sed 's/^/    /' || true
    echo

    LOCAL_SHA=$(git rev-parse main 2>/dev/null || echo "")
    ORIGIN_SHA=$(git rev-parse origin/main 2>/dev/null || echo "")

    if [[ -z "$LOCAL_SHA" || -z "$ORIGIN_SHA" ]]; then
        warn "No se pudo verificar main vs origin/main."
    elif [[ "$LOCAL_SHA" == "$ORIGIN_SHA" ]]; then
        ok "main alineada con origin/main ($(git rev-parse --short main))."
    else
        AHEAD=$(git rev-list --count "origin/main..main" 2>/dev/null || echo "0")
        BEHIND=$(git rev-list --count "main..origin/main" 2>/dev/null || echo "0")
        if [[ "$BEHIND" -gt 0 && "$AHEAD" -eq 0 ]]; then
            action "main behind $BEHIND — pull --ff-only..."
            git pull --ff-only origin main >/dev/null && ok "main actualizada."
        else
            warn "main diverged (ahead $AHEAD, behind $BEHIND) — resolver antes de continuar."
        fi
    fi
else
    ok "Sin remote origin — repo local, sin sincronización."
fi

echo
echo "=== Resumen ==="
if [[ "$ALERTAS" -eq 0 ]]; then
    ok "Repo listo."
else
    echo -e "${C_ERR}✗${C_END} $ALERTAS atención(es) pendiente(s)."
    exit 1
fi
