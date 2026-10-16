# Dia 028 — Revisão local de regras de exclusão Git

## Objetivo

Regras de exclusão bem revisadas ajudam a reduzir a inclusão acidental de arquivos locais em novos commits. Este exercício valida, sem acessar a rede ou ler os arquivos ignorados, se um arquivo `.gitignore` local contém um conjunto mínimo de padrões escolhidos pela equipe. Use a lista como ponto de partida e adapte-a à estrutura do projeto.

## Limites éticos e operacionais

- Revise somente repositórios que você possui ou administra, ou para os quais tem autorização explícita.
- O exemplo lê apenas o arquivo `.gitignore` informado; não percorre o repositório, não lê valores de arquivos sensíveis, não altera arquivos e não executa comandos Git.
- Os padrões sugeridos são exemplos, não uma política universal. Um padrão genérico pode ocultar arquivos necessários ao projeto; confirme cada um com os responsáveis.
- `.gitignore` afeta arquivos ainda não rastreados. Ele não remove do índice arquivos que já foram commitados, não apaga dados do histórico e não é um mecanismo de controle de acesso ou de proteção contra segredos. Se um segredo foi commitado, siga o processo aprovado de resposta e rotação, sem reproduzi-lo em logs ou relatórios.
- O verificador identifica apenas a presença literal de padrões. Não interpreta toda a sintaxe, precedência, negações ou regras globais do Git; portanto, um resultado positivo não prova que o repositório está seguro.

## Exemplo seguro em Python

Salve como `check_gitignore.py`. O programa lê somente o arquivo explicitamente indicado e imprime apenas padrões ausentes, nunca o conteúdo completo do arquivo.

```python
#!/usr/bin/env python3
"""Verifica padrões literais selecionados em um .gitignore local."""
import argparse
import sys
from pathlib import Path

REQUIRED_PATTERNS = {".env", "*.pem", "*.key", ".venv/", "__pycache__/"}
MAX_BYTES = 256 * 1024


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gitignore", type=Path, help="caminho local para o .gitignore autorizado")
    args = parser.parse_args()

    try:
        if args.gitignore.is_symlink():
            parser.error("não são aceitos links simbólicos")
        with args.gitignore.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            parser.error("arquivo excede o limite de 256 KiB")
        lines = raw.decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        print("falha ao ler o arquivo local indicado", file=sys.stderr)
        return 2

    present = {line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")}
    missing = sorted(REQUIRED_PATTERNS - present)
    if missing:
        print("Revisar padrões ausentes:")
        for pattern in missing:
            print(f"- {pattern}")
        return 1
    print("OK: todos os padrões selecionados estão presentes; revise também a semântica e o escopo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste localmente, em um diretório temporário com dados fictícios:

```bash
printf '%s\n' '.env' '*.pem' '*.key' '.venv/' '__pycache__/' > /tmp/gitignore-ficticio
python3 check_gitignore.py /tmp/gitignore-ficticio
# Esperado: saída 0; nenhuma rede é acessada.
printf '%s\n' '.env' '*.pem' > /tmp/gitignore-ficticio
python3 check_gitignore.py /tmp/gitignore-ficticio
# Esperado: saída 1 e somente a lista de padrões ausentes.
rm -f /tmp/gitignore-ficticio
```

A saída `1` indica padrões escolhidos ausentes e requer revisão humana; não prova exposição. A saída `2` indica erro de leitura ou argumento. Não execute o teste em arquivos de terceiros ou em dados reais não autorizados.

## Checklist

- [ ] Confirmei que o repositório revisado está sob minha administração ou autorização explícita.
- [ ] Testei o programa apenas com um `.gitignore` fictício/local e confirmei os casos positivo e negativo.
- [ ] Revisei cada padrão com o contexto do projeto para evitar ocultar arquivos necessários.
- [ ] Verifiquei separadamente os arquivos já rastreados e o histórico por meio do fluxo interno autorizado; este script não faz essa verificação.
- [ ] Não abri, copiei, imprimi nem publiquei conteúdo de arquivos potencialmente sensíveis.
- [ ] Não acessei rede, sistemas ou repositórios de terceiros.
- [ ] Se houve indício de segredo já commitado, encaminhei-o pelo processo aprovado sem divulgar o valor.
