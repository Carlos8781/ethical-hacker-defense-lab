# Dia 066 — Revisão local de divergências em inventário de serviços

Comparar um inventário aprovado com um relatório local já existente ajuda a identificar serviços que precisam de revisão: itens esperados que não aparecem no registro, ou itens registrados que não constam no inventário autorizado. A ferramenta abaixo apenas compara dois arquivos JSON locais. Ela não descobre serviços, consulta a rede, inicia processos nem altera os arquivos.

## Exemplo seguro em Python

Salve como `compare_services.py`. Cada arquivo deve ser um objeto JSON com uma lista `services` de identificadores textuais. O exemplo usa nomes fictícios; adapte o formato somente a inventários sob sua administração ou autorização explícita.

```python
import json
import sys
from pathlib import Path


def load_services(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("services"), list):
        raise ValueError("esperado objeto JSON com lista 'services'")
    values = data["services"]
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError("cada serviço deve ser texto não vazio")
    normalized = [value.strip() for value in values]
    if len(normalized) != len(set(normalized)):
        raise ValueError("lista contém identificadores duplicados")
    return set(normalized)


def compare(expected_path: Path, recorded_path: Path) -> tuple[list[str], list[str]]:
    expected = load_services(expected_path)
    recorded = load_services(recorded_path)
    return sorted(expected - recorded), sorted(recorded - expected)


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python3 compare_services.py <inventario-aprovado.json> <registro-local.json>")
        return 2
    try:
        missing, unapproved = compare(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Não foi possível comparar os arquivos: {exc}")
        return 2
    print("Ausentes no registro: " + (", ".join(missing) if missing else "nenhum"))
    print("Fora do inventário aprovado: " + (", ".join(unapproved) if unapproved else "nenhum"))
    return 1 if missing or unapproved else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Limitações e cuidados éticos

- O programa compara somente os registros fornecidos; não confirma se um serviço realmente existe, está ativo, vulnerável ou acessível.
- A qualidade do resultado depende da atualidade e da precisão dos dois arquivos e da convenção de nomes adotada.
- Não use o exemplo para coletar dados de terceiros nem acrescente sondagem de rede. Confirme autorização e escopo antes de processar inventários de uma organização.
- Nomes de serviços e topologias podem ser informação interna. Use dados fictícios nos testes e sanitize relatórios antes de compartilhá-los. Não inclua senhas, tokens ou outros segredos.
- Divergências são sinais para revisão humana, não prova de incidente. Valide mudanças autorizadas e janelas de manutenção com a equipe responsável antes de tomar providências.
- O script é somente leitura; qualquer correção deve seguir o processo aprovado de gestão de mudanças e rollback.

## Checklist

- [ ] Confirme a autorização, o proprietário e a finalidade dos dois arquivos locais.
- [ ] Verifique a data, a origem e a convenção de identificadores do inventário aprovado e do registro.
- [ ] Execute primeiro os testes com dados fictícios; não use alvos externos nem descoberta de rede.
- [ ] Investigue cada diferença com a equipe responsável, considerando mudanças planejadas e registros desatualizados.
- [ ] Restrinja o acesso aos arquivos e sanitize nomes internos antes de guardar ou compartilhar resultados.
- [ ] Registre a revisão e qualquer correção pelo processo de mudanças autorizado.

## Teste local

O teste abaixo usa apenas arquivos temporários fictícios, verifica as duas categorias de divergência e rejeita identificadores duplicados. Não acessa a rede nem altera arquivos fora do diretório temporário.

```bash
python3 - <<'PY'
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from compare_services import compare

with TemporaryDirectory() as folder:
    root = Path(folder)
    expected = root / "expected.json"
    recorded = root / "recorded.json"
    expected.write_text(json.dumps({"services": ["demo-api", "demo-worker"]}), encoding="utf-8")
    recorded.write_text(json.dumps({"services": ["demo-api", "demo-legacy"]}), encoding="utf-8")
    assert compare(expected, recorded) == (["demo-worker"], ["demo-legacy"])
    recorded.write_text(json.dumps({"services": ["demo-api", "demo-api"]}), encoding="utf-8")
    try:
        compare(expected, recorded)
    except ValueError:
        pass
    else:
        raise AssertionError("identificadores duplicados deveriam ser rejeitados")
print("Testes sintéticos aprovados.")
PY
```
