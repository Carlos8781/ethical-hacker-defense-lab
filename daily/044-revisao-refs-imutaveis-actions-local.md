# Dia 044 — Revisão local de referências imutáveis em GitHub Actions

Workflows de integração contínua dependem de ações externas, e uma referência móvel como `@v4` pode apontar para conteúdo que muda ao longo do tempo. Fixar uma dependência em um commit completo e revisar atualizações por um processo controlado melhora a reprodutibilidade e reduz riscos na cadeia de fornecimento. Este guia apresenta uma triagem estática de linhas `uses:` em um workflow local autorizado.

## Exemplo seguro em Python

O programa lê somente o arquivo local indicado. Sem argumento, analisa uma amostra fictícia; não executa workflows, instala dependências, altera arquivos ou acessa a rede.

```python
from pathlib import Path
import re
import sys
import tempfile

# SHA completo de 40 caracteres hexadecimais; não valida a procedência do commit.
FULL_COMMIT = re.compile(r"^[0-9a-fA-F]{40}$")
USES_LINE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)")


def review(text: str) -> list[dict[str, int | str]]:
    findings = []
    for number, raw_line in enumerate(text.splitlines(), start=1):
        match = USES_LINE.match(raw_line)
        if not match:
            continue
        reference = match.group(1)
        if "@" not in reference:
            findings.append({"linha": number, "referencia": reference,
                             "motivo": "referência sem versão explícita"})
            continue
        version = reference.rsplit("@", 1)[1]
        if not FULL_COMMIT.fullmatch(version):
            findings.append({"linha": number, "referencia": reference,
                             "motivo": "não aparenta estar fixada em SHA completo"})
    return findings


def main() -> None:
    if len(sys.argv) == 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    elif len(sys.argv) == 1:
        sample = """name: exemplo-ficticio
steps:
  - uses: actions/checkout@v4
  - uses: exemplo/acao@0123456789abcdef0123456789abcdef01234567
  - uses: ./actions/local
"""
        with tempfile.TemporaryDirectory() as tmp:
            sample_path = Path(tmp) / "workflow-ficticio.yml"
            sample_path.write_text(sample, encoding="utf-8")
            text = sample_path.read_text(encoding="utf-8")
    else:
        raise SystemExit(f"Uso: {sys.argv[0]} [workflow-local.yml]")

    for finding in review(text):
        print(finding)
    if not review(text):
        print("Nenhuma referência móvel detectada pelas regras simples.")


if __name__ == "__main__":
    main()
```

Salve como `revisar_refs_actions.py` e execute `python3 revisar_refs_actions.py` para testar a amostra. O resultado deve sinalizar a linha 3 (`actions/checkout@v4`) e a linha 5 (`./actions/local`); a referência de exemplo com SHA completo não deve ser sinalizada. Para revisar um arquivo autorizado, execute `python3 revisar_refs_actions.py caminho/do/workflow.yml`.

## Limitações e ética

- Analise apenas workflows locais de repositórios que você administra ou para os quais tem autorização explícita. Não faça varredura de repositórios ou alvos externos.
- O verificador é uma triagem por expressão regular, não um parser YAML. Pode ignorar sintaxes alternativas, referências em blocos complexos ou comentários e produzir falsos positivos.
- Uma string de 40 caracteres hexadecimais não prova que o commit existe, pertence ao projeto esperado ou é seguro. Confirme a origem do SHA e revise mudanças por fontes e processos confiáveis.
- Ações locais (`./...`) não têm uma versão remota indicada na linha e exigem revisão do código e do histórico correspondente.
- Fixar SHA não elimina vulnerabilidades, riscos em dependências transitivas ou a necessidade de atualização. Use revisão por pares, menor privilégio, testes e política documentada de atualização.
- O exemplo não lê segredos intencionalmente, não executa o workflow e não transmite dados. Não publique arquivos privados, tokens ou detalhes operacionais.

## Checklist

- [ ] Confirmei autorização e escolhi um workflow local específico.
- [ ] Testei o script com a amostra fictícia e conferi as linhas sinalizadas.
- [ ] Verifiquei que a análise é somente leitura e não faz chamadas de rede nem executa código do workflow.
- [ ] Confirmei manualmente a procedência dos SHAs e revisei as ações locais e transitivas.
- [ ] Planejei atualizações controladas, revisão por pares e permissões mínimas para os workflows.
- [ ] Não incluí segredos nem dados privados em saídas ou publicações.
