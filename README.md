# Ethical Hacker Defense Lab

Projeto educacional de **hacking ético defensivo**: um novo guia prático por dia para ajudar pessoas e pequenas equipes a proteger seus sistemas usando Python, Node.js e ferramentas abertas.

## Princípios de segurança

- Use os exemplos apenas em sistemas, arquivos, domínios e redes que você possui ou para os quais tem autorização explícita.
- O projeto não ensina invasão, roubo de credenciais, evasão de controles, exploração de terceiros ou acesso não autorizado.
- Faça backup antes de testar scripts que alterem arquivos.
- Revise cada exemplo em ambiente de testes e adapte-o à sua política de segurança.

## Conteúdo

- `daily/`: um guia prático por dia, com explicação, checklist e código defensivo.
- `python/`: utilitários locais de auditoria e integridade.
- `node/`: exemplos de verificação de dependências e boas práticas.
- `CONTRIBUTING.md`: como sugerir melhorias com responsabilidade.

## Primeiros exemplos

```bash
python3 python/file_integrity.py --help
node node/dependency-audit.js --help
```

Os scripts são deliberadamente limitados a verificações locais e a alvos autorizados.

## Guias diários

- [Dia 001 — Integridade de arquivos](daily/001-integridade-de-arquivos.md)
- [Dia 002 — Detecção local de segredos](daily/002-detectando-segredos-locais.md)
- [Dia 003 — Auditoria local de dependências](daily/003-auditoria-dependencias-locais.md)
- [Dia 004 — Cabeçalhos de segurança locais](daily/004-cabecalhos-seguranca-local.md)
- [Dia 005 — Integridade de backups locais](daily/005-verificacao-integridade-backup-local.md)
- [Dia 006 — Auditoria de permissões locais](daily/006-auditoria-permissoes-locais.md)
- [Dia 007 — Triagem de logs locais](daily/007-triagem-logs-locais.md)
- [Dia 008 — Baseline de configuração local](daily/008-verificacao-baseline-config-local.md)
- [Dia 009 — Revisão da cobertura de MFA](daily/009-revisao-cobertura-mfa-local.md)
- [Dia 010 — Revisão local do ciclo de atualizações](daily/010-revisao-local-ciclo-atualizacoes.md)
- [Dia 011 — Exercício de mesa para resposta a incidentes](daily/011-exercicio-mesa-resposta-incidentes.md)
- [Dia 012 — Minimização de dados em logs locais](daily/012-minimizacao-dados-logs-locais.md)
- [Dia 013 — Revisão local de testes de restauração de backups](daily/013-revisao-local-testes-restauracao.md)
- [Dia 014 — Revisão local de acessos privilegiados](daily/014-revisao-acessos-privilegiados-local.md)
- [Dia 015 — Verificação local da integridade de exportações de logs](daily/015-verificacao-integridade-logs-locais.md)
- [Dia 016 — Revisão de baseline de hardening SSH local](daily/016-revisao-baseline-ssh-local.md)

## Licença

MIT. Consulte também os avisos de uso autorizado em cada guia.
