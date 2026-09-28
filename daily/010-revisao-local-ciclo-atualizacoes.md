# Dia 010 — Revisão local do ciclo de atualizações

Manter sistemas atualizados reduz a exposição a falhas já corrigidas. Esta lição mostra como revisar, a partir de um CSV local, se a data da última atualização registrada de cada ativo ultrapassou o intervalo de revisão definido pela própria equipe. O relatório é agregado: não imprime identificadores de ativos e não consulta nenhum serviço.

## Uso autorizado e limitações éticas

Use o programa somente com um inventário que sua equipe administra e cujo tratamento esteja autorizado. O teste abaixo contém referências fictícias e roda localmente. O script é somente leitura: não acessa a rede, não identifica dispositivos, não instala nem remove atualizações, não altera configurações e não executa comandos do sistema. Não inclua nomes de clientes, endereços, usuários, segredos ou outros dados reais no exemplo nem publique inventários operacionais.

O intervalo de revisão deve vir de uma política aprovada para cada classe de ativo; os dias do CSV não são recomendação universal. O programa confia nas datas e intervalos informados, não verifica a origem, atualidade ou completude do inventário, não confirma quais atualizações foram instaladas e não avalia se uma correção é aplicável ou suficiente. Um ativo marcado para revisão não prova vulnerabilidade ou incidente; um ativo dentro do intervalo tampouco prova que esteja seguro. Valide os dados e os resultados com responsáveis autorizados antes de priorizar qualquer mudança.

## Exemplo seguro em Python

Salve como `review_patch_cycle.py`. O CSV precisa ter exatamente as colunas `asset_ref,last_patch_date,review_interval_days`. Datas usam `AAAA-MM-DD`. O intervalo aceito é de 1 a 3660 dias para ajudar a detectar valores digitados incorretamente; ajuste esse limite somente por revisão explícita do código e da política local. Linhas inválidas são contadas, sem expor seu conteúdo.

```python
#!/usr/bin/env python3
"""Summarize patch-review dates from an authorized local CSV inventory."""
import argparse
import csv
from datetime import date
from pathlib import Path
from typing import TextIO


def iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use uma data válida no formato AAAA-MM-DD") from exc


def analyze(stream: TextIO, as_of: date) -> tuple[int, int, int]:
    reader = csv.DictReader(stream, strict=True)
    expected = ["asset_ref", "last_patch_date", "review_interval_days"]
    if reader.fieldnames != expected:
        raise ValueError("cabeçalho esperado: asset_ref,last_patch_date,review_interval_days")

    seen: set[str] = set()
    reviewed = 0
    due = 0
    invalid = 0

    for row in reader:
        if None in row or any(value is None for value in row.values()):
            invalid += 1
            continue

        asset_ref = row["asset_ref"].strip()
        patch_text = row["last_patch_date"].strip()
        interval_text = row["review_interval_days"].strip()
        if not asset_ref or asset_ref in seen:
            invalid += 1
            continue

        try:
            last_patch = date.fromisoformat(patch_text)
            interval = int(interval_text)
        except ValueError:
            invalid += 1
            continue

        if last_patch > as_of or not 1 <= interval <= 3660:
            invalid += 1
            continue

        seen.add(asset_ref)
        reviewed += 1
        if (as_of - last_patch).days > interval:
            due += 1

    return reviewed, due, invalid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path, help="CSV local de ativos autorizados")
    parser.add_argument(
        "--as-of",
        type=iso_date,
        default=date.today(),
        help="data de referência AAAA-MM-DD (padrão: data local de hoje)",
    )
    args = parser.parse_args()
    if not args.inventory.is_file():
        parser.error("informe um arquivo local existente")

    try:
        with args.inventory.open("r", encoding="utf-8", newline="") as stream:
            reviewed, due, invalid = analyze(stream, args.as_of)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        parser.error(f"não foi possível processar um CSV válido: {exc}")

    print(f"data de referência: {args.as_of.isoformat()}")
    print(f"ativos válidos revisados: {reviewed}")
    print(f"fora do intervalo declarado e para revisão: {due}")
    print(f"linhas inválidas ou duplicadas: {invalid}")

    if invalid:
        return 2
    return 1 if due else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste com um arquivo descartável e apenas dados fictícios:

```bash
cat > /tmp/patch-cycle-lab.csv <<'EOF'
asset_ref,last_patch_date,review_interval_days
LAB-APP-01,2026-07-01,30
LAB-APP-02,2026-09-10,30
LAB-APP-03,2026-08-29,30
EOF
python3 review_patch_cycle.py /tmp/patch-cycle-lab.csv --as-of 2026-09-28
```

A saída esperada informa três ativos válidos, um fora do intervalo declarado e zero linhas inválidas; o processo termina com código `1` para sinalizar revisão humana. O terceiro registro está exatamente no limite de 30 dias e não é contado como vencido, pois a regra usa `idade > intervalo`. O código de saída não representa vulnerabilidade confirmada. Para verificar dados inválidos, use uma cópia sintética com data impossível ou referência repetida; o relatório deve contar a linha inválida sem imprimir seu conteúdo e terminar com código `2`.

## Checklist

- [ ] O inventário pertence à equipe ou há autorização explícita para analisá-lo.
- [ ] O teste inicial usa somente referências e datas fictícias em arquivo local temporário.
- [ ] A política de atualização define intervalos por classe de ativo e tem responsável e aprovação.
- [ ] O inventário é atual, completo e mantido por uma fonte autorizada.
- [ ] O CSV contém apenas as colunas necessárias; não há segredos, dados pessoais ou detalhes desnecessários.
- [ ] Datas, intervalos e duplicatas foram validados antes de interpretar o resumo.
- [ ] Cada item fora do intervalo foi confirmado com a equipe responsável e com a política aplicável.
- [ ] Priorização e instalação de atualizações seguem gestão de mudanças, testes e plano de reversão aprovados.
- [ ] O arquivo, o resultado e eventuais inventários reais permanecem sob os controles de acesso e retenção internos.
- [ ] Nenhum host, rede, serviço externo ou sistema de terceiros foi consultado ou alterado.

## Limitações e próximos passos

Este exemplo analisa somente as datas e intervalos declarados em um CSV simples. Não comprova a instalação de atualizações, não interpreta versões ou avisos de segurança, não considera janelas de manutenção, exceções, dependências ou criticidade e não valida a identidade dos ativos. `date.today()` usa a data local da máquina; para uma revisão reproduzível, informe `--as-of` explicitamente. Um resumo sem itens vencidos não é uma certificação de segurança. Para uso operacional, mantenha inventário e critérios em fontes aprovadas, proteja os dados, investigue inconsistências com revisão humana e faça qualquer atualização por processo autorizado. Não automatize instalação, reinicialização ou alteração de sistemas com base neste exemplo.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `csv`, `datetime`, `argparse` e `pathlib`.
- Política interna de gestão de vulnerabilidades, atualização, inventário e mudanças.

> Esta lição revisa localmente dados autorizados. Não ensina varredura, exploração ou acesso a sistemas.

<!-- Testado localmente com Python 3 e CSV sintético. -->
