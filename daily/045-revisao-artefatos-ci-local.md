# Dia 045 — Revisão local de artefatos de CI

Artefatos produzidos por integração contínua podem reter arquivos por mais tempo que o necessário ou incluir conteúdo amplo demais, como diretórios inteiros. Uma revisão estática de um workflow local ajuda a identificar configurações que merecem validação humana antes da publicação ou retenção de resultados. O exemplo abaixo procura referências textuais a `actions/upload-artifact` e exibe apenas linhas do arquivo escolhido; não executa o workflow, não acessa a rede e não altera arquivos.

## Exemplo seguro em Python

Sem argumento, o programa analisa uma amostra fictícia em memória. Com um argumento, lê apenas o arquivo local indicado. As regras são heurísticas: apontam configurações que valem uma revisão, não confirmam exposição nem determinam uma política universal de retenção.

```python
from pathlib import Path
import re
import sys

UPLOAD = re.compile(r"^\s*(?:-\s*)?uses:\s*actions/upload-artifact(?:@|\s|$)", re.I)


def review(text: str) -> list[dict[str, int | str]]:
    lines = text.splitlines()
    findings = []
    in_upload_step = False
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if UPLOAD.search(raw):
            in_upload_step = True
            findings.append({"linha": number, "sinal": "etapa de upload: revisar origem e escopo"})
            continue
        if in_upload_step and stripped and not raw.startswith((" ", "\t")):
            in_upload_step = False
        if in_upload_step:
            lower = stripped.lower()
            if lower.startswith("path:") and any(token in lower for token in (". ", "./", "**", " - ")):
                findings.append({"linha": number, "sinal": "caminho possivelmente amplo; conferir arquivos incluídos"})
            if lower.startswith("retention-days:"):
                value = lower.split(":", 1)[1].strip().strip("'\"")
                if value.isdigit() and int(value) > 30:
                    findings.append({"linha": number, "sinal": "retenção acima de 30 dias; justificar conforme política"})
    return findings


def main() -> None:
    if len(sys.argv) == 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    elif len(sys.argv) == 1:
        text = """name: exemplo-ficticio
steps:
  - uses: actions/upload-artifact@v4
    with:
      name: resultado
      path: ./
      retention-days: 45
"""
    else:
        raise SystemExit(f"Uso: {sys.argv[0]} [workflow-local.yml]")

    for finding in review(text):
        print(finding)
    if not review(text):
        print("Nenhum sinal previsto foi detectado; isso não comprova ausência de risco.")


if __name__ == "__main__":
    main()
```

Salve como `revisar_artefatos_ci.py` e execute `python3 revisar_artefatos_ci.py` para usar somente a amostra fictícia. O resultado esperado sinaliza a etapa de upload, o caminho `./` e a retenção de 45 dias. Para uma revisão autorizada, passe o caminho de um workflow local: `python3 revisar_artefatos_ci.py caminho/do/workflow.yml`.

## Limitações e ética

- Analise apenas workflows locais que você administra ou para os quais tem autorização explícita. Não faça busca, varredura ou consulta de repositórios externos.
- O código apenas lê texto local. Não baixa, publica, executa ou modifica workflows ou artefatos, nem acessa rede, segredos ou credenciais.
- A análise textual não interpreta YAML. Blocos complexos, expressões, aliases, arquivos auxiliares e convenções de caminho podem gerar falsos positivos ou deixar configurações sem detectar.
- Um caminho amplo não significa automaticamente que dados sensíveis serão incluídos; confirme expansão de padrões, diretório de trabalho, arquivos gerados e exclusões na ferramenta e no contexto autorizados.
- O limite de 30 dias é apenas um indicador de revisão deste exemplo, não uma exigência normativa. Siga a política organizacional, requisitos legais e necessidades de resposta a incidentes; retenção menor também pode ser inadequada.
- Revise quem pode acessar artefatos, o conteúdo produzido e o ciclo de vida de exclusão. Evite colocar segredos, dados pessoais ou arquivos de configuração sensíveis em artefatos.
- Não publique configurações internas ou saídas privadas. Use dados fictícios em exemplos e relatórios públicos.

## Checklist

- [ ] Confirmei autorização e selecionei um workflow local específico.
- [ ] Testei primeiro a amostra fictícia e conferi os três sinais esperados.
- [ ] Verifiquei que o exemplo apenas lê o workflow e não usa rede, credenciais ou execução de CI.
- [ ] Revisei manualmente caminhos, padrões, diretório de trabalho e arquivos efetivamente incluídos.
- [ ] Justifiquei a retenção conforme a política aplicável e confirmei acesso e descarte dos artefatos.
- [ ] Excluí segredos e dados sensíveis dos artefatos e não publiquei detalhes internos.
