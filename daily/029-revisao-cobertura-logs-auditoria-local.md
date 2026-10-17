# Dia 029 — Revisão local da cobertura de eventos de auditoria

## Objetivo

Uma revisão periódica da cobertura ajuda a identificar se os registros de auditoria esperados estão sendo produzidos antes que uma investigação dependa deles. Este exercício confere a presença de tipos de evento previamente definidos em um arquivo JSONL local de exemplo. Use os nomes de evento aprovados pela equipe e os requisitos documentados do sistema que você administra.

## Limites éticos e operacionais

- Execute somente sobre arquivos de laboratório ou logs de sistemas que você administra e tem autorização explícita para revisar; o exemplo de teste abaixo usa dados inteiramente fictícios.
- O programa só lê o caminho local informado, não acessa a rede, não altera arquivos, não executa comandos e não coleta eventos por conta própria.
- A saída contém apenas contagens e tipos de evento definidos no próprio script. O conteúdo bruto dos registros, nomes de usuário, endereços, mensagens e outros campos não são impressos.
- O exemplo aceita JSONL UTF-8 com objetos que tenham `event_type` textual. Linhas inválidas ou sem esse campo são contadas como inválidas, sem exibir seu conteúdo. O limite de bytes e linhas reduz o risco de consumo excessivo de recursos.
- A presença de eventos não prova que os logs sejam completos, autênticos, protegidos contra adulteração ou retidos pelo prazo correto. Eventos ausentes podem refletir diferenças de configuração ou nomenclatura, não necessariamente um incidente. Confirme os requisitos com os responsáveis e investigue pelo processo aprovado.
- Não use este exemplo para contornar controles de acesso, coletar dados pessoais desnecessários ou examinar logs de terceiros.

## Exemplo seguro em Python

Salve como `audit_coverage.py`. A lista de eventos é ilustrativa: adapte-a somente após confirmar os requisitos do ambiente autorizado.

```python
#!/usr/bin/env python3
"""Conta cobertura de tipos de evento em um arquivo JSONL local autorizado."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

EXPECTED_EVENTS = ("login_success", "login_failure", "permission_change", "backup_completed")
MAX_BYTES = 2 * 1024 * 1024
MAX_LINES = 20_000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path, help="caminho para JSONL local autorizado ou fictício")
    args = parser.parse_args()
    if args.jsonl.is_symlink():
        print("não são aceitos links simbólicos", file=sys.stderr)
        return 2

    counts: Counter[str] = Counter()
    invalid = 0
    total_bytes = 0
    try:
        with args.jsonl.open("rb") as stream:
            for line_number, raw in enumerate(stream, start=1):
                total_bytes += len(raw)
                if total_bytes > MAX_BYTES or line_number > MAX_LINES:
                    print("arquivo excede o limite local de tamanho ou linhas", file=sys.stderr)
                    return 2
                try:
                    record = json.loads(raw.decode("utf-8"))
                    event = record.get("event_type") if isinstance(record, dict) else None
                    if isinstance(event, str) and event in EXPECTED_EVENTS:
                        counts[event] += 1
                    else:
                        invalid += 1
                except (UnicodeDecodeError, json.JSONDecodeError):
                    invalid += 1
    except OSError:
        print("falha ao ler o arquivo local indicado", file=sys.stderr)
        return 2

    missing = [event for event in EXPECTED_EVENTS if counts[event] == 0]
    print("Cobertura de tipos de evento (contagens agregadas):")
    for event in EXPECTED_EVENTS:
        print(f"- {event}: {counts[event]}")
    print(f"- linhas inválidas ou sem evento esperado: {invalid}")
    if missing:
        print("Revisão necessária: um ou mais tipos esperados não aparecem.")
        return 1
    print("Tipos esperados presentes; isso não comprova completude nem integridade dos logs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste em um diretório temporário com dados fictícios:

```bash
cat > /tmp/audit-ficticio.jsonl <<'EOF'
{"event_type":"login_success","user":"usuario-exemplo"}
{"event_type":"login_failure","user":"usuario-exemplo"}
{"event_type":"permission_change","target":"recurso-ficticio"}
{"event_type":"backup_completed","job":"backup-demo"}
EOF
python3 audit_coverage.py /tmp/audit-ficticio.jsonl
# Esperado: saída 0; quatro tipos aparecem, sem imprimir os campos fictícios.
printf '%s\n' '{"event_type":"login_success"}' > /tmp/audit-ficticio.jsonl
python3 audit_coverage.py /tmp/audit-ficticio.jsonl
# Esperado: saída 1 e indicação agregada de revisão necessária.
rm -f /tmp/audit-ficticio.jsonl
```

Código de saída `0` significa apenas que cada tipo listado ocorreu ao menos uma vez; `1` indica tipo esperado ausente; `2` indica erro de leitura ou limite excedido. Nenhum desses resultados substitui revisão humana ou validação da integridade e retenção dos logs.

## Checklist

- [ ] Confirmei autorização e usei somente um arquivo local de laboratório ou administrado pela minha equipe.
- [ ] Validei com dados fictícios os casos de cobertura completa e incompleta.
- [ ] Revisei e documentei a lista de eventos esperados com os responsáveis pelo sistema.
- [ ] Confirmei que o programa não publica nem imprime registros brutos ou dados pessoais.
- [ ] Avaliei separadamente completude, integridade, controle de acesso e retenção dos logs pelo processo interno.
- [ ] Não acessei rede, sistemas de terceiros nem arquivos fora do escopo autorizado.
