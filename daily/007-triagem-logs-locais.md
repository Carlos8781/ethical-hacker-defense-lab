# Dia 007 — Triagem defensiva de logs locais

Logs ajudam a detectar atividades que merecem investigação, mas um evento isolado não prova comprometimento. Nesta lição, um script local lê um arquivo JSON Lines (um objeto JSON por linha) com eventos fictícios e contabiliza falhas de autenticação por identificador de conta. Ele emite somente totais agregados, sem imprimir linhas do log ou identificadores. A análise pode apoiar uma triagem autorizada; não substitui a validação com os registros e procedimentos aprovados pela organização.

## Uso autorizado e limitações éticas

Use o exemplo somente com logs locais que você administra ou cujo uso esteja autorizado. O arquivo de demonstração abaixo contém exclusivamente dados fictícios. O script não tenta autenticar, não acessa serviços, não executa comandos, não altera o arquivo e não transmite dados pela rede. Não use dados obtidos sem autorização. Logs podem conter nomes, endereços, horários e outros dados sensíveis; aplique a política de retenção e acesso da organização e prefira dados sintéticos ao testar.

O exemplo conta apenas registros bem formados cujo campo `event` seja `auth_failure` e cujo `account_id` seja um texto não vazio. Eventos desconhecidos não são classificados. Linhas inválidas são contadas sem revelar seu conteúdo. O limiar é uma regra didática configurável, não uma regra universal: falhas legítimas, clientes compartilhados, diferenças de relógio, eventos ausentes e limitações na coleta podem gerar falsos positivos ou deixar incidentes sem detecção. A ferramenta não valida a origem nem a integridade dos logs, não correlaciona eventos entre sistemas e não identifica a causa das falhas.

## Exemplo seguro em Python

Salve o código em `triage_auth_failures.py`. O processamento é somente leitura e mantém os identificadores apenas em memória para fazer a contagem; eles não aparecem na saída.

```python
#!/usr/bin/env python3
"""Count fictional or authorized local authentication-failure log events."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import TextIO


def analyze(stream: TextIO, threshold: int) -> tuple[int, int, int, int]:
    failures_by_account: Counter[str] = Counter()
    valid_rows = 0
    malformed_rows = 0
    failure_events = 0

    for line in stream:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            malformed_rows += 1
            continue

        if not isinstance(record, dict):
            malformed_rows += 1
            continue
        valid_rows += 1

        if record.get("event") != "auth_failure":
            continue
        account_id = record.get("account_id")
        if not isinstance(account_id, str) or not account_id.strip():
            malformed_rows += 1
            continue

        failures_by_account[account_id] += 1
        failure_events += 1

    accounts_over_threshold = sum(
        count >= threshold for count in failures_by_account.values()
    )
    return valid_rows, malformed_rows, failure_events, accounts_over_threshold


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", type=Path, help="arquivo JSON Lines local autorizado")
    parser.add_argument(
        "--threshold", type=int, default=5,
        help="falhas por identificador que geram alerta (padrão: 5)",
    )
    args = parser.parse_args()

    if args.threshold < 1:
        parser.error("--threshold deve ser pelo menos 1")
    if not args.logfile.is_file():
        parser.error("informe um arquivo local existente")

    try:
        with args.logfile.open("r", encoding="utf-8") as stream:
            valid, malformed, failures, alerts = analyze(stream, args.threshold)
    except (OSError, UnicodeError) as exc:
        parser.error(f"não foi possível ler o arquivo: {exc}")

    print(f"registros JSON válidos: {valid}")
    print(f"linhas ou eventos malformados: {malformed}")
    print(f"eventos auth_failure: {failures}")
    print(f"identificadores no limiar ou acima: {alerts}")

    if malformed:
        return 2
    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Crie uma amostra descartável com identificadores inventados e rode o teste local. O limite `3` torna o resultado demonstrativo sem depender de dados reais.

```bash
cat > /tmp/auth-events-lab.jsonl <<'EOF'
{"timestamp":"2026-09-24T12:00:00Z","event":"auth_failure","account_id":"lab-user-a"}
{"timestamp":"2026-09-24T12:01:00Z","event":"auth_failure","account_id":"lab-user-a"}
{"timestamp":"2026-09-24T12:02:00Z","event":"auth_failure","account_id":"lab-user-a"}
{"timestamp":"2026-09-24T12:03:00Z","event":"service_started","account_id":"lab-service"}
EOF
python3 triage_auth_failures.py /tmp/auth-events-lab.jsonl --threshold 3
```

O programa deve mostrar quatro registros JSON válidos, três eventos de falha e um identificador no limiar, sem mostrar `lab-user-a`. O código de saída será `1` para indicar que há um alerta a revisar; isso não comprova ataque ou comprometimento. Com uma amostra sem falhas no limiar, o código de saída será `0`. Uma linha JSON inválida produz um resumo sem revelar a linha e código de saída `2`, para que a qualidade dos dados seja corrigida antes de interpretar o resultado.

## Checklist

- [ ] O arquivo analisado pertence à equipe ou está coberto por autorização explícita.
- [ ] O teste inicial usou somente eventos sintéticos e identificadores fictícios.
- [ ] A ferramenta foi executada localmente; não houve conexão a serviços ou destinos externos.
- [ ] O limiar foi escolhido conforme a política e o contexto do sistema, não tratado como prova de incidente.
- [ ] Linhas malformadas e eventos ausentes foram considerados antes de interpretar o resumo.
- [ ] Os totais foram comparados com fontes e alertas aprovados, sem publicar conteúdo bruto dos logs.
- [ ] O arquivo, sua cópia de teste e os resultados foram mantidos conforme controles de acesso e retenção.
- [ ] Nenhuma credencial, segredo, dado pessoal real ou log de terceiro foi incluído no teste ou compartilhado.
- [ ] Alertas foram encaminhados pelo processo de resposta a incidentes da organização.

## Limitações e próximos passos

Um contador simples é adequado apenas para uma demonstração e para triagem inicial de dados locais autorizados. Em uso operacional, prefira a plataforma de logs aprovada pela organização, preserve a cadeia de custódia quando necessária e correlacione eventos com contexto confiável, como janela de manutenção e histórico de mudanças. Restrinja o acesso aos dados, sincronize relógios por meios aprovados, mantenha retenção documentada e investigue alertas segundo o plano de resposta a incidentes. Não bloqueie contas nem altere configurações automaticamente com base neste exemplo.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `json`, `argparse` e `collections.Counter`.
- Política interna de logging, privacidade, retenção e resposta a incidentes.
- Procedimentos aprovados para preservar e investigar logs dos sistemas administrados.

> O objetivo desta lição é resumir eventos fictícios ou autorizados para apoiar uma revisão humana, não testar credenciais nem investigar sistemas de terceiros.

<!-- Testado localmente com Python 3.12 em eventos fictícios. -->
