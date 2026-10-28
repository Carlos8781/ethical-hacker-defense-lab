# Dia 040 — Revisão local de permissões de configuração

Arquivos de configuração podem conter parâmetros operacionais sensíveis. Uma revisão local simples ajuda a identificar arquivos regulares que permitem leitura ou escrita por grupo ou por outros usuários, para que o administrador compare o resultado com a política aprovada. A verificação abaixo inspeciona apenas o caminho informado e não lê nem imprime o conteúdo do arquivo.

## Exemplo seguro em Python

O script verifica os bits de permissão POSIX `0o077` (acesso de grupo ou outros). Não percorre diretórios, não segue links simbólicos como arquivos regulares, não altera permissões, não consulta usuários, não executa comandos e não acessa a rede. O modo sem argumentos testa um arquivo fictício criado em diretório temporário.

```python
from pathlib import Path
import os
import stat
import sys
import tempfile


def review(path: Path) -> dict[str, object]:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("o caminho não é um arquivo regular")
    access_bits = stat.S_IMODE(info.st_mode) & 0o077
    return {
        "arquivo_regular": True,
        "bits_grupo_ou_outros": oct(access_bits),
        "permissivo_para_politica_basica": access_bits != 0,
    }


if __name__ == "__main__":
    if len(sys.argv) == 2:
        print(review(Path(sys.argv[1])))
    elif len(sys.argv) == 1:
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "config-ficticia.conf"
            sample.write_text("# conteúdo fictício; não é exibido\n", encoding="utf-8")
            os.chmod(sample, 0o640)
            print(review(sample))
    else:
        raise SystemExit(f"Uso: {sys.argv[0]} [caminho-de-arquivo-local]")
```

Teste o exemplo fictício com `python3` e, se autorizado, passe um único caminho local para revisão. Um resultado `permissivo_para_politica_basica: True` indica apenas que há bits de acesso de grupo ou outros; isso não determina por si só uma violação. Permissões adequadas dependem da política, do propósito e dos controles adicionais.

## Limitações e ética

- Inspecione apenas arquivos de sistemas que você administra ou para os quais tem autorização explícita.
- O script é local e somente de leitura quanto ao alvo; não percorre pastas, não faz varredura, não acessa rede e não exibe conteúdo.
- A avaliação considera bits POSIX tradicionais. ACLs, atributos, permissões efetivas, compartilhamentos e sistemas não POSIX podem mudar o acesso real.
- A presença de bits `0o077` é um sinal para revisão, não prova de exposição indevida; valide contra a baseline e o contexto aprovados.
- Não altere permissões automaticamente como resultado deste exemplo. Encaminhe discrepâncias à equipe responsável para correção autorizada e controlada.
- Não inclua caminhos internos, conteúdo de configuração ou metadados sensíveis em relatórios públicos ou commits.

## Checklist

- [ ] Confirmei autorização e selecionei um único arquivo local esperado.
- [ ] Executei primeiro o exemplo com o arquivo fictício temporário.
- [ ] Verifiquei que o script não imprime o conteúdo nem segue links simbólicos.
- [ ] Comparei o sinal encontrado com a política e os controles locais, sem tratá-lo como conclusão automática.
- [ ] Não alterei permissões, não acessei a rede e não ampliei o escopo.
- [ ] Compartilhei somente conclusões necessárias e encaminhei correções pela via administrativa aprovada.
