# Dia 038 — Validação offline de cadeia de certificados TLS

A revisão de datas de validade, tratada em outro guia, não confirma por si só que um certificado foi emitido por uma autoridade confiável. Para uma análise autorizada e sem tráfego de rede, o OpenSSL pode verificar um certificado local contra um arquivo local de autoridades confiáveis. Este exercício usa somente arquivos PEM fornecidos pela equipe ou certificados fictícios gerados no laboratório. A opção `-no-CApath` impede a busca em diretórios implícitos de autoridades; a confiança vem explicitamente de `-CAfile`.

## Exemplo seguro em laboratório local

Requer OpenSSL instalado. Substitua os caminhos por arquivos PEM obtidos e aprovados para revisão. O comando valida a cadeia do certificado de exemplo contra a CA indicada; não contata o servidor nomeado no certificado nem modifica os arquivos:

```bash
openssl verify -no-CApath -CAfile ./lab/ca-confiavel.pem ./lab/servico.pem
```

O resultado `OK` significa apenas que o OpenSSL conseguiu validar aquele certificado sob a política e o conjunto de confiança configurados. Esta invocação não testa conexão TLS, hostname, configuração de protocolo/cifra do servidor, revogação ou se a CA é apropriada à política da organização. Para validar um hostname ou revogação, use um procedimento interno aprovado, contra sistemas administrados e com as opções adequadas; não transforme este exercício em teste de terceiros.

Teste reproduzível com certificados descartáveis, criados e removidos somente em diretório temporário. Nenhuma chave ou certificado de laboratório é adicionado ao repositório:

```bash
set -eu
lab="$(mktemp -d)"
trap 'rm -rf "$lab"' EXIT
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$lab/ca.key" \
  -out "$lab/ca.pem" -days 1 -subj '/CN=CA Ficticia de Teste' >/dev/null 2>&1
openssl req -new -newkey rsa:2048 -nodes -keyout "$lab/leaf.key" \
  -out "$lab/leaf.csr" -subj '/CN=servico.local' >/dev/null 2>&1
openssl x509 -req -in "$lab/leaf.csr" -CA "$lab/ca.pem" -CAkey "$lab/ca.key" \
  -CAcreateserial -out "$lab/leaf.pem" -days 1 >/dev/null 2>&1
openssl verify -no-CApath -CAfile "$lab/ca.pem" "$lab/leaf.pem"
```

O exemplo gera material temporário sem senha apenas para um teste efêmero: não reutilize essas chaves, não as copie para produção e não as publique. A remoção automática ocorre ao fim do comando; interrompê-lo abruptamente pode deixar arquivos no diretório temporário, que devem ser removidos.

## Limitações e ética

- Revise somente certificados e âncoras de confiança que você administra ou para os quais possui autorização explícita.
- Não use nomes de domínio, endereços de terceiros nem conecte este teste a serviços remotos; a validação mostrada é inteiramente local.
- `OK` não demonstra que a âncora de confiança foi aprovada, que o hostname é correto, que há revogação consultada ou que o serviço está configurado com segurança.
- Trate chaves privadas como segredos. O teste usa chaves fictícias descartáveis e nunca deve incluir chaves reais em comandos compartilhados, commits, logs ou relatórios.
- Considere versão do OpenSSL, política criptográfica, intermediárias necessárias e formato dos arquivos ao interpretar resultados. Um erro pode decorrer de cadeia incompleta ou CA incorreta e exige análise autorizada, não tentativa de contornar a validação.

## Checklist

- [ ] Confirmei autorização e origem dos certificados e do arquivo de CA.
- [ ] Usei somente arquivos locais e indiquei explicitamente a CA confiável com `-CAfile`.
- [ ] Confirmei que o exercício não abriu conexões de rede nem alterou certificados existentes.
- [ ] Testei o comando com certificado e chave fictícios em diretório temporário.
- [ ] Removi o material temporário e não incluí chaves privadas, certificados internos ou dados sensíveis no repositório.
- [ ] Registrei que a validação de cadeia não substitui verificações de hostname, revogação, política ou configuração do serviço.
- [ ] Encaminhei falhas à equipe responsável e não tentei ignorar validações ou ampliar o escopo da revisão.
