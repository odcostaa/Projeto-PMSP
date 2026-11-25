# Projeto PMSP

App de estudos com questões anteriores das provas de Soldado PM (PMESP/PMSP, banca VUNESP): filtros por disciplina, ano e prova, tesoura (eliminar alternativa), correção pelo gabarito, painel de desempenho, anotações e explicação por IA (Gemini).

## Estrutura
- `site/` — o app publicado (HTML único, `questoes.json` e `img/`). É a pasta que o Netlify serve (`netlify.toml`).
- `scripts/` — pipeline que extrai as questões dos PDFs (pdfplumber, tesseract) e gera `site/`.

## Hospedar no Netlify
1. Netlify → *Add new site* → *Import from Git* → escolha este repositório.
2. Build command: vazio. Publish directory: `site` (já definido em `netlify.toml`).
3. Cada `git push` na branch `main` publica a nova versão.

## Como os dados são salvos
Fora do Claude, respostas, tesouras, anotações e histórico do chat ficam no `localStorage` do navegador (por aparelho). A chave do Gemini está em `site/index.html` (constante `G.key`): troque por uma chave sua (`AIza…`, aistudio.google.com/apikey) e mantenha o repositório privado.

## Atualizar o banco de questões
`bash scripts/run_all.sh` (precisa dos PDFs em `provas_zip/`, que não vão para o git).
