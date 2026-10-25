# Dia 037 — Revisão local da completude de um inventário CycloneDX (SBOM)

Um inventário de componentes de software (SBOM) ajuda equipes a entender o que está incluído em uma aplicação e a priorizar revisões de dependências. Esta checagem estática lê um arquivo JSON CycloneDX local e aponta apenas contagens de componentes com campos `name` e `version` ausentes ou inválidos. Não instala pacotes, consulta serviços externos, executa componentes, altera o inventário nem imprime seus nomes ou valores. O exemplo aceita somente um objeto JSON com `bomFormat` igual a `CycloneDX` e restringe o tamanho da entrada.

## Limitações e ética

- Use apenas inventários gerados por você ou recebidos com autorização para revisão. Prefira SBOMs de teste sem dados internos que não sejam necessários.
- Esta verificação cobre apenas a estrutura básica de `components` e a presença de `name` e `version`; não valida integralmente uma versão do esquema CycloneDX, autenticidade, precisão, dependências transitivas ou vínculo com um artefato específico.
- SBOM completo não prova que componentes estejam livres de vulnerabilidades. Faça triagem de avisos com fontes e ferramentas aprovadas pela organização, em ambiente autorizado.
- O relatório mostra contagens, não os valores dos componentes. Ainda assim, trate o próprio SBOM como informação potencialmente sensível e não o publique sem aprovação.
- Não use o exemplo para buscar ou testar sistemas de terceiros. Não introduza segredos, URLs privadas, tokens ou dados de produção em exemplos compartilhados.

## Exemplo seguro em Python

Salve como `check_sbom.py`. O programa lê um único arquivo local, limita a entrada a 5 MiB e reporta somente totais:

```python
#!/usr/bin/env python3
"""Checagem estrutural mínima e local de componentes em SBOM CycloneDX JSON."""
import argparse
import json
import sys
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024


def check_sbom(path: Path) -> tuple[int, str]:
    if path.is_symlink():
        return 2, "entrada rejeitada: link simbólico não aceito"
    try:
        raw = path.read_bytes()
    except OSError:
        return 2, "entrada rejeitada: falha ao ler arquivo local"
    if len(raw) > MAX_BYTES:
        return 2, "entrada rejeitada: arquivo excede 5 MiB"
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 2, "entrada rejeitada: JSON UTF-8 inválido"
    if not isinstance(document, dict) or document.get("bomFormat") != "CycloneDX":
        return 2, "entrada rejeitada: objeto não identificado como CycloneDX"

    components = document.get("components", [])
    if not isinstance(components, list):
        return 2, "entrada rejeitada: components deve ser uma lista"

    incomplete = 0
    invalid_entries = 0
    for component in components:
        if not isinstance(component, dict):
            invalid_entries += 1
            continue
        name = component.get("name")
        version = component.get("version")
        if not isinstance(name, str) or not name.strip():
            incomplete += 1
        elif not isinstance(version, str) or not version.strip():
            incomplete += 1

    status = 1 if incomplete or invalid_entries else 0
    summary = (
        f"componentes={len(components)}; incompletos={incomplete}; "
        f"entradas_invalidas={invalid_entries}"
    )
    return status, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sbom_json", type=Path, help="arquivo CycloneDX JSON local autorizado")
    args = parser.parse_args()
    status, message = check_sbom(args.sbom_json)
    print(message)
    return status


if __name__ == "__main__":
    sys.exit(main())
```

Teste local, sem rede, com SBOMs fictícios:

```bash
python3 - <<'PY'
import json
import tempfile
from pathlib import Path
from check_sbom import check_sbom

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "fixture.json"
    path.write_text(json.dumps({
        "bomFormat": "CycloneDX",
        "components": [
            {"name": "biblioteca-ficticia", "version": "1.2.3"},
            {"name": "outro-componente-ficticio"},
            None,
        ],
    }), encoding="utf-8")
    status, summary = check_sbom(path)
    assert status == 1
    assert "componentes=3" in summary
    assert "incompletos=1" in summary
    assert "entradas_invalidas=1" in summary
    assert "biblioteca-ficticia" not in summary

    path.write_text(json.dumps({
        "bomFormat": "CycloneDX",
        "components": [{"name": "componente-ficticio", "version": "0.1"}],
    }), encoding="utf-8")
    status, summary = check_sbom(path)
    assert status == 0 and "incompletos=0" in summary

print("Teste local passou: SBOMs fictícios válidos e incompletos diferenciados sem revelar nomes.")
PY
```

Código de saída `0` indica apenas que todas as entradas da lista possuem nome e versão não vazios; `1` indica componentes incompletos ou entradas inválidas; `2` indica entrada rejeitada ou falha de leitura. A ausência de avisos não atesta conformidade com o esquema nem segurança dos componentes.

## Checklist

- [ ] Confirmei autorização para revisar o SBOM e usei dados fictícios no teste.
- [ ] Verifiquei que o exemplo só lê um arquivo local limitado e não acessa a rede nem executa componentes.
- [ ] Testei casos completos, incompletos e entrada inválida em diretório temporário.
- [ ] Confirmei que a saída contém apenas contagens, sem nomes ou valores do inventário.
- [ ] Interpretei a checagem como triagem estrutural, não como validação integral de esquema ou análise de vulnerabilidade.
- [ ] Mantive SBOMs internos, segredos e informações operacionais fora de commits e relatórios públicos.
- [ ] Encaminhei lacunas à equipe responsável e usei processos aprovados para análise posterior das dependências.
