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

## Temas planejados

1. Integridade de arquivos com SHA-256.
2. Auditoria segura de dependências Node.js.
3. Senhas: armazenamento correto e prevenção de segredos no código.
4. Cabeçalhos de segurança em aplicações web próprias.
5. Backups, logs e resposta a incidentes.
6. Princípio do menor privilégio.
7. Detecção de segredos acidentalmente versionados.

## Licença

MIT. Consulte também os avisos de uso autorizado em cada guia.
