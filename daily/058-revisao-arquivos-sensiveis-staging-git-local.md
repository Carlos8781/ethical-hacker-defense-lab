# Dia 058 — Revisão local de arquivos sensíveis no staging do Git

## Objetivo

Antes de criar um commit, uma revisão dos nomes de arquivos preparados (`staged`) pode ajudar a evitar a inclusão acidental de arquivos de configuração privada, chaves ou arquivos de ambiente. Esta barreira complementar consulta somente a lista local de caminhos staged; não abre nem lê o conteúdo, não altera o índice Git e não envia dados pela rede.

A política abaixo sinaliza nomes comuns como `.env`, `.npmrc`, chaves privadas com extensões usuais e arquivos `.env.*`, permitindo os modelos `.env.example` e `.env.template`. A classificação é intencionalmente conservadora e exige revisão humana.

## Exemplo seguro em Python

Salve como `review_staged_names.py` dentro do repositório local e execute `python3 review_staged_names.py` antes de criar o commit. O programa chama apenas `git diff --cached --name-only` com argumentos fixos, não usa shell, e imprime somente a quantidade de ocorrências — nunca os caminhos.

```python
import os
import subprocess
import sys

EXACT_NAMES = {".env", ".npmrc", ".pypirc", "id_rsa", "id_ed25519"}
PRIVATE_KEY_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
ALLOWED_ENV_TEMPLATES = {".env.example", ".env.template"}


def looks_sensitive(path: str) -> bool:
    name = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if name in ALLOWED_ENV_TEMPLATES:
        return False
    return (
        name in EXACT_NAMES
        or (name.startswith(".env.") and name not in ALLOWED_ENV_TEMPLATES)
        or any(name.endswith(suffix) for suffix in PRIVATE_KEY_SUFFIXES)
    )


def main() -> int:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Não foi possível consultar o staging local; interrompendo a revisão.")
        return 2

    staged_paths = [os.fsdecode(item) for item in result.stdout.split(b"\0") if item]
    count = sum(looks_sensitive(path) for path in staged_paths)
    if count:
        print(f"REVISAR: {count} caminho(s) staged com nome potencialmente sensível.")
        print("Não crie o commit antes de revisar o staging localmente.")
        return 1
    print("Nenhum nome sinalizado nesta verificação; revise o diff antes do commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Teste sintético: em um repositório temporário, prepare um arquivo fictício `.env` e um `nota.txt`. O resultado esperado é um alerta com a contagem `1`; nenhum conteúdo ou caminho deve aparecer na saída. Remova o arquivo fictício do staging e execute novamente para observar a mensagem sem alerta. Não use valores reais em `.env`.

## Limitações e cuidados éticos

- Use a revisão somente em repositórios locais que você administra ou para os quais tem autorização explícita. O comando consulta o índice Git local e não se conecta a serviços remotos.
- Uma lista de nomes é apenas uma heurística: segredos podem estar em arquivos com nomes comuns, enquanto arquivos com extensões sinalizadas podem conter material público ou não sensível. Revise o diff e os requisitos do projeto; não confie neste script como detector de conteúdo.
- O exemplo não lê arquivos, não verifica arquivos já commitados, submódulos, conteúdo binário, renomes antigos ou dados em outros mecanismos de publicação. Ele também não substitui regras de proteção no servidor nem revisão por pares.
- A verificação não muda o staging automaticamente. Se houver alerta, examine localmente e decida se deve remover o arquivo do índice ou aplicar o processo aprovado. Não exiba nem copie conteúdo secreto para logs, issues ou mensagens.
- Arquivos de chave com formato PEM podem conter certificados públicos ou chaves privadas; a sinalização não determina sua natureza. Mantenha chaves privadas fora do repositório e siga a política da organização.
- Não use esta demonstração para procurar ou coletar segredos de terceiros. Empregue apenas nomes e dados fictícios no teste compartilhado.

## Checklist

- [ ] Confirme que o repositório e a revisão são autorizados e locais.
- [ ] Execute a verificação antes do commit e trate qualquer alerta como pedido de revisão humana.
- [ ] Examine o diff localmente; não publique conteúdo sensível ao pedir ajuda.
- [ ] Confirme que `.env` e chaves privadas não estão no staging; use modelos sem segredos quando necessário.
- [ ] Revise arquivos não sinalizados, pois nomes comuns não provam que o conteúdo é seguro.
- [ ] Não altere o índice automaticamente; remova itens somente após validar o impacto.
- [ ] Use proteção adicional no fluxo de desenvolvimento e procedimentos de resposta caso um segredo tenha sido commitado.

## Teste local

Requer Python 3 e Git local, sem dependências adicionais, privilégios elevados ou rede. Valide em um repositório temporário com nomes e conteúdos fictícios: um `.env` sintético deve resultar em código de saída `1`, enquanto o índice sem nomes sinalizados deve resultar em `0`. A falha ao consultar Git resulta em `2` para evitar tratar uma verificação não executada como sucesso. Antes do uso operacional, revise a lista de nomes conforme a política aprovada da sua equipe.
