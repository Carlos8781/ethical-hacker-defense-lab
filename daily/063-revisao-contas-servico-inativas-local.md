# Dia 063 — Revisão local de contas de serviço sem uso recente

Contas de serviço esquecidas ou sem responsável claro podem ampliar o risco operacional. Uma revisão periódica de um inventário exportado e autorizado ajuda a identificar registros habilitados sem data de uso recente ou sem responsável. Este exemplo analisa um CSV local, não consulta sistemas, não autentica, não altera nem desativa contas.

## Exemplo seguro em Python

Salve como `review_service_accounts.py`. O CSV deve ter as colunas `account_id`, `account_type`, `enabled`, `last_used_utc` e `owner`. Use exclusivamente dados fictícios ou uma exportação sanitizada obtida com autorização; não inclua senhas, tokens, chaves ou outros segredos.

```python
import csv
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REQUIRED = {"account_id", "account_type", "enabled", "last_used_utc", "owner"}


def review(path: Path, today: date, stale_days: int = 90) -> list[str]:
    if stale_days < 1:
        raise ValueError("stale_days deve ser positivo")
    findings = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError("CSV sem todas as colunas obrigatórias")
        for line, row in enumerate(reader, start=2):
            account_id = (row.get("account_id") or "").strip()
            kind = (row.get("account_type") or "").strip().lower()
            enabled = (row.get("enabled") or "").strip().lower()
            last_used = (row.get("last_used_utc") or "").strip()
            owner = (row.get("owner") or "").strip()
            if not account_id or enabled not in {"true", "false"}:
                raise ValueError(f"linha {line}: identificador ou enabled inválido")
            if kind != "service" or enabled != "true":
                continue
            if not owner:
                findings.append(f"{account_id}: responsável ausente")
            if not last_used:
                findings.append(f"{account_id}: último uso não registrado")
                continue
            try:
                used = datetime.strptime(last_used, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError(f"linha {line}: last_used_utc deve usar AAAA-MM-DD") from exc
            age = (today - used).days
            if age < 0:
                raise ValueError(f"linha {line}: data de uso está no futuro")
            if age >= stale_days:
                findings.append(f"{account_id}: sem uso há {age} dias")
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python3 review_service_accounts.py <inventario.csv>")
        return 2
    try:
        results = review(Path(sys.argv[1]), datetime.now(timezone.utc).date())
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"Não foi possível revisar o inventário: {exc}")
        return 2
    print("\n".join(results) if results else "Nenhuma observação para revisão.")
    return 1 if results else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

O campo `last_used_utc` neste exemplo é uma data em UTC no formato `AAAA-MM-DD`; o nome não implica verificação independente da origem do registro.

## Limitações e cuidados éticos

- Execute somente sobre uma exportação local cuja consulta e revisão estejam autorizadas. Prefira registros sintéticos ou sanitizados e proteja a exportação conforme a política interna.
- O resultado é triagem, não prova de que uma conta está abandonada ou comprometida. Processos sazonais, recuperação de desastres e dependências indiretas podem explicar longos períodos sem uso.
- Confirme cada observação com o proprietário do serviço e o processo de gestão de acessos. Não desative, exclua ou altere contas automaticamente com base neste relatório.
- O script não conecta a serviços, não lê credenciais e não modifica o CSV. A saída inclui identificadores: trate-a como informação potencialmente sensível e não a publique sem sanitização.
- A janela de 90 dias é apenas um exemplo; adote limites aprovados pela organização e valide fuso horário, qualidade e atualidade da exportação.

## Checklist

- [ ] Confirme autorização, escopo e responsável pela exportação local.
- [ ] Remova segredos e dados pessoais desnecessários; use identificadores fictícios no teste.
- [ ] Valide as colunas, a data de geração e a semântica dos campos com a equipe responsável.
- [ ] Escolha um limite de inatividade aprovado, considerando serviços sazonais e de contingência.
- [ ] Execute a revisão em cópia local e proteja o relatório gerado.
- [ ] Investigue cada apontamento com o responsável antes de qualquer mudança de acesso.
- [ ] Registre decisões pelo processo de auditoria da organização e descarte cópias conforme a política de retenção.

## Teste local

Este teste cria um inventário sintético temporário, testa sinalização de conta antiga e responsável ausente, e confirma a rejeição de data inválida. Não acessa rede ou contas reais:

```bash
python3 - <<'PY'
import csv
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from review_service_accounts import review

with TemporaryDirectory() as temp:
    path = Path(temp) / "accounts.csv"
    fields = ["account_id", "account_type", "enabled", "last_used_utc", "owner"]
    rows = [
        {"account_id": "svc-demo-1", "account_type": "service", "enabled": "true", "last_used_utc": "2025-01-01", "owner": "Equipe Demo"},
        {"account_id": "svc-demo-2", "account_type": "service", "enabled": "true", "last_used_utc": "", "owner": ""},
        {"account_id": "user-demo", "account_type": "human", "enabled": "true", "last_used_utc": "2020-01-01", "owner": "Equipe Demo"},
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    findings = review(path, date(2025, 4, 1))
    assert "svc-demo-1: sem uso há 90 dias" in findings
    assert "svc-demo-2: responsável ausente" in findings
    assert "svc-demo-2: último uso não registrado" in findings
    assert not any("user-demo" in item for item in findings)

    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"account_id": "svc-demo-3", "account_type": "service", "enabled": "true", "last_used_utc": "data-invalida", "owner": "Equipe Demo"})
    try:
        review(path, date(2025, 4, 1))
    except ValueError:
        pass
    else:
        raise AssertionError("data inválida deveria ser rejeitada")
print("Testes sintéticos aprovados.")
PY
```
