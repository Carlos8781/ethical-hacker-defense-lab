# Dia 027 — Validação local de restauração de backup

Um backup só é útil se puder ser restaurado corretamente. Uma validação simples e segura consiste em comparar, em um laboratório local, uma pasta de referência com uma cópia restaurada: os caminhos relativos e os hashes SHA-256 devem coincidir. Essa checagem detecta arquivos ausentes, extras ou alterados sem modificar nenhuma das pastas.

## Limites éticos e operacionais

- Execute apenas em diretórios locais que você possui ou administra e para os quais tem autorização.
- Use uma cópia de teste e dados fictícios ou não sensíveis; não exponha conteúdo de backup em logs ou relatórios públicos.
- O exemplo apenas lê arquivos regulares e calcula hashes. Não restaura, altera ou exclui arquivos, não acessa a rede e não tenta contornar permissões.
- Uma comparação bem-sucedida não prova que o backup está completo, recente, protegido contra adulteração ou que uma aplicação conseguirá iniciar. Faça periodicamente um exercício de restauração isolado e siga a política de retenção e acesso da organização.

## Exemplo seguro em Python

Salve como `compare_restore.py`. O programa compara dois diretórios explicitamente fornecidos; a pasta de origem e a pasta restaurada devem ser distintas. Ele informa somente os caminhos relativos diferentes, sem imprimir conteúdo.

```python
#!/usr/bin/env python3
"""Compara localmente uma pasta de teste e sua restauração, sem alterá-las."""
import argparse
import hashlib
from pathlib import Path


def inventory(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"links simbólicos não são aceitos: {path.relative_to(root)}")
        if path.is_file():
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            result[path.relative_to(root).as_posix()] = digest.hexdigest()
        elif not path.is_dir():
            raise ValueError(f"tipo de arquivo não suportado: {path.relative_to(root)}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="diretório local de referência")
    parser.add_argument("restored", type=Path, help="cópia restaurada local")
    args = parser.parse_args()

    reference = args.reference.resolve(strict=True)
    restored = args.restored.resolve(strict=True)
    if not reference.is_dir() or not restored.is_dir():
        parser.error("ambos os caminhos devem ser diretórios existentes")
    if reference == restored or reference in restored.parents or restored in reference.parents:
        parser.error("os diretórios devem ser distintos e não podem conter um ao outro")

    try:
        expected, actual = inventory(reference), inventory(restored)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    changed = sorted(name for name in expected.keys() & actual.keys()
                     if expected[name] != actual[name])
    if not (missing or extra or changed):
        print(f"OK: {len(expected)} arquivo(s) conferem; conteúdo não exibido.")
        return 0

    print("Divergências encontradas (caminhos relativos apenas):")
    for label, paths in (("ausente", missing), ("extra", extra), ("alterado", changed)):
        for name in paths:
            print(f"  {label}: {name}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste em uma área temporária criada por você, com arquivos fictícios:

```bash
mkdir -p /tmp/backup-lab/original /tmp/backup-lab/restaurado
printf 'amostra ficticia\n' > /tmp/backup-lab/original/nota.txt
cp /tmp/backup-lab/original/nota.txt /tmp/backup-lab/restaurado/nota.txt
python3 compare_restore.py /tmp/backup-lab/original /tmp/backup-lab/restaurado
```

A saída esperada é `OK: 1 arquivo(s) conferem; conteúdo não exibido.` Faça também um teste negativo em outra cópia de laboratório: altere ou remova um arquivo apenas dentro da pasta restaurada de teste e confirme que o programa retorna código 1 e identifica a divergência. Não use dados reais para esse teste.

## Checklist

- [ ] Confirmei a autorização e escolhi duas pastas locais de teste distintas.
- [ ] Usei dados fictícios/não sensíveis e preservei o backup original.
- [ ] Executei a comparação positiva e a negativa em uma cópia de laboratório.
- [ ] Registrei o resultado sem divulgar conteúdo nem caminhos sensíveis.
- [ ] Se houve divergência, investiguei o processo de backup/restauração antes de confiar nele.
- [ ] Mantive acesso restrito aos backups e agendei testes de restauração conforme a política interna.
