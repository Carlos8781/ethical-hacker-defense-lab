# Dia 036 — Revisão local de privacidade em configurações de logging

Logs são úteis para auditoria e resposta a incidentes, mas registrar tokens, senhas ou dados pessoais pode ampliar o impacto de uma exposição. Esta revisão estática verifica um arquivo JSON local de configuração de logging em busca de três controles explícitos: nível de log reconhecido, lista de campos a redigir contendo nomes sensíveis comuns e retenção limitada a um intervalo configurado. O exemplo só lê o arquivo e informa controles ausentes; não imprime valores de configuração, não altera arquivos e não acessa a rede.

## Limitações e ética

- Faça a revisão apenas em um arquivo de um projeto que você administra ou para o qual recebeu autorização explícita. Prefira uma cópia de trabalho sem valores operacionais ou segredos.
- A checagem é deliberadamente simples: não entende todos os formatos, frameworks, configurações herdadas, filtros ou comportamentos em execução. Nomes de campo na lista de redação não provam que a aplicação realmente remove valores sensíveis.
- Um resultado sem avisos não certifica privacidade, conformidade, retenção efetiva ou segurança. Confirme a configuração efetiva com a equipe responsável e testes autorizados.
- O intervalo de retenção aceitável depende da política e da legislação aplicável. O limite do exemplo é uma regra demonstrativa, que deve ser adaptada por responsáveis autorizados.
- Não compartilhe nem publique logs reais, dados pessoais, segredos, caminhos internos ou configurações confidenciais. Não envie alterações à produção sem revisão, aprovação e plano de reversão.

## Exemplo seguro em Python

Salve como `review_logging_config.py`. O programa lê somente o arquivo JSON indicado, limita o tamanho e não revela valores de configuração:

```python
#!/usr/bin/env python3
"""Triagem estática de controles de privacidade em configuração JSON local."""
import argparse
import json
import sys
from pathlib import Path

MAX_BYTES = 256 * 1024
ALLOWED_LEVELS = {"debug", "info", "warning", "error", "critical"}
SENSITIVE_NAMES = {"password", "passwd", "token", "authorization", "secret", "api_key"}
MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 365


def review(path: Path) -> tuple[int, list[str]]:
    if path.is_symlink():
        return 2, ["entrada rejeitada: links simbólicos não são aceitos"]
    try:
        raw = path.read_bytes()
    except OSError:
        return 2, ["entrada rejeitada: não foi possível ler o arquivo local"]
    if len(raw) > MAX_BYTES:
        return 2, ["entrada rejeitada: arquivo excede 256 KiB"]
    try:
        config = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 2, ["entrada rejeitada: JSON UTF-8 inválido"]
    if not isinstance(config, dict):
        return 2, ["entrada rejeitada: o objeto JSON raiz deve ser um dicionário"]

    findings = []
    level = config.get("level")
    if not isinstance(level, str) or level.lower() not in ALLOWED_LEVELS:
        findings.append("revisar: nível de logging ausente ou não reconhecido")

    redact_fields = config.get("redact_fields")
    if not isinstance(redact_fields, list) or not all(isinstance(item, str) for item in redact_fields):
        findings.append("revisar: lista redact_fields ausente ou inválida")
    else:
        normalized = {item.strip().lower() for item in redact_fields}
        if not (normalized & SENSITIVE_NAMES):
            findings.append("revisar: nenhum nome sensível comum consta em redact_fields")

    retention = config.get("retention_days")
    if (isinstance(retention, bool) or not isinstance(retention, int)
            or not MIN_RETENTION_DAYS <= retention <= MAX_RETENTION_DAYS):
        findings.append("revisar: retention_days deve ser inteiro entre 1 e 365")

    if not findings:
        findings.append("controles declarativos selecionados encontrados; validar o comportamento efetivo")
    return (1 if any(item.startswith("revisar:") for item in findings) else 0), findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_json", type=Path, help="configuração JSON local autorizada")
    args = parser.parse_args()
    code, findings = review(args.config_json)
    for finding in findings:
        print(f"- {finding}")
    return code


if __name__ == "__main__":
    sys.exit(main())
```

Teste sem rede e apenas com dados fictícios (salve o script como `review_logging_config.py` no diretório de execução):

```bash
python3 - <<'PY'
import json
import tempfile
from pathlib import Path
from review_logging_config import review

with tempfile.TemporaryDirectory() as folder:
    config_path = Path(folder) / "logging.json"
    good = {"level": "INFO", "redact_fields": ["password", "authorization"], "retention_days": 30}
    config_path.write_text(json.dumps(good), encoding="utf-8")
    code, findings = review(config_path)
    assert code == 0 and "validar o comportamento efetivo" in findings[0]

    incomplete = {"level": "verbose", "redact_fields": ["request_id"], "retention_days": 999}
    config_path.write_text(json.dumps(incomplete), encoding="utf-8")
    code, findings = review(config_path)
    assert code == 1 and len(findings) == 3
print("Teste local passou: configuração fictícia completa e incompleta diferenciadas sem exibir valores.")
PY
```

Código de saída `0` significa somente que os três controles declarativos passaram pela checagem; `1` indica itens para revisão; `2` indica rejeição ou falha de leitura. A aplicação deve ser testada em ambiente local controlado para confirmar que a redação e a retenção funcionam de fato.

## Checklist

- [ ] Confirmei autorização e usei uma cópia local adequada, sem segredos ou dados reais desnecessários.
- [ ] Verifiquei que o exemplo só lê um JSON limitado, não usa rede e não altera arquivos.
- [ ] Executei o teste local com configurações fictícias válidas e incompletas.
- [ ] Confirmei que nenhuma saída reproduz valores ou conteúdo da configuração.
- [ ] Validei com a equipe responsável a configuração efetiva, redação de campos e política de retenção.
- [ ] Mantive dados, caminhos internos e segredos fora de exemplos, relatórios e commits.
- [ ] Submeti mudanças de configuração a revisão, teste autorizado e plano de reversão antes de implantação.
