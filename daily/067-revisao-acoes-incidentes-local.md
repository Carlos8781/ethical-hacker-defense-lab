# Dia 067 — Revisão local de ações de resposta a incidentes

Uma lista estruturada de ações ajuda a equipe a acompanhar melhorias após um exercício ou incidente autorizado. Uma revisão local pode apontar registros incompletos, estados inválidos e prazos vencidos para triagem humana. O exemplo abaixo lê somente um arquivo JSON local e não executa ações, contata sistemas ou altera os dados.

## Exemplo seguro em Python

Salve como `review_actions.py`. O JSON deve conter uma lista `actions`; cada ação usa `id`, `owner`, `status` e `due_date` (`AAAA-MM-DD`). Os valores de estado aceitos são `open`, `in_progress` e `done`. Use registros fictícios ou exportações sanitizadas sob sua administração.

```python
import json
import sys
from datetime import date
from pathlib import Path

ALLOWED_STATUSES = {"open", "in_progress", "done"}
REQUIRED_FIELDS = {"id", "owner", "status", "due_date"}


def review(path: Path, as_of: date) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("actions"), list):
        raise ValueError("esperado objeto JSON com lista 'actions'")

    findings: list[str] = []
    seen_ids: set[str] = set()
    for number, action in enumerate(data["actions"], start=1):
        if not isinstance(action, dict):
            raise ValueError(f"ação {number} deve ser um objeto")
        missing = REQUIRED_FIELDS - action.keys()
        if missing:
            raise ValueError(f"ação {number} sem campos obrigatórios: {', '.join(sorted(missing))}")

        action_id, owner, status = action["id"], action["owner"], action["status"]
        if not all(isinstance(value, str) and value.strip() for value in (action_id, owner)):
            raise ValueError(f"ação {number}: id e owner devem ser textos não vazios")
        if action_id in seen_ids:
            raise ValueError(f"id duplicado: {action_id}")
        seen_ids.add(action_id)
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"ação {action_id}: estado inválido")
        try:
            due = date.fromisoformat(action["due_date"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"ação {action_id}: due_date deve usar AAAA-MM-DD") from exc

        if status != "done" and due < as_of:
            findings.append(f"{action_id}: prazo vencido; revisar com {owner}")
    return findings


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python3 review_actions.py <acoes.json> <data-referencia-AAAA-MM-DD>")
        return 2
    try:
        as_of = date.fromisoformat(sys.argv[2])
        findings = review(Path(sys.argv[1]), as_of)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Não foi possível revisar o arquivo: {exc}")
        return 2
    print("\n".join(findings) if findings else "Nenhuma ação vencida encontrada.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Exemplo de execução: `python3 review_actions.py acoes-demo.json 2026-11-25`. A data é explícita para tornar a revisão reproduzível; substitua-a pela data da revisão autorizada.

## Limitações e cuidados éticos

- O programa valida campos e compara datas; não verifica se uma ação foi realmente concluída, se o responsável está correto ou se a recomendação técnica é adequada.
- A data de referência é fornecida por quem executa o script. Confirme fuso horário, calendário e política interna antes de interpretar prazos.
- Use apenas registros de exercícios/incidentes sob sua responsabilidade ou autorização expressa. Prefira dados fictícios ou sanitizados e não inclua credenciais, tokens, dados pessoais ou detalhes sensíveis desnecessários.
- Um prazo vencido é um sinal para revisão humana, não uma avaliação de culpa ou evidência suficiente de falha de segurança. Siga o processo autorizado de resposta a incidentes e gestão de mudanças.
- O exemplo é somente leitura e não se conecta a serviços externos, cria persistência, contorna controles nem executa correções.

## Checklist

- [ ] Confirme autorização, finalidade e proprietário do arquivo local.
- [ ] Minimize e sanitize os dados; remova segredos e informações pessoais desnecessárias.
- [ ] Verifique a data de referência e a convenção de datas usada pela equipe.
- [ ] Execute primeiro o teste com dados sintéticos e confira os registros incompletos ou inválidos.
- [ ] Trate cada resultado como item de triagem; valide contexto e mudanças planejadas com responsáveis autorizados.
- [ ] Registre decisões e correções pelos canais aprovados de resposta a incidentes e gestão de mudanças.

## Teste local

O teste usa um arquivo temporário sintético, confirma a identificação de uma ação vencida e verifica que identificadores duplicados são rejeitados. Não usa rede nem modifica arquivos preexistentes.

```bash
python3 - <<'PY'
import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from review_actions import review

with TemporaryDirectory() as folder:
    path = Path(folder) / "actions.json"
    path.write_text(json.dumps({"actions": [
        {"id": "demo-1", "owner": "Equipe Demo", "status": "open", "due_date": "2026-11-24"},
        {"id": "demo-2", "owner": "Equipe Demo", "status": "done", "due_date": "2026-11-20"},
    ]}), encoding="utf-8")
    assert review(path, date(2026, 11, 25)) == ["demo-1: prazo vencido; revisar com Equipe Demo"]
    path.write_text(json.dumps({"actions": [
        {"id": "same", "owner": "Demo", "status": "open", "due_date": "2026-11-26"},
        {"id": "same", "owner": "Demo", "status": "done", "due_date": "2026-11-26"},
    ]}), encoding="utf-8")
    try:
        review(path, date(2026, 11, 25))
    except ValueError as exc:
        assert "id duplicado" in str(exc)
    else:
        raise AssertionError("ids duplicados deveriam ser rejeitados")
print("Testes sintéticos aprovados.")
PY
```
