# Dia 004 — Cabeçalhos de segurança em uma aplicação web local

Cabeçalhos HTTP bem escolhidos reduzem riscos comuns em uma aplicação web, como interpretação incorreta de tipos, inclusão da página em frames de outros sites e envio desnecessário de informações de referência. Eles são uma camada de hardening: não corrigem falhas de autenticação, autorização, validação de entrada, dependências ou configuração de TLS. A política deve ser testada com as funcionalidades reais da aplicação e revisada quando a arquitetura mudar.

## Uso autorizado e limitações éticas

Use o exemplo somente em uma aplicação que você administra ou para a qual tem autorização explícita. O código abaixo inicia apenas um servidor local em `127.0.0.1`, não faz varredura, não envia requisições a terceiros, não coleta credenciais e não tenta contornar controles. Os valores são uma linha de base educacional, não uma garantia de segurança. Uma Content Security Policy (CSP) muito restritiva pode quebrar recursos legítimos; uma política permissiva demais oferece pouca proteção. `Strict-Transport-Security` (HSTS) deve ser enviado somente por uma aplicação acessada com HTTPS válido e não deve ser ativado casualmente em um domínio que ainda precise funcionar por HTTP. Não publique cabeçalhos, logs ou exemplos contendo tokens, cookies reais, dados pessoais ou nomes internos.

## Exemplo seguro em Node.js

O servidor de demonstração responde a uma única rota fictícia e aplica cabeçalhos de hardening sem depender de pacotes externos. Ele escuta somente no loopback e usa uma porta escolhida pelo sistema, o que evita ocupar uma porta compartilhada do laboratório.

```javascript
#!/usr/bin/env node
const http = require('node:http');

function applySecurityHeaders(response) {
  response.setHeader('Content-Security-Policy', "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");
  response.setHeader('X-Content-Type-Options', 'nosniff');
  response.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
}

const server = http.createServer((request, response) => {
  applySecurityHeaders(response);
  if (request.url !== '/' || request.method !== 'GET') {
    response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    response.end('not found\n');
    return;
  }

  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end('<!doctype html><title>Laboratório local</title><p>Resposta fictícia.</p>\n');
});

server.listen(0, '127.0.0.1', () => {
  const address = server.address();
  console.log(`servidor local em http://${address.address}:${address.port}/`);
});
```

Salve o trecho como `local-security-headers.js` fora do repositório e valide sua sintaxe:

```bash
node --check local-security-headers.js
node local-security-headers.js
```

Em outro terminal do mesmo ambiente autorizado, confirme apenas a resposta local com `curl`, substituindo a porta exibida pelo programa:

```bash
curl --silent --show-error --dump-header - http://127.0.0.1:PORTA/ -o /tmp/resposta-ficticia.html
```

A saída deve conter `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy` e `Permissions-Policy`. Interrompa o processo com `Ctrl-C` após o teste. Em uma aplicação real, valide primeiro em staging, revise recursos legítimos (scripts, estilos, imagens e frames), use HTTPS e registre a decisão de política. Só acrescente HSTS depois de confirmar que todo o domínio e seus subdomínios relevantes suportam HTTPS; nesse caso, a aplicação pode emitir, por exemplo, `Strict-Transport-Security: max-age=31536000; includeSubDomains` conforme a política aprovada.

## Checklist

- [ ] A aplicação testada pertence à equipe ou está coberta por autorização explícita.
- [ ] O teste foi feito somente em `127.0.0.1`, staging autorizado ou outro ambiente sob controle.
- [ ] A CSP foi revisada contra os recursos legítimos e não foi enfraquecida apenas para esconder erros.
- [ ] `X-Content-Type-Options`, `Referrer-Policy` e `Permissions-Policy` foram verificados na resposta.
- [ ] HSTS só será ativado após confirmar HTTPS válido e a política de domínio apropriada.
- [ ] O comportamento foi testado com as rotas e métodos necessários, incluindo respostas de erro.
- [ ] Não foram usados cookies, tokens, dados pessoais, domínios externos ou segredos reais.
- [ ] O teste ocorreu em staging antes da produção e existe um plano de reversão versionado.
- [ ] A configuração será revisada junto com mudanças de frontend, integrações e dependências.

## Limitações e próximos passos

Cabeçalhos não substituem controle de acesso no servidor, proteção contra CSRF quando aplicável, escape e validação de dados, gestão segura de sessão, atualização de dependências ou monitoramento. Depois do teste local, faça uma revisão autorizada da configuração de TLS, dos logs e das dependências, mantendo os resultados mínimos necessários e sem registrar valores sensíveis.
