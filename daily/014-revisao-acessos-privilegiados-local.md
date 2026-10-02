# Dia 014 — Revisão local de acessos privilegiados

Contas com privilégios elevados precisam de revisão periódica e documentada. Este guia mostra como resumir um inventário fictício de revisão de acessos usando somente categorias genéricas e a idade declarada da última revisão. O resumo pode ajudar a priorizar uma análise humana; não decide se um acesso é apropriado nem altera contas.

## Uso autorizado e limitações éticas

Use o exemplo apenas com um arquivo local cuja leitura e tratamento estejam autorizados. Comece com a amostra sintética deste guia. Não inclua nomes de usuários, e-mails, identificadores de conta, equipes, sistemas, hosts, caminhos internos, motivos de concessão, dados pessoais ou segredos — especialmente em arquivos destinados a um repositório público. O formato deliberadamente não aceita identificadores individuais.

O programa lê somente o CSV indicado, não acessa diretórios, serviços ou redes, não consulta provedores de identidade e não modifica nem desativa contas. Ele imprime totais agregados e não revela linhas inválidas. As categorias, o limite demonstrativo de 90 dias e os campos aceitos não constituem uma política universal; defina-os com os responsáveis por segurança, identidade, privacidade e auditoria. Registros agregados não identificam contas específicas a corrigir e não devem ser usados para decisões automáticas.

A presença de uma conta elevada não é, por si só, evidência de abuso: avalie necessidade, proprietário, escopo, aprovação, controles compensatórios e contexto por um processo interno autorizado. Preserve os registros originais de acordo com as regras de acesso, retenção e auditoria; não publique inventários reais.

## Exemplo seguro em Python

Salve como `review_privileged_access.py`. O CSV deve conter exatamente as colunas `tipo,privilegio,estado,dias_desde_revisao`. O código aceita somente valores enumerados e números inteiros entre 0 e 3650. Cada linha representa um registro fictício ou autorizado sem identificador de conta.

```python
#!/usr/bin/env python3
"""Summarize an authorized, identifier-free local access-review CSV."""
import argparse
import csv
import re
from pathlib import Path
from typing import TextIO

FIELDS = ["tipo", "privilegio", "estado", "dias_desde_revisao"]
TYPES = {"pessoa", "servico"}
PRIVILEGES = {"padrao", "elevado"}
STATES = {"ativo", "desativado"}
REVIEW_LIMIT_DAYS = 90
MAX_AGE_DAYS = 3650


def summarize(stream: TextIO) -> dict[str, int]:
    reader = csv.DictReader(stream, strict=True)
    if reader.fieldnames != FIELDS:
        raise ValueError("cabecalho invalido")

    totals = {
        "registros": 0,
        "elevados_ativos": 0,
        "revisoes_vencidas": 0,
        "elevados_desativados": 0,
        "invalidos": 0,
    }
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            totals["invalidos"] += 1
            continue

        kind = row["tipo"].strip()
        privilege = row["privilegio"].strip()
        state = row["estado"].strip()
        age_text = row["dias_desde_revisao"].strip()
        if (
            kind not in TYPES
            or privilege not in PRIVILEGES
            or state not in STATES
            or not re.fullmatch(r"[0-9]{1,4}", age_text)
        ):
            totals["invalidos"] += 1
            continue

        age = int(age_text)
        if age > MAX_AGE_DAYS:
            totals["invalidos"] += 1
            continue

        totals["registros"] += 1
        if privilege == "elevado" and state == "ativo":
            totals["elevados_ativos"] += 1
        if age > REVIEW_LIMIT_DAYS:
            totals["revisoes_vencidas"] += 1
        if privilege == "elevado" and state == "desativado":
            totals["elevados_desativados"] += 1

    return totals


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="CSV local autorizado e sem identificadores")
    args = parser.parse_args()
    if not args.csv_file.is_file():
        parser.error("informe um arquivo CSV local existente")

    try:
        with args.csv_file.open("r", encoding="utf-8", newline="") as stream:
            totals = summarize(stream)
    except (OSError, UnicodeError, csv.Error, ValueError):
        parser.error("não foi possível ler um CSV local válido")

    print(f"registros válidos: {totals['registros']}")
    print(f"acessos elevados ativos: {totals['elevados_ativos']}")
    print(f"revisões acima de 90 dias: {totals['revisoes_vencidas']}")
    print(f"registros elevados desativados: {totals['elevados_desativados']}")
    print(f"registros inválidos: {totals['invalidos']}")

    if totals["invalidos"]:
        return 2
    if totals["revisoes_vencidas"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste com um CSV descartável de dados fictícios:

```bash
cat > /tmp/acessos-ficticios.csv <<'EOF'
tipo,privilegio,estado,dias_desde_revisao
pessoa,elevado,ativo,30
servico,elevado,ativo,140
pessoa,padrao,desativado,20
EOF
python3 review_privileged_access.py /tmp/acessos-ficticios.csv
```

O exemplo imprime três registros válidos, dois acessos elevados ativos, uma revisão com mais de 90 dias, nenhum registro elevado desativado e zero inválidos. O processo retorna `1` porque há uma revisão vencida; esse código apenas sinaliza que há algo a avaliar, não conclui que exista uma violação. Retorna `0` se não houver registros inválidos ou revisões vencidas e `2` se houver linha inválida. O número de acessos elevados ativos é um total para priorização, não uma conclusão sobre sua legitimidade.

## Checklist

- [ ] A revisão foi aprovada, tem escopo, responsáveis e periodicidade definidos.
- [ ] O primeiro teste usa apenas dados fictícios em um CSV temporário local.
- [ ] O arquivo não contém nomes, e-mails, IDs, sistemas, caminhos internos, justificativas, dados pessoais ou segredos.
- [ ] Os campos, categorias, limite de idade e critérios foram aprovados pelos responsáveis pertinentes.
- [ ] Totais são tratados como triagem; decisões sobre acessos são realizadas por pessoas autorizadas e com contexto suficiente.
- [ ] A política interna define como preservar, restringir e reter os registros de origem.
- [ ] Qualquer alteração ou revogação é feita separadamente, por procedimento aprovado, com responsável e trilha de auditoria.
- [ ] A saída agregada não é interpretada como prova de conformidade ou de ausência de abuso.
- [ ] Nenhuma conta foi consultada, modificada ou desativada pelo exemplo.
- [ ] Nenhum serviço externo, sistema de terceiros ou rede foi acessado.

## Limitações e próximos passos

O exemplo valida apenas o cabeçalho, categorias enumeradas e idade declarada; não verifica a origem, completude, autenticidade ou atualidade do inventário, nem confirma que a revisão ocorreu. Como não há identificadores, não detecta duplicatas, não aponta proprietários e não permite corrigir uma conta específica. Não integra um diretório, não autentica revisores e não substitui controles de acesso, auditoria ou uma revisão formal. Ajuste o processo com as equipes responsáveis e execute mudanças somente em sistemas administrados por você ou sob autorização explícita e documentada.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `csv`, `re`, `argparse` e `pathlib`.
- Políticas internas aprovadas de identidade, acesso, privacidade, auditoria e retenção.

> Este exemplo resume apenas metadados locais e agregados; não acessa contas, redes ou serviços e não altera privilégios.

<!-- Testado localmente com Python 3 e CSV sintético. -->
