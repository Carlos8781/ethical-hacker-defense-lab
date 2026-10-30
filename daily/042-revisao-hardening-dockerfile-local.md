# Dia 042 — Revisão local de hardening de Dockerfile

Uma revisão estática de um Dockerfile pode apontar itens para conferência antes de uma construção aprovada: ausência de uma instrução `USER`, uso explícito de `USER root`/`USER 0`, tags `latest` em imagens-base e instruções `ADD` que merecem análise. O exemplo abaixo examina somente um arquivo local ou um Dockerfile fictício temporário; não constrói nem executa contêineres, não invoca o Docker e não acessa a rede.

## Exemplo seguro em Python

O verificador produz apenas indicadores para revisão humana. Ele não altera o Dockerfile nem recomenda automaticamente mudanças de produção.

```python
from pathlib import Path
import re
import sys
import tempfile


def review(text: str) -> dict[str, object]:
    instructions = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"([A-Za-z]+)\s+(.*)", line)
        if match:
            instructions.append((match.group(1).upper(), match.group(2).strip()))

    users = [value for name, value in instructions if name == "USER"]
    base_images = [value for name, value in instructions if name == "FROM"]
    additions = [value for name, value in instructions if name == "ADD"]

    return {
        "tem_instrucao_user": bool(users),
        "user_root_explicito": any(
            re.match(r"^(root|0)(?:\s|$)", value, re.IGNORECASE)
            for value in users
        ),
        "from_com_tag_latest": any(
            re.search(r":latest(?:\s|$|@)", value, re.IGNORECASE)
            for value in base_images
        ),
        "quantidade_add_para_revisar": len(additions),
    }


def main() -> None:
    if len(sys.argv) == 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
        print(review(text))
    elif len(sys.argv) == 1:
        sample = """FROM python:latest
WORKDIR /app
ADD app.tar.gz /app/
CMD [\"python\", \"app.py\"]
"""
        with tempfile.TemporaryDirectory() as tmp:
            sample_path = Path(tmp) / "Dockerfile-ficticio"
            sample_path.write_text(sample, encoding="utf-8")
            print(review(sample_path.read_text(encoding="utf-8")))
    else:
        raise SystemExit(f"Uso: {sys.argv[0]} [Dockerfile-local]")


if __name__ == "__main__":
    main()
```

Execute o exemplo fictício com `python3` ou passe o caminho de um Dockerfile local que você administra. Com a amostra, o resultado esperado é `tem_instrucao_user: False`, `user_root_explicito: False`, `from_com_tag_latest: True` e `quantidade_add_para_revisar: 1`. Esses sinais indicam pontos de revisão, não uma avaliação completa nem uma falha confirmada.

## Limitações e ética

- Revise somente arquivos locais de projetos que você administra ou para os quais tem autorização explícita.
- O script é somente leitura quanto ao alvo: não executa Docker, não constrói imagens, não busca imagens, não acessa registros e não faz varredura.
- A análise é textual e simplificada. Sintaxe continuada em múltiplas linhas, argumentos JSON, variáveis, aliases, estágios múltiplos e formatos alternativos podem não ser interpretados corretamente.
- A presença de uma instrução `USER` em qualquer estágio não prova que todos os estágios ou processos executem com privilégio mínimo; avalie cada estágio e o comando efetivo no contexto.
- `ADD` pode ter usos legítimos, e uma tag fixa também pode exigir estratégia de atualização. Compare os resultados com a política de construção e manutenção aprovada.
- Não publique Dockerfiles internos, nomes de imagens privadas, caminhos, parâmetros de construção ou detalhes operacionais. Use dados fictícios em exemplos públicos.

## Checklist

- [ ] Confirmei autorização e selecionei um Dockerfile local específico.
- [ ] Executei primeiro o exemplo com a amostra fictícia e conferi os indicadores esperados.
- [ ] Verifiquei que o exemplo não invoca Docker, não altera arquivos e não acessa a rede.
- [ ] Revisei os resultados por estágio e contexto, sem tratar alertas heurísticos como prova de vulnerabilidade.
- [ ] Comparei as decisões com a baseline aprovada e encaminhei mudanças pelo processo de revisão responsável.
- [ ] Não incluí arquivos internos, segredos ou configurações privadas no commit.
