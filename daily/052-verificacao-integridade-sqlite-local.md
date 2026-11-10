# Dia 052 — Verificação local de integridade de um banco SQLite

Antes de usar uma cópia de trabalho ou backup de um banco SQLite, uma verificação local pode identificar corrupção estrutural básica. O comando `PRAGMA integrity_check` é uma checagem de consistência do SQLite; não prova a autenticidade, a origem, a completude ou a atualidade dos dados. O exemplo abaixo abre o arquivo em modo somente leitura e não altera o banco.

## Exemplo seguro em Python

Salve como `verificar_sqlite.py` e execute `python3 verificar_sqlite.py CAMINHO_DO_BANCO.sqlite`. Informe apenas um banco de um sistema que você administra ou tem autorização explícita para revisar. O programa não acessa a rede, não carrega extensões SQLite e não imprime o conteúdo das tabelas.

```python
import sqlite3
import sys
from pathlib import Path


def verificar_integridade(caminho: str) -> bool:
    arquivo = Path(caminho).expanduser().resolve(strict=True)
    if not arquivo.is_file():
        raise ValueError("O caminho precisa apontar para um arquivo regular.")

    # URI mode=ro impede gravações pela conexão deste programa.
    uri = arquivo.as_uri() + "?mode=ro"
    conexao = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        resultado = conexao.execute("PRAGMA integrity_check").fetchall()
    finally:
        conexao.close()

    valido = resultado == [("ok",)]
    print("integrity_check: ok" if valido else "integrity_check: problemas encontrados")
    return valido


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: {Path(sys.argv[0]).name} CAMINHO_DO_BANCO.sqlite", file=sys.stderr)
        raise SystemExit(2)
    try:
        raise SystemExit(0 if verificar_integridade(sys.argv[1]) else 1)
    except (OSError, ValueError, sqlite3.Error) as erro:
        print(f"Verificação não concluída ({type(erro).__name__}).", file=sys.stderr)
        raise SystemExit(2)
```

Para testar sem dados reais, crie um banco descartável local com `python3 -c 'import sqlite3; c=sqlite3.connect("demo.sqlite"); c.execute("CREATE TABLE exemplo (id INTEGER PRIMARY KEY)"); c.commit(); c.close()'` e execute `python3 verificar_sqlite.py demo.sqlite`. A saída esperada é `integrity_check: ok`. Apague o arquivo de demonstração quando não for mais necessário.

## Limitações e ética

- Use somente bancos locais que você administra ou para os quais tenha autorização explícita. Confirme escopo e política de tratamento de dados antes de revisar qualquer arquivo real.
- A abertura em modo somente leitura protege contra gravação por esta conexão, mas não substitui uma cópia de segurança; outros processos podem modificar o arquivo e a checagem pode competir com cargas de trabalho locais.
- `integrity_check` verifica aspectos estruturais do SQLite, não validade de negócio, consistência semântica, integridade criptográfica, procedência, ausência de adulteração ou recuperação completa de um backup.
- Não compartilhe banco, caminho interno, saída detalhada, registros ou dados pessoais. O exemplo limita deliberadamente a saída a um estado geral.
- Um arquivo não confiável ainda pode consumir tempo e recursos ao ser analisado. Execute apenas em ambiente local apropriado, com recursos e cópias de segurança compatíveis com o risco.
- Não adapte o exemplo para acessar serviços, contornar controles, extrair dados ou inspecionar arquivos de terceiros sem autorização.

## Checklist

- [ ] Confirmei que o arquivo e o escopo pertencem a um sistema que administro ou estão explicitamente autorizados.
- [ ] Preservei uma cópia de segurança apropriada antes de qualquer operação de recuperação ou reparo.
- [ ] Executei primeiro o exemplo com um banco descartável e fictício.
- [ ] Confirmei que a conexão usa `mode=ro` e que o script não acessa rede nem imprime linhas das tabelas.
- [ ] Interpretei `ok` somente como resultado da verificação estrutural, não como prova de autenticidade, atualidade ou restauração válida.
- [ ] Mantive dados reais e caminhos internos fora de commits, issues e relatórios públicos.
