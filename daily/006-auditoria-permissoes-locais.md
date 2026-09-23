# Dia 006 — Auditoria local de permissões e menor privilégio

O princípio do menor privilégio reduz o impacto de erros e compromissos: cada arquivo, processo e conta deve ter somente as permissões necessárias para sua finalidade. Antes de corrigir permissões, uma auditoria somente leitura pode identificar arquivos graváveis pelo grupo ou por qualquer usuário em uma árvore de laboratório administrada pela equipe. O resultado deve ser revisado contra o funcionamento esperado da aplicação, porque permissões amplas podem ser intencionais em diretórios compartilhados.

## Uso autorizado e limitações éticas

Use este exemplo apenas em diretórios locais que você administra ou para os quais possui autorização explícita. Ele não faz varredura de rede, não consulta hosts externos, não tenta acessar arquivos protegidos, não altera permissões e não contorna controles do sistema operacional. A saída pode revelar nomes e caminhos internos; salve-a somente em local aprovado e remova dados desnecessários antes de compartilhá-la. Nunca use este procedimento para enumerar sistemas de terceiros, coletar credenciais ou testar acesso não autorizado.

A auditoria identifica apenas bits de permissão POSIX de arquivos regulares visíveis na árvore indicada. Ela não determina se uma permissão é necessária, não cobre ACLs, permissões de compartilhamentos, políticas MAC, contêineres ou permissões específicas de aplicações, e não substitui uma revisão de identidade e acesso. Links simbólicos são ignorados para evitar seguir caminhos inesperados.

## Exemplo seguro em Python

O script abaixo percorre uma árvore local escolhida pelo operador e lista arquivos regulares que possuem escrita para o grupo (`g+w`) ou para qualquer usuário (`o+w`). Ele é deliberadamente somente leitura: não executa os arquivos encontrados e não chama comandos externos.

```python
#!/usr/bin/env python3
"""Audit excessive POSIX write permissions in an authorized local tree."""
from __future__ import annotations

import argparse
import stat
from pathlib import Path


def writable_files(root: Path) -> list[tuple[Path, int]]:
    findings: list[tuple[Path, int]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        mode = path.stat(follow_symlinks=False).st_mode
        if mode & (stat.S_IWGRP | stat.S_IWOTH):
            findings.append((path, stat.S_IMODE(mode)))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="diretório local autorizado")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"diretório inexistente: {root}")

    findings = writable_files(root)
    for path, mode in findings:
        print(f"REVISAR {path.relative_to(root)} modo={mode:04o}")
    print(f"arquivos revisados: {sum(1 for p in root.rglob('*') if p.is_file() and not p.is_symlink())}")
    print(f"achados para revisão: {len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Salve o trecho como `permission_audit.py` fora do repositório ou em um diretório de testes descartável. Teste primeiro com dados sintéticos em `localhost` ou no próprio computador:

```bash
mkdir -p /tmp/permissions-lab
printf 'relatorio ficticio\n' > /tmp/permissions-lab/privado.txt
printf 'arquivo compartilhado de teste\n' > /tmp/permissions-lab/compartilhado.txt
chmod 0644 /tmp/permissions-lab/privado.txt
chmod 0664 /tmp/permissions-lab/compartilhado.txt
python3 permission_audit.py /tmp/permissions-lab
```

Nesse exemplo, `compartilhado.txt` deve aparecer como `REVISAR` e o programa deve terminar com código de saída 1, sinalizando que há algo para revisar; isso não significa que a permissão esteja necessariamente errada. Depois de uma decisão documentada do responsável pelo diretório, uma correção pode ser aplicada separadamente pela equipe autorizada, por exemplo com `chmod` em um arquivo sintético. Não automatize a correção sem conhecer os requisitos da aplicação e sem um plano de reversão.

Para uma árvore sem arquivos graváveis pelo grupo ou por qualquer usuário, o programa deve exibir `achados para revisão: 0` e terminar com código 0. Registre apenas o caminho relativo e o modo necessário para o atendimento, sem anexar conteúdo de arquivos.

## Checklist

- [ ] A árvore analisada pertence à equipe ou está coberta por autorização explícita.
- [ ] O primeiro teste usou somente arquivos sintéticos em um diretório local descartável.
- [ ] A auditoria foi executada em modo somente leitura e não seguiu links simbólicos.
- [ ] Cada achado foi comparado com o requisito real da aplicação antes de qualquer mudança.
- [ ] Permissões de contas, grupos, ACLs, compartilhamentos e políticas adicionais foram revisadas quando aplicável.
- [ ] Correções, quando aprovadas, foram feitas por responsável autorizado e têm plano de reversão.
- [ ] O resultado foi armazenado com controle de acesso e sem conteúdo sensível desnecessário.
- [ ] Não foram usados tokens, chaves, credenciais, dados pessoais ou sistemas externos.
- [ ] A revisão periódica e o alerta de novas permissões excessivas estão definidos para os ativos relevantes.

## Limitações e próximos passos

Uma permissão POSIX ampla não prova, por si só, que exista exploração ou falha de segurança; em contrapartida, um resultado limpo não prova que o controle de acesso esteja correto. Combine a auditoria com inventário de proprietários, revisão de grupos, ACLs, logs de alterações, gestão de configuração e testes de restauração. Priorize diretórios com dados sensíveis e arquivos de configuração, mas preserve explicitamente as exceções necessárias e versionadas. Em produção, use ferramentas aprovadas pela organização para monitoramento contínuo e registre quem autorizou cada alteração.

> A finalidade desta lição é encontrar configurações que merecem revisão em sistemas administrados pela equipe, não testar os limites de acesso de terceiros.

## Referências de consulta local

- `man 2 stat` e `man 1 chmod` no sistema operacional administrado.
- A política de controle de acesso e de menor privilégio da própria organização.
