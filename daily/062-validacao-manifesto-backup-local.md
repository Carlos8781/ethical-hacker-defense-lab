# Dia 062 — Validação local de manifesto de backup

Um manifesto com caminhos relativos e hashes SHA-256 pode ajudar a detectar arquivos ausentes ou alterados em uma cópia local de backup antes de uma revisão de recuperação. Este exemplo compara um manifesto JSON a arquivos dentro de uma raiz explicitamente escolhida. Ele apenas lê arquivos; não faz rede, não restaura dados nem substitui cópias independentes e testes periódicos de recuperação.

## Exemplo seguro em Python

Salve como `verify_backup_manifest.py`. O manifesto deve ser um objeto JSON com uma lista `files`; cada item contém um caminho relativo `path` e um hash hexadecimal `sha256`. Use apenas uma cópia de laboratório ou backup sob sua administração, com dados fictícios ou sanitizados.

```python
import hashlib
import json
import re
import sys
from pathlib import Path

HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def verify(root: Path, manifest_path: Path) -> list[str]:
    root = root.resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("manifesto deve conter uma lista 'files'")

    findings: list[str] = []
    seen: set[str] = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise ValueError("cada entrada deve ser um objeto")
        name, expected = entry.get("path"), entry.get("sha256")
        if not isinstance(name, str) or not name or Path(name).is_absolute():
            raise ValueError("path deve ser um caminho relativo não vazio")
        parts = Path(name).parts
        if ".." in parts or name in seen:
            raise ValueError("caminho duplicado ou com componente '..'")
        seen.add(name)
        if not isinstance(expected, str) or not HASH_RE.fullmatch(expected):
            raise ValueError(f"hash SHA-256 inválido para {name}")

        candidate = root
        for part in parts:
            candidate = candidate / part
            if candidate.is_symlink():
                raise ValueError(f"link simbólico não permitido: {name}")
        if not candidate.is_file():
            findings.append(f"Ausente ou não é arquivo regular: {name}")
            continue
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest.lower() == expected.lower():
            findings.append(f"OK: {name}")
        else:
            findings.append(f"Divergência de hash: {name}")
    return findings


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python3 verify_backup_manifest.py <raiz-backup> <manifesto.json>")
        return 2
    try:
        results = verify(Path(sys.argv[1]), Path(sys.argv[2]))
        print("\n".join(results) if results else "Manifesto sem arquivos para verificar.")
        return 1 if any(item.startswith(("Ausente", "Divergência")) for item in results) else 0
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Não foi possível validar o manifesto: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

Exemplo de manifesto fictício: `{"files": [{"path": "docs/demo.txt", "sha256": "<64 caracteres hexadecimais>"}]}`. Para executar: `python3 verify_backup_manifest.py ./backup-lab ./manifest.json`.

## Limitações e cuidados éticos

- Execute somente contra uma cópia local de backup que você administra ou cuja revisão foi autorizada. O manifesto e os dados de exemplo devem ser fictícios ou sanitizados.
- Um hash só confirma correspondência com o valor informado; não prova origem confiável, autenticidade do manifesto, confidencialidade, recuperabilidade nem ausência de comprometimento.
- Arquivos grandes são lidos integralmente em memória neste exemplo; para conjuntos volumosos, use leitura em blocos e revise o impacto operacional antes.
- O programa não altera arquivos, não segue links simbólicos, não acessa rede ou credenciais e não restaura conteúdo. Ainda assim, revise a origem e permissões dos arquivos antes de executá-lo.
- Não publique nomes internos, caminhos sensíveis, conteúdo de backup, dados pessoais ou segredos.

## Checklist

- [ ] Confirme autorização e escolha uma raiz de laboratório ou backup administrado.
- [ ] Gere o manifesto por processo aprovado e proteja-o contra alteração independente do backup.
- [ ] Use somente caminhos relativos; não inclua dados reais sensíveis no guia ou no teste.
- [ ] Confira que os arquivos esperados constam no manifesto e que o armazenamento está disponível.
- [ ] Investigue arquivos ausentes e divergências por um processo de resposta e recuperação aprovado.
- [ ] Trate hash correspondente como evidência limitada, não como prova de backup recuperável.
- [ ] Revise e sanitize qualquer saída antes de compartilhá-la.

## Teste local

Este teste cria arquivos fictícios temporários e valida correspondência, divergência e rejeição de tentativa de sair da raiz. Não acessa a rede:

```bash
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from verify_backup_manifest import verify

with TemporaryDirectory() as temp:
    root = Path(temp) / "backup"
    root.mkdir()
    payload = root / "demo.txt"
    payload.write_text("conteúdo fictício\n", encoding="utf-8")
    manifest = Path(temp) / "manifest.json"
    entry = {"path": "demo.txt", "sha256": hashlib.sha256(payload.read_bytes()).hexdigest()}
    manifest.write_text(json.dumps({"files": [entry]}), encoding="utf-8")
    assert verify(root, manifest) == ["OK: demo.txt"]
    payload.write_text("conteúdo alterado\n", encoding="utf-8")
    assert verify(root, manifest) == ["Divergência de hash: demo.txt"]
    manifest.write_text(json.dumps({"files": [{"path": "../fora.txt", "sha256": "0" * 64}]}), encoding="utf-8")
    try:
        verify(root, manifest)
    except ValueError:
        pass
    else:
        raise AssertionError("caminho fora da raiz deveria ser rejeitado")
print("Testes sintéticos aprovados.")
PY
```
