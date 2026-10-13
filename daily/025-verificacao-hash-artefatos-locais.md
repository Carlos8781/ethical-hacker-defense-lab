# Dia 025 — Verificação local de hash de artefatos

## Objetivo

Compare o SHA-256 de um arquivo local com um valor de referência obtido por um canal confiável e independente. Isso ajuda a detectar alterações acidentais ou inesperadas em artefatos administrados por você, como um backup ou pacote interno. Um hash identifica o conteúdo; por si só, não demonstra quem o produziu nem que a fonte é confiável.

## Exemplo seguro em Python

O exemplo abaixo só lê um arquivo informado pelo operador, exige um arquivo regular local de até 50 MiB e compara seu hash com uma referência hexadecimal fornecida. Não acessa a rede, não altera o arquivo e não imprime seu conteúdo. Use apenas arquivos próprios ou explicitamente autorizados e referências obtidas conforme o processo da sua organização.

```python
import hashlib
import hmac
import os
import re
import stat
import sys

MAX_BYTES = 50 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def main(path: str, expected: str) -> int:
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        print("referência inválida: informe 64 dígitos hexadecimais", file=sys.stderr)
        return 2

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = None
    try:
        fd = os.open(path, flags)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            raise ValueError("tipo ou tamanho não permitido")

        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(fd, CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError("arquivo excede o limite")
            digest.update(chunk)
    except (OSError, ValueError):
        print("não foi possível verificar o arquivo local permitido", file=sys.stderr)
        return 2
    finally:
        if fd is not None:
            os.close(fd)

    matches = hmac.compare_digest(digest.hexdigest(), expected.lower())
    print("SHA-256 confere" if matches else "SHA-256 diferente da referência")
    return 0 if matches else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"uso: {sys.argv[0]} ARQUIVO SHA256_ESPERADO", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
```

Salve como `verify_local_hash.py`. Teste somente com fixture fictício em diretório temporário:

```bash
printf 'conteudo de teste ficticio\n' > /tmp/hash-fixture.txt
python3 -c "import hashlib; print(hashlib.sha256(b'conteudo de teste ficticio\\n').hexdigest())"
python3 verify_local_hash.py /tmp/hash-fixture.txt <HASH_IMPRESSO>
# Resultado esperado: SHA-256 confere; código de saída 0
python3 verify_local_hash.py /tmp/hash-fixture.txt 0000000000000000000000000000000000000000000000000000000000000000
# Resultado esperado: SHA-256 diferente da referência; código de saída 1
rm /tmp/hash-fixture.txt
```

Substitua `<HASH_IMPRESSO>` pela saída do comando local. Não inclua o arquivo de teste ou dados internos no repositório.

## Checklist

- [ ] O arquivo é local, regular, de origem conhecida e está dentro do escopo autorizado.
- [ ] A referência SHA-256 veio de canal independente e confiável, não do mesmo local potencialmente alterado.
- [ ] O teste inicial usou conteúdo fictício e confirmou tanto igualdade quanto divergência.
- [ ] Nenhum dado sensível, segredo ou conteúdo do arquivo foi exibido, enviado ou publicado.
- [ ] Um resultado divergente foi tratado como sinal para revisão humana e processo aprovado, não como prova automática de comprometimento.
- [ ] A ferramenta e o fluxo de custódia são adequados à criticidade do artefato.

## Limitações e ética

SHA-256 permite comparar conteúdo, mas não autentica a origem da referência. Se o artefato e o hash forem obtidos pelo mesmo canal comprometido, ambos podem ter sido substituídos. A verificação também não avalia se o conteúdo é benigno, correto, completo ou seguro para execução. O limite de tamanho é uma escolha didática; o exemplo não foi projetado para arquivos especiais, volumes muito grandes ou cenários concorrentes em que outro processo modifica o arquivo durante a leitura. `O_NOFOLLOW` depende do suporte do sistema operacional; em plataformas sem essa opção, não confie neste exemplo como proteção contra links simbólicos sem antes revisar a implementação. Em falhas, a mensagem é genérica para evitar revelar detalhes de caminhos ou dados.

Não use o script para acessar arquivos de terceiros, contornar permissões ou validar artefatos de origem desconhecida para então executá-los. Em caso de divergência, preserve o original conforme a política local, confirme a referência com a equipe responsável e siga o procedimento autorizado de resposta a incidentes.

> Exemplo somente leitura, limitado a arquivo local autorizado e sem qualquer conexão de rede.
<!-- Testado localmente com fixture fictício; nenhum arquivo sensível ou acesso de rede foi utilizado. -->
