# Dia 005 — Verificação da integridade de um backup local

Um backup só é útil se puder ser lido e se os arquivos mantiverem o conteúdo esperado. Uma prática defensiva simples é gerar um manifesto SHA-256 de uma cópia de laboratório e compará-lo posteriormente, antes de depender dela em uma recuperação. A verificação detecta alterações acidentais ou corrupção; ela não prova que o backup contém todos os dados necessários nem substitui testes de restauração.

## Uso autorizado e limitações éticas

Use este exemplo somente com diretórios que você administra e com dados fictícios, sintéticos ou previamente aprovados para o laboratório. O script trabalha apenas em caminhos locais informados pelo operador, não faz descoberta de rede, não acessa sistemas de terceiros, não coleta credenciais e não tenta contornar permissões. Não inclua no manifesto conteúdo sensível, tokens, chaves privadas, cookies, dados pessoais ou caminhos que revelem informações internas. O SHA-256 confirma igualdade do conteúdo observado, mas não oferece confidencialidade, não substitui criptografia, não garante a origem do backup e não detecta um manifesto que tenha sido alterado junto com os arquivos; mantenha uma cópia do manifesto em armazenamento com controle de acesso e retenção apropriados.

## Exemplo seguro em Python

O programa abaixo oferece dois comandos locais: `create` cria um manifesto JSON para um diretório de laboratório e `verify` compara os arquivos atuais com esse manifesto. Links simbólicos são ignorados para evitar seguir caminhos inesperados; diretórios e arquivos ocultos continuam sujeitos à política do laboratório e devem ser avaliados antes do uso. O manifesto é escrito somente no caminho de saída escolhido pelo operador.

```python
#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def files_in(root: Path):
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    )


def create_manifest(root: Path, manifest: Path) -> int:
    root = root.resolve()
    entries = [
        {"path": str(path.relative_to(root)), "sha256": sha256(path)}
        for path in files_in(root)
        if path.resolve() != manifest.resolve()
    ]
    manifest.write_text(
        json.dumps({"algorithm": "sha256", "files": entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Manifesto criado: {manifest} ({len(entries)} arquivo(s))")
    return 0


def verify_manifest(root: Path, manifest: Path) -> int:
    root = root.resolve()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("algorithm") != "sha256" or not isinstance(data.get("files"), list):
        print("Manifesto inválido: formato ou algoritmo inesperado", file=sys.stderr)
        return 2

    expected = {entry["path"]: entry["sha256"] for entry in data["files"]}
    actual = {
        str(path.relative_to(root)): sha256(path)
        for path in files_in(root)
        if path.resolve() != manifest.resolve()
    }
    missing = sorted(set(expected) - set(actual))
    added = sorted(set(actual) - set(expected))
    changed = sorted(
        path for path in set(expected) & set(actual)
        if expected[path] != actual[path]
    )
    if missing or added or changed:
        print("Falha de integridade")
        for label, paths in (("ausentes", missing), ("novos", added), ("alterados", changed)):
            for path in paths:
                print(f"- {label}: {path}")
        return 1
    print(f"Integridade confirmada: {len(actual)} arquivo(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manifesto SHA-256 para backup local autorizado")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("create", "verify"):
        sub = subparsers.add_parser(name)
        sub.add_argument("root", type=Path, help="diretório local do laboratório")
        sub.add_argument("manifest", type=Path, help="arquivo JSON local do manifesto")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"diretório inexistente: {args.root}")
    return create_manifest(args.root, args.manifest) if args.command == "create" else verify_manifest(args.root, args.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
```

Salve o trecho como `backup_integrity.py` fora do repositório ou em um diretório de testes descartável. Execute apenas contra uma árvore sintética:

```bash
mkdir -p /tmp/backup-lab
printf 'relatorio ficticio\n' > /tmp/backup-lab/relatorio.txt
python3 backup_integrity.py create /tmp/backup-lab /tmp/backup-manifest.json
python3 backup_integrity.py verify /tmp/backup-lab /tmp/backup-manifest.json
```

A segunda execução deve informar `Integridade confirmada`. Para testar a detecção sem usar dados reais, altere o arquivo fictício e espere código de saída 1:

```bash
printf 'alteracao de teste\n' > /tmp/backup-lab/relatorio.txt
python3 backup_integrity.py verify /tmp/backup-lab /tmp/backup-manifest.json
```

Em produção, prefira uma ferramenta de backup com criptografia, retenção, controle de acesso, versionamento e logs centralizados. Faça restaurações periódicas em ambiente isolado, registre quem autorizou o teste, meça o RPO/RTO e mantenha um procedimento de reversão. O manifesto deve ser protegido contra alteração indevida e nunca deve ser tratado como prova única de recuperação.

## Checklist

- [ ] O diretório verificado pertence à equipe ou está coberto por autorização explícita.
- [ ] O primeiro teste usou somente arquivos sintéticos em um diretório local descartável.
- [ ] O manifesto usa SHA-256 e fica protegido contra alteração junto com a cópia verificada.
- [ ] Links simbólicos, permissões, arquivos ocultos e exclusões foram avaliados pela política do backup.
- [ ] A verificação foi executada antes de uma restauração e o resultado foi registrado sem conteúdo sensível.
- [ ] Uma restauração real foi testada em ambiente isolado, com RPO e RTO documentados.
- [ ] O backup possui criptografia, retenção, controle de acesso e monitoramento adequados ao risco.
- [ ] Não foram usados tokens, chaves, credenciais, dados pessoais ou sistemas externos.
- [ ] Existe um procedimento versionado para desfazer configurações e responder a uma falha de restauração.

## Limitações e próximos passos

A verificação de hash não confirma completude, legibilidade de cada formato, validade das permissões ou capacidade de iniciar a aplicação restaurada. Combine-a com testes de restauração, cópias em locais independentes, proteção contra exclusão acidental, alertas de falha e revisão periódica do plano de resposta a incidentes. Se a ameaça incluir adulteração do próprio armazenamento de backup, avalie cópias imutáveis ou somente para leitura e um mecanismo de autenticação do manifesto aprovado pela política da organização.
