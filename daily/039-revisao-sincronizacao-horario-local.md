# Dia 039 — Revisão local da configuração de sincronização de horário

Relógios coerentes ajudam a correlacionar eventos de segurança, investigar incidentes e interpretar certificados. Uma revisão de configuração pode confirmar se o host declara uma fonte de horário aprovada e se a configuração mantém registros úteis, sem iniciar conexões ou mudar o serviço. Este guia inspeciona somente um arquivo local fornecido pelo administrador, como `/etc/chrony/chrony.conf`; os nomes das diretivas podem variar entre implementações e políticas.

## Exemplo seguro em Python

O script abaixo lê um arquivo especificado, ignora comentários e verifica apenas a presença de diretivas `pool` ou `server` e `log`. Não resolve nomes, consulta servidores, executa comandos ou altera arquivos. Use-o somente em uma máquina que você administra. O exemplo de teste cria uma configuração fictícia em diretório temporário.

```python
from pathlib import Path
import sys
import tempfile


def review(path: Path) -> dict[str, bool]:
    directives = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            directives.add(line.split(maxsplit=1)[0].lower())
    return {
        "fonte_de_horario_declarada": bool(directives & {"pool", "server"}),
        "registro_declarado": "log" in directives,
    }


if __name__ == "__main__":
    if len(sys.argv) == 2:
        config = Path(sys.argv[1])
        print(review(config))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "chrony.conf"
            sample.write_text("# Exemplo fictício\npool time.lab.invalid iburst\nlog tracking\n", encoding="utf-8")
            print(review(sample))
```

Execute o teste fictício com `python3` e, para revisar um arquivo real autorizado, passe o caminho como único argumento. O programa não avalia se uma fonte é confiável ou alcançável, se o serviço está ativo, se o relógio está sincronizado nem se a política de logging está adequada. A simples presença de diretivas não comprova funcionamento; valide esses pontos por procedimento administrativo aprovado e sem ampliar o escopo.

## Limitações e ética

- Leia apenas configurações de sistemas sob sua administração ou com autorização explícita.
- O exemplo é offline, não faz varredura, não acessa rede e não altera o estado do sistema.
- Não publique configurações internas, endereços, nomes de host ou outros dados operacionais sem autorização.
- A sintaxe depende da implementação e da distribuição; adapte a revisão à documentação e à baseline aprovadas pela equipe responsável.
- Um resultado positivo significa somente que certas diretivas aparecem no arquivo lido. Não é um teste de conectividade, sincronização, precisão, autenticidade da fonte ou conformidade completa.
- Não edite nem reinicie serviços como parte desta revisão; encaminhe discrepâncias à equipe responsável para correção autorizada.

## Checklist

- [ ] Confirmei a autorização e identifiquei o arquivo local que será lido.
- [ ] Comparei as fontes declaradas com a lista aprovada pela organização, sem contatá-las.
- [ ] Interpretei a saída como uma verificação textual limitada, não como prova de sincronização.
- [ ] Testei o código somente com a configuração fictícia temporária antes de usá-lo.
- [ ] Evitei expor caminhos, endereços ou conteúdo de configuração em logs e commits.
- [ ] Encaminhei qualquer diferença à equipe responsável, sem modificar serviço ou configuração.
