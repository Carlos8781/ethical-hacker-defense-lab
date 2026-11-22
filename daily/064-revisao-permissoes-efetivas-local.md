# Dia 064 — Revisão local de permissões efetivas de arquivos

Permissões excessivas em arquivos podem expor dados ou permitir alterações indevidas. Uma revisão periódica de arquivos conhecidos e administrados pela equipe ajuda a identificar casos que merecem confirmação. Este exemplo em Python examina apenas metadados locais, sem abrir o conteúdo dos arquivos, sem seguir links simbólicos e sem fazer alterações.

Salve como `review_file_modes.py`:

```python
#!/usr/bin/env python3
"""Sinaliza permissões de leitura/escrita para grupo ou outros em caminhos locais."""
import stat
import sys
from pathlib import Path


def review(path: Path) -> list[str]:
    # lstat evita seguir um link simbólico para outro objeto.
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode):
        return [f"{path}: link simbólico ignorado; revise o destino separadamente"]
    if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
        return [f"{path}: tipo de arquivo não avaliado"]

    mode = stat.S_IMODE(info.st_mode)
    findings = []
    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        findings.append(f"{path}: escrita por grupo/outros habilitada (modo {mode:04o})")
    if mode & (stat.S_IROTH):
        findings.append(f"{path}: leitura por outros habilitada (modo {mode:04o})")
    return findings


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python3 review_file_modes.py <caminho-local> [...]")
        return 2
    findings = []
    for raw in sys.argv[1:]:
        path = Path(raw)
        try:
            findings.extend(review(path))
        except OSError as exc:
            findings.append(f"{path}: não foi possível ler metadados ({exc.strerror})")
    print("\n".join(findings) if findings else "Nenhuma permissão sinalizada nos caminhos fornecidos.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Exemplo seguro com um arquivo temporário sintético, sem acessar dados reais:

```bash
python3 - <<'PY'
import os
import tempfile
from pathlib import Path
from review_file_modes import review

with tempfile.TemporaryDirectory() as folder:
    sample = Path(folder) / "demo.txt"
    sample.write_text("conteúdo fictício\n", encoding="utf-8")
    sample.chmod(0o640)
    assert review(sample) == []
    sample.chmod(0o646)
    findings = review(sample)
    assert any("escrita por grupo/outros" in item for item in findings)
    assert any("leitura por outros" in item for item in findings)
print("Teste sintético aprovado.")
PY
```

## Limitações e cuidados éticos

- Use somente em arquivos e diretórios locais sob sua administração ou com autorização explícita. Comece por dados fictícios ou uma amostra aprovada.
- O script verifica bits tradicionais de modo Unix, não ACLs, permissões do Windows, atributos de montagem, políticas de compartilhamento ou permissões efetivas herdadas. O resultado é uma triagem, não uma avaliação completa de acesso.
- Uma permissão sinalizada pode ser intencional; confirme proprietário, uso, plataforma e política antes de propor mudanças. Não altere permissões automaticamente com base no resultado.
- `lstat` evita seguir o link simbólico examinado, mas não elimina toda condição de corrida nem substitui uma revisão segura de diretórios. Não use caminhos fornecidos por fontes não confiáveis.
- Não leia nem publique conteúdo sensível ou a saída contendo caminhos internos. O exemplo não faz conexões de rede e não modifica os objetos examinados.

## Checklist

- [ ] Confirme autorização e delimite os caminhos locais da revisão.
- [ ] Use arquivo de teste fictício antes de apontar o script para dados administrados.
- [ ] Verifique proprietário, grupo, modo, ACLs e controles específicos da plataforma por meios aprovados.
- [ ] Avalie se o acesso observado é necessário para o funcionamento autorizado do sistema.
- [ ] Submeta qualquer ajuste ao responsável e ao processo de gestão de mudanças; faça backup quando aplicável.
- [ ] Proteja e sanitize os resultados antes de compartilhá-los; retenha-os conforme a política interna.
