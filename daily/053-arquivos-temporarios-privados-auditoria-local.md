# Dia 053 — Arquivos temporários privados para auditoria local

## Objetivo

Relatórios de auditoria podem conter caminhos internos, nomes de serviços ou detalhes operacionais. Ao gerar um relatório temporário, crie-o em um diretório temporário restrito e remova-o automaticamente ao concluir o processamento. Isso reduz a chance de deixar dados de trabalho espalhados em locais compartilhados ou previsíveis.

O exemplo abaixo usa apenas um resumo fictício, cria um diretório temporário com a biblioteca padrão do Python e verifica as permissões no POSIX. O arquivo é criado exclusivamente, sem sobrescrever outro arquivo, com modo restrito no POSIX; o contexto de `TemporaryDirectory` tenta remover os artefatos ao sair do bloco.

## Exemplo seguro em Python

Salve como `temp_audit_demo.py` e execute com `python3 temp_audit_demo.py`. O programa não lê arquivos do usuário nem acessa a rede.

```python
import json
import os
import stat
import tempfile
from pathlib import Path

# Conteúdo sintético: não inclua credenciais nem dados reais de incidentes.
summary = {"source": "laboratorio-local", "findings": 0}

with tempfile.TemporaryDirectory(prefix="audit-report-") as temp_dir:
    report_path = Path(temp_dir) / "summary.json"

    # O_EXCL impede sobrescrita acidental; 0o600 restringe o arquivo no POSIX.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(report_path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as report:
        json.dump(summary, report, ensure_ascii=False)
        report.write("\n")

    if os.name == "posix":
        mode = stat.S_IMODE(report_path.stat().st_mode)
        if mode & 0o077:
            raise RuntimeError(f"Permissões POSIX mais abertas que o esperado: {mode:o}")
        print(f"Relatório temporário criado com modo POSIX {mode:04o}")
    else:
        print("Relatório temporário criado; revise ACLs conforme a política do sistema.")

# Ao sair do bloco, TemporaryDirectory remove o diretório e o relatório.
print("Diretório temporário removido pelo gerenciador de contexto.")
```

## Limitações e cuidados éticos

- Execute somente em seu próprio ambiente ou em ambiente para o qual você tenha autorização explícita.
- O relatório do exemplo contém apenas dados fictícios. Não escreva senhas, tokens, chaves, dados pessoais ou evidências de incidentes sem necessidade e autorização.
- `0o600` e a verificação apresentada são garantias de permissões POSIX. No Windows, ACLs e políticas corporativas devem ser avaliadas separadamente; o código não altera ACLs.
- A remoção automática é uma tentativa ao sair normalmente do contexto, não uma garantia de apagamento forense nem de limpeza após falha abrupta, queda de energia, cópias ou snapshots.
- O diretório temporário é escolhido pela configuração do sistema. Em ambientes multiusuário, confirme que a pasta temporária e o volume atendem à política local.
- Não use o exemplo para ocultar atividade, contornar controles ou manter dados após o período autorizado.

## Checklist

- [ ] Confirme autorização e use somente dados sintéticos ou minimizados.
- [ ] Verifique se o diretório temporário do sistema é apropriado para a classificação dos dados.
- [ ] Crie arquivos de forma exclusiva e com permissões restritas suportadas pelo sistema.
- [ ] Evite registrar conteúdo sensível em stdout, logs ou nomes de arquivos.
- [ ] Confirme que o processamento falha de forma segura e que o ciclo de vida temporário está documentado.
- [ ] Revise as ACLs no Windows e as políticas de armazenamento em nuvem ou contêineres quando aplicável.
- [ ] Não interprete a exclusão lógica como apagamento seguro de mídia.

## Teste local

Execute o script com Python 3 em uma máquina de laboratório. Em POSIX, o modo esperado para o arquivo é `0600`; após a execução, o caminho temporário criado pelo contexto não deve mais existir. O teste não requer dependências externas, privilégios elevados ou conectividade de rede.
