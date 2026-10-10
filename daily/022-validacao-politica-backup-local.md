# Dia 022 — Validação local de política de backup

Uma política de backup explícita facilita revisar se os controles mínimos foram definidos antes de uma rotina ser aprovada. Este guia demonstra uma verificação **local e somente de leitura** de um único arquivo JSON que representa uma política: criptografia em repouso, retenção dentro de uma faixa aprovada e uma cópia isolada. O verificador não executa backups, não acessa destinos, não altera arquivos e não prova que os controles estejam efetivamente ativos.

## Uso autorizado e limitações éticas

Comece com os fixtures fictícios deste guia. Use o verificador apenas em um arquivo local que você possui ou tem autorização explícita para revisar. Não publique configurações reais, nomes de clientes, caminhos internos, credenciais, chaves ou dados pessoais. O exemplo não envia conteúdo a nenhum serviço.

Os limites numéricos são ilustrativos, não uma recomendação universal. A organização responsável deve defini-los segundo os requisitos operacionais, legais e de privacidade. Uma política declarada não comprova criptografia efetiva, isolamento, imutabilidade, restauração bem-sucedida ou cobertura de todos os dados. Não altere políticas ou backups de produção sem autorização, revisão e plano de reversão.

## Exemplo seguro em Python

Salve como `check_backup_policy.py`. O programa lê apenas um arquivo local regular, rejeita symlinks finais, limita o tamanho e imprime somente o resultado das verificações. Não segue diretórios, não se conecta à rede e não modifica o arquivo analisado.

```python
#!/usr/bin/env python3
"""Validate selected fields in one authorized local backup-policy JSON."""
import json
import os
import stat
import sys

MAX_BYTES = 16 * 1024
MIN_RETENTION_DAYS = 7
MAX_RETENTION_DAYS = 365


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: python3 check_backup_policy.py <politica-local.json>", file=sys.stderr)
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
                chunk = os.read(fd, min(4096, MAX_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError("size")
            policy = json.loads(b"".join(chunks).decode("utf-8"))
        finally:
            os.close(fd)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        print("não foi possível ler um JSON local regular dentro do limite; nenhuma alteração foi feita", file=sys.stderr)
        return 2

    if not isinstance(policy, dict):
        print("revisão necessária: a raiz da política deve ser um objeto JSON")
        return 1

    encryption = policy.get("encryption_at_rest") is True
    retention = policy.get("retention_days")
    retention_ok = (
        isinstance(retention, int)
        and not isinstance(retention, bool)
        and MIN_RETENTION_DAYS <= retention <= MAX_RETENTION_DAYS
    )
    isolated = policy.get("isolated_copy") is True
    missing = []
    if not encryption:
        missing.append("encryption_at_rest=true")
    if not retention_ok:
        missing.append(f"retention_days entre {MIN_RETENTION_DAYS} e {MAX_RETENTION_DAYS}")
    if not isolated:
        missing.append("isolated_copy=true")

    if missing:
        print("revisão necessária: " + "; ".join(missing))
        return 1
    print("campos selecionados presentes; confirme controles reais e política aprovada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste em um diretório temporário usando somente dados fictícios:

```bash
cat > /tmp/backup-policy-ficticia.json <<'EOF'
{
  "encryption_at_rest": true,
  "retention_days": 30,
  "isolated_copy": true
}
EOF
python3 check_backup_policy.py /tmp/backup-policy-ficticia.json
```

O teste válido deve terminar com código `0`. Para conferir a detecção, crie outro fixture fictício com `"isolated_copy": false`; o programa deve solicitar revisão e terminar com código `1`. Arquivo ausente, JSON inválido, arquivo acima do limite ou plataforma incompatível resulta em código `2`. Apague os fixtures temporários após o teste. Nunca use conteúdo real para reproduzir exemplos ou erros.

## Checklist

- [ ] O teste foi realizado primeiro com política inteiramente fictícia.
- [ ] O arquivo revisado é local e está dentro do escopo autorizado; nenhum destino de backup foi contatado.
- [ ] A faixa de retenção foi aprovada pela equipe responsável e considera requisitos de negócio, privacidade e obrigações aplicáveis.
- [ ] Responsáveis confirmaram criptografia, isolamento, controle de acesso, proteção contra exclusão indevida e monitoramento no sistema real.
- [ ] A restauração foi exercitada em ambiente aprovado, sem expor dados ou interromper serviços.
- [ ] Nenhum segredo, caminho identificável, dado pessoal ou configuração real foi adicionado ao repositório.
- [ ] O script foi usado apenas como verificação declarativa; não faz alterações, não executa tarefas e não acessa a rede.

## Limitações e próximos passos

O verificador valida apenas três campos e seus tipos/valores básicos em um objeto JSON. Não valida esquema completo, assinatura, origem, permissões de acesso ou adequação jurídica. Também não verifica implementação, criptografia, imutabilidade, isolamento de contas, disponibilidade, retenção real, alertas ou restauração. Um resultado positivo não é certificação de segurança nem substitui auditoria técnica.

Compare a política com os padrões aprovados da organização e confirme controles efetivos com responsáveis e evidências autorizadas. Testes de recuperação devem ocorrer em ambiente controlado, com plano e proteção dos dados. Não use este script para alterar sistemas ou acessar serviços de terceiros.

> Este exemplo lê um único arquivo local autorizado e não faz conexões, varreduras ou alterações.

<!-- Testado localmente com fixtures fictícios; nenhuma conexão de rede foi realizada. -->
