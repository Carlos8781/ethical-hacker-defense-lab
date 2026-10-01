# Dia 013 — Revisão local de testes de restauração de backups

Ter um backup concluído não demonstra, por si só, que a equipe consegue recuperar os dados necessários. Esta lição propõe uma revisão periódica das evidências de exercícios de restauração autorizados. Um pequeno programa local valida um CSV de inventário fictício e resume se o teste mais recente de cada categoria foi recente, falhou ou ainda não foi feito. Ele avalia somente os registros fornecidos; não abre, verifica, restaura, altera nem apaga backups.

## Uso autorizado e limitações éticas

Use o roteiro e o programa apenas em processos de continuidade aprovados e em arquivos locais que você tem autorização para ler. Comece com a amostra sintética abaixo. Não coloque nomes de clientes, pessoas, caminhos internos, nomes de servidores, detalhes de infraestrutura, incidentes reais ou segredos no CSV, especialmente em arquivos destinados a um repositório público.

O CSV deve representar o resultado mais recente de um exercício para cada uma das categorias genéricas permitidas no exemplo. A lista e o limite de 90 dias são demonstrações; defina categorias, frequência e critérios com os responsáveis por segurança, privacidade, continuidade e retenção. `sucesso` significa somente que o registro diz que um exercício foi concluído; o programa não confirma a veracidade, qualidade ou escopo do teste.

O exemplo lê apenas o CSV indicado, não acessa a rede ou sistemas, não executa restaurações, não toca nos arquivos de backup e não transmite nem grava resultados. Ele imprime apenas totais agregados. Registros malformados são contados sem revelar seu conteúdo. Não use as contagens como prova de recuperabilidade, conformidade ou prontidão; preserve evidências conforme as políticas internas e investigue resultados com as pessoas autorizadas.

## Exemplo seguro em Python

Salve como `review_restore_tests.py`. O formato é CSV com exatamente as colunas `categoria,resultado,data_teste`. Categorias e resultados são enumerados no código; datas seguem `AAAA-MM-DD`. Para `nao_testado`, a data deve ficar vazia. Cada categoria pode aparecer uma única vez.

```python
#!/usr/bin/env python3
"""Aggregate a fictional local register of authorized backup restore tests."""
import argparse
import csv
from datetime import date
from pathlib import Path
from typing import TextIO

CATEGORIES = {"config", "documentos", "dados"}
OUTCOMES = {"sucesso", "falha", "nao_testado"}
MAX_AGE_DAYS = 90


def summarize(stream: TextIO, today: date) -> dict[str, int]:
    reader = csv.DictReader(stream, strict=True)
    if reader.fieldnames != ["categoria", "resultado", "data_teste"]:
        raise ValueError("cabecalho invalido")

    records: dict[str, str] = {}
    counts = {
        "recentes": 0,
        "desatualizados": 0,
        "falhas": 0,
        "nao_testados": 0,
    }
    invalid = 0

    for row in reader:
        if None in row or any(value is None for value in row.values()):
            invalid += 1
            continue

        category = row["categoria"].strip()
        outcome = row["resultado"].strip()
        date_text = row["data_teste"].strip()
        if category not in CATEGORIES or category in records or outcome not in OUTCOMES:
            invalid += 1
            continue

        if outcome == "nao_testado":
            if date_text:
                invalid += 1
                continue
            records[category] = outcome
            counts["nao_testados"] += 1
            continue

        try:
            tested_on = date.fromisoformat(date_text)
        except ValueError:
            invalid += 1
            continue
        if tested_on.isoformat() != date_text or tested_on > today:
            invalid += 1
            continue

        records[category] = outcome
        if outcome == "falha":
            counts["falhas"] += 1
        elif (today - tested_on).days <= MAX_AGE_DAYS:
            counts["recentes"] += 1
        else:
            counts["desatualizados"] += 1

    counts["ausentes"] = len(CATEGORIES - records.keys())
    counts["invalidos"] = invalid
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="CSV local autorizado")
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=date.today(),
        help="data de referência ISO para revisão reproduzível (opcional)",
    )
    args = parser.parse_args()
    if not args.csv_file.is_file():
        parser.error("informe um arquivo CSV local existente")

    try:
        with args.csv_file.open("r", encoding="utf-8", newline="") as stream:
            counts = summarize(stream, args.today)
    except (OSError, UnicodeError, csv.Error, ValueError):
        parser.error("não foi possível ler um CSV local válido")

    print(f"testes recentes: {counts['recentes']}")
    print(f"testes desatualizados: {counts['desatualizados']}")
    print(f"falhas registradas: {counts['falhas']}")
    print(f"categorias sem teste: {counts['nao_testados']}")
    print(f"categorias ausentes: {counts['ausentes']}")
    print(f"registros inválidos: {counts['invalidos']}")

    if counts["invalidos"]:
        return 2
    if any(counts[key] for key in ("desatualizados", "falhas", "nao_testados", "ausentes")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Crie um CSV descartável com dados fictícios e execute a revisão local com data de referência fixa:

```bash
cat > /tmp/testes-restauracao-ficticios.csv <<'EOF'
categoria,resultado,data_teste
config,sucesso,2026-09-15
documentos,falha,2026-09-20
dados,nao_testado,
EOF
python3 review_restore_tests.py /tmp/testes-restauracao-ficticios.csv --today 2026-10-01
```

A saída esperada informa um teste recente, nenhuma categoria desatualizada, uma falha, uma categoria sem teste, nenhuma categoria ausente e nenhum registro inválido. O programa termina com código `1` porque há resultados que precisam de avaliação humana; isso não significa que um backup esteja comprometido. Código `0` significa somente que todas as categorias têm um registro de sucesso dentro do limite e nenhum registro inválido. Código `2` indica linhas inválidas; nenhuma linha é impressa.

## Checklist

- [ ] A revisão e os exercícios de restauração foram aprovados e têm responsáveis definidos.
- [ ] O primeiro teste usa somente dados fictícios e um CSV temporário local.
- [ ] O inventário não contém nomes de pessoas, clientes, hosts, caminhos internos, segredos ou incidentes reais.
- [ ] Categorias, frequência, limite de validade e critérios de sucesso foram aprovados pelos responsáveis.
- [ ] O resultado mais recente de cada categoria foi registrado; falhas e lacunas têm acompanhamento humano.
- [ ] Uma amostra de restauração real, se necessária, é planejada e executada separadamente em ambiente autorizado, isolado e controlado, por responsáveis competentes.
- [ ] A execução real segue aprovações, políticas de retenção, privacidade, gestão de mudanças e plano de reversão.
- [ ] Evidências e dados de backup permanecem protegidos; o resumo agregado não é tratado como prova técnica.
- [ ] Nenhum backup foi lido, alterado, apagado ou restaurado pelo exemplo deste guia.
- [ ] Nenhum serviço externo ou sistema de terceiros foi consultado.

## Limitações e próximos passos

O script verifica formato, categorias permitidas, datas e idade declarada dos registros. Não verifica a existência ou integridade de backups, não valida conteúdo restaurado, permissões, criptografia, tempos de recuperação ou dependências, e não autentica quem preencheu o CSV. Uma data recente não garante que um teste tenha sido completo; uma falha registrada requer análise conforme o plano interno, não uma ação automática. Adapte o processo com as equipes responsáveis e execute exercícios práticos somente sob autorização, em ambiente de teste adequado, com salvaguardas e critérios documentados.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `csv`, `datetime`, `argparse` e `pathlib`.
- Políticas internas aprovadas de continuidade, backup, retenção, privacidade e gestão de mudanças.

> Este exemplo resume metadados fictícios de exercícios autorizados; não acessa redes, backups ou sistemas e não executa restaurações.

<!-- Testado localmente com Python 3 e CSV fictício. -->
