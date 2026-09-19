# Dia 001 — Detectando alterações inesperadas em arquivos

Um inventário de hashes SHA-256 ajuda a perceber mudanças inesperadas em arquivos importantes. Ele não substitui backups, controle de acesso, logs ou uma investigação completa; é um sinal de detecção.

## Uso autorizado

Execute somente em uma pasta local que você administra. Não use este guia para acessar ou monitorar arquivos de terceiros.

## Exemplo

```bash
python3 python/file_integrity.py --path ./pasta-importante --write-baseline ./baseline.json
python3 python/file_integrity.py --path ./pasta-importante --check-baseline ./baseline.json
```

## Checklist

- [ ] A baseline foi criada a partir de uma fonte confiável.
- [ ] O arquivo de baseline tem permissões restritas.
- [ ] A baseline está armazenada separadamente dos arquivos monitorados.
- [ ] Alterações esperadas foram documentadas.
- [ ] Alterações inesperadas geraram investigação e backup antes de qualquer correção.
