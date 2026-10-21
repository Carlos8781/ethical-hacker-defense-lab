# Dia 033 — Revisão local da consistência temporal de logs JSONL

## Objetivo

Em uma triagem defensiva, a ordem temporal dos eventos ajuda a reconstruir uma sequência. Este exemplo verifica, em um arquivo JSON Lines (JSONL) local autorizado, se cada linha contém os campos mínimos `timestamp` e `event`, se o timestamp é ISO 8601 com fuso horário e se os horários aparecem em ordem não decrescente. Ele informa apenas contagens e números de linha: não imprime conteúdo de eventos, que pode conter dados sensíveis.

A ferramenta é somente leitura e não acessa a rede, não altera o arquivo e não tenta autenticar, sondar ou interagir com qualquer sistema. Use-a em uma cópia de trabalho autorizada, preservando o original segundo os procedimentos da organização.

## Limitações e ética

- Um horário fora de ordem ou uma linha inválida é um indício para revisão, não prova de adulteração ou incidente. Sistemas podem ter relógios desalinhados, fusos ou formatos diferentes.
- A validação não confirma a origem, autenticidade, completude, cadeia de custódia ou sincronização do log; não substitui SIEM, auditoria ou resposta a incidentes.
- Só analise logs que você possui ou para os quais tem autorização explícita. Respeite retenção, privacidade e políticas internas.
- Não cole dados reais em exemplos ou commits. O teste abaixo cria apenas eventos fictícios temporários; o script não exibe valores de eventos.
- O limite de 2 MiB e 10.000 linhas reduz consumo acidental, mas não é uma garantia contra todos os arquivos malformados ou condições do ambiente.

## Exemplo seguro em Python

Salve como `review_jsonl_timestamps.py` e execute apenas sobre um arquivo local autorizado:

```python
#!/usr/bin/env python3
"""Valida estrutura básica e ordem temporal de um JSONL local autorizado."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MAX_LINES = 10_000


def review(path: Path) -> tuple[int, int, int, int]:
    if path.is_symlink():
        print("Entrada rejeitada: links simbólicos não são aceitos.")
        return 0, 0, 0, 1
    try:
        raw = path.read_bytes()
    except OSError:
        print("Entrada rejeitada: não foi possível ler o arquivo local.")
        return 0, 0, 0, 1
    if len(raw) > MAX_BYTES:
        print("Entrada rejeitada: arquivo excede o limite de 2 MiB.")
        return 0, 0, 0, 1
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        print("Entrada rejeitada: o arquivo não é UTF-8 válido.")
        return 0, 0, 0, 1

    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        print("Entrada rejeitada: arquivo excede 10.000 linhas.")
        return 0, 0, 0, 1

    invalid = out_of_order = valid = 0
    previous = None
    for number, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
            if not isinstance(record, dict) or not isinstance(record.get("event"), str):
                raise ValueError
            timestamp = record.get("timestamp")
            if not isinstance(timestamp, str):
                raise ValueError
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if parsed.utcoffset() is None:
                raise ValueError
        except (json.JSONDecodeError, ValueError, TypeError):
            invalid += 1
            print(f"Linha {number}: estrutura ou timestamp inválido.")
            continue

        valid += 1
        if previous is not None and parsed < previous:
            out_of_order += 1
            print(f"Linha {number}: horário anterior ao registro válido precedente.")
        previous = parsed

    print(f"Resumo: {valid} linha(s) válida(s), {invalid} inválida(s), {out_of_order} fora de ordem.")
    return valid, invalid, out_of_order, 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path, help="arquivo JSONL local autorizado")
    args = parser.parse_args()
    valid, invalid, out_of_order, error = review(args.jsonl)
    if error:
        return 2
    return 1 if invalid or out_of_order else 0


if __name__ == "__main__":
    sys.exit(main())
```

Teste com arquivo temporário fictício, salvando o script como `review_jsonl_timestamps.py` no mesmo diretório:

```bash
python3 - <<'PY'
import tempfile
from pathlib import Path
from review_jsonl_timestamps import review

sample = (
    '{"timestamp":"2026-01-01T10:00:00Z","event":"login_ok"}\n'
    '{"timestamp":"2026-01-01T09:59:00Z","event":"logout"}\n'
    '{"timestamp":"sem-fuso","event":"test"}\n'
)
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "synthetic.jsonl"
    path.write_text(sample, encoding="utf-8")
    assert review(path) == (2, 1, 1, 0)
print("Teste local passou: linha inválida e inversão temporal sinalizadas sem exibir eventos.")
PY
```

Código de saída `0` significa que as verificações limitadas passaram; `1` indica linha inválida ou horário fora de ordem; `2` indica falha/rejeição da entrada. Trate os achados conforme o processo autorizado da equipe e mantenha os registros originais protegidos.

## Checklist

- [ ] Confirmei autorização explícita para analisar o arquivo e usei uma cópia local apropriada.
- [ ] Usei somente dados fictícios no teste e não incluí dados pessoais, conteúdo sensível ou segredos.
- [ ] Verifiquei que a ferramenta só lê o arquivo, não usa rede e não modifica os registros.
- [ ] Executei o teste local e confirmei os resultados sem revelar o conteúdo dos eventos.
- [ ] Considerei relógios desalinhados, fusos e diferenças de formato antes de interpretar alertas.
- [ ] Preservei a evidência original e encaminhei achados por canal autorizado, sem publicar logs reais.
