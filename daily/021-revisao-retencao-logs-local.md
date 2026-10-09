# Dia 021 — Revisão local de retenção e rotação de logs

Uma política explícita de rotação ajuda a limitar o crescimento de logs e a preservar dados pelo período aprovado. Este guia demonstra uma revisão **local e somente de leitura** de um único arquivo de configuração no formato comum do `logrotate`. O verificador aponta a presença de diretivas selecionadas; não executa o `logrotate`, não abre logs, não percorre diretórios e não altera configurações.

## Uso autorizado e limitações éticas

Comece com o arquivo fictício abaixo, criado em um diretório temporário. Use o exemplo apenas em arquivos locais que você possui ou tem autorização explícita para revisar. Configurações podem expor caminhos, nomes de serviços e detalhes internos: não publique configurações reais, caminhos identificáveis nem conteúdo de logs. Não inclua segredos ou dados pessoais em exemplos ou no repositório.

O verificador aplica uma heurística didática a um subconjunto de diretivas. A presença de uma diretiva não prova que a configuração completa seja válida, esteja habilitada, seja carregada pelo serviço ou cumpra uma obrigação legal. Retenção, acesso, compressão e descarte devem seguir a política aprovada e os requisitos de privacidade. Um alerta é uma solicitação de revisão, não confirmação de incidente. Não altere configurações de produção sem autorização, revisão e plano de reversão.

## Exemplo seguro em Python

Salve como `check_logrotate_policy.py`. Ele recebe **um único arquivo local**, rejeita links simbólicos finais, limita a leitura a 64 KiB e imprime somente as diretivas encontradas ou ausentes. Não imprime o caminho nem o conteúdo do arquivo.

```python
#!/usr/bin/env python3
"""Review selected directives in one authorized local logrotate config."""
import os
import re
import stat
import sys

MAX_BYTES = 64 * 1024
REQUIRED = {"daily", "rotate", "compress", "missingok", "notifempty"}


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: python3 check_logrotate_policy.py <config-local>", file=sys.stderr)
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

    # Evaluate directives outside comments; this intentionally does not parse
    # nested blocks or validate the complete logrotate grammar.
    directives = set()
    for line in text.splitlines():
        content = line.split("#", 1)[0].strip()
        match = re.match(r"([A-Za-z][A-Za-z0-9_]*)", content)
        if match:
            directives.add(match.group(1))

    missing = sorted(REQUIRED - directives)
    if missing:
        print("revisão necessária: diretivas ausentes — " + ", ".join(missing))
        return 1
    print("diretivas selecionadas presentes; confirme a política e a configuração completa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste com uma configuração fictícia em `/tmp`; ela não contém caminhos reais e o script só a lê:

```bash
cat > /tmp/logrotate-ficticio.conf <<'EOF'
/var/log/example/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
}
EOF
python3 check_logrotate_policy.py /tmp/logrotate-ficticio.conf
```

O teste deve terminar com código `0`. Para testar a detecção de ausência sem modificar o arquivo aprovado, crie um segundo fixture fictício omitindo `compress`; o verificador deve indicar a diretiva ausente e terminar com código `1`. Arquivo ausente, inválido, maior que o limite ou plataforma incompatível resulta em código `2`. Remova os fixtures temporários após o teste. Nunca passe logs reais ou conteúdo de produção para o exemplo.

## Checklist

- [ ] O teste foi feito primeiro com configuração fictícia; o arquivo examinado é local e está dentro do escopo autorizado.
- [ ] A política de retenção e o número de cópias foram definidos pelo responsável, considerando requisitos operacionais, privacidade e regras aplicáveis.
- [ ] A compressão, permissões de acesso, espaço disponível e descarte foram revisados por uma pessoa responsável.
- [ ] A configuração completa foi validada com ferramentas e procedimentos aprovados antes de qualquer mudança.
- [ ] Nenhum log, dado pessoal, caminho real ou segredo foi copiado para o repositório ou enviado a serviços externos.
- [ ] Mudanças de produção têm revisão, janela aprovada e plano de reversão; o script não aplica mudanças.
- [ ] Nenhum host ou serviço foi consultado; o exemplo apenas lê um arquivo local e não altera dados.

## Limitações e próximos passos

A análise reconhece somente nomes de diretivas em linhas não comentadas e não interpreta blocos, inclusões, ordem, argumentos, variáveis ou regras condicionais. Comentários embutidos em valores e diferenças entre versões podem afetar a interpretação. O script não valida sintaxe, permissões, propriedade, políticas efetivamente carregadas, funcionamento da rotação, retenção em armazenamento remoto, criptografia ou restauração. Uma diretiva presente pode estar fora do bloco relevante ou ser inadequada à política.

Confirme a política e a configuração efetiva com documentação local da versão instalada e com o responsável pelo serviço. Valide qualquer mudança em laboratório ou ambiente de teste aprovado. Não execute ferramentas de rotação sobre dados reais como parte deste exercício.

> Este exemplo inspeciona um único arquivo local autorizado, sem executar serviços, abrir logs, acessar rede ou modificar arquivos.

<!-- Testado localmente com fixtures fictícios; nenhuma conexão de rede foi realizada. -->
