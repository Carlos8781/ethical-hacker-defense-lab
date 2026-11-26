# Dia 068 — Validação local de política de capacidade para logs

Uma política de capacidade bem definida ajuda a evitar que logs importantes parem de ser registrados por falta de espaço. Esta revisão verifica, offline, se um arquivo JSON de configuração contém limites coerentes para alertas de uso, reserva mínima de espaço e retenção. Ela não mede discos, não altera configurações e não envia alertas; serve como etapa de revisão antes de uma mudança autorizada.

## Exemplo seguro em Python

Salve como `validate_log_policy.py`. O programa lê apenas o arquivo de configuração explicitamente fornecido e valida seus campos. Os valores no exemplo são fictícios.

```python
import json
import sys
from pathlib import Path


def validate(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("a raiz deve ser um objeto JSON")

    required = {"warning_percent", "critical_percent", "minimum_free_gb", "retention_days"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"campos ausentes: {', '.join(sorted(missing))}")

    warning = data["warning_percent"]
    critical = data["critical_percent"]
    free_gb = data["minimum_free_gb"]
    retention = data["retention_days"]
    for name, value in (("warning_percent", warning), ("critical_percent", critical)):
        if type(value) is not int or not 1 <= value <= 99:
            raise ValueError(f"{name} deve ser inteiro entre 1 e 99")
    if warning >= critical:
        raise ValueError("warning_percent deve ser menor que critical_percent")
    if isinstance(free_gb, bool) or not isinstance(free_gb, (int, float)) or free_gb <= 0:
        raise ValueError("minimum_free_gb deve ser número positivo")
    if type(retention) is not int or retention < 1:
        raise ValueError("retention_days deve ser inteiro positivo")

    return [
        f"Revisar alerta preventivo em {warning}% de uso.",
        f"Revisar alerta crítico em {critical}% de uso.",
        f"Reserva mínima configurada: {free_gb:g} GB; retenção: {retention} dias.",
    ]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python3 validate_log_policy.py <politica.json>")
    try:
        for line in validate(Path(sys.argv[1])):
            print(line)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"Política inválida ou ilegível: {exc}")
```

Exemplo de arquivo `politica-demo.json`:

```json
{
  "warning_percent": 70,
  "critical_percent": 90,
  "minimum_free_gb": 5,
  "retention_days": 30
}
```

Execute localmente com `python3 validate_log_policy.py politica-demo.json`. O resultado é uma lista de valores para revisão humana, não uma garantia de que a política atende à capacidade ou às obrigações da organização.

## Limitações e cuidados éticos

- O programa apenas valida a forma e a coerência básica dos valores; não acessa discos, serviços, logs nem infraestrutura externa.
- Limites apropriados dependem do volume de eventos, criticidade, requisitos legais, retenção aprovada e capacidade disponível. Confirme-os com os responsáveis antes de qualquer alteração.
- Use apenas configurações fictícias ou arquivos de sistemas que você administra ou tem autorização explícita para revisar. Não inclua caminhos sensíveis, dados pessoais ou segredos no exemplo ou no repositório.
- Alertas e retenção devem ser implementados por ferramentas e processos aprovados. Não reduza retenção para liberar espaço sem avaliar impacto em auditoria e resposta a incidentes.
- A validação não substitui monitoramento operacional, teste de restauração ou revisão de capacidade; não faz mudanças e não envia dados pela rede.

## Checklist

- [ ] Confirme escopo, autorização, proprietário e finalidade da revisão.
- [ ] Use uma cópia sanitizada ou um arquivo JSON sintético para o primeiro teste.
- [ ] Verifique que o alerta preventivo é inferior ao crítico e que os limites são compatíveis com a política interna.
- [ ] Revise retenção, volume estimado, reserva mínima e processo de arquivamento com a equipe responsável.
- [ ] Trate os resultados como sugestões de revisão; aprove mudanças por gestão de mudanças e teste-as em ambiente controlado.
- [ ] Não publique logs, configurações reais, identificadores internos ou credenciais.

## Teste local

Este teste cria arquivos temporários sintéticos, confirma a aceitação de uma política válida e rejeita limites invertidos. Não usa rede nem altera arquivos preexistentes.

```bash
python3 - <<'PY'
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from validate_log_policy import validate

valid = {
    "warning_percent": 70,
    "critical_percent": 90,
    "minimum_free_gb": 5,
    "retention_days": 30,
}
with TemporaryDirectory() as folder:
    path = Path(folder) / "policy.json"
    path.write_text(json.dumps(valid), encoding="utf-8")
    assert len(validate(path)) == 3
    invalid = {**valid, "warning_percent": 95}
    path.write_text(json.dumps(invalid), encoding="utf-8")
    try:
        validate(path)
    except ValueError as exc:
        assert "menor que" in str(exc)
    else:
        raise AssertionError("limites invertidos deveriam ser rejeitados")
print("Testes sintéticos aprovados.")
PY
```
