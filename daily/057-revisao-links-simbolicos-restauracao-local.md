# Dia 057 — Revisão local de links simbólicos em área de restauração

## Objetivo

Links simbólicos em uma área de restauração podem apontar para caminhos fora da árvore esperada. Antes de usar um conjunto de arquivos recuperados, uma revisão defensiva pode sinalizar esses links para análise humana, sem segui-los nem ler seus destinos. A política de restauração deve definir se links simbólicos são esperados e quem pode aprová-los.

O exemplo cria uma pasta temporária com um arquivo e um link simbólico fictícios. Ele examina apenas as entradas diretas da pasta, classifica links usando `is_symlink()` e não abre arquivos, não percorre subdiretórios e não segue os links.

## Exemplo seguro em Python

Salve como `symlink_review_demo.py` e execute com `python3 symlink_review_demo.py`.

```python
from pathlib import Path
from tempfile import TemporaryDirectory


def review_directory(directory: Path) -> None:
    for entry in sorted(directory.iterdir()):
        if entry.is_symlink():
            print(f"REVISAR link simbólico: {entry.name}")
        elif entry.is_dir():
            print(f"DIRETÓRIO (não percorrido): {entry.name}")
        else:
            print(f"ARQUIVO comum (conteúdo não lido): {entry.name}")


if __name__ == "__main__":
    with TemporaryDirectory(prefix="restore-demo-") as temporary:
        staging = Path(temporary) / "staging"
        staging.mkdir()
        (staging / "nota-ficticia.txt").write_text(
            "Conteúdo sintético para demonstração.\n", encoding="utf-8"
        )
        (staging / "atalho-demo").symlink_to("destino-ausente-demo")
        review_directory(staging)
```

Resultado esperado: uma linha `REVISAR link simbólico: atalho-demo` e uma linha identificando `nota-ficticia.txt` como arquivo comum. O alvo do link não precisa existir e não é aberto. Em plataformas nas quais a criação de links simbólicos esteja desabilitada, execute em um ambiente local de teste autorizado que permita esse recurso ou adapte o exercício sem elevar privilégios.

## Limitações e cuidados éticos

- Use a revisão somente em diretórios de restauração pertencentes à sua organização ou cobertos por autorização explícita. O exemplo opera apenas em uma pasta temporária criada pelo próprio processo.
- O código analisa somente o primeiro nível e não valida permissões, conteúdo, hard links, pontos de montagem nem alterações concorrentes. A saída é um sinal para revisão, não uma decisão automática de segurança.
- Não siga nem abra o destino de um link apenas porque ele foi sinalizado. Compare a entrada com a política aprovada e peça validação do responsável pelos dados e pelo processo de recuperação.
- Não altere nem apague evidências ou dados restaurados durante uma triagem. Faça qualquer validação operacional em cópia isolada e mantenha registros conforme a política da organização.
- Não use caminhos, nomes de arquivos ou conteúdos reais em demonstrações compartilhadas; evite dados pessoais, segredos e detalhes operacionais sensíveis.

## Checklist

- [ ] Confirme o escopo autorizado e trabalhe em uma cópia ou área de teste aprovada.
- [ ] Defina previamente se links simbólicos são permitidos no conjunto de restauração.
- [ ] Liste links sem seguir seus destinos e encaminhe cada ocorrência para revisão humana.
- [ ] Não percorra recursivamente diretórios nem leia conteúdo sem necessidade e autorização.
- [ ] Registre achados com nomes sintéticos ou minimizados e preserve a cópia original.
- [ ] Valide o processo em laboratório local com dados fictícios antes de incorporá-lo ao runbook.
- [ ] Solicite aprovação do responsável antes de restaurar ou modificar qualquer arquivo sinalizado.

## Teste local

Requer Python 3 e apenas a biblioteca padrão. Execute `python3 symlink_review_demo.py` e confirme as duas linhas esperadas. O script não precisa de privilégios elevados, dependências externas, rede, argumentos de caminho nem dados de produção; todos os arquivos de demonstração são removidos automaticamente com a pasta temporária.
