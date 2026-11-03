# Dia 046 — Verificação local de isolamento de ambientes Python

Executar ferramentas administrativas ou scripts de auditoria no interpretador global pode misturar dependências de projetos distintos. Um ambiente virtual dedicado reduz esse acoplamento e torna mais previsível a revisão de dependências. Este pequeno verificador informa apenas se o processo Python atual está em um `venv`; não inspeciona pacotes, lê arquivos, altera configurações ou acessa a rede.

## Exemplo seguro em Python

Salve como `verificar_venv.py` e execute com `python3 verificar_venv.py`. O programa não imprime caminhos nem valores do ambiente, que poderiam revelar detalhes locais.

```python
import sys


def is_isolated() -> bool:
    # Python 3.3+: em um venv, prefix difere de base_prefix.
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def main() -> int:
    if is_isolated():
        print("Ambiente virtual ativo; confirme também as dependências aprovadas.")
        return 0
    print("Nenhum ambiente virtual detectado; considere criar/ativar um venv.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Para preparar um ambiente em um projeto que você administra, use os comandos oficiais do Python: `python3 -m venv .venv` e então ative-o conforme seu sistema operacional. Instale apenas dependências revisadas e necessárias; registre versões em um arquivo de dependências apropriado e siga o processo de atualização da equipe. Não execute scripts desconhecidos apenas para testar o isolamento.

## Limitações e ética

- O resultado é um indicador simples, não uma certificação de sandbox, isolamento de sistema operacional ou segurança do interpretador.
- Ambientes gerenciados por ferramentas específicas podem não se identificar exatamente como um `venv`; interprete o resultado conforme a documentação do runtime.
- O verificador não avalia procedência, vulnerabilidades ou integridade de pacotes, nem substitui revisão de lockfiles e políticas de dependências.
- Execute apenas em dispositivos e projetos que você administra ou tem autorização explícita para revisar. O exemplo não acessa outros sistemas, arquivos, rede, credenciais ou segredos.
- Crie e use ambientes virtuais em diretórios controlados. Não compartilhe pastas de ambiente virtual entre projetos nem inclua `.venv` em commits; confirme as regras de exclusão do repositório.

## Checklist

- [ ] Confirmei que o projeto e o computador estão sob minha administração ou autorização explícita.
- [ ] Executei o verificador com um interpretador Python confiável e conferi apenas a indicação de isolamento.
- [ ] Usei um ambiente virtual dedicado ao projeto, quando compatível com a plataforma.
- [ ] Revisei e limitei dependências às necessárias; fixei versões conforme a política do projeto.
- [ ] Evitei executar código desconhecido e verifiquei que `.venv` e dados locais não serão publicados.
- [ ] Não divulguei caminhos privados, credenciais, tokens ou outros segredos nos resultados.
