# Dia 009 — Revisão local da cobertura de MFA

Uma revisão periódica do inventário de identidades pode ajudar a equipe responsável a localizar registros que precisam de acompanhamento quanto à autenticação multifator (MFA). Esta lição apresenta um verificador local de CSV que conta registros habilitados e desabilitados sem mostrar os identificadores. Os dados de demonstração são fictícios; o script não se conecta a provedores de identidade nem modifica contas.

## Uso autorizado e limitações éticas

Use o exemplo somente com um inventário que sua equipe administra e cujo uso esteja autorizado. Para aprender e testar, use a amostra sintética abaixo; não copie para o repositório nem compartilhe inventários reais, nomes de usuários ou outros dados pessoais. O programa é somente leitura, não acessa a rede, não autentica, não altera configurações e não executa comandos. Identificadores são mantidos temporariamente em memória para detectar duplicatas, mas não aparecem na saída.

O relatório avalia apenas o campo `mfa_enabled` fornecido no CSV. Não comprova que um provedor esteja aplicando a política, que fatores cadastrados funcionem, nem que a MFA seja resistente a phishing. Um inventário desatualizado, incompleto ou incorreto pode produzir conclusões erradas. Contas de serviço, emergência ou outras exceções podem ter políticas aprovadas próprias; não trate uma contagem como ordem para habilitar ou desabilitar contas. Revise resultados com a equipe responsável e siga o processo de gestão de mudanças.

## Exemplo seguro em Python

Salve como `review_mfa_inventory.py`. O formato esperado é exatamente o cabeçalho `account_id,mfa_enabled`, com estado `true` ou `false` por linha. O script exige identificadores não vazios e únicos; linhas inválidas são contabilizadas, sem imprimir seu conteúdo.

```python
#!/usr/bin/env python3
"""Summarize MFA status in an authorized local CSV inventory."""
import argparse
import csv
from pathlib import Path
from typing import TextIO


def analyze(stream: TextIO) -> tuple[int, int, int, int]:
    reader = csv.DictReader(stream, strict=True)
    if reader.fieldnames != ["account_id", "mfa_enabled"]:
        raise ValueError("cabeçalho esperado: account_id,mfa_enabled")

    seen_ids: set[str] = set()
    enabled = 0
    disabled = 0
    invalid = 0

    for row in reader:
        account_id = row.get("account_id")
        status = row.get("mfa_enabled")
        if (
            None in row
            or not isinstance(account_id, str)
            or not account_id.strip()
            or not isinstance(status, str)
            or status.strip().lower() not in {"true", "false"}
        ):
            invalid += 1
            continue

        account_id = account_id.strip()
        if account_id in seen_ids:
            invalid += 1
            continue
        seen_ids.add(account_id)

        if status.strip().lower() == "true":
            enabled += 1
        else:
            disabled += 1

    return enabled + disabled, enabled, disabled, invalid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path, help="inventário CSV local autorizado")
    args = parser.parse_args()
    if not args.inventory.is_file():
        parser.error("informe um arquivo local existente")

    try:
        with args.inventory.open("r", encoding="utf-8", newline="") as stream:
            total, enabled, disabled, invalid = analyze(stream)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        parser.error(f"não foi possível processar um CSV válido: {exc}")

    print(f"registros válidos: {total}")
    print(f"MFA habilitada no inventário: {enabled}")
    print(f"MFA desabilitada no inventário: {disabled}")
    print(f"linhas inválidas ou duplicadas: {invalid}")

    if invalid:
        return 2
    return 1 if disabled else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Crie um arquivo temporário com dados inventados e execute localmente:

```bash
cat > /tmp/mfa-inventory-lab.csv <<'EOF'
account_id,mfa_enabled
lab-admin-01,true
lab-user-02,false
lab-service-03,false
EOF
python3 review_mfa_inventory.py /tmp/mfa-inventory-lab.csv
```

A saída esperada é de três registros válidos, um com MFA habilitada, dois desabilitados e zero linhas inválidas. O programa termina com código `1` porque há registros desabilitados a revisar; isso não prova uma falha de segurança. Uma planilha vazia ou uma linha inválida deve ser tratada como problema de qualidade do inventário, não como autorização para alterar contas.

## Checklist

- [ ] O inventário pertence à equipe ou há autorização explícita para analisá-lo.
- [ ] O teste inicial usou somente identificadores e estados fictícios em arquivo local temporário.
- [ ] O arquivo contém apenas as colunas necessárias; segredos e dados pessoais desnecessários foram removidos.
- [ ] O CSV está atualizado, completo e conciliado com uma fonte aprovada de inventário.
- [ ] Linhas inválidas e duplicadas foram resolvidas antes de interpretar as contagens.
- [ ] Exceções para contas de serviço ou emergência foram validadas com os responsáveis e documentadas.
- [ ] A política da organização define os fatores aceitos e o tratamento de exceções.
- [ ] A saída agregada foi compartilhada somente com pessoas autorizadas, conforme retenção e privacidade internas.
- [ ] Qualquer alteração de MFA será feita por administrador autorizado, com aprovação, registro e plano de reversão.
- [ ] Nenhuma conta, credencial, provedor ou sistema externo foi acessado ou modificado pelo exemplo.

## Limitações e próximos passos

Este exemplo verifica apenas a consistência de um CSV local e a classificação textual `true`/`false`. Não valida origem, atualidade, completude ou integridade criptográfica do inventário; tampouco consulta políticas, sessões, métodos registrados ou eventos do provedor. Um código de saída zero significa somente que não havia linhas inválidas ou registros marcados como desabilitados nos dados fornecidos. Para uso operacional, use relatórios e APIs aprovados pela organização com escopo mínimo e autorização documentada, proteja os dados conforme a política de privacidade e faça a revisão humana antes de qualquer mudança. Não automatize bloqueios ou alterações de conta com base neste exemplo.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `csv`, `argparse` e `pathlib`.
- Política interna de identidade, MFA, exceções, privacidade e gestão de mudanças.
- Procedimentos aprovados pelo provedor de identidade administrado pela organização.

> Esta lição ajuda a revisar localmente um inventário autorizado. Não ensina a testar credenciais, enumerar contas externas ou acessar serviços.

<!-- Testado localmente com Python 3 em CSV sintético. -->
