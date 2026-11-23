# Dia 065 — Validação local de digests de imagens de contêiner

Fixar uma imagem de contêiner por digest torna a referência declarativa mais estável do que uma tag móvel, como `latest`. Uma revisão offline de um manifesto JSON local pode apontar imagens que ainda não estão fixadas. Este exemplo apenas lê um arquivo JSON com a chave `images`; não consulta registries, baixa imagens, executa contêineres ou altera arquivos.

## Exemplo seguro em Python

Salve como `check_image_digests.py`. O formato de entrada é um objeto JSON contendo `images`, uma lista de referências textuais. Use manifestos fictícios ou arquivos sob sua administração e autorização.

```python
import json
import re
import sys
from pathlib import Path

DIGEST_REF = re.compile(r"^.+@sha256:[0-9a-f]{64}$")


def review(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("images"), list):
        raise ValueError("esperado objeto JSON com uma lista 'images'")

    findings = []
    for index, image in enumerate(data["images"]):
        if not isinstance(image, str) or not image.strip():
            raise ValueError(f"images[{index}] deve ser uma referência textual não vazia")
        if not DIGEST_REF.fullmatch(image.strip()):
            findings.append(f"images[{index}]: referência não fixada por digest")
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python3 check_image_digests.py <manifesto.json>")
        return 2
    try:
        findings = review(Path(sys.argv[1]))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Não foi possível revisar o manifesto: {exc}")
        return 2
    print("\n".join(findings) if findings else "Todas as referências usam digest sha256.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Limitações e cuidados éticos

- A expressão regular apenas verifica o formato `@sha256:` seguido de 64 caracteres hexadecimais minúsculos; não prova que o digest existe, é confiável ou corresponde ao conteúdo esperado.
- O exemplo não interpreta YAML, Docker Compose, Helm ou outros formatos. Converta para o JSON simples documentado por um processo local aprovado; não amplie o escopo para consultar registries.
- Use somente arquivos de configuração administrados por você ou autorizados. Não inclua tokens de registry, credenciais nem configurações secretas no manifesto ou no relatório.
- Tags podem ser apropriadas em ambientes específicos, e a adoção de digests deve seguir o processo de atualização, revisão e rollback da organização. Não altere manifestos automaticamente com base no relatório.
- A ferramenta não faz conexões de rede, não executa imagens e não modifica o arquivo de entrada.

## Checklist

- [ ] Confirme autorização e escopo do manifesto local a revisar.
- [ ] Use primeiro o exemplo sintético abaixo e valide que a chave `images` representa referências de imagem, não outros artefatos.
- [ ] Confirme a política interna sobre uso de tags e digests, incluindo revisão e atualização de versões.
- [ ] Investigue cada referência sinalizada com o responsável pela implantação antes de propor mudanças.
- [ ] Não publique manifestos internos, nomes de imagens privados, credenciais ou relatórios sem sanitização.
- [ ] Registre as decisões e alterações pelo processo aprovado de gestão de mudanças.

## Teste local

O teste cria um manifesto fictício em diretório temporário, valida uma referência com digest e detecta uma tag não fixada. Não acessa rede nem executa contêineres:

```bash
python3 - <<'PY'
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from check_image_digests import review
with TemporaryDirectory() as folder:
    manifest = Path(folder) / "images.json"
    manifest.write_text(json.dumps({"images": [
        "registry.example/demo/app@sha256:" + "a" * 64,
        "registry.example/demo/worker:stable",
    ]}), encoding="utf-8")
    findings = review(manifest)
    assert findings == ["images[1]: referência não fixada por digest"]
    manifest.write_text(json.dumps({"images": ["demo:latest"]}), encoding="utf-8")
    assert len(review(manifest)) == 1
    manifest.write_text(json.dumps({"images": [None]}), encoding="utf-8")
    try:
        review(manifest)
    except ValueError:
        pass
    else:
        raise AssertionError("referência inválida deveria ser rejeitada")
print("Testes sintéticos aprovados.")
PY
```
