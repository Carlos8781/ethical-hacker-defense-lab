# Dia 061 — Validação local de objetivos de recuperação (RTO/RPO)

Um exercício de restauração só é útil se seus resultados forem comparados com metas aprovadas. Este exemplo analisa um registro JSON local de um teste de recuperação e calcula o tempo de indisponibilidade observado (RTO medido) e a idade do último backup no momento do incidente (RPO medido). Use horários com fuso explícito e registros sintéticos ou sanitizados; não é uma ferramenta de backup nem executa restaurações.

## Exemplo seguro em Python

Salve como `review_recovery.py`. O arquivo JSON local deve ter `incident_at`, `service_restored_at`, `last_backup_at`, `rto_target_minutes` e `rpo_target_minutes`; os horários devem ser ISO 8601, por exemplo `2026-01-15T10:30:00+00:00`.

```python
import json
import sys
from datetime import datetime
from pathlib import Path


def parse_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("horário deve ser texto ISO 8601")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("horário precisa incluir fuso horário")
    return parsed


def review(record: dict) -> list[str]:
    incident = parse_time(record["incident_at"])
    restored = parse_time(record["service_restored_at"])
    backup = parse_time(record["last_backup_at"])
    rto_target = record["rto_target_minutes"]
    rpo_target = record["rpo_target_minutes"]
    if any(type(x) not in (int, float) or x < 0 for x in (rto_target, rpo_target)):
        raise ValueError("metas RTO/RPO devem ser números não negativos")
    if restored < incident or backup > incident:
        raise ValueError("cronologia inconsistente no registro")

    rto = (restored - incident).total_seconds() / 60
    rpo = (incident - backup).total_seconds() / 60
    results = [f"RTO medido: {rto:.1f} min (meta: {rto_target:g} min)",
               f"RPO medido: {rpo:.1f} min (meta: {rpo_target:g} min)"]
    results.append("RTO dentro da meta." if rto <= rto_target else "Revisar: RTO excedeu a meta.")
    results.append("RPO dentro da meta." if rpo <= rpo_target else "Revisar: RPO excedeu a meta.")
    return results


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python3 review_recovery.py <registro-json-local>")
        return 2
    try:
        record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("a raiz do JSON deve ser um objeto")
        print("\n".join(review(record)))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"Registro inválido: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

## Limitações e cuidados éticos

- Utilize somente registros de exercícios ou serviços que você administra ou cuja revisão foi explicitamente autorizada; prefira dados fictícios ou sanitizados.
- O cálculo depende dos horários informados e não verifica a integridade do backup, a consistência dos dados restaurados, a disponibilidade real do serviço nem o cumprimento de controles de segurança.
- RTO e RPO são metas definidas pela organização. Confirme definições, fusos, relógios e critérios de início/fim com os responsáveis antes de interpretar os resultados.
- O exemplo lê um arquivo local, não usa rede, não acessa credenciais e não inicia nem modifica backups ou serviços.
- Não inclua neste repositório nomes internos, dados de clientes, detalhes operacionais confidenciais ou segredos.

## Checklist

- [ ] Confirme autorização e utilize somente dados fictícios ou sanitizados.
- [ ] Valide que as metas RTO/RPO refletem a política aprovada para o serviço.
- [ ] Confirme horários ISO 8601 com fuso e a cronologia do exercício.
- [ ] Execute o script localmente e compare os resultados com evidências revisadas por responsáveis.
- [ ] Investigue desvios e documente ações corretivas no processo interno aprovado.
- [ ] Não trate o resultado como prova de que o backup é íntegro ou recuperável.
- [ ] Revise o arquivo antes de compartilhá-lo e remova qualquer informação sensível.

## Teste local

O teste usa somente dados sintéticos em memória e verifica tanto o cálculo aprovado quanto a rejeição de cronologia inconsistente:

```bash
python3 - <<'PY'
from datetime import datetime
from review_recovery import review

fixture = {
    "incident_at": "2026-01-15T10:00:00+00:00",
    "service_restored_at": "2026-01-15T10:40:00+00:00",
    "last_backup_at": "2026-01-15T09:50:00+00:00",
    "rto_target_minutes": 60,
    "rpo_target_minutes": 15,
}
result = review(fixture)
assert "RTO dentro da meta." in result
assert "RPO dentro da meta." in result
fixture["last_backup_at"] = "2026-01-15T10:01:00+00:00"
try:
    review(fixture)
except ValueError:
    pass
else:
    raise AssertionError("cronologia inválida deveria ser rejeitada")
print("Testes sintéticos aprovados.")
PY
```
