# Dia 055 — Validação local de checklist de resposta a incidentes

## Objetivo

Um checklist claro ajuda uma equipe a não esquecer etapas de contenção, preservação de evidências, comunicação e recuperação durante um incidente. Esta lição demonstra como verificar se um checklist local contém os tópicos mínimos acordados pela própria organização. O programa não detecta incidentes, não acessa sistemas, não altera arquivos e não envia informações.

O exemplo opera apenas sobre dados fictícios definidos no próprio script. Adapte a lista de requisitos à política, aos papéis e às obrigações aplicáveis à sua organização.

## Exemplo seguro em Python

Salve como `incident_checklist_demo.py` e execute com `python3 incident_checklist_demo.py`.

```python
# Checklist inteiramente fictício: não inclua nomes, contatos ou detalhes reais.
REQUIRED_TOPICS = {
    "responsavel": "Responsável pelo registro inicial",
    "escopo": "Como delimitar sistemas e período afetados",
    "preservacao": "Como preservar evidências sem modificá-las",
    "comunicacao": "Canal aprovado para escalar o incidente",
    "recuperacao": "Critérios de recuperação e validação",
}

sample_runbook = {
    "responsavel": "Equipe de plantão (exemplo)",
    "escopo": "Registrar ativos administrados e janela temporal",
    "preservacao": "Seguir o procedimento interno de preservação",
    "comunicacao": "Canal interno de incidentes (fictício)",
    "recuperacao": "Validar serviços e monitorar conforme política",
}

def validate_checklist(checklist: dict[str, str]) -> list[str]:
    missing = []
    for key, description in REQUIRED_TOPICS.items():
        value = checklist.get(key)
        if not isinstance(value, str) or not value.strip():
            missing.append(description)
    return missing

if __name__ == "__main__":
    gaps = validate_checklist(sample_runbook)
    if gaps:
        print("Revisar os tópicos ausentes:")
        for topic in gaps:
            print(f"- {topic}")
    else:
        print("Todos os tópicos mínimos do exemplo estão presentes.")
```

Resultado esperado: `Todos os tópicos mínimos do exemplo estão presentes.` Para testar o alerta, remova temporariamente o valor fictício de `preservacao` e confirme que esse tópico aparece como ausente.

## Limitações e cuidados éticos

- Use o exemplo apenas como exercício local e substitua os tópicos de acordo com os procedimentos da sua organização. O código não acessa rede, contas, dispositivos ou arquivos.
- A presença de um texto não prova que uma etapa seja correta, suficiente, atualizada ou executável. Faça revisão humana com as pessoas responsáveis e exercícios de mesa autorizados.
- Não coloque no checklist senhas, tokens, dados pessoais, detalhes de vulnerabilidades exploráveis ou informações que possam expor pessoas e sistemas. Use armazenamento aprovado e acesso mínimo para documentação operacional real.
- Durante um incidente real, siga o plano aprovado, as obrigações legais e os canais internos de escalonamento; não improvise ações destrutivas nem altere evidências.
- Este pequeno validador verifica apenas campos ausentes ou vazios. Não substitui gestão de incidentes, aconselhamento jurídico, investigação forense ou uma avaliação de risco.

## Checklist

- [ ] Confirme que o procedimento pertence à organização e tem responsáveis definidos.
- [ ] Revise se escopo, preservação de evidências, escalonamento e recuperação estão cobertos.
- [ ] Confirme que cada etapa tem responsável, canal e critério verificável no runbook real.
- [ ] Remova credenciais, dados pessoais e detalhes desnecessários de exemplos e relatórios.
- [ ] Teste alterações em uma cópia fictícia/local e revise o resultado com os responsáveis.
- [ ] Registre data de revisão, versão e justificativa para exceções no sistema interno aprovado.
- [ ] Faça exercícios de mesa autorizados e atualize o plano após lições aprendidas.

## Teste local

Requer apenas Python 3 e sua biblioteca padrão. Execute `python3 incident_checklist_demo.py`; confirme a mensagem de sucesso. Como teste negativo, remova temporariamente uma chave ou deixe seu valor vazio e confirme que o tópico correspondente é listado. Não são necessários privilégios elevados, dependências adicionais, dados reais ou acesso à rede.
