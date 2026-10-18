# Dia 030 — Revisão local de minimização de dados em logs

## Objetivo

Logs úteis para auditoria e resposta a incidentes não devem reter dados pessoais ou segredos sem necessidade. Esta revisão identifica, em um arquivo JSONL local, nomes de campos que merecem avaliação pela equipe responsável. O exemplo imprime somente nomes de campos previamente definidos e contagens agregadas; não imprime nem persiste valores dos registros.

## Limites éticos e operacionais

- Use apenas logs fictícios, de laboratório ou de sistemas que você administra e tem autorização explícita para revisar. O teste abaixo usa exclusivamente dados fictícios.
- O programa lê somente o arquivo local informado; não acessa rede, não altera arquivos, não executa comandos e não envia dados a serviços externos.
- Os nomes de campos sinalizados são heurísticas configuráveis, não uma classificação completa. Campos com nomes incomuns podem escapar, e campos legítimos podem ser sinalizados.
- O programa não verifica conteúdo, contexto, necessidade legal ou política de retenção. Um resultado sem alertas não prova que o log esteja livre de dados sensíveis.
- Não inclua valores de tokens, senhas, identificadores pessoais ou outros dados reais em exemplos, commits, issues ou saídas. Se encontrar exposição, siga o processo de resposta a incidentes da organização; não copie o valor para o relatório.
- O limite de tamanho e linhas reduz consumo acidental de recursos. Arquivos malformados são contabilizados sem que a linha seja exibida.

## Exemplo seguro em Python

Salve como `review_log_fields.py`. Ajuste a lista de campos somente com a equipe responsável. O programa analisa apenas as chaves dos objetos JSON, sem acessar ou imprimir os valores.

```python
#!/usr/bin/env python3
"""Sinaliza nomes de campos que merecem revisão em JSONL local autorizado."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REVIEW_FIELDS = {"password", "access_token", "authorization", "email", "phone"}
MAX_BYTES = 2 * 1024 * 1024
MAX_LINES = 20_000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path, help="arquivo JSONL local autorizado ou fictício")
    args = parser.parse_args()
    if args.jsonl.is_symlink():
        print("não são aceitos links simbólicos", file=sys.stderr)
        return 2

    counts: Counter[str] = Counter()
    invalid = total_bytes = 0
    try:
        with args.jsonl.open("rb") as stream:
            for line_number, raw in enumerate(stream, start=1):
                total_bytes += len(raw)
                if total_bytes > MAX_BYTES or line_number > MAX_LINES:
                    print("arquivo excede o limite local de tamanho ou linhas", file=sys.stderr)
                    return 2
                try:
                    record = json.loads(raw.decode("utf-8"))
                    if not isinstance(record, dict):
                        invalid += 1
                        continue
                    for key in record:
                        if isinstance(key, str) and key.casefold() in REVIEW_FIELDS:
                            counts[key.casefold()] += 1
                except (UnicodeDecodeError, json.JSONDecodeError):
                    invalid += 1
    except OSError:
        print("falha ao ler o arquivo local indicado", file=sys.stderr)
        return 2

    print("Revisão de nomes de campos (contagens; valores não são exibidos):")
    if counts:
        for field in sorted(counts):
            print(f"- {field}: {counts[field]}")
        print("Revisão necessária: avalie necessidade, minimização e retenção conforme a política aprovada.")
        result = 1
    else:
        print("- nenhum campo da lista configurada foi encontrado")
        print("Isso não prova ausência de dados sensíveis; a lista é apenas uma heurística.")
        result = 0
    print(f"- linhas inválidas ou não-objeto: {invalid}")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste em um diretório temporário com dados inteiramente fictícios:

```bash
cat > /tmp/logs-ficticios.jsonl <<'EOF'
{"event":"login","user":"pessoa-exemplo","email":"exemplo.invalid"}
{"event":"job","status":"ok"}
EOF
python3 review_log_fields.py /tmp/logs-ficticios.jsonl
# Esperado: saída 1; reporta apenas "email: 1", sem imprimir o valor fictício.
printf '%s\n' '{"event":"backup","status":"ok"}' > /tmp/logs-ficticios.jsonl
python3 review_log_fields.py /tmp/logs-ficticios.jsonl
# Esperado: saída 0, com aviso de que a heurística não prova ausência de dados sensíveis.
rm -f /tmp/logs-ficticios.jsonl
```

Código de saída `0` significa apenas que nenhum nome listado foi encontrado; `1` significa que um ou mais nomes configurados merecem revisão; `2` indica erro de leitura ou limite excedido. Não use este resultado como certificação de conformidade nem como substituto da revisão humana.

## Checklist

- [ ] Confirmei autorização e usei somente dados fictícios, de laboratório ou logs sob minha administração.
- [ ] Verifiquei que o relatório mostra somente nomes de campos, contagens e estado agregado, nunca valores de registros.
- [ ] Testei localmente um caso sinalizado e outro sem correspondências, ambos com dados fictícios.
- [ ] Revisei a lista de campos com os responsáveis e adaptei-a à política de minimização aprovada.
- [ ] Avaliei separadamente a necessidade, retenção, acesso e proteção dos logs; o script não comprova conformidade.
- [ ] Não usei rede, não examinei sistemas de terceiros e não publiquei segredos ou dados pessoais.
