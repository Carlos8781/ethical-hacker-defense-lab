# Dia 003 — Auditoria local de dependências Node.js

Dependências de terceiros ampliam a superfície de risco de uma aplicação: uma versão vulnerável, ausente ou diferente do lockfile pode introduzir falhas difíceis de perceber em uma revisão comum. Uma auditoria local e repetível ajuda a detectar inconsistências antes de uma entrega, mas não substitui a revisão de avisos de segurança, a política de atualização, os testes e a avaliação de risco da equipe.

## Uso autorizado e limitações éticas

Execute o exemplo somente em um projeto Node.js que você administra ou para o qual tem autorização explícita. O script inspeciona apenas a árvore local de dependências por meio de `npm ls`; ele não instala, remove ou atualiza pacotes, não executa scripts de terceiros, não faz varredura de rede e não tenta explorar vulnerabilidades. O resultado pode conter falsos positivos, especialmente quando há dependências opcionais, pares de versões incompatíveis ou módulos instalados de forma incompleta. Não copie dados sensíveis para relatórios. Para uma decisão de atualização, confirme a origem do pacote, a compatibilidade, os avisos publicados pelos mantenedores e a política de mudança da organização.

## Exemplo seguro em Node.js

O verificador abaixo recebe uma pasta local, solicita ao npm a árvore já instalada e resume problemas informados pelo próprio gerenciador. A opção `--depth=0` mantém o exemplo pequeno e previsível: ele verifica as dependências diretas do projeto e não baixa nada. O código também trata a saída JSON mesmo quando `npm ls` retorna código diferente de zero para indicar uma árvore inválida ou incompleta.

```javascript
#!/usr/bin/env node
/** Inspeciona dependências diretas de um projeto Node.js local autorizado. */
const { spawnSync } = require('node:child_process');
const path = require('node:path');

const project = path.resolve(process.argv[2] || process.cwd());
const result = spawnSync('npm', ['ls', '--json', '--depth=0'], {
  cwd: project,
  encoding: 'utf8',
  stdio: ['ignore', 'pipe', 'pipe'],
});

if (result.error) {
  console.error(`não foi possível executar npm ls: ${result.error.message}`);
  process.exit(2);
}

let report;
try {
  report = JSON.parse(result.stdout || result.stderr || '{}');
} catch {
  console.error('a saída do npm não era JSON; revise a execução local manualmente');
  process.exit(2);
}

const problems = Object.entries(report.problems || {});
if (problems.length === 0 && (result.status ?? 0) === 0) {
  console.log('dependências diretas locais sem problemas reportados pelo npm ls');
  process.exit(0);
}

for (const [name, detail] of problems) {
  console.log(`${name}: ${detail}`);
}
console.log(`revisar ${problems.length} problema(s) reportado(s); nenhuma alteração foi feita`);
process.exit(1);
```

Salve o exemplo como `local-dependency-check.js` fora do repositório, ou adapte-o ao procedimento aprovado pela equipe. Uma execução local seria:

```bash
node local-dependency-check.js ./projeto-node-autorizado
```

Um retorno `0` significa que não houve problema reportado para as dependências diretas. Um retorno `1` pede revisão; um retorno `2` indica erro na execução ou no formato da saída. Antes de corrigir algo, faça uma cópia ou use o fluxo de mudanças da equipe. Não use `npm install` automaticamente como resposta a um alerta: confirme a versão desejada, atualize o lockfile de maneira revisável e execute os testes em um ambiente isolado.

## Checklist

- [ ] O projeto auditado pertence à equipe ou está coberto por autorização explícita.
- [ ] Foi feita uma cópia ou criado um ponto de restauração antes de qualquer mudança.
- [ ] A verificação usou apenas a árvore local e não instalou, removeu ou atualizou pacotes.
- [ ] O `package-lock.json` ou lockfile equivalente está versionado e foi revisado junto com `package.json`.
- [ ] Cada problema reportado foi confirmado, classificado e tratado conforme a política de risco.
- [ ] Atualizações foram testadas em ambiente local ou de CI antes da entrega.
- [ ] Nenhum segredo, token, arquivo de configuração privado ou conteúdo sensível entrou no relatório.
- [ ] A equipe registrou a decisão, a versão escolhida e o plano de acompanhamento.
- [ ] A auditoria foi combinada com revisão de código, avisos de segurança e monitoramento autorizado.

## Ideias para aprofundar

Em um ambiente controlado, compare a árvore instalada com o lockfile, use um serviço de advisories aprovado pela organização e defina uma janela de atualização. Faça isso com credenciais de serviço mínimas, sem enviar código privado a terceiros e sem transformar a auditoria em uma varredura de sistemas que não pertencem à equipe.

