# Dia 051 — Revisão local da cobertura de eventos de auditoria JSONL

Uma revisão defensiva de logs pode confirmar se categorias essenciais de eventos aparecem em uma amostra, sem consultar sistemas externos. O exemplo abaixo analisa apenas três linhas JSONL fictícias definidas no próprio programa e compara as categorias encontradas com uma lista esperada. Isso ajuda a identificar lacunas para investigação autorizada; presença de um evento não prova que o registro seja autêntico ou completo.

## Exemplo seguro em Python

Salve como `verificar_cobertura.py` e execute `python3 verificar_cobertura.py`. O programa usa dados fictícios embutidos, não abre arquivos, não recebe argumentos, não acessa a rede e não altera o sistema.

```python
import json
from datetime import datetime

# Eventos totalmente fictícios para um exercício local.
SAMPLE_JSONL = """\
{"timestamp":"2026-11-08T09:00:00Z","category":"auth_success"}
{"timestamp":"2026-11-08T09:05:00Z","category":"policy_change"}
{"timestamp":"2026-11-08T09:10:00Z","category":"backup_result"}
"""

EXPECTED_CATEGORIES = {"auth_success", "policy_change", "backup_result"}


def review_coverage(jsonl: str) -> tuple[set[str], int]:
    found = set()
    valid_records = 0
    for line_number, line in enumerate(jsonl.splitlines(), start=1):
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("registro não é um objeto")
            category = record.get("category")
            timestamp = record.get("timestamp")
            if category not in EXPECTED_CATEGORIES:
                raise ValueError("categoria ausente ou não esperada")
            if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
                raise ValueError("timestamp UTC esperado")
            datetime.fromisoformat(timestamp[:-1] + "+00:00")
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            # Não imprimir a linha: ela pode conter dados sensíveis.
            print(f"Linha {line_number}: registro inválido ({exc}).")
            continue
        found.add(category)
        valid_records += 1

    missing = EXPECTED_CATEGORIES - found
    print(f"Registros válidos: {valid_records}")
    print("Categorias ausentes: " + (", ".join(sorted(missing)) if missing else "nenhuma"))
    return missing, valid_records


if __name__ == "__main__":
    review_coverage(SAMPLE_JSONL)
```

A execução de demonstração deve informar três registros válidos e nenhuma categoria ausente. Em uma revisão real, uma amostra só deve vir de logs sob sua administração e autorização; não copie valores de eventos para mensagens de erro ou relatórios públicos.

## Limitações e ética

- Use a amostra fornecida com dados fictícios. Só adapte o procedimento a logs de sistemas que você administra ou para os quais tenha autorização explícita.
- A lista de categorias é ilustrativa: alinhe-a com a política de auditoria aprovada e documente o período e a fonte da amostra.
- A presença de categorias não comprova que eventos tenham sido gerados, preservados ou ordenados corretamente. Este código não autentica registros, detecta adulteração nem garante completude.
- O exemplo faz validação básica de JSON, categoria e timestamp, mas não valida a semântica dos eventos, a precisão do relógio, duplicatas ou requisitos regulatórios.
- Linhas inválidas são ignoradas após aviso minimizado. Em uso operacional, quantifique falhas sem expor conteúdo e encaminhe-as ao responsável autorizado; nunca trate uma amostra incompleta como prova conclusiva.
- Não use o guia para sondar sistemas, obter logs alheios ou contornar controles. Não publique segredos, dados pessoais reais, endereços ou identificadores de terceiros.

## Checklist

- [ ] Confirmei que a origem dos logs e o escopo da revisão são autorizados.
- [ ] Defini as categorias esperadas segundo a política de auditoria aplicável.
- [ ] Executei primeiro o exemplo apenas com os dados fictícios e confirmei três registros válidos e nenhuma categoria ausente.
- [ ] Investiguei lacunas e linhas rejeitadas sem divulgar o conteúdo bruto dos registros.
- [ ] Registrei período, limitações e responsável, sem tratar a verificação como validação forense ou prova de integridade.
- [ ] Revisei qualquer saída antes de compartilhá-la para evitar segredos, dados pessoais ou informações internas.
