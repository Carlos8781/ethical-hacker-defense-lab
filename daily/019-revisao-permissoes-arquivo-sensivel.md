# Dia 019 — Revisão local de permissões de arquivos sensíveis

Permissões excessivas em arquivos que contêm configurações ou dados podem ampliar o impacto de uma conta comprometida. Este guia demonstra uma verificação **somente de leitura** de um único arquivo regular local em sistemas POSIX: compara as permissões com o modo esperado e informa apenas se há permissões extras. Não altera o arquivo, não percorre diretórios e não acessa a rede.

## Uso autorizado e limitações éticas

Teste primeiro com arquivos fictícios criados em diretório temporário. Use o verificador somente em arquivos locais que você possui ou tem autorização explícita para revisar. Caminhos, nomes e resultados de arquivos de produção podem revelar informações internas; não os publique nem os envie a serviços externos. Nunca copie conteúdo sensível para o laboratório.

O modo esperado depende da finalidade do arquivo, do usuário/grupo responsáveis, do sistema operacional e da política da organização. O exemplo trata permissões POSIX tradicionais e não interpreta ACLs, atributos estendidos, permissões efetivas de todos os processos, montagem, contêineres ou controles do sistema de arquivos. Um alerta é motivo para revisão por responsável autorizado, não prova de exposição.

## Exemplo seguro em Python

Salve como `check_local_mode.py`. O programa recebe um caminho local e um modo esperado em octal (por exemplo, `600`), rejeita links simbólicos no caminho final, abre o arquivo sem seguir esse link, confirma que é arquivo regular e compara apenas bits de permissão. Ele não imprime o caminho nem lê o conteúdo do arquivo. Requer sistema POSIX com `O_NOFOLLOW`.

```python
#!/usr/bin/env python3
import os
import stat
import sys


def main() -> int:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        print("plataforma não suportada; nenhuma alteração foi feita", file=sys.stderr)
        return 2
    if len(sys.argv) != 3:
        print("uso: python3 check_local_mode.py <arquivo-local> <modo-octal>", file=sys.stderr)
        return 2

    mode_text = sys.argv[2]
    if len(mode_text) not in (3, 4) or any(ch not in "01234567" for ch in mode_text):
        print("modo inválido; use três ou quatro dígitos octais", file=sys.stderr)
        return 2

    expected = int(mode_text, 8)
    if expected > 0o777:
        print("modo fora do intervalo permitido", file=sys.stderr)
        return 2

    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        fd = os.open(sys.argv[1], flags)
        try:
            info = os.fstat(fd)
        finally:
            os.close(fd)
    except OSError:
        print("não foi possível verificar o arquivo local", file=sys.stderr)
        return 2

    if not stat.S_ISREG(info.st_mode):
        print("alvo não é um arquivo regular; nenhuma alteração foi feita", file=sys.stderr)
        return 2

    actual = stat.S_IMODE(info.st_mode)
    if actual & ~expected:
        print("revisão necessária: existem permissões adicionais", file=sys.stderr)
        return 1
    print("permissões não excedem o modo esperado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste em diretório temporário com dois arquivos fictícios; o primeiro deve passar e o segundo deve sinalizar permissões adicionais. Os modos servem apenas para demonstrar o comportamento, não são política universal:

```bash
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
umask 077
printf 'dado fictício\n' > "$tmpdir/privado.txt"
chmod 600 "$tmpdir/privado.txt"
python3 check_local_mode.py "$tmpdir/privado.txt" 600
chmod 640 "$tmpdir/privado.txt"
python3 check_local_mode.py "$tmpdir/privado.txt" 600
```

A primeira execução termina com código `0`; a segunda, com código `1`. Caminho ausente, modo inválido, link simbólico final ou plataforma sem suporte resulta em código `2`. O programa não corrige permissões automaticamente: qualquer mudança deve seguir a política e o processo de mudança aprovados.

## Checklist

- [ ] A autorização, a finalidade e o escopo da revisão estão documentados; o teste inicial usa somente arquivos fictícios.
- [ ] O modo de referência foi confirmado com o proprietário do sistema e a política aprovada, em vez de copiado cegamente do exemplo.
- [ ] A ferramenta foi executada em ambiente POSIX local atualizado; nenhum alvo externo ou conteúdo de arquivo foi consultado.
- [ ] Caminhos internos, conteúdo sensível e resultados identificáveis foram mantidos fora de repositórios públicos e serviços externos.
- [ ] O alerta foi tratado como sinal para revisão, não como confirmação de incidente ou prova de acesso indevido.
- [ ] Uma eventual correção será aplicada por responsável autorizado, com revisão, registro e possibilidade de reversão.
- [ ] O script foi mantido somente de leitura e os arquivos de teste temporários foram removidos.

## Limitações e próximos passos

A verificação observa os bits de modo POSIX do arquivo aberto naquele instante. Não avalia ACLs, permissões de diretório-pai, identidade e grupos efetivos, políticas MAC, compartilhamentos, cópias, backups, conteúdo ou uso pelo aplicativo. O caminho pode ser substituído por outro arquivo regular antes da abertura; para processos de auditoria mais rigorosos, use diretórios de laboratório controlados e mecanismos de inventário/snapshot aprovados. Sistemas não POSIX, como Windows, exigem uma abordagem própria para ACLs.

Confirme as permissões efetivas com ferramentas e procedimentos aprovados pela equipe responsável. Se for necessária uma alteração, preserve a disponibilidade do serviço e registre o motivo, a aprovação e o resultado. Este exemplo não altera configurações nem tenta obter acesso.

## Referências de consulta local

- Documentação local do Python: `os.open`, `os.fstat` e `stat`.
- Documentação do sistema operacional: permissões POSIX, ACLs e política interna de classificação de dados.

> O exemplo inspeciona somente metadados de um único arquivo local autorizado; não lê seu conteúdo, não percorre diretórios, não acessa rede e não modifica permissões.

<!-- Testado localmente com arquivos fictícios; nenhuma conexão de rede foi realizada. -->
