# Dia 054 — Revisão local de atributos de cookies

## Objetivo

Cookies de sessão e outros identificadores podem ficar expostos se as aplicações omitirem atributos de proteção. Uma revisão defensiva pode verificar, em ambiente de desenvolvimento, se os cabeçalhos `Set-Cookie` incluem `Secure`, `HttpOnly` quando não há necessidade de acesso por JavaScript e uma política `SameSite` explícita. Esta verificação é um auxílio de revisão; não substitui testes da aplicação nem uma análise contextual.

O exemplo abaixo analisa apenas strings sintéticas em memória. Não faz requisições, não recebe cookies reais e não se conecta a nenhum serviço.

## Exemplo seguro em Python

Salve como `cookie_review_demo.py` e execute com `python3 cookie_review_demo.py`.

```python
from dataclasses import dataclass

@dataclass
class Finding:
    name: str
    issues: list[str]

# Exemplos fictícios: nunca cole cabeçalhos de produção ou valores de sessão.
samples = {
    "session": "session=REDACTED; Path=/; Secure; HttpOnly; SameSite=Lax",
    "preference": "theme=dark; Path=/; SameSite=Strict",
    "insecure_demo": "demo=synthetic; Path=/",
}

def review_cookie(header: str) -> Finding:
    parts = [part.strip() for part in header.split(";")]
    cookie_pair = parts[0].split("=", 1)
    name = cookie_pair[0].strip() if cookie_pair else "(sem nome)"
    attributes = {part.lower() for part in parts[1:]}
    issues = []

    if "secure" not in attributes:
        issues.append("Secure ausente")
    if "httponly" not in attributes:
        issues.append("HttpOnly ausente; confirme se JavaScript precisa ler o cookie")
    if not any(attr.startswith("samesite=") for attr in attributes):
        issues.append("SameSite explícito ausente")
    return Finding(name=name, issues=issues)

for label, synthetic_header in samples.items():
    result = review_cookie(synthetic_header)
    status = "; ".join(result.issues) if result.issues else "atributos básicos presentes"
    print(f"{label}: {status}")
```

Resultado esperado: `session` é reportado com atributos básicos presentes; `preference` alerta para `Secure` e `HttpOnly`; `insecure_demo` sinaliza os três itens.

## Limitações e cuidados éticos

- Execute revisões somente em aplicações que você administra ou para as quais possui autorização explícita. O exemplo usa apenas texto fictício, sem tráfego de rede.
- A análise é deliberadamente simples: não valida a gramática completa de `Set-Cookie`, domínios, caminhos, expiração, prefixos (`__Host-`/`__Secure-`) nem duplicidade de atributos.
- `HttpOnly` pode não ser apropriado quando uma função legítima da aplicação exige acesso via JavaScript. Decida com base na arquitetura e minimize o acesso ao cookie.
- `SameSite` ajuda a reduzir certos riscos de requisições cross-site, mas não substitui proteção CSRF adequada nem outras defesas.
- A recomendação de `Secure` pressupõe entrega por HTTPS; ambientes de desenvolvimento local podem ter exceções controladas. Não remova a proteção em produção.
- Não copie valores reais de cookies para relatórios, issues, logs ou ferramentas externas. Redija ou use dados sintéticos.

## Checklist

- [ ] Confirme autorização e revise configurações da aplicação sob seu controle.
- [ ] Use dados fictícios ou cabeçalhos redigidos; nunca publique valores de sessão.
- [ ] Verifique `Secure` em cookies destinados a HTTPS.
- [ ] Avalie `HttpOnly` e restrinja o acesso por JavaScript sempre que possível.
- [ ] Defina `SameSite` de acordo com os fluxos legítimos da aplicação e complemente com defesa CSRF quando necessária.
- [ ] Revise escopo de `Domain` e `Path`, duração e prefixos usando ferramenta apropriada e contexto da aplicação.
- [ ] Registre exceções justificadas e valide a configuração em ambiente de teste antes de implantar.

## Teste local

O exemplo depende apenas da biblioteca padrão do Python 3. Execute `python3 cookie_review_demo.py`; confirme os três resultados descritos. O teste não requer privilégios elevados, dependências extras, dados reais ou acesso à rede.
