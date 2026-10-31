# Dia 043 — Revisão local de permissões em workflows GitHub Actions

Workflows de integração contínua podem receber permissões de escrita desnecessárias ou manter credenciais durante etapas que não precisam delas. Uma revisão estática antes de integrar mudanças ajuda a identificar pontos para análise humana. O exemplo abaixo lê somente um arquivo YAML local indicado explicitamente, não executa o workflow, não altera arquivos e não acessa a rede.

## Exemplo seguro em Python

O verificador é intencionalmente simples e gera apenas indicadores de revisão. Sem argumento, usa uma amostra fictícia temporária; com um argumento, examina apenas aquele arquivo local.

```python
from pathlib import Path
import sys
import tempfile


def review(text: str) -> dict[str, object]:
    findings = {
        "permissoes_write_all": [],
        "evento_pull_request_target": [],
        "credencial_persistente_checkout": [],
        "bloco_permissions_presente": False,
    }

    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip().lower()
        if line.startswith("permissions:"):
            findings["bloco_permissions_presente"] = True
            if "write-all" in line:
                findings["permissoes_write_all"].append(number)
        elif line == "write-all":
            findings["permissoes_write_all"].append(number)

        if "pull_request_target:" in line:
            findings["evento_pull_request_target"].append(number)
        if "persist-credentials: true" in line:
            findings["credencial_persistente_checkout"].append(number)

    return findings


def main() -> None:
    if len(sys.argv) == 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    elif len(sys.argv) == 1:
        sample = """name: exemplo-ficticio
on:
  pull_request_target:
permissions: write-all
steps:
  - uses: actions/checkout@v4
    with:
      persist-credentials: true
"""
        with tempfile.TemporaryDirectory() as tmp:
            sample_path = Path(tmp) / "workflow-ficticio.yml"
            sample_path.write_text(sample, encoding="utf-8")
            text = sample_path.read_text(encoding="utf-8")
    else:
        raise SystemExit(f"Uso: {sys.argv[0]} [workflow-local.yml]")

    print(review(text))


if __name__ == "__main__":
    main()
```

Teste a amostra executando `python3` com o código salvo em um arquivo local. O resultado esperado aponta `permissoes_write_all: [4]`, `evento_pull_request_target: [3]`, `credencial_persistente_checkout: [8]` e `bloco_permissions_presente: True`. Para uma revisão real, forneça somente um workflow de um repositório que você administra ou tem autorização para avaliar.

## Limitações e ética

- Revise apenas arquivos locais pertencentes a projetos sob sua administração ou cobertos por autorização explícita; não busque nem examine repositórios de terceiros.
- O programa é somente leitura do arquivo indicado: não executa Actions, comandos do workflow ou ferramentas externas e não faz chamadas de rede.
- A inspeção textual não interpreta YAML. Formatação alternativa, comentários, âncoras, expressões, permissões por job, múltiplos workflows e valores calculados podem causar falsos positivos ou deixar riscos sem detecção.
- `pull_request_target` pode ter usos legítimos, mas merece revisão cuidadosa de contexto, checkout e execução de código não confiável. Sua presença, isoladamente, não prova uma vulnerabilidade.
- `write-all` e `persist-credentials: true` são sinais para conferir necessidade, escopo e duração conforme a documentação e a política aprovadas; não são conclusões automáticas de falha.
- Não cole conteúdo privado, nomes internos, segredos ou tokens em relatórios públicos. Use dados fictícios nos exemplos e proteja saídas operacionais.

## Checklist

- [ ] Confirmei autorização e selecionei um único workflow local para revisão.
- [ ] Testei primeiro com a amostra fictícia e conferi as linhas indicadas.
- [ ] Verifiquei que o código não executa workflows, não altera o alvo e não acessa a rede.
- [ ] Revisei manualmente permissões no nível do workflow e dos jobs e apliquei menor privilégio conforme a política aprovada.
- [ ] Avaliei o contexto de eventos privilegiados e a necessidade de persistir credenciais sem tratar heurísticas como prova.
- [ ] Não publiquei YAML interno, segredos, tokens ou detalhes operacionais; encaminhei mudanças pelo processo de revisão responsável.
