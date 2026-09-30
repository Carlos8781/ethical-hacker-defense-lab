# Dia 012 — Minimização de dados em logs locais

Logs ajudam a detectar e investigar problemas, mas texto livre pode registrar dados pessoais, segredos ou detalhes operacionais desnecessários. Esta lição demonstra uma etapa local de minimização: converter cada evento JSONL para um esquema pequeno de campos enumerados e descartar todos os campos não aprovados. A prática preferível é evitar coletar dados desnecessários na origem; este exemplo não substitui essa revisão.

## Uso autorizado e limitações éticas

Use o programa somente com arquivos de log locais cuja leitura e tratamento estejam autorizados. O teste abaixo contém dados sintéticos. O programa lê o arquivo informado, não acessa a rede, não altera nem apaga o original, não tenta identificar pessoas e não transmite nem grava o resultado: os eventos minimizados são enviados ao terminal. Evite exibir a saída em sessões compartilhadas.

O esquema aceita apenas valores previamente enumerados para componente, evento e resultado, além de uma duração inteira opcional dentro de um limite. Campos extras — inclusive texto livre, nomes, caminhos, endereços e possíveis segredos — nunca são copiados para a saída. Registros inválidos são contados sem imprimir seu conteúdo. Isso reduz a exposição na saída, mas não protege o arquivo de entrada, não remove dados já coletados e não impede que alguém com acesso leia o original.

A filtragem também pode descartar contexto relevante para uma investigação. Não use o resultado como única fonte de evidência, não altere a política de retenção nem elimine o original com base neste exemplo. Preserve registros conforme as regras internas de segurança, privacidade, retenção e resposta a incidentes; restrinja acesso e amplie o esquema somente após aprovação. O script não detecta incidentes nem prova que os dados de origem sejam corretos ou completos.

## Exemplo seguro em Python

Salve como `minimize_local_logs.py`. O formato de entrada é JSON Lines (um objeto JSON por linha). O exemplo processa somente um arquivo local; registros com formato ou valores fora do esquema são ignorados e contabilizados sem revelar seu conteúdo.

```python
#!/usr/bin/env python3
"""Emit only allow-listed fields from an authorized local JSONL log."""
import argparse
import json
from pathlib import Path

ALLOWED_COMPONENTS = {"auth", "backup", "config"}
ALLOWED_EVENTS = {"access_check", "backup_check", "config_review"}
ALLOWED_OUTCOMES = {"allowed", "denied", "success", "needs_review"}
MAX_RECORD_CHARS = 4096
MAX_DURATION_MS = 3_600_000


def sanitize(record: object) -> dict[str, str | int] | None:
    if not isinstance(record, dict):
        return None

    component = record.get("component")
    event = record.get("event")
    outcome = record.get("outcome")
    if (
        type(component) is not str or component not in ALLOWED_COMPONENTS
        or type(event) is not str or event not in ALLOWED_EVENTS
        or type(outcome) is not str or outcome not in ALLOWED_OUTCOMES
    ):
        return None

    safe: dict[str, str | int] = {
        "component": component,
        "event": event,
        "outcome": outcome,
    }
    if "duration_ms" in record:
        duration = record["duration_ms"]
        if type(duration) is not int or not 0 <= duration <= MAX_DURATION_MS:
            return None
        safe["duration_ms"] = duration
    return safe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", type=Path, help="arquivo JSONL local autorizado")
    args = parser.parse_args()
    if not args.logfile.is_file():
        parser.error("informe um arquivo local existente")

    valid = 0
    invalid = 0
    try:
        with args.logfile.open("r", encoding="utf-8") as stream:
            for line in stream:
                if len(line) > MAX_RECORD_CHARS:
                    invalid += 1
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    invalid += 1
                    continue
                safe = sanitize(record)
                if safe is None:
                    invalid += 1
                    continue
                print(json.dumps(safe, ensure_ascii=False, sort_keys=True))
                valid += 1
    except (OSError, UnicodeError):
        parser.error("não foi possível ler o arquivo local")

    parser.exit(2 if invalid else 0, f"registros minimizados: {valid}; inválidos: {invalid}\n")


if __name__ == "__main__":
    raise SystemExit(main())
```

Crie uma entrada descartável com eventos fictícios e execute no próprio computador:

```bash
cat > /tmp/logs-sinteticos.jsonl <<'EOF'
{"component":"auth","event":"access_check","outcome":"denied","user":"pessoa-sintetica","detail":"texto livre de teste"}
{"component":"backup","event":"backup_check","outcome":"success","duration_ms":850}
EOF
python3 minimize_local_logs.py /tmp/logs-sinteticos.jsonl
```

A saída JSONL deve conter somente os campos aprovados: `component`, `event`, `outcome` e, quando válido, `duration_ms`. O primeiro registro não deve reproduzir `user` ou `detail`; o segundo mantém a duração. A mensagem resumida aparece no canal de erro. O processo retorna `0` se todos os registros forem válidos e `2` se algum for inválido. Teste entradas malformadas ou valores não enumerados somente com dados sintéticos; a contagem de inválidos não deve revelar o conteúdo descartado.

## Checklist

- [ ] O arquivo é local, pertence à equipe ou tem autorização explícita para tratamento.
- [ ] O primeiro teste usa apenas registros fictícios em arquivo descartável.
- [ ] A coleta na origem foi revisada para evitar texto livre, dados pessoais e segredos desnecessários.
- [ ] O esquema e cada valor permitido foram aprovados pelos responsáveis de segurança e privacidade.
- [ ] Campos extras são descartados; a saída não contém nomes, endereços, caminhos, cabeçalhos, tokens ou texto livre.
- [ ] Acesso, retenção, compartilhamento e exibição dos logs originais seguem a política interna.
- [ ] Registros inválidos são investigados em ambiente autorizado, sem publicar seu conteúdo.
- [ ] O resultado minimizado não é tratado como evidência completa nem usado para apagar o original.
- [ ] Nenhum serviço externo ou sistema de terceiros foi consultado ou alterado.

## Limitações e próximos passos

O programa implementa apenas uma allowlist fixa sobre objetos JSONL locais. Não verifica autenticidade, integridade, sequência temporal, origem, completude nem significado operacional dos registros; também não detecta incidentes. Campos omitidos podem ser importantes para auditoria, e a saída no terminal ainda pode ser capturada pelo ambiente local. Em uso real, defina o esquema, controles de acesso, retenção, proteção e processo de preservação com as equipes responsáveis. Prefira minimizar na origem e revise qualquer ampliação de campos antes de implantá-la.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `json`, `argparse` e `pathlib`.
- Políticas internas aprovadas de registro, privacidade, retenção e resposta a incidentes.

> Este exemplo reduz campos de registros locais autorizados; não acessa redes, não explora sistemas e não coleta credenciais.

<!-- Testado localmente com Python 3 e JSONL sintético. -->
