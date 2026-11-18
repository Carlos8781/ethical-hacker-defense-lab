# Dia 060 — Revisão offline de proteção de branch

Uma exportação local de configuração de proteção de branch pode ser revisada antes de adotar uma política ou durante uma auditoria autorizada. Este guia verifica requisitos defensivos comuns em um arquivo JSON: exigência de revisões por pull request, verificações de status obrigatórias e aplicação das regras também a administradores. O programa não consulta o GitHub, não altera políticas e não tenta acessar repositórios.

## Exemplo seguro em Python

Salve como `review_branch_protection.py` e execute `python3 review_branch_protection.py caminho/para/politica.json`. O exemplo espera um objeto JSON no formato de uma exportação sanitizada com as chaves `required_pull_request_reviews`, `required_status_checks` e `enforce_admins`. Ajuste as expectativas à política aprovada pela sua organização.

```python
import json
import sys
from pathlib import Path


def review(path: Path) -> list[str]:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ["Não foi possível ler um arquivo JSON local válido."]
    if not isinstance(policy, dict):
        return ["A raiz do JSON deve ser um objeto."]

    findings: list[str] = []
    reviews = policy.get("required_pull_request_reviews")
    if not isinstance(reviews, dict):
        findings.append("Revisar: revisões por pull request não estão configuradas.")
    elif not isinstance(reviews.get("required_approving_review_count"), int) or reviews["required_approving_review_count"] < 1:
        findings.append("Revisar: exigir ao menos uma aprovação antes do merge.")

    checks = policy.get("required_status_checks")
    if not isinstance(checks, dict):
        findings.append("Revisar: verificações de status obrigatórias não estão configuradas.")
    elif not checks.get("contexts") and not checks.get("checks"):
        findings.append("Revisar: nenhuma verificação de status foi listada.")

    admins = policy.get("enforce_admins")
    if not isinstance(admins, dict) or admins.get("enabled") is not True:
        findings.append("Revisar: confirme a aplicação das regras também a administradores.")

    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python3 review_branch_protection.py <arquivo-json-local>")
        return 2
    findings = review(Path(sys.argv[1]))
    if findings:
        for finding in findings:
            print(finding)
        return 1
    print("Controles básicos presentes; confirme a política com a equipe responsável.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Limitações e cuidados éticos

- Use somente exportações de configurações de organizações ou repositórios que você administra ou para os quais tem autorização explícita.
- O verificador analisa apenas algumas chaves locais e não confirma que o arquivo representa a configuração atual, que as verificações são eficazes, nem que todos os controles recomendados estão presentes.
- O formato de exportação pode variar. Compare a estrutura com uma cópia sanitizada obtida por um processo aprovado, sem incluir tokens ou dados privados neste guia.
- Uma aprovação sintática não substitui revisão humana, avaliação de risco ou processo formal de mudança. Aplique políticas somente com autorização e por canais aprovados.
- O código não usa rede, não enumera repositórios, não acessa credenciais e não modifica configurações.

## Checklist

- [ ] Confirme a autorização para revisar a política e a origem da exportação.
- [ ] Remova tokens, nomes privados, URLs internas e outros dados sensíveis antes de compartilhar o JSON.
- [ ] Verifique se revisões por pull request exigem pelo menos uma aprovação.
- [ ] Confirme que as verificações de status obrigatórias correspondem aos controles aprovados pela equipe.
- [ ] Decida formalmente se as regras devem aplicar-se também a administradores; não altere essa configuração sem aprovação.
- [ ] Execute o exemplo apenas sobre um arquivo local sanitizado e dados fictícios.
- [ ] Trate os resultados como alertas para revisão, não como garantia de segurança ou conformidade.

## Teste local

Este teste usa somente arquivos JSON sintéticos em um diretório temporário. Salve o código acima como `review_branch_protection.py` e execute:

```bash
python3 - <<'PY'
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from review_branch_protection import review

with TemporaryDirectory() as directory:
    path = Path(directory) / "policy.json"
    path.write_text(json.dumps({
        "required_pull_request_reviews": {"required_approving_review_count": 1},
        "required_status_checks": {"contexts": ["ci"]},
        "enforce_admins": {"enabled": True},
    }), encoding="utf-8")
    assert review(path) == []
    path.write_text(json.dumps({
        "required_pull_request_reviews": {"required_approving_review_count": 0},
        "required_status_checks": {"contexts": []},
        "enforce_admins": {"enabled": False},
    }), encoding="utf-8")
    assert len(review(path)) == 3
print("Testes sintéticos aprovados.")
PY
```
