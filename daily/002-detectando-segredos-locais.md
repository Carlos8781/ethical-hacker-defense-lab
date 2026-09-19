# Dia 002 — Detectando segredos acidentalmente versionados

Segredos colocados em código ou arquivos de configuração podem ser copiados por backups, logs e repositórios. Uma verificação preventiva local ajuda a encontrar padrões suspeitos antes do commit, mas não prova que um arquivo está seguro nem substitui um gerenciador de segredos, revisão humana e rotação imediata de credenciais expostas.

## Uso autorizado e limitações éticas

Execute o exemplo somente em uma cópia local de um projeto que você administra ou para o qual tem autorização explícita. O script não faz varredura de rede, não consulta serviços externos, não tenta validar credenciais e não lê fora da pasta indicada. Os resultados são apenas sinais: podem existir falsos positivos e falsos negativos, e o conteúdo encontrado não deve ser colado em issues, logs ou mensagens. Se um segredo real for encontrado, não o publique; remova-o do código, revogue-o ou faça sua rotação pelo procedimento oficial e verifique o histórico conforme a política da organização.

## Exemplo seguro em Python

O detector abaixo examina somente arquivos de texto pequenos dentro da pasta local informada. Ele ignora `.git` e diretórios comuns de dependências, exibe apenas caminho, linha e tipo do padrão, e usa exemplos de padrões — não valores secretos — para apoiar uma revisão manual.

```python
#!/usr/bin/env python3
"""Detectar padrões suspeitos em arquivos de um projeto local autorizado."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERNS = {
    "chave AWS": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "token GitHub": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "chave privada": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "atributo sensível": re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|token)\b"
        r"\s*[:=]\s*['\"]([^'\"]+)['\"]"
    ),
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}
MAX_BYTES = 1_000_000


def scan(root: Path) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.stat().st_size > MAX_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append((str(path.relative_to(root)), line_number, label))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="pasta local sob sua administração")
    args = parser.parse_args()
    root = args.path.resolve()
    if not root.is_dir():
        parser.error(f"não é uma pasta: {root}")

    findings = scan(root)
    for filename, line_number, label in findings:
        print(f"{filename}:{line_number}: padrão suspeito ({label})")
    print(f"verificados arquivos de texto locais; achados: {len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Salve o exemplo como `detect-secrets.py` fora do repositório ou adapte-o a uma ferramenta aprovada pela sua equipe. Uma execução local seria:

```bash
python3 detect-secrets.py ./projeto-local
```

O código retorna `0` quando não encontra padrões e `1` quando pede revisão. Ele não apaga, altera ou envia arquivos.

## Checklist

- [ ] O escaneamento foi executado somente em um projeto local autorizado.
- [ ] `.git`, dependências e arquivos binários foram tratados conforme a política local.
- [ ] Cada achado foi revisado sem copiar o possível segredo para logs ou tickets.
- [ ] Qualquer credencial real foi revogada ou rotacionada antes de ser removida do código.
- [ ] O valor foi substituído por configuração segura ou cofre de segredos, sem hardcoding.
- [ ] O repositório, backups e histórico foram revisados conforme o procedimento aprovado.
- [ ] O detector foi combinado com revisão humana e testes para reduzir falsos positivos e negativos.
