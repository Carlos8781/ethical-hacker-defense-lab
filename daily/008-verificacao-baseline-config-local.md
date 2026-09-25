# Dia 008 — Verificação local de baseline de hardening

Uma baseline documenta valores aprovados para configurações relevantes de um sistema administrado, como modo de depuração e registro de auditoria. Comparar um arquivo de configuração local com uma baseline versionada pode revelar desvios que merecem revisão humana. Nesta lição, um programa Python compara somente as chaves de nível superior declaradas na baseline e informa os nomes ausentes ou divergentes — nunca imprime os valores configurados.

## Uso autorizado e limitações éticas

Use o exemplo apenas com arquivos locais que você administra ou cujo uso esteja autorizado. O teste abaixo usa arquivos fictícios; o script não acessa a rede, não invoca comandos, não altera os arquivos e não tenta autenticar ou contornar controles. Não use configurações obtidas sem autorização.

Uma baseline deve ser aprovada e mantida pela equipe responsável: os valores do exemplo não são uma política universal. Arquivos de configuração podem conter segredos ou dados sensíveis; embora o programa não imprima os valores, ele os lê em memória. Para testes e revisão, prefira amostras sintéticas ou cópias sanitizadas, limite permissões de acesso e não compartilhe configurações reais sem autorização.

O comparador verifica apenas as chaves presentes na baseline, no nível superior do objeto JSON. Ele não confirma se a aplicação realmente carregou o arquivo, não avalia controles fora do JSON, não verifica a procedência ou integridade da baseline, e não distingue um desvio malicioso de uma mudança aprovada ainda não incorporada. Chaves extras no arquivo atual são ignoradas. Um resultado sem divergências não prova que o sistema esteja seguro; cada achado exige validação contra a política e o contexto do ativo.

## Exemplo seguro em Python

Salve como `compare_baseline.py`. O modo é somente leitura; a saída contém o resultado e nomes de chaves, não os valores encontrados.

```python
#!/usr/bin/env python3
"""Compare an authorized local JSON configuration with an approved baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("a raiz do JSON precisa ser um objeto")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="baseline JSON local aprovada")
    parser.add_argument("current", type=Path, help="configuração JSON local autorizada")
    args = parser.parse_args()

    try:
        baseline = load_object(args.baseline)
        current = load_object(args.current)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        parser.error(f"não foi possível ler objetos JSON válidos: {exc}")

    if not baseline:
        parser.error("a baseline precisa declarar ao menos uma chave")

    missing = sorted(key for key in baseline if key not in current)
    changed = sorted(
        key for key in baseline.keys() & current.keys()
        if baseline[key] != current[key]
    )

    if not missing and not changed:
        print(f"chaves da baseline verificadas: {len(baseline)}")
        print("nenhuma divergência nas chaves declaradas")
        return 0

    print(f"chaves da baseline verificadas: {len(baseline)}")
    print(f"chaves ausentes: {len(missing)}")
    for key in missing:
        print(f"AUSENTE {key}")
    print(f"chaves divergentes: {len(changed)}")
    for key in changed:
        print(f"DIVERGÊNCIA {key}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste em um diretório descartável com valores fictícios. Neste exemplo, `debug` diverge da baseline e deve ser revisado; não é uma instrução para alterar um sistema real.

```bash
mkdir -p /tmp/config-baseline-lab
cat > /tmp/config-baseline-lab/approved.json <<'EOF'
{"debug":false,"updates_enabled":true,"audit_logging":true}
EOF
cat > /tmp/config-baseline-lab/current.json <<'EOF'
{"debug":true,"updates_enabled":true,"audit_logging":true,"lab_note":"sample"}
EOF
python3 compare_baseline.py /tmp/config-baseline-lab/approved.json /tmp/config-baseline-lab/current.json
```

A saída deve indicar três chaves verificadas e `DIVERGÊNCIA debug`, sem imprimir `true` ou `false`. O código de saída `1` significa que há um item a revisar, não que houve ataque ou comprometimento. Para o teste sem divergências, use uma cópia sintética em que as três chaves da baseline correspondam; a ferramenta deve terminar com código `0`. Chaves extras, como `lab_note`, não são avaliadas.

## Checklist

- [ ] Os dois arquivos pertencem à equipe ou há autorização explícita para analisá-los.
- [ ] O primeiro teste foi feito com JSON sintético e valores fictícios em diretório local descartável.
- [ ] A baseline tem aprovação, responsável e processo de revisão documentados.
- [ ] Os nomes das chaves são adequados para aparecer em uma saída de auditoria.
- [ ] Nenhum segredo, dado pessoal ou configuração de terceiros foi colocado no teste ou compartilhado.
- [ ] Cada divergência foi validada com a política aplicável e com o responsável pelo sistema.
- [ ] Mudanças corretivas serão feitas separadamente, por pessoa autorizada, com revisão e plano de reversão.
- [ ] A saída e os arquivos reais, se usados, permanecem sob os controles de acesso e retenção da organização.
- [ ] O resultado não foi tratado como prova de segurança, exploração ou comprometimento.

## Limitações e próximos passos

Este exemplo é adequado apenas a JSON simples e comparação exata de valores. Ele não entende comentários, herança, variáveis de ambiente, precedência entre arquivos ou a semântica específica de cada aplicação. Para uso operacional, defina baselines por função do ativo, registre aprovações e exceções, proteja o repositório e os arquivos de configuração, e use uma ferramenta de gestão de configuração aprovada quando for preciso monitoramento contínuo. Não aplique correções automaticamente com base neste relatório.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `json`, `argparse` e `pathlib`.
- Política de hardening, gestão de configuração e controle de mudanças da própria organização.

> A finalidade desta lição é apoiar a revisão de configurações autorizadas em sistemas administrados, não obter acesso a sistemas ou informações de terceiros.

<!-- Testado localmente com Python 3 em JSON sintético. -->
