# Dia 059 — Validação local de `security.txt`

Um arquivo `security.txt` documenta como pesquisadores podem comunicar vulnerabilidades de forma responsável. Revisá-lo ajuda a equipe administradora a detectar campos ausentes, datas inválidas ou contatos malformados antes de publicar a política. Este exercício verifica uma cópia local; não visita o domínio nem testa se contatos ou URLs existem.

## Exemplo seguro em Python

Salve como `check_security_txt.py` e execute `python3 check_security_txt.py caminho/para/security.txt`. O programa só lê o arquivo indicado, não segue links, não conecta à rede, não imprime valores dos campos e não altera o arquivo. Requer Python 3.10 ou mais recente.

```python
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import sys


def validate(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return ["Não foi possível ler o arquivo local em UTF-8."]

    fields: dict[str, list[str]] = {}
    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            return [f"Linha {number}: formato de campo inválido."]
        name, value = line.split(":", 1)
        name, value = name.strip().lower(), value.strip()
        if not name or not value:
            return [f"Linha {number}: campo ou valor vazio."]
        fields.setdefault(name, []).append(value)

    errors: list[str] = []
    contacts = fields.get("contact", [])
    if not contacts:
        errors.append("Campo Contact ausente.")
    for contact in contacts:
        if contact.startswith("mailto:"):
            address = contact[len("mailto:"):]
            if address.count("@") != 1 or any(ch.isspace() for ch in address):
                errors.append("Formato de Contact mailto inválido.")
        else:
            parts = urlsplit(contact)
            if parts.scheme != "https" or not parts.netloc:
                errors.append("Contact deve ser mailto: ou URL HTTPS absoluta.")

    expirations = fields.get("expires", [])
    if len(expirations) != 1:
        errors.append("Deve existir exatamente um campo Expires.")
    else:
        try:
            expiry = datetime.fromisoformat(expirations[0].replace("Z", "+00:00"))
            if expiry.tzinfo is None or expiry.utcoffset() != timezone.utc.utcoffset(expiry):
                raise ValueError("Expires deve estar em UTC.")
            if expiry <= datetime.now(timezone.utc):
                errors.append("Expires está vencido.")
        except ValueError:
            errors.append("Expires deve ser uma data ISO 8601 futura em UTC.")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python3 check_security_txt.py <arquivo-local>")
        return 2
    errors = validate(Path(sys.argv[1]))
    if errors:
        for error in errors:
            print(f"REVISAR: {error}")
        return 1
    print("Estrutura básica válida; revise manualmente antes da publicação.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Limitações e cuidados éticos

- Use a ferramenta somente em arquivos locais de um domínio ou organização que você administra ou para os quais tem autorização explícita.
- O validador verifica apenas campos básicos, formato de contato e expiração; não implementa toda a especificação, não comprova a identidade do contato, não testa links, não consulta DNS e não verifica a localização canônica do arquivo.
- Um resultado válido não garante que a política esteja correta, atualizada ou operacional. Uma pessoa responsável deve confirmar autorização, conteúdo, canal de divulgação e processo de resposta antes da publicação.
- Não inclua tokens, senhas, dados pessoais ou informações internas no arquivo ou na saída. Use valores fictícios nos testes.
- Este exemplo não examina alvos externos nem tenta descobrir vulnerabilidades. Não use `security.txt` como convite para testar sistemas sem autorização.

## Checklist

- [ ] Confirme que administra o arquivo e o domínio ou tem autorização explícita.
- [ ] Verifique se há ao menos um `Contact` e exatamente um `Expires`.
- [ ] Confirme manualmente que os contatos e a política são aprovados e apropriados para divulgação.
- [ ] Revise se a data de expiração está em UTC e programe uma renovação responsável.
- [ ] Execute o exemplo somente contra uma cópia local com dados fictícios durante os testes.
- [ ] Não trate a validação sintática como prova de disponibilidade ou de segurança.
- [ ] Não teste o domínio, endereços ou sistemas de terceiros sem autorização expressa.

## Teste local

O teste abaixo cria arquivos sintéticos temporários; não acessa a rede nem precisa de dependências adicionais. Salve o programa como `check_security_txt.py` e execute no terminal:

```bash
python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from check_security_txt import validate

with TemporaryDirectory() as directory:
    good = Path(directory) / "security.txt"
    good.write_text(
        "Contact: mailto:security@example.invalid\n"
        "Expires: 2099-01-01T00:00:00Z\n",
        encoding="utf-8",
    )
    assert validate(good) == []

    bad = Path(directory) / "invalid.txt"
    bad.write_text("Contact: http://example.invalid/contact\n", encoding="utf-8")
    assert validate(bad)
print("Testes sintéticos aprovados.")
PY
```

A asserção do arquivo válido deve passar e a do arquivo inválido deve confirmar pelo menos um alerta. O domínio `.invalid` é reservado para exemplos e não é contatado pelo script.
