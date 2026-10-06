# Dia 018 — Revisão local da validade de certificados TLS

Uma rotina de inventário pode identificar certificados que já expiraram ou estão próximos do vencimento, dando tempo para que responsáveis autorizados planejem a renovação. Este guia demonstra a leitura **local e somente de metadados** de um único certificado X.509 em formato PEM. O exemplo não abre conexões, não consulta serviços, não renova certificados e não altera arquivos.

## Uso autorizado e limitações éticas

Comece pelos certificados sintéticos criados em `/tmp`. Use o verificador somente com arquivos locais que você possui ou tem autorização explícita para revisar. Certificados e seus metadados podem revelar nomes internos, unidades ou arquitetura; não publique certificados de produção, nomes, caminhos internos ou resultados identificáveis. A chave privada criada apenas para o teste também deve permanecer fora do repositório e ser removida ao final.

O limite de 30 dias é didático, não uma política universal. Ajuste-o somente conforme uma política aprovada e os requisitos do serviço. Uma indicação de vencimento próximo é um alerta para revisão, não evidência de incidente. Não tente usar o resultado para acessar um sistema, testar um domínio ou contornar controles.

## Exemplo seguro em Node.js

Salve como `check_cert_expiry.js`. O programa recebe um único caminho para um certificado PEM local, rejeita links simbólicos diretos, limita a leitura a 64 KiB e não imprime o certificado, o nome do titular ou outros campos. Ele informa somente a proximidade do vencimento. Requer uma versão de Node.js que ofereça `crypto.X509Certificate`.

```javascript
#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const { X509Certificate } = require('node:crypto');

const MAX_BYTES = 64 * 1024;
const REVIEW_WITHIN_DAYS = 30;

function readLocalCertificate(filePath) {
  if (!filePath) throw new Error('input');
  const noFollow = fs.constants.O_NOFOLLOW;
  if (typeof noFollow !== 'number') throw new Error('platform');

  const fd = fs.openSync(filePath, fs.constants.O_RDONLY | noFollow);
  try {
    const info = fs.fstatSync(fd);
    if (!info.isFile() || info.size > MAX_BYTES) throw new Error('file');

    const buffer = Buffer.alloc(MAX_BYTES + 1);
    let total = 0;
    while (total < buffer.length) {
      const count = fs.readSync(fd, buffer, total, buffer.length - total, null);
      if (count === 0) break;
      total += count;
    }
    if (total > MAX_BYTES) throw new Error('size');
    return buffer.subarray(0, total).toString('utf8');
  } finally {
    fs.closeSync(fd);
  }
}

function main() {
  if (process.argv.length !== 3) {
    console.error('uso: node check_cert_expiry.js <certificado-PEM-local>');
    return 2;
  }

  try {
    const pem = readLocalCertificate(process.argv[2]);
    const certificate = new X509Certificate(pem);
    const expiration = Date.parse(certificate.validTo);
    if (!Number.isFinite(expiration)) throw new Error('date');

    const remainingMs = expiration - Date.now();
    const remainingDays = Math.ceil(remainingMs / (24 * 60 * 60 * 1000));
    if (remainingMs < 0) {
      console.log('revisão necessária: certificado expirado');
      return 1;
    }
    if (remainingDays <= REVIEW_WITHIN_DAYS) {
      console.log(`revisão necessária: vencimento em até ${REVIEW_WITHIN_DAYS} dias`);
      return 1;
    }
    console.log(`validade: mais de ${REVIEW_WITHIN_DAYS} dias restantes`);
    return 0;
  } catch {
    console.error('não foi possível ler ou interpretar o certificado local; nenhuma alteração foi feita');
    return 2;
  }
}

process.exitCode = main();
```

Teste com dois certificados autoassinados de laboratório e chaves temporárias, usando nomes inteiramente fictícios. Os artefatos ficam em `/tmp`, não devem ser adicionados ao Git e podem ser removidos ao final:

```bash
for days in 90 7; do
  openssl req -x509 -newkey rsa:2048 -nodes -days "$days" \
    -subj "/CN=example.invalid" \
    -keyout "/tmp/cert-ficticio-${days}d.key" \
    -out "/tmp/cert-ficticio-${days}d.pem"
done
node check_cert_expiry.js /tmp/cert-ficticio-90d.pem
node check_cert_expiry.js /tmp/cert-ficticio-7d.pem
rm -f /tmp/cert-ficticio-90d.key /tmp/cert-ficticio-90d.pem \
  /tmp/cert-ficticio-7d.key /tmp/cert-ficticio-7d.pem
```

O certificado de 90 dias deve resultar em código `0`; o de 7 dias deve sinalizar revisão necessária e terminar com código `1`. Arquivo ausente, PEM inválido, tamanho acima do limite ou opção de plataforma indisponível resulta em código `2`, sem exibir detalhes do certificado. Em um uso real, examine somente cópias ou fontes de inventário aprovadas e mantenha os dados resultantes em canal autorizado.

## Checklist

- [ ] A autorização, a finalidade e o escopo da revisão estão documentados; o teste inicial usa somente os certificados fictícios.
- [ ] O código é executado em Node.js atualizado e o limite de tamanho e a janela de revisão foram aprovados para o uso pretendido.
- [ ] Certificados, nomes internos, caminhos e resultados de sistemas reais não foram publicados nem enviados a serviços externos.
- [ ] A chave privada sintética e os certificados de teste permaneceram fora do repositório e foram removidos após o teste.
- [ ] O alerta é tratado como lembrete operacional, não como incidente confirmado nem como autorização para acessar serviços.
- [ ] A renovação e a implantação são realizadas por responsáveis autorizados, com revisão, plano de reversão e controles de mudança.
- [ ] Nenhum host, domínio, serviço ou sistema externo foi consultado; o exemplo não transmite nem altera dados.

## Limitações e próximos passos

O programa verifica somente a data de expiração indicada no certificado PEM fornecido. Não valida cadeia de confiança, assinatura, emissor, nome do host, usos permitidos, revogação, política criptográfica, instalação, configuração do serviço ou correspondência entre o arquivo e o certificado efetivamente apresentado por uma aplicação. Um certificado ainda dentro da validade pode ser inválido ou inadequado; um arquivo não analisado pode não representar o estado implantado. O relógio local incorreto também afeta o resultado.

Use inventário e processo de gestão de certificados aprovados para confirmar quais certificados estão implantados e quem é responsável por renová-los. Valide as mudanças em ambiente controlado, preserve a continuidade do serviço e nunca compartilhe chaves privadas. O script não automatiza renovação nem implantação.

## Referências de consulta local

- Documentação local do Node.js: `node:crypto` (`X509Certificate`) e `node:fs`.
- Documentação local do OpenSSL: `req` e política interna de gestão de certificados e mudanças.

> Este exemplo lê somente um certificado PEM local autorizado e verifica sua data de expiração; não acessa rede, valida confiança ou modifica arquivos.

<!-- Testado localmente com Node.js e certificados X.509 sintéticos; nenhuma conexão de rede foi realizada. -->
