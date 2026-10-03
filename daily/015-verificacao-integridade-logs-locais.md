# Dia 015 — Verificação local da integridade de exportações de logs

Uma exportação local de logs pode ser comparada com uma impressão criptográfica (hash) registrada anteriormente por um processo confiável. Essa comparação ajuda a detectar alterações acidentais ou divergências no arquivo desde a criação da referência. Este guia usa SHA-256 em um arquivo fictício, sem abrir serviços, consultar a rede ou exibir o conteúdo do log.

## Uso autorizado e limitações éticas

Use o exemplo somente com um arquivo local que você possui ou tem autorização explícita para ler. Comece com o arquivo fictício abaixo. Logs reais podem conter dados pessoais, endereços, nomes de contas, tokens, detalhes internos ou informações de incidentes: não os copie para um repositório público, não os compartilhe e não inclua seu conteúdo ou hash em relatórios públicos sem aprovação.

O script lê, em blocos, apenas o arquivo indicado; não altera, apaga, transmite ou imprime seu conteúdo. Ele não acessa rede, contas, sistemas ou arquivos adjacentes. A execução é somente uma verificação, não uma autorização para coletar logs. Respeite escopo, finalidade, acesso mínimo, retenção e políticas internas.

Uma correspondência SHA-256 demonstra somente que os bytes lidos correspondem à referência informada. Não prova quem criou o arquivo, quando foi criado, se a referência é autêntica ou se o próprio log é completo e verdadeiro. Se alguém puder substituir tanto o arquivo como o hash de referência, a comparação não oferece garantia independente. Guarde a referência em canal ou registro protegido contra alteração, com controle de acesso e, quando necessário, assinatura ou trilha de auditoria. Não use o resultado isoladamente para decisões disciplinares, legais ou de resposta a incidentes.

## Exemplo seguro em Python

Salve o código como `verify_log_hash.py`. O programa requer um caminho para um arquivo local regular, não aceita links simbólicos diretos, recebe uma referência SHA-256 de 64 dígitos hexadecimais e imprime somente o resultado agregado. Ele processa o arquivo em blocos para evitar carregar todo o conteúdo na memória.

```python
#!/usr/bin/env python3
"""Compare one authorized local file with a trusted SHA-256 reference."""
import argparse
import hashlib
import re
from pathlib import Path

CHUNK_SIZE = 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="arquivo local autorizado")
    parser.add_argument("expected_sha256", help="referência SHA-256 confiável, 64 dígitos hexadecimais")
    args = parser.parse_args()

    if not SHA256_PATTERN.fullmatch(args.expected_sha256):
        parser.error("a referência deve conter exatamente 64 dígitos hexadecimais")
    if args.file.is_symlink() or not args.file.is_file():
        parser.error("informe um arquivo local regular, existente e sem link simbólico direto")

    digest = hashlib.sha256()
    try:
        with args.file.open("rb") as stream:
            while chunk := stream.read(CHUNK_SIZE):
                digest.update(chunk)
    except OSError:
        parser.error("não foi possível ler o arquivo local autorizado")

    if digest.hexdigest().casefold() == args.expected_sha256.casefold():
        print("integridade: corresponde à referência informada")
        return 0
    print("integridade: divergência detectada; encaminhe para revisão autorizada")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Teste usando um arquivo descartável com conteúdo fictício e uma referência conhecida para esses bytes:

```bash
printf 'simulacao-ficticia: alerta de integridade\n' > /tmp/log-ficticio.txt
python3 verify_log_hash.py /tmp/log-ficticio.txt b382f41f29813adee3412fa4a8c7feb17f56d2acbfa3165caffe4bbdfd7edf3e
```

A execução de teste deve imprimir `integridade: corresponde à referência informada` e terminar com código `0`. Para conferir o caminho de divergência, repita o comando alterando um único dígito da referência: o programa deve imprimir a mensagem de divergência e terminar com código `1`. Argumentos inválidos, caminho inexistente, link simbólico ou falha de leitura resultam em erro de argumento e código `2`; nenhum conteúdo nem hash calculado é impresso.

A referência fixa acima serve exclusivamente para o texto fictício mostrado. Em um processo real, obtenha a referência por uma fonte independente e autorizada, como um registro controlado criado no momento da exportação; não a calcule do mesmo arquivo apenas na hora da verificação e conclua que isso prova a integridade histórica.

## Checklist

- [ ] Há autorização documentada para ler o arquivo e realizar a verificação neste escopo.
- [ ] O primeiro teste usa somente o conteúdo fictício e o arquivo temporário local.
- [ ] Logs reais, nomes, identificadores, tokens, dados pessoais, caminhos internos e detalhes de incidentes não foram incluídos no repositório ou na saída.
- [ ] A referência esperada veio de registro independente e protegido contra alteração, e sua origem e responsabilidade estão documentadas.
- [ ] A referência foi compartilhada apenas com as pessoas autorizadas; hashes de arquivos sensíveis também podem revelar informação e devem ser tratados conforme a política interna.
- [ ] Uma divergência é preservada e encaminhada a responsáveis autorizados; não se sobrescreve o original nem se tira conclusão automática sobre causa ou autoria.
- [ ] A cadeia de custódia, retenção, acesso mínimo e resposta a incidentes seguem os procedimentos aprovados.
- [ ] Nenhum serviço externo, rede, conta ou sistema de terceiros foi acessado; o script não alterou o arquivo.

## Limitações e próximos passos

A comparação não verifica a semântica, completude, cronologia, origem ou legitimidade dos eventos no log; não autentica a referência e não impede alterações futuras. O arquivo também pode mudar enquanto é lido; para investigações formais, use cópias/snapshots estáveis, relógios e coleta controlados, registro de custódia e ferramentas aprovadas. Um hash não substitui controles de acesso, armazenamento protegido, backups, assinatura digital ou monitoramento. Investigue divergências por um processo autorizado, preservando evidências e evitando expor dados sensíveis.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `hashlib`, `argparse` e `pathlib`.
- Políticas internas aprovadas de registro, privacidade, retenção, auditoria e resposta a incidentes.

> Este exemplo compara apenas um arquivo local autorizado com uma referência fornecida; não consulta rede, não revela conteúdo e não altera o arquivo.

<!-- Testado localmente com Python 3 e arquivo fictício. -->
