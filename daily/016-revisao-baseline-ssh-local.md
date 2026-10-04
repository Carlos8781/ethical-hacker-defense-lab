# Dia 016 — Revisão de baseline de hardening SSH local

Uma baseline documentada ajuda uma equipe a revisar escolhas de hardening antes de implantá-las. Este exercício valida um pequeno perfil **fictício** de opções SSH em JSON e sinaliza valores fora dos critérios didáticos definidos abaixo. Ele não lê `sshd_config`, não calcula a configuração efetiva do OpenSSH e não se conecta a nenhum servidor.

## Uso autorizado e limitações éticas

Use primeiro o exemplo sintético. O programa lê somente o arquivo JSON explicitamente indicado, não acessa a rede, não consulta hosts, não executa comandos remotos, não altera configurações e não imprime valores recebidos. Não coloque nomes de hosts, endereços, caminhos internos, usuários, chaves privadas, senhas, tokens ou configurações reais em um repositório público.

Os critérios no exemplo — autenticação por senha e login direto de root desabilitados, autenticação por chave habilitada, encaminhamento X11 desabilitado e no máximo quatro tentativas — são **um exercício ilustrativo**, não uma norma universal. Aplicabilidade depende do modelo de acesso, dos controles compensatórios, dos requisitos operacionais e da política aprovada da organização. Nunca aplique uma mudança em produção sem revisão, autorização, plano de recuperação e teste de acesso administrativo para evitar bloqueio acidental.

Este formato reduz deliberadamente as opções a cinco campos; não é um parser do OpenSSH. Arquivos reais podem combinar diretivas repetidas, `Include`, blocos `Match`, padrões e valores padrão que determinam o resultado efetivo. Portanto, a aprovação deste JSON não demonstra que um servidor esteja configurado de forma segura nem que a configuração em execução corresponda ao perfil.

## Exemplo seguro em Python

Salve como `check_ssh_baseline.py`. O verificador aceita apenas um objeto JSON com exatamente os campos e tipos enumerados no código, limita a leitura a 16 KiB e informa somente se há critérios pendentes. Ele não mostra o conteúdo do arquivo.

```python
#!/usr/bin/env python3
"""Review a synthetic, local SSH-hardening profile; never connects to a host."""
import argparse
import json
from pathlib import Path

MAX_BYTES = 16 * 1024
BOOLEAN_OPTIONS = {
    "password_authentication",
    "permit_root_login",
    "pubkey_authentication",
    "x11_forwarding",
}
EXPECTED_KEYS = BOOLEAN_OPTIONS | {"max_auth_tries"}


def validate(profile: object) -> dict[str, object]:
    if not isinstance(profile, dict) or set(profile) != EXPECTED_KEYS:
        raise ValueError("schema")
    for key in BOOLEAN_OPTIONS:
        if not isinstance(profile[key], str) or profile[key] not in {"yes", "no"}:
            raise ValueError("value")
    tries = profile["max_auth_tries"]
    if type(tries) is not int or not 1 <= tries <= 20:
        raise ValueError("value")
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path, help="perfil JSON local e sintético")
    args = parser.parse_args()

    try:
        if args.json_file.is_symlink() or not args.json_file.is_file():
            raise ValueError("file")
        if args.json_file.stat().st_size > MAX_BYTES:
            raise ValueError("size")
        with args.json_file.open("r", encoding="utf-8") as stream:
            profile = validate(json.load(stream))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        parser.error("arquivo JSON local inválido, grande demais ou fora do esquema esperado")

    findings = []
    if profile["password_authentication"] != "no":
        findings.append("autenticação por senha requer revisão")
    if profile["permit_root_login"] != "no":
        findings.append("login direto de root requer revisão")
    if profile["pubkey_authentication"] != "yes":
        findings.append("autenticação por chave requer revisão")
    if profile["x11_forwarding"] != "no":
        findings.append("encaminhamento X11 requer revisão")
    if profile["max_auth_tries"] > 4:
        findings.append("limite de tentativas requer revisão")

    if findings:
        print(f"revisão necessária: {len(findings)} critério(s) fora da baseline ilustrativa")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("perfil sintético: critérios da baseline ilustrativa atendidos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Crie arquivos temporários com valores inteiramente fictícios e teste os dois resultados:

```bash
cat > /tmp/ssh-baseline-ficticia.json <<'EOF'
{
  "password_authentication": "yes",
  "permit_root_login": "no",
  "pubkey_authentication": "yes",
  "x11_forwarding": "no",
  "max_auth_tries": 3
}
EOF
python3 check_ssh_baseline.py /tmp/ssh-baseline-ficticia.json
printf '{"password_authentication":"no","permit_root_login":"no","pubkey_authentication":"yes","x11_forwarding":"no","max_auth_tries":3}\n' > /tmp/ssh-baseline-ok-ficticia.json
python3 check_ssh_baseline.py /tmp/ssh-baseline-ok-ficticia.json
```

No primeiro teste, o programa sinaliza que um critério requer revisão e termina com código `1`; no segundo, informa que o perfil sintético atende à baseline ilustrativa e termina com código `0`. Arquivo inexistente, JSON inválido, link simbólico, tamanho acima do limite, chave adicional/ausente ou valor fora do esquema encerra com erro de argumento (código `2`). O sinal de revisão não comprova vulnerabilidade nem determina sozinho uma mudança.

## Checklist

- [ ] O teste inicial usa somente os arquivos sintéticos descartáveis descritos neste guia.
- [ ] Há autorização e escopo documentados antes de revisar qualquer configuração real por processo separado.
- [ ] Nenhum host, usuário, chave, segredo, endereço, caminho interno ou configuração real foi copiado para o exemplo, saída ou repositório público.
- [ ] Os critérios foram aprovados pelas equipes responsáveis e adaptados aos requisitos de acesso e continuidade.
- [ ] O resultado foi tratado como triagem de um perfil simplificado, não como validação da configuração SSH efetiva.
- [ ] Antes de qualquer alteração autorizada, há revisão por pares, backup/recuperação e teste que evite bloquear o acesso administrativo.
- [ ] Mudanças em sistemas são realizadas somente por responsáveis autorizados, com registro e processo de mudança aprovados.
- [ ] Nenhuma conexão, varredura, alteração ou ação foi realizada contra sistemas de terceiros.

## Limitações e próximos passos

O script valida estrutura e compara valores fornecidos com uma baseline didática fixa. Não inspeciona processos, serviços, arquivos de configuração, permissões, versões, chaves, logs, rede ou controles compensatórios; tampouco prova a identidade do autor ou a atualidade dos dados. Não o use para inferir o estado de um servidor. Para uma revisão real, siga o procedimento interno aprovado, utilize ferramentas administrativas autorizadas para obter o estado efetivo, preserve dados sensíveis e obtenha validação de responsáveis por segurança e operações antes de qualquer mudança.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `argparse`, `json` e `pathlib`.
- Manual local do OpenSSH (`sshd_config(5)`) e políticas aprovadas de hardening e gestão de mudanças.

> Este exemplo valida apenas um JSON sintético local; não lê configurações reais, não acessa rede e não aplica alterações.

<!-- Testado localmente com Python 3 e JSON sintético. -->
