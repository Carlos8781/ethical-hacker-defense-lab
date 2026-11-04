# Dia 047 — Revisão local de hardening do Docker Compose

Arquivos Compose descrevem como serviços de contêineres são iniciados e quais recursos do host podem ser expostos. Uma revisão estática local pode destacar algumas configurações que merecem justificativa, como modo privilegiado ou compartilhamento do namespace de rede do host. O exemplo abaixo apenas lê texto local e sinaliza ocorrências literais; não inicia contêineres, altera arquivos, consulta a rede ou acessa outros sistemas.

## Exemplo seguro em Python

Salve como `revisar_compose.py` e execute `python3 revisar_compose.py` para analisar a amostra fictícia. Para revisar um arquivo Compose que você administra, passe seu caminho como argumento: `python3 revisar_compose.py caminho/compose.yml`.

```python
from pathlib import Path
import re
import sys

RULES = (
    ("privileged", re.compile(r"^\s*privileged\s*:\s*['\"]?true['\"]?\s*(?:#.*)?$", re.I),
     "serviço solicita modo privilegiado; validar necessidade e escopo"),
    ("network_mode", re.compile(r"^\s*network_mode\s*:\s*['\"]?host['\"]?\s*(?:#.*)?$", re.I),
     "serviço compartilha a rede do host; revisar isolamento necessário"),
    ("pid", re.compile(r"^\s*pid\s*:\s*['\"]?host['\"]?\s*(?:#.*)?$", re.I),
     "serviço compartilha o namespace PID do host; revisar necessidade"),
)

SAMPLE = """services:
  app:
    image: exemplo-local:1.0
    privileged: true
  diagnostico:
    image: exemplo-local:1.0
    network_mode: host
"""

def review(text: str) -> list[dict[str, int | str]]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for key, pattern, message in RULES:
            if pattern.search(line):
                findings.append({"linha": number, "configuracao": key, "revisao": message})
    return findings

def main() -> int:
    if len(sys.argv) == 1:
        text = SAMPLE
    elif len(sys.argv) == 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        raise SystemExit(f"Uso: {sys.argv[0]} [compose-local.yml]")

    findings = review(text)
    if findings:
        for finding in findings:
            print(f"Linha {finding['linha']}: {finding['configuracao']} — {finding['revisao']}")
    else:
        print("Nenhum dos indicadores previstos foi detectado; isso não comprova segurança.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Na amostra, são esperados dois indicadores: `privileged` e `network_mode`. Trate cada resultado como uma pergunta para revisão, não como prova de vulnerabilidade nem como recomendação automática de mudança.

## Limitações e ética

- Analise somente arquivos locais de projetos que você administra ou para os quais tem autorização explícita. O exemplo não baixa arquivos, chama o Docker, faz consultas de rede ou altera configurações.
- As regras reconhecem apenas formas textuais literais de três opções. YAML válido pode expressar valores de outras formas, usar extensões, âncoras, interpolação ou configurações distribuídas por múltiplos arquivos; por isso, podem ocorrer falsos positivos e falsos negativos.
- Um modo de host ou privilegiado pode ter justificativa operacional. Confirme necessidade, alternativas menos permissivas, ambiente de execução e política da equipe antes de qualquer mudança.
- O script não interpreta YAML, não avalia imagens, volumes, capacidades Linux, segredos, políticas do daemon ou o estado efetivo de execução. Não substitui revisão do Compose completo nem ferramentas aprovadas.
- Não cole configurações internas em serviços externos. Remova tokens, senhas, dados pessoais e outros segredos de exemplos e relatórios; use a amostra fictícia para testes.

## Checklist

- [ ] Confirmei que o arquivo local pertence a um projeto sob minha administração ou autorização explícita.
- [ ] Testei primeiro a amostra fictícia e confirmei os dois indicadores esperados.
- [ ] Verifiquei que o código apenas lê o arquivo escolhido e não executa contêineres nem acessa a rede.
- [ ] Revisei manualmente cada ocorrência no contexto de todos os arquivos Compose aplicáveis.
- [ ] Avaliei necessidade e alternativas de menor privilégio antes de propor alterações.
- [ ] Evitei divulgar segredos, dados pessoais ou detalhes internos nos resultados.
