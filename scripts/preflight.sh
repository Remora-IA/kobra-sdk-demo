#!/usr/bin/env bash
# Wrapper para compatibilidad con `make sync` y workflows existentes.
# La fuente de verdad vive en protocolo/scripts/preflight.sh
exec bash "$(git rev-parse --show-toplevel)/protocolo/scripts/preflight.sh" "$@"
