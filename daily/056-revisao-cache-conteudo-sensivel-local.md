# Dia 056 — Revisão local de cache para conteúdo sensível

## Objetivo

Respostas HTTP com informações pessoais, financeiras ou autenticadas exigem uma política de cache deliberada. `Cache-Control: no-store` instrui caches compatíveis a não armazenar a resposta; `private` impede que caches compartilhados a armazenem, mas ainda permite cache privado no navegador. A política correta depende do conteúdo e do fluxo da aplicação.

O exemplo abaixo revisa cabeçalhos sintéticos em memória. Não faz requisições, não lê cookies, não acessa arquivos e não se conecta a sistemas.

## Exemplo seguro em Python

Salve como `cache_policy_demo.py` e execute com `python3 cache_policy_demo.py`.

```python
from dataclasses import dataclass

@dataclass
class Review:
    label: str
    findings: list[str]

# Respostas fictícias; não cole cabeçalhos, URLs ou dados de produção.
responses = {
    "perfil_autenticado_demo": {
        "sensitive": True,
        "cache_control": "private, max-age=60",
    },
    "recibo_sintetico": {
        "sensitive": True,
        "cache_control": "no-store",
    },
    "pagina_publica_demo": {
        "sensitive": False,
        "cache_control": "public, max-age=300",
    },
}

def review(label: str, sensitive: bool, cache_control: str) -> Review:
    directives = {
        part.strip().lower()
        for part in cache_control.split(",")
        if part.strip()
    }
    findings = []

    if sensitive and "no-store" not in directives:
        findings.append("conteúdo sensível sem no-store explícito")
    if sensitive and "public" in directives:
        findings.append("diretiva public incompatível com a classificação sensível")
    if not cache_control.strip():
        findings.append("Cache-Control ausente; definir política conforme a classificação")

    return Review(label, findings)

for label, item in responses.items():
    result = review(label, item["sensitive"], item["cache_control"])
    status = "; ".join(result.findings) if result.findings else "sem alerta nesta verificação"
    print(f"{result.label}: {status}")
```

Resultado esperado: `perfil_autenticado_demo` gera alerta por não declarar `no-store`; `recibo_sintetico` e `pagina_publica_demo` não geram alerta nesta verificação.

## Limitações e cuidados éticos

- Use a revisão somente em aplicações sob sua administração ou com autorização explícita. O exemplo é offline e contém valores fictícios.
- É uma verificação didática de diretivas textuais: não implementa integralmente a gramática HTTP, não examina `Expires`, cabeçalhos duplicados, proxies, CDN, service workers nem o comportamento real do navegador.
- `no-store` reduz armazenamento por caches compatíveis, mas não apaga cópias já existentes nem impede captura de tela, gravação pelo usuário ou registro por sistemas fora do controle da aplicação.
- `private` não significa “sem armazenamento”; ele permite cache no dispositivo do usuário. Escolha a diretiva segundo a sensibilidade e os requisitos do serviço.
- Não aplique `no-store` indiscriminadamente: conteúdo público estático pode se beneficiar de cache. Valide efeitos de desempenho e requisitos regulatórios com os responsáveis.
- Nunca inclua em exemplos ou relatórios conteúdo privado, tokens, cookies, identificadores de sessão, URLs internas ou dados pessoais.

## Checklist

- [ ] Confirme autorização e classifique os dados retornados pela rota.
- [ ] Para respostas sensíveis, avalie `Cache-Control: no-store` e confirme a política com a equipe responsável.
- [ ] Não confunda `private` com ausência total de armazenamento.
- [ ] Revise configurações de CDN, proxy, navegador e service worker em ambiente de teste autorizado.
- [ ] Mantenha cache eficiente para recursos públicos quando apropriado, sem misturá-los com respostas autenticadas.
- [ ] Use somente exemplos sintéticos em relatórios e testes compartilhados.
- [ ] Registre exceções, justificativas e responsáveis pela aprovação da política.

## Teste local

O exemplo requer apenas a biblioteca padrão do Python 3. Execute `python3 cache_policy_demo.py` e confirme os três resultados descritos. Não requer privilégios elevados, dependências extras, dados reais ou acesso à rede.
