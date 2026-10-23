# Dia 035 — Revisão local de versões fixadas em dependências Python

Fixar versões de dependências ajuda a tornar instalações reproduzíveis e facilita revisar mudanças antes de uma implantação. Uma inspeção estática de um arquivo `requirements.txt` pode apontar requisitos sem uma versão exata, sem acessar a rede ou executar o gerenciador de pacotes. Ela é uma triagem: não confirma que a versão escolhida é segura, atual, compatível ou disponível.

## Uso autorizado e limitações éticas

Use o exemplo somente em um projeto local que você administra ou para o qual tem autorização explícita. O programa lê um único arquivo indicado pelo operador, não instala, remove ou atualiza dependências, não executa conteúdo do arquivo, não consulta serviços externos e não altera arquivos. Para reduzir exposição acidental, os avisos mostram apenas números de linha e não reproduzem o conteúdo examinado.

A verificação reconhece deliberadamente apenas requisitos simples no formato `nome==versão` (extras opcionais também são aceitos). Opções do pip, referências a arquivos/URLs, requisitos editáveis, marcadores ou sintaxes não reconhecidas são encaminhados para revisão manual; não são tratados como vulneráveis nem seguros. Uma versão fixada pode estar desatualizada ou comprometida, e a ausência de avisos não é uma avaliação de vulnerabilidade. Nunca coloque tokens, senhas ou URLs com credenciais em exemplos ou relatórios. Siga a política da equipe para índices privados, hashes, atualização e aprovação de dependências.

## Exemplo seguro em Python

Salve como `review_requirements.py` fora do projeto auditado. O script usa apenas a biblioteca padrão e não mostra o conteúdo das linhas:

```python
#!/usr/bin/env python3
"""Triagem estática e somente de leitura de requisitos Python locais."""
import argparse
import re
import sys
from pathlib import Path

# Aceita apenas um nome de distribuição opcionalmente com extras, seguido de ==versão.
PINNED = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9_,.-]+\])?"
    r"\s*==\s*[A-Za-z0-9][A-Za-z0-9.!+_-]*"
    r"(?:\s*;\s*[^#]+)?\s*(?:#.*)?$"
)


def review(path: Path) -> tuple[int, list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return 2, [f"não foi possível ler o arquivo ({type(exc).__name__})"]

    findings = []
    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if PINNED.fullmatch(line):
            continue
        # Não ecoa o conteúdo, que pode incluir caminhos internos ou credenciais.
        findings.append(f"linha {number}: sintaxe não reconhecida ou versão não fixada; revisar manualmente")

    if not findings:
        findings.append("todas as linhas de requisito não comentadas correspondem ao formato simples nome==versão")
    return (1 if any("revisar manualmente" in item for item in findings) else 0), findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements_file", type=Path, help="requirements.txt local autorizado")
    args = parser.parse_args()
    code, findings = review(args.requirements_file)
    for finding in findings:
        print(f"- {finding}")
    return code


if __name__ == "__main__":
    sys.exit(main())
```

Teste sem rede e apenas com dados fictícios:

```bash
python3 - <<'PY'
import tempfile
from pathlib import Path
from review_requirements import review

with tempfile.TemporaryDirectory() as folder:
    sample = Path(folder) / "requirements.txt"
    sample.write_text("# exemplo fictício\nrequests==2.32.3\nDemo_Pkg[extra]==1.4.0\n", encoding="utf-8")
    code, findings = review(sample)
    assert code == 0 and "formato simples" in findings[0]

    sample.write_text("requests>=2.0\n-e .\n", encoding="utf-8")
    code, findings = review(sample)
    assert code == 1 and len(findings) == 2
    assert all("requests>=" not in item and "-e ." not in item for item in findings)

print("Teste local passou: versões fixadas e casos para revisão manual foram distinguidos sem ecoar linhas.")
PY
```

Código de saída `0` significa apenas que todas as linhas não comentadas se encaixaram no formato estrito aceito; `1` indica linhas para revisão manual; `2` indica falha ao ler o arquivo. Antes de alterar a lista, confirme as versões desejadas em fontes aprovadas, avalie compatibilidade, integridade e avisos de segurança, e faça a mudança em branch e ambiente de testes controlados.

## Checklist

- [ ] Confirmei que o projeto e o arquivo local estão sob minha administração ou autorização explícita.
- [ ] Usei um arquivo de teste fictício e executei o exemplo localmente, sem rede.
- [ ] Revisei manualmente cada linha que não segue o formato simples `nome==versão`.
- [ ] Confirmei que a versão escolhida atende à política de suporte, segurança e compatibilidade da equipe.
- [ ] Mantive lockfile, hashes e configuração de índices conforme os controles aprovados pela organização.
- [ ] Não incluí tokens, senhas, URLs privadas ou conteúdo sensível em exemplos, saídas ou commits.
- [ ] Testei qualquer atualização em ambiente local/CI autorizado antes de implantá-la.
