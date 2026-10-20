# Dia 032 — Revisão local de política CORS

## Objetivo

Uma política de compartilhamento de recursos entre origens (CORS) muito permissiva pode ampliar a exposição de dados de uma aplicação web. Esta revisão estática lê um arquivo JSON local com a política declarada, sinaliza origens curinga e a combinação de credenciais habilitadas com origem curinga, sem fazer requisições à aplicação. Use o resultado para revisar a configuração com a equipe responsável antes de qualquer mudança.

## Limites éticos e operacionais

- Analise somente arquivos de configuração fictícios, de laboratório ou de uma aplicação que você administra e tem autorização explícita para revisar.
- O exemplo lê apenas o arquivo local informado, não acessa rede, não faz varredura, não altera arquivos e não tenta contornar políticas de navegador ou controles de acesso.
- A ferramenta espera um JSON com as chaves `allowed_origins` (lista de strings) e `allow_credentials` (booleano). Ela não interpreta todos os formatos de frameworks ou proxies; converta apenas uma cópia segura para esse formato.
- `*` é sinalizado para revisão. A combinação `*` e credenciais também é sinalizada como configuração que exige correção conforme a especificação e a política da aplicação. Origens amplas, curingas em subdomínios e regras de middleware podem exigir avaliação manual adicional.
- Um resultado sem alertas não prova que a configuração efetiva em produção seja segura: outra camada pode sobrescrever a política, e o script não avalia autenticação, autorização, cookies, cabeçalhos ou comportamento do navegador.
- Não copie para o arquivo de exemplo tokens, cookies, cabeçalhos de autenticação, domínios privados ou dados de usuários. Não publique configurações internas; use somente dados fictícios no teste e no repositório.

## Exemplo seguro em Python

Salve como `review_cors_policy.py`. O script aceita somente JSON local limitado a 64 KiB; mostra apenas nomes de verificações e contagens, nunca os valores de origem fornecidos.

```python
#!/usr/bin/env python3
"""Sinaliza aspectos de uma política CORS em JSON local autorizado."""
import argparse
import json
import sys
from pathlib import Path

MAX_BYTES = 64 * 1024


def review(path: Path) -> tuple[int, list[str]]:
    if path.is_symlink():
        return 2, ["links simbólicos não são aceitos"]
    try:
        raw = path.read_bytes()
    except OSError:
        return 2, ["não foi possível ler o arquivo local"]
    if len(raw) > MAX_BYTES:
        return 2, ["arquivo excede o limite de 64 KiB"]
    try:
        policy = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 2, ["arquivo não contém JSON UTF-8 válido"]
    if not isinstance(policy, dict):
        return 2, ["a política deve ser um objeto JSON"]
    origins = policy.get("allowed_origins")
    credentials = policy.get("allow_credentials")
    if not isinstance(origins, list) or not all(isinstance(item, str) for item in origins):
        return 2, ["allowed_origins deve ser uma lista de strings"]
    if not isinstance(credentials, bool):
        return 2, ["allow_credentials deve ser booleano"]

    findings = []
    wildcard_count = sum(origin.strip() == "*" for origin in origins)
    if wildcard_count:
        findings.append(f"origem curinga encontrada ({wildcard_count}); revisar escopo")
    if wildcard_count and credentials:
        findings.append("credenciais habilitadas com origem curinga; corrigir conforme política")
    if not findings:
        findings.append("nenhum dos padrões específicos verificados foi encontrado")
    return (1 if wildcard_count else 0), findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy_json", type=Path, help="arquivo JSON local autorizado")
    args = parser.parse_args()
    code, findings = review(args.policy_json)
    for finding in findings:
        print(f"- {finding}")
    if code == 0:
        print("Resultado limitado: não é uma certificação de segurança nem valida a configuração efetiva.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste local usando arquivos fictícios temporários:

```bash
python3 - <<'PY'
import json
import tempfile
from pathlib import Path
from review_cors_policy import review

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "policy.json"
    path.write_text(json.dumps({"allowed_origins": ["*"], "allow_credentials": True}), encoding="utf-8")
    code, findings = review(path)
    assert code == 1 and len(findings) == 2
    path.write_text(json.dumps({"allowed_origins": ["https://app.example.invalid"], "allow_credentials": False}), encoding="utf-8")
    code, findings = review(path)
    assert code == 0 and len(findings) == 1
    print("Testes locais passaram: política fictícia ampla sinalizada e política restrita sem esses padrões.")
PY
```

Código de saída `0` indica apenas que os padrões específicos verificados não foram encontrados; `1` indica origem curinga que merece revisão; `2` indica entrada ou leitura inválida. A equipe responsável deve validar a política real em processo autorizado e decidir a alteração adequada.

## Checklist

- [ ] Confirmei que tenho autorização para revisar o arquivo local e não usei configurações de terceiros.
- [ ] Usei somente origens fictícias no teste; não incluí tokens, cookies, domínios internos ou dados pessoais.
- [ ] Verifiquei que o código apenas lê JSON local, não faz chamadas de rede e não modifica configurações.
- [ ] Executei os testes locais para uma política fictícia permissiva e outra restrita.
- [ ] Interpretei o resultado como uma sinalização parcial, confirmando a configuração efetiva com a equipe responsável.
- [ ] Não apliquei mudanças automaticamente nem publiquei detalhes internos ou segredos.
