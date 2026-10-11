# Dia 023 — Revisão local de alertas de autenticação

Uma revisão periódica dos registros de autenticação pode ajudar a equipe responsável a priorizar verificações, reconhecer falhas recorrentes e confirmar que alertas foram tratados. Este guia demonstra uma triagem **local e somente de leitura** de um único arquivo JSON Lines (JSONL) com eventos fictícios. O programa conta eventos com resultado `failure` e `success`, sem imprimir identificadores, endereços, nomes, caminhos ou linhas originais. Ele não autentica usuários, não tenta senhas, não consulta serviços e não modifica registros.

## Uso autorizado e limitações éticas

Comece exclusivamente com os dados fictícios deste guia. Use o script apenas em um arquivo local que você possui ou tem autorização explícita para revisar e cujo tratamento esteja de acordo com a política da organização. Logs podem conter dados pessoais, identificadores e detalhes operacionais: não copie registros reais para issues, commits, exemplos, mensagens ou serviços externos. Não inclua segredos.

A contagem é apenas uma triagem. Falhas podem decorrer de erros legítimos, configurações ou eventos automatizados; um número elevado não prova ataque nem identifica uma pessoa. Os limites ilustrativos não são política universal. Não bloqueie contas, altere controles ou tome medidas contra usuários com base somente neste resultado. Encaminhe achados pelo processo aprovado, com acesso mínimo, contexto e revisão humana. Respeite retenção, privacidade e autorização aplicáveis.

## Exemplo seguro em Python

Salve como `review_auth_events.py`. O programa lê um único arquivo regular local, rejeita symlinks finais, limita a leitura a 1 MiB e aceita somente objetos JSON com o campo `result` igual a `success` ou `failure`. Registros inválidos são contados sem revelar seu conteúdo. O arquivo nunca é alterado, e nenhum dado é enviado pela rede.

```python
#!/usr/bin/env python3
"""Count selected outcomes in one authorized local JSONL file."""
import json
import os
import stat
import sys

MAX_BYTES = 1024 * 1024


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: python3 review_auth_events.py <eventos-ficticios.jsonl>", file=sys.stderr)
        return 2
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        print("plataforma não suportada; nenhum arquivo foi alterado", file=sys.stderr)
        return 2

    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        fd = os.open(sys.argv[1], flags)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                raise ValueError("file")
            chunks = []
            total = 0
            while total <= MAX_BYTES:
                chunk = os.read(fd, min(8192, MAX_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError("size")
            text = b"".join(chunks).decode("utf-8")
        finally:
            os.close(fd)
    except (OSError, UnicodeError, ValueError):
        print("não foi possível ler um arquivo local regular dentro do limite; nenhuma alteração foi feita", file=sys.stderr)
        return 2

    counts = {"success": 0, "failure": 0}
    invalid = 0
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid += 1
            continue
        if not isinstance(event, dict) or event.get("result") not in counts:
            invalid += 1
            continue
        counts[event["result"]] += 1

    print(f"eventos válidos: {sum(counts.values())}")
    print(f"success: {counts['success']}; failure: {counts['failure']}; registros inválidos: {invalid}")
    print("triagem informativa; revise contexto e política antes de qualquer ação")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Crie um fixture fictício em um diretório temporário e execute a revisão:

```bash
cat > /tmp/auth-events-ficticios.jsonl <<'EOF'
{"result":"success","actor":"usuario-ficticio-1"}
{"result":"failure","actor":"usuario-ficticio-2"}
{"result":"failure","actor":"usuario-ficticio-2"}
EOF
python3 review_auth_events.py /tmp/auth-events-ficticios.jsonl
```

O exemplo deve contar um sucesso, duas falhas e zero registros inválidos. Acrescente uma linha propositalmente malformada ao fixture para confirmar que o programa aumenta apenas a contagem de inválidos, sem exibir a linha. Um arquivo ausente, inválido em UTF-8, maior que o limite, não regular, symlink final ou uma plataforma sem suporte resulta em código `2`. Apague o fixture após o teste. Não use logs reais para reproduzir o exemplo.

## Checklist

- [ ] O teste foi feito primeiro com registros inteiramente fictícios.
- [ ] O arquivo revisado é local, regular e está dentro do escopo autorizado; nenhuma rede ou serviço foi contatado.
- [ ] O acesso e o tratamento dos logs seguem autorização, política de privacidade, retenção e necessidade de conhecimento.
- [ ] Identificadores, dados pessoais, endereços, caminhos internos e segredos não foram copiados para o repositório ou para serviços externos.
- [ ] Os resultados foram tratados como contagens preliminares, com contexto e revisão humana, não como prova de abuso.
- [ ] Ações sobre contas ou controles seguem processo aprovado, com responsável e evidência independente.
- [ ] O script foi confirmado como somente leitura e não foi usado para alterar, filtrar remotamente ou apagar registros.

## Limitações e próximos passos

O exemplo espera uma linha JSON por evento e reconhece somente o campo `result` com valores minúsculos `success` ou `failure`. Não valida esquema, fuso horário, origem, integridade, completude, duplicatas, correlação, identidade nem significado dos eventos. Linhas inválidas são resumidas sem diagnóstico para evitar vazamento acidental. O limite é didático. Logs truncados, campos diferentes ou formatos distintos podem produzir contagens incompletas. Um resultado não confirma incidente nem substitui um SIEM, controles de auditoria ou investigação formal.

Confirme o formato e as definições com a documentação aprovada da fonte de logs. Se surgir um padrão que mereça análise, siga o processo interno de resposta a incidentes, preserve evidências conforme a política e limite a divulgação. Não investigue contas, sistemas ou usuários fora do escopo autorizado.

> Este exemplo processa um arquivo local autorizado e dados fictícios, sem conexões, tentativas de autenticação ou alterações.

<!-- Testado localmente com fixtures fictícios; nenhuma conexão de rede foi realizada. -->
