#!/bin/bash
# uso: bash scripts/sync_repo.sh "mensagem do commit"
set -e
R=/home/claude/projeto-pmsp
rm -rf $R/site $R/scripts; cp -a /home/claude/site $R/site
cp -a /home/claude/scripts $R/scripts; rm -rf $R/scripts/__pycache__ $R/scripts/srv.py
cd $R
[ -d .git ] || git init -q -b main
git add -A
if git diff --cached --quiet; then echo "sem mudanças"; exit 0; fi
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "$1

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H7oynzvDZS63FWqAaV8AGe"
if git remote | grep -q origin; then git push -q origin main && echo enviado; else echo "commit local feito (sem remote ainda)"; fi
