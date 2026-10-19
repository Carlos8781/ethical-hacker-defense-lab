# Dia 031 — Revisão local de permissões de diretório de backup

## Objetivo

Permissões excessivas em diretórios de backup podem expor cópias de dados ou permitir alterações por usuários locais não previstos. Este guia apresenta uma verificação somente leitura para identificar permissões POSIX de grupo ou de outros usuários no diretório informado. A decisão sobre permissões corretas deve seguir a política aprovada pela organização.

## Limites éticos e operacionais

- Use somente um diretório de laboratório ou um backup de sistema que você administra e tem autorização explícita para revisar. Os testes abaixo criam diretórios fictícios temporários.
- O programa examina apenas o diretório local indicado: não percorre conteúdo, não abre arquivos, não altera permissões, não acessa rede e não executa comandos externos.
- Links simbólicos são recusados para evitar que a verificação siga um caminho inesperado. O programa não percorre subdiretórios.
- Qualquer bit de permissão POSIX para grupo ou outros usuários é sinalizado para revisão, não automaticamente declarado incorreto. Uma permissão compartilhada pode ser necessária se estiver formalmente autorizada.
- O teste não avalia ACLs, permissões efetivas, controles do sistema de arquivos remoto, criptografia, política de retenção ou acesso por cópias externas. A ausência de alertas não comprova a segurança do backup.
- Não altere permissões em produção com base apenas neste resultado. Consulte a equipe responsável, confirme requisitos de restauração e registre a mudança aprovada em um procedimento separado.
- Saída e mensagens não incluem o caminho do diretório. Não inclua caminhos internos sensíveis ou dados de backup em commits, issues ou relatórios públicos.

## Exemplo seguro em Python

Salve como `review_backup_dir.py`. O exemplo é compatível com sistemas POSIX; em outros sistemas, a semântica de permissões pode ser diferente.

```python
#!/usr/bin/env python3
"""Sinaliza bits de permissão POSIX de grupo/outros em um diretório local."""
import argparse
import stat
import sys
from pathlib import Path

GROUP_OTHER_BITS = stat.S_IRWXG | stat.S_IRWXO


def inspect_directory(path: Path) -> tuple[int, str]:
    if path.is_symlink():
        return 2, "links simbólicos não são aceitos"
    try:
        info = path.stat(follow_symlinks=False)
    except OSError:
        return 2, "não foi possível consultar o diretório indicado"
    if not stat.S_ISDIR(info.st_mode):
        return 2, "o caminho indicado não é um diretório"

    mode = stat.S_IMODE(info.st_mode)
    if mode & GROUP_OTHER_BITS:
        return 1, f"revisão necessária: modo POSIX {mode:04o} concede bits a grupo/outros"
    return 0, f"nenhum bit POSIX de grupo/outros encontrado (modo {mode:04o})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="diretório local de backup autorizado")
    args = parser.parse_args()
    code, message = inspect_directory(args.directory)
    print(message)
    if code == 1:
        print("Confirme a política aprovada; este resultado é apenas um sinal para revisão.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste com diretórios temporários fictícios, sem usar dados reais:

```bash
python3 - <<'PY'
import tempfile
from pathlib import Path
from review_backup_dir import inspect_directory

with tempfile.TemporaryDirectory() as temp:
    safe = Path(temp) / "backup-lab-restrito"
    shared = Path(temp) / "backup-lab-compartilhado"
    safe.mkdir(mode=0o700)
    shared.mkdir(mode=0o755)
    safe.chmod(0o700)
    shared.chmod(0o755)
    assert inspect_directory(safe)[0] == 0
    assert inspect_directory(shared)[0] == 1
    print("Testes locais passaram: modo restrito e modo a revisar.")
PY
```

Código de saída `0` significa apenas que o modo POSIX não contém bits de grupo/outros; `1` sinaliza bits que merecem revisão conforme a política local; `2` indica erro, caminho não diretório ou link simbólico. Para avaliar o ambiente por completo, combine a revisão com controles de ACL, armazenamento, criptografia e testes autorizados de restauração.

## Checklist

- [ ] Confirmei que administro o diretório e tenho autorização explícita para examiná-lo.
- [ ] Usei um diretório local de laboratório ou sistema sob minha responsabilidade, sem expor conteúdo do backup.
- [ ] Revisei o código e confirmei que é somente leitura, não recursivo e sem acesso à rede.
- [ ] Testei localmente os casos fictícios com modo restrito e modo que exige revisão.
- [ ] Comparei qualquer sinalização com a política aprovada, os requisitos de acesso e a necessidade de restauração.
- [ ] Não alterei permissões automaticamente nem publiquei caminhos sensíveis, dados ou segredos.
