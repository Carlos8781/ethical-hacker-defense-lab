# Dia 020 — Verificação local da atualidade de um backup

Um inventário periódico pode detectar se um artefato de backup esperado deixou de ser atualizado dentro da janela definida pela equipe. Este guia apresenta uma verificação **local e somente de leitura** de um arquivo de backup específico: consulta seus metadados, compara a última modificação com um limite configurado e informa se é necessário revisar. Não abre o conteúdo, não percorre diretórios, não acessa a rede e não altera arquivos.

## Uso autorizado e limitações éticas

Teste primeiro com um arquivo descartável criado por você. Use o verificador somente para artefatos locais que você possui ou tem autorização explícita para revisar. Nomes de arquivos e caminhos podem revelar detalhes de infraestrutura; não publique caminhos, resultados identificáveis, nomes de clientes ou informações de backups reais. Nunca inclua credenciais, chaves ou conteúdo de backup neste repositório.

O limite de horas é um parâmetro didático e deve refletir a política aprovada, a frequência de backup e a janela de manutenção. A data de modificação pode estar ausente, incorreta ou ser alterada; um arquivo recente **não prova** que o backup terminou corretamente, está íntegro, contém os dados esperados ou pode ser restaurado. Este teste não verifica retenção, criptografia, cadeia de custódia nem cópias remotas. Um alerta é motivo para revisão pelo responsável autorizado, não evidência de incidente.

## Exemplo seguro em Python

Salve como `check_backup_freshness.py`. O programa abre um único arquivo local sem seguir link simbólico final, confirma que o descritor se refere a um arquivo regular e usa somente o horário de modificação informado pelo sistema. Não lê nem exibe o conteúdo ou o caminho do arquivo.

```python
#!/usr/bin/env python3
"""Check the age of one authorized local backup artifact, without reading it."""
import argparse
import os
import stat
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup_file", help="arquivo local de backup autorizado")
    parser.add_argument(
        "--max-age-hours", type=float, default=26.0,
        help="idade máxima em horas para revisão (padrão didático: 26)",
    )
    args = parser.parse_args()
    if not (0 < args.max_age_hours <= 24 * 365):
        parser.error("--max-age-hours deve ser maior que 0 e no máximo 8760")
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        print("plataforma não suportada; nenhum arquivo foi alterado", file=sys.stderr)
        return 2

    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        fd = os.open(args.backup_file, flags)
        try:
            info = os.fstat(fd)
        finally:
            os.close(fd)
    except OSError:
        print("não foi possível verificar o arquivo local", file=sys.stderr)
        return 2
    if not stat.S_ISREG(info.st_mode):
        print("alvo não é um arquivo regular", file=sys.stderr)
        return 2

    age_seconds = max(0.0, time.time() - info.st_mtime)
    age_hours = age_seconds / 3600
    print(f"idade observada: {age_hours:.2f} horas")
    if age_hours > args.max_age_hours:
        print("revisão necessária: artefato fora da janela configurada")
        return 1
    print("idade dentro da janela configurada; valide o backup pelo processo aprovado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste somente com arquivos fictícios em diretório temporário:

Salve o código do exemplo como `check_backup_freshness.py` no diretório de trabalho e execute:

```bash
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
printf 'conteúdo fictício, não é um backup real\n' > "$tmpdir/backup-lab.bin"
python3 check_backup_freshness.py "$tmpdir/backup-lab.bin" --max-age-hours 1
# Demonstra a condição de alerta sem esperar:
touch -d '2 hours ago' "$tmpdir/backup-lab.bin"
python3 check_backup_freshness.py "$tmpdir/backup-lab.bin" --max-age-hours 1
```

Na primeira execução, o código de saída esperado é `0`; após o ajuste de horário, o esperado é `1`. Um caminho ausente, link simbólico final, arquivo não regular ou opção inválida resulta em código `2`. O uso de `touch` acima altera apenas o arquivo fictício do laboratório. Não altere timestamps de artefatos operacionais para contornar uma verificação.

## Checklist

- [ ] A autorização e o escopo da consulta ao artefato local estão documentados.
- [ ] O teste inicial usou exclusivamente um arquivo fictício e descartável.
- [ ] O limite foi definido conforme política de backup e janela operacional aprovadas.
- [ ] O verificador foi executado localmente e somente consultou metadados de um arquivo explícito.
- [ ] Nenhum conteúdo de backup, caminho interno ou dado identificável foi publicado ou enviado a terceiros.
- [ ] Um resultado recente não foi confundido com prova de integridade, conclusão ou capacidade de restauração.
- [ ] Alertas foram revisados por responsável autorizado usando logs e ferramentas de backup aprovados.
- [ ] A integridade e a restauração são verificadas separadamente em exercícios controlados, conforme procedimento da organização.
- [ ] Nenhuma senha, chave, token ou outro segredo foi incluído no código, teste ou repositório.

## Limitações e próximos passos

O exemplo consulta somente `st_mtime` de um arquivo regular aberto localmente em sistema POSIX. Não confirma se o arquivo é um backup, se a tarefa terminou sem erro, se os dados são completos, se há corrupção, se existe uma cópia em outro local ou se a restauração funciona. Relógios incorretos, cópias de arquivos e políticas que preservam timestamps podem produzir resultados enganosos. Para operação real, compare o resultado com o status da ferramenta de backup aprovada, logs protegidos e um teste periódico de restauração em ambiente controlado. Não automatize exclusão, substituição ou alteração de configuração com base neste exemplo.

## Referências de consulta local

- Documentação local do Python: `os.open`, `os.fstat`, `stat` e `time`.
- Política aprovada de backup, retenção, monitoramento e recuperação da organização.

> Este exemplo é uma verificação local e passiva de metadados em um artefato autorizado. Não acessa sistemas externos, não lê o conteúdo do backup e não substitui validação de integridade ou teste de restauração.
<!-- Testado localmente com arquivo fictício; nenhuma conexão de rede foi realizada. -->
