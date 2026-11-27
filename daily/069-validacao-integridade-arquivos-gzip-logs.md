# Dia 069 — Verificação local de integridade de arquivos gzip de logs

Arquivos de log arquivados podem ficar truncados ou corrompidos durante cópia e armazenamento. O exemplo abaixo valida um arquivo `.gz` explicitamente indicado, lendo-o em blocos para que a biblioteca padrão do Python confira o formato, o fim do fluxo e o CRC-32 declarado pelo gzip. Ele não extrai arquivos, não imprime conteúdo e não acessa a rede.

## Exemplo seguro em Python

Requer Python 3. O limite de bytes descompactados reduz o risco de consumir recursos excessivos com um arquivo comprimido muito expansivo. O exemplo usa apenas um arquivo sintético criado em diretório temporário; para uso operacional, escolha apenas arquivo sob sua administração e autorização.

```python
import gzip
import os
import stat
import sys
from pathlib import Path

MAX_EXPANDED_BYTES = 64 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


def validate_gzip(path: Path) -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("a origem deve ser um arquivo regular")
        total = 0
        with os.fdopen(fd, "rb") as raw:
            fd = -1
            with gzip.GzipFile(fileobj=raw, mode="rb") as archive:
                while True:
                    chunk = archive.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_EXPANDED_BYTES:
                        raise ValueError("limite de descompactação excedido")
        return total
    finally:
        if fd >= 0:
            os.close(fd)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python3 validate_gzip.py <arquivo-local.gz>")
    try:
        count = validate_gzip(Path(sys.argv[1]))
    except (OSError, EOFError, gzip.BadGzipFile, ValueError) as exc:
        raise SystemExit(f"Arquivo inválido ou ilegível ({type(exc).__name__}).")
    print(f"gzip válido; {count} byte(s) descompactado(s), conteúdo não exibido")
```

A validação lê o fluxo até o final porque erros de truncamento e checksum só podem ser identificados ao processar o conteúdo. Ela não altera o arquivo de origem. Se ultrapassar o limite, o programa interrompe a leitura e informa falha; isso não equivale a afirmar que o arquivo está corrompido.

## Teste local

Este teste usa dados inventados em diretório temporário e confirma a aceitação de um gzip íntegro e a rejeição de um arquivo truncado. Salve o código acima como `validate_gzip.py` e execute:

```bash
python3 - <<'PY'
import gzip
import tempfile
from pathlib import Path
from validate_gzip import validate_gzip

with tempfile.TemporaryDirectory() as folder:
    good = Path(folder) / "demo.log.gz"
    with gzip.open(good, "wb") as stream:
        stream.write(b"evento ficticio\n")
    assert validate_gzip(good) == len(b"evento ficticio\n")

    truncated = Path(folder) / "truncado.gz"
    truncated.write_bytes(good.read_bytes()[:-5])
    try:
        validate_gzip(truncated)
    except (OSError, EOFError):
        pass
    else:
        raise AssertionError("o arquivo truncado deveria falhar")
print("Testes sintéticos aprovados.")
PY
```

## Limitações éticas e técnicas

- Use somente arquivos locais que você administra ou tem autorização explícita para verificar. O teste não acessa serviços, redes, contas ou sistemas de terceiros.
- A verificação de gzip confirma propriedades do formato e checksum interno; não prova autenticidade, origem, autoria, completude histórica nem ausência de adulteração deliberada.
- O limite padrão de 64 MiB é uma escolha demonstrativa, não uma recomendação universal. Ajuste-o conforme capacidade e política aprovadas, sem remover limites indiscriminadamente.
- O script não examina o significado dos registros, não confirma política de retenção e não recupera nem corrige arquivos danificados. Não publique conteúdo, nomes internos ou metadados de logs reais.
- Um arquivo pode mudar por outro processo durante a leitura. Para evidências formais, preserve originais e siga o procedimento aprovado de resposta a incidentes e custódia.

## Checklist

- [ ] Confirme propriedade/autorização, escopo, finalidade e aprovação para o arquivo selecionado.
- [ ] Teste primeiro com gzip sintético em diretório temporário; mantenha um limite de leitura adequado.
- [ ] Execute apenas a validação local; não extraia nem execute conteúdo de arquivos recebidos.
- [ ] Preserve a origem, controle o acesso ao resultado e não copie logs reais, dados pessoais ou segredos para repositórios públicos.
- [ ] Trate falha de CRC, truncamento ou limite excedido como sinal para revisão por responsável autorizado, não como prova isolada de incidente.
- [ ] Para investigação formal, siga o processo organizacional de preservação, registro e transferência de evidências.
