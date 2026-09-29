# Dia 011 — Exercício de mesa para resposta a incidentes

Um exercício de mesa ajuda uma equipe a discutir responsabilidades e decisões antes de um incidente real. Esta lição apresenta um roteiro curto e um programa local que resume o estado de cinco etapas de um cenário fictício. O exemplo não detecta incidentes, não acessa sistemas e não executa ações de contenção ou recuperação.

## Uso autorizado e limitações éticas

Use o roteiro apenas em um exercício aprovado pela organização e com participantes autorizados. Comece com um cenário inventado; não inclua incidentes reais, nomes, endereços, clientes, detalhes de infraestrutura, credenciais ou outros dados sensíveis no arquivo ou em repositórios públicos. Combine previamente objetivo, escopo, facilitador, participantes e forma de registrar resultados.

Neste exercício, `revisado` significa que a equipe discutiu uma etapa e identificou responsáveis e procedimentos aprovados — não que uma ação tenha sido executada. Não simule ataques reais, não acesse contas ou sistemas, não desative controles, não altere produção e não envie notificações externas. Qualquer ação real deve seguir o plano de resposta, as aprovações e a gestão de mudanças da organização.

O resumo do programa mede somente os valores registrados no CSV. Não verifica se o plano existe, se os contatos estão atualizados, se os controles funcionam ou se a equipe está preparada. Uma etapa marcada como revisada não comprova eficácia; uma etapa pendente não confirma um incidente. Interprete o resultado com um facilitador e os responsáveis autorizados.

## Roteiro do exercício

Use um cenário fictício e discuta estas etapas, sem interagir com sistemas reais:

1. **Detecção:** que canal interno aprovado receberia um alerta e quem faria a triagem?
2. **Triagem:** quais fontes autorizadas seriam consultadas e como seria registrada a incerteza?
3. **Plano de contenção:** quem poderia aprovar medidas, e como seriam avaliados impacto e reversão? Discuta o plano; não aplique mudanças.
4. **Plano de recuperação:** quais responsáveis, backups e critérios de validação seriam considerados? Não restaure nem altere dados neste exercício.
5. **Retrospectiva:** como registrar decisões, lacunas e ações de acompanhamento sem expor dados sensíveis?

## Exemplo seguro em Python

Salve como `tabletop_summary.py`. O script lê somente um CSV local, aceita exatamente as colunas `etapa,status` e os identificadores e estados definidos abaixo. Ele imprime totais agregados, não mostra o conteúdo das linhas e não grava nem transmite dados.

```python
#!/usr/bin/env python3
"""Summarize a fictional, local incident-response tabletop checklist."""
import argparse
import csv
from pathlib import Path
from typing import TextIO

REQUIRED_STEPS = {
    "deteccao",
    "triagem",
    "plano_contencao",
    "plano_recuperacao",
    "retrospectiva",
}
ALLOWED_STATUSES = {"revisado", "pendente", "bloqueado"}


def summarize(stream: TextIO) -> tuple[int, int, int, int, int, int]:
    reader = csv.DictReader(stream, strict=True)
    if reader.fieldnames != ["etapa", "status"]:
        raise ValueError("cabeçalho esperado: etapa,status")

    seen: set[str] = set()
    counts = {status: 0 for status in ALLOWED_STATUSES}
    invalid = 0

    for row in reader:
        if None in row or any(value is None for value in row.values()):
            invalid += 1
            continue

        step = row["etapa"].strip()
        status = row["status"].strip()
        if step not in REQUIRED_STEPS or status not in ALLOWED_STATUSES or step in seen:
            invalid += 1
            continue

        seen.add(step)
        counts[status] += 1

    missing = len(REQUIRED_STEPS - seen)
    return (
        len(seen), counts["revisado"], counts["pendente"],
        counts["bloqueado"], missing, invalid,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checklist", type=Path, help="CSV local de exercício autorizado")
    args = parser.parse_args()
    if not args.checklist.is_file():
        parser.error("informe um arquivo local existente")

    try:
        with args.checklist.open("r", encoding="utf-8", newline="") as stream:
            total, reviewed, pending, blocked, missing, invalid = summarize(stream)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        parser.error(f"não foi possível processar um CSV válido: {exc}")

    print(f"etapas válidas registradas: {total}")
    print(f"etapas discutidas/revisadas: {reviewed}")
    print(f"etapas pendentes: {pending}")
    print(f"etapas bloqueadas: {blocked}")
    print(f"etapas ausentes: {missing}")
    print(f"linhas inválidas ou duplicadas: {invalid}")

    if invalid:
        return 2
    if pending or blocked or missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Crie uma amostra descartável com dados inteiramente fictícios e execute-a localmente:

```bash
cat > /tmp/tabletop-lab.csv <<'EOF'
etapa,status
deteccao,revisado
triagem,revisado
plano_contencao,bloqueado
plano_recuperacao,pendente
retrospectiva,revisado
EOF
python3 tabletop_summary.py /tmp/tabletop-lab.csv
```

A saída esperada informa cinco etapas válidas: três revisadas, uma pendente, uma bloqueada e nenhuma ausente ou inválida. O código de saída `1` indica que há itens para acompanhamento humano; não indica comprometimento. Quando todas as etapas estiverem revisadas e não houver linhas inválidas, o código de saída é `0`. Uma linha duplicada, estado não reconhecido ou etapa desconhecida é contada como inválida sem revelar seu conteúdo, e o processo termina com código `2`.

## Checklist

- [ ] O exercício tem objetivo, escopo, facilitador e participantes autorizados definidos.
- [ ] O cenário e o CSV usam somente dados fictícios, sem nomes, segredos ou detalhes operacionais.
- [ ] O grupo discute procedimentos aprovados; ninguém acessa sistemas nem executa contenção ou recuperação.
- [ ] Cada etapa revisada tem responsável e referência a um procedimento interno aprovado.
- [ ] Impactos, aprovações necessárias, dependências e plano de reversão são discutidos antes de qualquer ação futura.
- [ ] Lacunas e decisões são registradas em local autorizado, com acesso e retenção adequados.
- [ ] O resumo agregado foi interpretado por pessoas responsáveis e não tratado como prova de prontidão.
- [ ] Ações de acompanhamento têm responsável e prazo definidos pela organização.
- [ ] Nenhum dado real ou resultado sensível foi publicado neste exercício ou no repositório.

## Limitações e próximos passos

Este exemplo verifica apenas formato, estados permitidos e cobertura de cinco etapas fixas. Não avalia a qualidade de decisões, não substitui um plano formal, não verifica contatos ou sistemas e não preserva uma trilha de auditoria. Adapte o roteiro somente com aprovação e revisão de privacidade e segurança. Faça exercícios mais amplos com responsáveis autorizados, registre aprendizados conforme a política interna e valide separadamente qualquer mudança real por gestão de mudanças. Não use o programa para acionar tarefas, enviar alertas ou tomar decisões automáticas.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `csv`, `argparse` e `pathlib`.
- Plano interno aprovado de resposta a incidentes, gestão de mudanças, continuidade e retenção de registros.

> Este guia é para preparação defensiva autorizada com cenário fictício; não inclui acesso, varredura, exploração ou alteração de sistemas.

<!-- Testado localmente com Python 3 e CSV fictício. -->
