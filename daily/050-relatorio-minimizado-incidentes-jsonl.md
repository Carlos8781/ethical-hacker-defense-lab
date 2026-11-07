# Dia 050 — Resumo minimizado de eventos de incidentes

Ao compartilhar uma linha do tempo de incidente para revisão, dados como nomes, endereços, tokens e caminhos internos podem expor pessoas ou a infraestrutura. Uma estratégia mais segura do que tentar reconhecer toda informação sensível é construir a saída a partir de uma lista curta de campos permitidos e valores categóricos conhecidos. Este exemplo demonstra a ideia somente com eventos fictícios embutidos no próprio código.

## Exemplo seguro em Python

Salve como `resumo_incidentes.py` e execute `python3 resumo_incidentes.py`. O programa não lê arquivos, não recebe argumentos, não acessa a rede e não altera o sistema.

```python
import json

# Registros inteiramente fictícios para demonstração.
SAMPLE_EVENTS = [
    {"timestamp": "2026-11-07T12:00:00Z", "category": "login", "outcome": "blocked",
     "username": "alice@example.invalid", "source_ip": "203.0.113.25", "token": "FAKE-DO-NOT-USE"},
    {"timestamp": "2026-11-07T12:05:00Z", "category": "backup", "outcome": "verified",
     "path": "/srv/internal/backup.tar", "operator": "Pessoa Exemplo"},
]

ALLOWED_CATEGORIES = {"login", "backup", "endpoint", "policy"}
ALLOWED_OUTCOMES = {"blocked", "reviewed", "verified", "contained"}


def minimized_summary(events: list[dict[str, str]]) -> list[dict[str, str]]:
    summary = []
    for event in events:
        category = event.get("category")
        outcome = event.get("outcome")
        timestamp = event.get("timestamp")
        # Validar formato e vocabulário antes de copiar para a saída.
        if category not in ALLOWED_CATEGORIES or outcome not in ALLOWED_OUTCOMES:
            continue
        if not isinstance(timestamp, str) or len(timestamp) != 20 or not timestamp.endswith("Z"):
            continue
        summary.append({
            "timestamp": timestamp,
            "category": category,
            "outcome": outcome,
        })
    return summary


if __name__ == "__main__":
    print(json.dumps(minimized_summary(SAMPLE_EVENTS), indent=2, ensure_ascii=False))
```

A saída contém somente `timestamp`, `category` e `outcome`; campos fictícios como `username`, `source_ip`, `token`, `path` e `operator` não são copiados. O uso de um conjunto permitido reduz a chance de expor acidentalmente campos novos, mas não torna automaticamente seguro qualquer dado mantido na saída.

## Limitações e ética

- Use o exemplo tal como fornecido com dados fictícios. Só adapte para registros de um sistema que você administra ou para os quais tenha autorização explícita, seguindo a política de privacidade e retenção da organização.
- O filtro valida apenas um vocabulário simples e uma forma superficial de timestamp; não confirma datas válidas, causalidade, fuso horário, integridade ou completude dos eventos.
- Mesmo os campos permitidos podem revelar atividade, horários ou detalhes operacionais. Faça avaliação de privacidade e controle de acesso antes de compartilhar qualquer resumo.
- Eventos inválidos são omitidos silenciosamente neste exemplo. Em um fluxo operacional, conte e investigue rejeições sem registrar os valores descartados; não interprete saída parcial como relatório completo.
- A saída é um resumo para revisão, não evidência forense nem substituto de logs originais protegidos. Preserve evidências de acordo com os procedimentos autorizados.
- Nunca inclua segredos, dados pessoais reais ou indicadores de terceiros em exemplos, commits, issues ou relatórios públicos.

## Checklist

- [ ] Executei a amostra fictícia e confirmei que somente os três campos permitidos aparecem.
- [ ] Confirmei que nomes, IPs, caminhos e tokens não são copiados para o resumo.
- [ ] Se adaptei o código, tenho autorização e apliquei as políticas de privacidade e retenção pertinentes.
- [ ] Tratei a saída como parcial e não a confundi com evidência completa ou validação forense.
- [ ] Revisei a saída para evitar exposição de dados pessoais, segredos ou informações internas antes de compartilhá-la.
