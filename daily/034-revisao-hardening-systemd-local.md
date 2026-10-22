# Dia 034 — Revisão local de hardening de unidades systemd

## Objetivo

Unidades systemd podem declarar controles de isolamento e redução de privilégios para serviços Linux. Esta revisão estática lê um arquivo de unidade local autorizado e verifica se a seção `[Service]` declara quatro opções de hardening: `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=strict` e `ProtectHome=true`. O relatório mostra somente quais opções precisam de revisão; não imprime o conteúdo do arquivo.

O exemplo não executa `systemctl`, não inicia nem altera serviços, não usa rede e não modifica a unidade. Analise uma cópia de um arquivo que você administra ou tem autorização explícita para revisar.

## Limitações e ética

- Uma opção ausente é um ponto de revisão, não prova de vulnerabilidade. A escolha correta depende da função do serviço e de requisitos legítimos de acesso a arquivos e recursos.
- A ferramenta verifica apenas declarações textuais nessa unidade. Não interpreta integralmente a sintaxe systemd, diretivas duplicadas, drop-ins, arquivos de usuário, valores herdados, versão do systemd, permissões ou o estado efetivo do serviço.
- Um resultado sem itens pendentes não certifica a configuração em execução nem a segurança do serviço. A equipe responsável deve validar a unidade efetiva e testar compatibilidade em ambiente controlado.
- Não altere produção sem autorização, revisão, plano de rollback e janela apropriada. Não leia ou publique arquivos de terceiros, configurações internas ou dados sensíveis.
- O limite de 256 KiB evita leitura acidental de arquivos muito grandes, mas não é uma garantia geral contra problemas do ambiente.

## Exemplo seguro em Python

Salve como `review_systemd_unit.py`. O programa só lê um arquivo local limitado; não chama comandos do sistema.

```python
#!/usr/bin/env python3
"""Revisa declarações selecionadas de hardening em unidade systemd local."""
import argparse
import sys
from pathlib import Path

MAX_BYTES = 256 * 1024
REQUIRED = {
    "NoNewPrivileges": "true",
    "PrivateTmp": "true",
    "ProtectSystem": "strict",
    "ProtectHome": "true",
}


def review(path: Path) -> tuple[int, list[str]]:
    if path.is_symlink():
        return 2, ["entrada rejeitada: links simbólicos não são aceitos"]
    try:
        raw = path.read_bytes()
    except OSError:
        return 2, ["entrada rejeitada: não foi possível ler o arquivo local"]
    if len(raw) > MAX_BYTES:
        return 2, ["entrada rejeitada: arquivo excede 256 KiB"]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return 2, ["entrada rejeitada: arquivo não é UTF-8 válido"]

    in_service = False
    declared = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_service = line[1:-1].strip() == "Service"
            continue
        if not in_service or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in REQUIRED:
            declared[key] = value.strip().lower()

    findings = []
    for key, expected in REQUIRED.items():
        if declared.get(key) != expected:
            findings.append(f"revisar opção {key}: declaração esperada não localizada")
    if not findings:
        findings.append("as quatro declarações selecionadas foram localizadas; validar configuração efetiva")
    return (1 if any(declared.get(k) != v for k, v in REQUIRED.items()) else 0), findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unit_file", type=Path, help="arquivo de unidade local autorizado")
    args = parser.parse_args()
    code, findings = review(args.unit_file)
    for finding in findings:
        print(f"- {finding}")
    return code


if __name__ == "__main__":
    sys.exit(main())
```

Teste com conteúdo fictício e temporário (salve o script anterior como `review_systemd_unit.py` no diretório de execução):

```bash
python3 - <<'PY'
import tempfile
from pathlib import Path
from review_systemd_unit import review

complete = """[Unit]\nDescription=Exemplo fictício\n[Service]\nNoNewPrivileges=true\nPrivateTmp=true\nProtectSystem=strict\nProtectHome=true\n[Install]\nWantedBy=multi-user.target\n"""
incomplete = """[Service]\nPrivateTmp=false\nProtectSystem=full\n"""
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "example.service"
    path.write_text(complete, encoding="utf-8")
    code, findings = review(path)
    assert code == 0 and "validar configuração efetiva" in findings[0]
    path.write_text(incomplete, encoding="utf-8")
    code, findings = review(path)
    assert code == 1 and len(findings) == 4
print("Teste local passou: declarações fictícias completas e incompletas foram distinguidas.")
PY
```

Código de saída `0` indica somente que as quatro declarações selecionadas foram encontradas; `1` indica opções a revisar; `2` indica rejeição ou erro de leitura. Nenhum desses resultados substitui a revisão da unidade efetiva pela equipe responsável.

## Checklist

- [ ] Confirmei autorização para revisar o arquivo e usei uma cópia local apropriada.
- [ ] Usei somente conteúdo fictício no teste; não incluí segredos nem configurações internas.
- [ ] Verifiquei que o exemplo apenas lê o arquivo, não executa comandos, não usa rede e não modifica serviços.
- [ ] Executei o teste local para exemplos fictícios completos e incompletos.
- [ ] Considerei requisitos do serviço, drop-ins e diferenças de versão antes de interpretar os achados.
- [ ] Planejei revisão, teste de compatibilidade e rollback antes de qualquer mudança autorizada.
