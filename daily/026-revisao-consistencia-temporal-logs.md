# Dia 026 — Revisão local da consistência temporal de logs

## Objetivo

A ordem temporal dos registros pode ajudar uma equipe autorizada a correlacionar eventos durante uma revisão ou resposta a incidentes. Este exemplo verifica um arquivo JSON Lines local e fictício, procurando timestamps inválidos, registros fora de ordem e intervalos maiores que um limite escolhido. Ele informa somente números de linha e contagens — nunca reproduz o conteúdo dos registros — e não acessa a rede nem modifica o arquivo.

## Limitações éticas e escopo

Use primeiro apenas o fixture fictício abaixo. Só revise logs reais se você administra o sistema ou tem autorização explícita, escopo, finalidade, retenção e controles de acesso aprovados. Logs podem conter dados pessoais, identificadores, endereços internos e outros dados sensíveis; não os copie para serviços externos nem publique arquivos, linhas, caminhos internos ou resultados detalhados.

Uma lacuna temporal não prova que houve perda ou adulteração; pode refletir baixo volume, filtragem ou a política de registro. Uma ordem inesperada pode decorrer de buffering, múltiplas fontes ou relógios desalinhados. O analisador não valida autenticidade, completude, fuso horário correto ou cadeia de custódia, e não corrige relógios. Preserve os originais e encaminhe anomalias a responsáveis autorizados; não atribua culpa nem tome medidas contra pessoas com base neste indicador isolado.

## Exemplo seguro em Python

Salve como `review_log_timestamps.py`. Cada linha deve ser um objeto JSON com o campo `timestamp` em formato ISO 8601 e fuso explícito, como `2026-10-14T12:00:00Z`. O programa lê sequencialmente um arquivo regular local, limitado a 10 MiB, não segue links simbólicos em sistemas que suportam `O_NOFOLLOW`, não altera os dados e não imprime o conteúdo. O intervalo padrão para sinalizar uma lacuna é 15 minutos.

```python
#!/usr/bin/env python3
"""Check timestamp ordering and large gaps in an authorized local JSONL log."""
import argparse
import json
import os
import stat
import sys
from datetime import datetime, timedelta

MAX_BYTES = 10 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024


def parse_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp ausente ou inválido")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    result = datetime.fromisoformat(normalized)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp sem fuso explícito")
    return result


def review(path, gap_minutes):
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = None
    invalid = out_of_order = large_gaps = records = 0
    previous = None
    try:
        fd = os.open(path, flags)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            raise ValueError("tipo ou tamanho não permitido")
        total = 0
        with os.fdopen(fd, "rb") as stream:
            fd = None
            for line_number, raw in enumerate(stream, 1):
                total += len(raw)
                if total > MAX_BYTES or len(raw) > MAX_LINE_BYTES:
                    raise ValueError("limite de leitura excedido")
                if not raw.strip():
                    continue
                records += 1
                try:
                    obj = json.loads(raw)
                    current = parse_timestamp(obj.get("timestamp"))
                except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, ValueError):
                    invalid += 1
                    continue
                if previous is not None:
                    delta = current - previous
                    if delta < timedelta(0):
                        out_of_order += 1
                    elif delta > timedelta(minutes=gap_minutes):
                        large_gaps += 1
                previous = current
    finally:
        if fd is not None:
            os.close(fd)
    return records, invalid, out_of_order, large_gaps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", help="arquivo JSONL local dentro do escopo autorizado")
    parser.add_argument("--gap-minutes", type=int, default=15, help="limiar de lacuna positiva (padrão: 15)")
    args = parser.parse_args()
    if args.gap_minutes < 1 or args.gap_minutes > 1440:
        parser.error("--gap-minutes deve estar entre 1 e 1440")
    try:
        records, invalid, out_of_order, large_gaps = review(args.logfile, args.gap_minutes)
    except (OSError, ValueError):
        print("falha ao revisar o arquivo local permitido", file=sys.stderr)
        return 2
    print(f"registros={records} timestamps_invalidos={invalid} fora_de_ordem={out_of_order} lacunas={large_gaps}")
    return 1 if invalid or out_of_order or large_gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste com um fixture fictício em diretório temporário:

```bash
cat > /tmp/log-ficticio.jsonl <<'EOF'
{"timestamp":"2026-10-14T12:00:00Z","event":"login_ok"}
{"timestamp":"2026-10-14T12:01:00Z","event":"backup_ok"}
EOF
python3 review_log_timestamps.py /tmp/log-ficticio.jsonl
# Esperado: registros=2 timestamps_invalidos=0 fora_de_ordem=0 lacunas=0; saída 0
cat >> /tmp/log-ficticio.jsonl <<'EOF'
{"timestamp":"2026-10-14T11:59:00Z","event":"fixture"}
{"timestamp":"sem-fuso","event":"fixture"}
EOF
python3 review_log_timestamps.py /tmp/log-ficticio.jsonl
# Esperado: saída 1 e contagens de anomalias; nenhum conteúdo de evento é exibido
rm -f /tmp/log-ficticio.jsonl
```

A saída `1` no segundo teste significa somente que há itens para revisão. A saída `2` indica argumento ou erro de leitura.

## Checklist

- [ ] O teste foi feito com registros inteiramente fictícios; o arquivo real, se houver, pertence ao escopo autorizado.
- [ ] A fonte, o fuso e a política de sincronização dos relógios são conhecidos e revisados separadamente.
- [ ] O limiar de lacuna foi escolhido conforme o volume e a política do sistema, não tratado como regra universal.
- [ ] O script foi executado localmente, sem transmitir, imprimir ou publicar o conteúdo dos logs.
- [ ] Os originais foram preservados conforme a política de retenção e resposta a incidentes.
- [ ] Anomalias foram encaminhadas a uma pessoa responsável para validação contextual; não são tratadas como prova isolada.
- [ ] Nenhum sistema, conta, serviço ou rede de terceiros foi acessado.

> Exemplo somente leitura para arquivo local autorizado; usa timestamps e eventos fictícios, sem qualquer conexão de rede.
<!-- Testado localmente com fixture fictício; nenhuma rede foi acessada. -->
