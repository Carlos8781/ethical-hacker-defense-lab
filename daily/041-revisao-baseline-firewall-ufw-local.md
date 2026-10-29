# Dia 041 — Revisão local de baseline do firewall UFW

Uma revisão defensiva pode comparar uma captura local do estado do UFW com uma política aprovada. Este exemplo verifica apenas duas condições de alto nível: firewall indicado como ativo e política padrão de entrada indicada como `deny`. Ele não executa `ufw`, não altera regras e não envia tráfego.

## Exemplo seguro em Python

Salve uma captura obtida por um administrador autorizado em um arquivo local, ou use o exemplo fictício abaixo. O script lê somente o arquivo explicitamente indicado e imprime os resultados das duas verificações, não o conteúdo da captura.

```python
from pathlib import Path
import sys
import tempfile


def review(text: str) -> dict[str, bool]:
    lines = [line.strip().lower() for line in text.splitlines()]
    active = any(line == "status: active" for line in lines)
    incoming_deny = any(
        line.startswith("default:") and "deny (incoming)" in line
        for line in lines
    )
    return {
        "ufw_indicado_ativo": active,
        "entrada_padrao_deny": incoming_deny,
    }


def main() -> None:
    if len(sys.argv) == 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    elif len(sys.argv) == 1:
        sample = """Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
"""
        with tempfile.TemporaryDirectory() as tmp:
            sample_path = Path(tmp) / "ufw-status-ficticio.txt"
            sample_path.write_text(sample, encoding="utf-8")
            text = sample_path.read_text(encoding="utf-8")
    else:
        raise SystemExit(f"Uso: {sys.argv[0]} [captura-local.txt]")

    print(review(text))


if __name__ == "__main__":
    main()
```

Teste o caso fictício executando `python3` com o código salvo em um arquivo local. Para uma revisão real, use apenas uma captura de um sistema que você administra e compare os sinais com a política aprovada. Um resultado positivo não prova que todas as regras estejam corretas.

## Limitações e ética

- Use somente uma captura local fornecida por um administrador autorizado; não consulte hosts, endereços ou serviços externos.
- O exemplo é somente leitura: não executa comandos, não ativa/desativa o UFW e não altera regras.
- A análise textual é intencionalmente simples e pode não corresponder a todas as versões, idiomas ou formatos de saída. Saída ausente, truncada ou diferente deve ser revisada manualmente.
- A indicação `Status: active` e a política padrão `deny (incoming)` não avaliam regras específicas, IPv6, encaminhamento, interfaces, serviços expostos ou a política institucional completa.
- Não conclua que há exposição ou conformidade apenas com este resultado; valide-o com a baseline aprovada e a equipe responsável.
- Não publique capturas reais, endereços, nomes de host, regras internas ou outros detalhes operacionais. Use dados fictícios em exemplos públicos.

## Checklist

- [ ] Confirmei autorização e origem da captura local.
- [ ] Testei primeiro com o texto fictício e confirmei as duas verificações esperadas.
- [ ] Revisei somente o arquivo escolhido; não executei comandos nem gerei tráfego.
- [ ] Comparei o resultado com a baseline aprovada, considerando as limitações do parser.
- [ ] Não alterei regras nem ampliei o escopo sem aprovação administrativa.
- [ ] Removi ou protegi capturas operacionais e não incluí dados internos no commit.
