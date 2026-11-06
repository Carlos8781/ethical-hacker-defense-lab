# Dia 049 — Validação estrita de opções de segurança em JSON local

Uma opção de segurança mal tipada pode ser interpretada de modo inesperado. Por exemplo, em Python, a string `"false"` é verdadeira em um teste de valor booleano, embora pareça indicar o contrário para uma pessoa. Validar tipo e intervalo explicitamente ajuda a detectar configurações ambíguas antes de uma revisão ou implantação. Este exemplo apenas lê JSON local escolhido explicitamente; não altera arquivos nem acessa a rede.

## Exemplo seguro em Python

Salve como `validar_config.py`. Sem argumentos, o programa testa uma configuração fictícia que deve gerar alertas. Para revisar um arquivo JSON local de um projeto ou sistema que você administra, informe seu caminho: `python3 validar_config.py ./config-local.json`.

```python
import json
import sys
from pathlib import Path

SAMPLE = {
    "debug": "false",  # Tipo incorreto: string não é o booleano false.
    "require_mfa": True,
    "session_timeout_minutes": 30,
}


def review(config: object) -> list[str]:
    if not isinstance(config, dict):
        return ["raiz: esperado um objeto JSON"]

    findings = []
    debug = config.get("debug")
    if type(debug) is not bool:
        findings.append("debug: esperado booleano explícito")
    elif debug is not False:
        findings.append("debug: deve estar desativado")

    if config.get("require_mfa") is not True:
        findings.append("require_mfa: deve estar explicitamente ativado")

    timeout = config.get("session_timeout_minutes")
    if type(timeout) is not int or not 5 <= timeout <= 120:
        findings.append("session_timeout_minutes: esperado inteiro entre 5 e 120")

    return findings


def main() -> int:
    if len(sys.argv) == 1:
        config = SAMPLE
        print("Usando somente a amostra fictícia.")
    elif len(sys.argv) == 2:
        path = Path(sys.argv[1])
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise SystemExit(f"Não foi possível ler o JSON local: {error}")
    else:
        raise SystemExit(f"Uso: {sys.argv[0]} [arquivo-json-local-autorizado]")

    findings = review(config)
    if findings:
        for finding in findings:
            print(f"Revisar {finding}")
        return 1

    print("As opções verificadas correspondem às regras deste exemplo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

A amostra fictícia deve sinalizar `debug` porque seu valor é uma string, e não o booleano `false`. O exemplo não imprime valores da configuração; exibe apenas nomes de opções e motivos genéricos. Um resultado sem alertas vale somente para as três regras ilustrativas e não certifica a segurança do aplicativo.

## Limitações e ética

- Examine apenas arquivos locais de sistemas que você administra ou para os quais tem autorização explícita. Comece pela amostra fictícia; não use caminhos de terceiros ou compartilhados sem aprovação.
- As regras são exemplos: a política real pode exigir outros valores, nomes, intervalos ou controles. Confirme os requisitos com a documentação e os responsáveis pelo sistema antes de concluir que uma configuração é adequada.
- O verificador não conhece valores padrão, precedência, variáveis de ambiente, arquivos sobrepostos ou a forma como o aplicativo consome as opções. Uma configuração válida aqui pode ser ignorada ou substituída em execução.
- JSON inválido ou falhas de leitura interrompem a análise. O programa é somente de leitura, não corrige configurações, não segue referências externas e não faz conexões de rede.
- Não compartilhe arquivos de configuração, caminhos internos, dados pessoais ou segredos. Use dados fictícios nos exemplos e remova informações sensíveis de qualquer relatório.

## Checklist

- [ ] Tenho autorização para revisar o arquivo local escolhido e entendo sua finalidade.
- [ ] Executei primeiro a amostra fictícia e confirmei que a string `"false"` para `debug` é sinalizada.
- [ ] Testei também uma configuração fictícia conforme as regras e confirmei que ela não gera alertas.
- [ ] Verifiquei que o código apenas lê JSON local, não altera arquivos e não acessa a rede.
- [ ] Comparei as regras ilustrativas com a política e com a configuração efetiva do aplicativo.
- [ ] Removi dados pessoais, caminhos internos e segredos antes de compartilhar resultados.
