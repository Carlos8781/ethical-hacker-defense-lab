# Dia 017 — Revisão defensiva de arquivos ZIP antes da restauração

Antes de restaurar um backup ou abrir um pacote recebido por um canal autorizado, uma revisão preliminar pode identificar metadados que merecem atenção: caminhos absolutos ou com `..`, links simbólicos, membros criptografados, volumes inesperadamente grandes ou taxas de compressão fora de um limite definido. Este guia demonstra uma triagem **local e somente de leitura** de arquivos ZIP fictícios. O exemplo não extrai arquivos nem acessa a rede.

## Uso autorizado e limitações éticas

Comece pelos arquivos sintéticos criados neste guia. Use a triagem somente sobre arquivos locais que você possui ou tem autorização explícita para revisar. Não baixe nem procure arquivos de terceiros, não envie o arquivo a serviços externos e não publique nomes de membros, caminhos internos, conteúdo, metadados sensíveis ou detalhes de backups reais.

Os limites numéricos do exemplo (20 MiB de arquivo, 1.000 membros, 32 MiB por membro, 100 MiB descompactados no total e razão máxima de 100:1) são **parâmetros didáticos**, não uma política universal. Ajuste-os somente com aprovação dos responsáveis, considerando o uso legítimo e o tamanho esperado dos arquivos. Um alerta não prova que o arquivo seja malicioso; um resultado sem alertas tampouco prova que seja seguro.

A ferramenta apenas consulta o diretório central e metadados do ZIP. Ela não extrai, executa, altera ou transmite arquivos e imprime somente um resumo, sem nomes de membros. Ainda assim, bibliotecas que analisam formatos complexos podem ter vulnerabilidades; use runtime atualizado e, para material não confiável, faça a triagem em estação de trabalho isolada e controlada. Não tente abrir conteúdo suspeito para “confirmar” o alerta.

## Exemplo seguro em Python

Salve como `review_zip.py`. O programa aceita um único arquivo regular local, rejeita links simbólicos diretos, impõe limites à leitura e procura sinais comuns de risco em metadados. Os nomes são normalizados para detectar separadores de caminho Windows e POSIX, mas nunca são exibidos.

```python
#!/usr/bin/env python3
"""Review ZIP metadata locally without extracting or displaying member names."""
import argparse
import re
import stat
import zipfile
from pathlib import Path

MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_ENTRIES = 1_000
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


def safe_member_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    if not normalized or normalized.startswith("/") or DRIVE_PREFIX.match(normalized):
        return False
    if ":" in normalized:
        return False
    return all(part not in {".", ".."} for part in normalized.split("/"))


def review(path: Path) -> set[str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("file")
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        return {"tamanho do arquivo"}
    if not zipfile.is_zipfile(path):
        raise ValueError("zip")

    findings: set[str] = set()
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ENTRIES:
                return {"quantidade de membros"}

            total_size = 0
            for member in members:
                if not safe_member_name(member.filename):
                    findings.add("caminho de membro")

                mode = (member.external_attr >> 16) & 0o170000
                if mode == stat.S_IFLNK:
                    findings.add("link simbólico")
                if member.flag_bits & 0x1:
                    findings.add("membro criptografado")
                if member.file_size < 0 or member.compress_size < 0:
                    findings.add("tamanho inválido")
                    continue
                if member.file_size > MAX_MEMBER_BYTES:
                    findings.add("tamanho por membro")
                total_size += member.file_size
                if member.file_size and (
                    member.compress_size == 0
                    or member.file_size / member.compress_size > MAX_COMPRESSION_RATIO
                ):
                    findings.add("razão de compressão")

            if total_size > MAX_TOTAL_BYTES:
                findings.add("tamanho descompactado total")
    except (OSError, RuntimeError, zipfile.BadZipFile):
        raise ValueError("zip") from None
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="arquivo ZIP local autorizado")
    args = parser.parse_args()

    try:
        findings = review(args.archive)
    except (OSError, ValueError):
        parser.error("arquivo local inválido, inacessível ou fora do formato esperado")

    if findings:
        print(f"revisão necessária: {len(findings)} categoria(s); não extraia o arquivo")
        return 1
    print("metadados dentro dos limites didáticos; isso não autoriza a extração")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Crie dois ZIPs descartáveis contendo somente dados fictícios — um com caminho comum e outro com um nome de membro que simula tentativa de sair da pasta de restauração. O exemplo escreve somente em `/tmp` e não extrai nenhum deles:

```bash
python3 - <<'PY'
from zipfile import ZIP_DEFLATED, ZipFile
for path, member in [
    ("/tmp/zip-ficticio-ok.zip", "docs/readme.txt"),
    ("/tmp/zip-ficticio-revisar.zip", "../fora-da-pasta.txt"),
]:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(member, "conteudo totalmente ficticio\n")
PY
python3 review_zip.py /tmp/zip-ficticio-ok.zip
python3 review_zip.py /tmp/zip-ficticio-revisar.zip
```

O primeiro comando do verificador deve terminar com código `0` e o segundo com código `1`. O segundo apenas sinaliza que a revisão autorizada deve continuar por procedimento seguro; ele não demonstra intenção, exploração ou dano. Arquivo ausente, inválido ou inacessível resulta em erro de argumento (código `2`).

## Checklist

- [ ] A autorização e a finalidade da revisão do arquivo estão documentadas; o teste inicial usa somente os ZIPs fictícios.
- [ ] O runtime Python está atualizado e o arquivo é tratado em estação isolada quando sua origem não é confiável.
- [ ] Os limites foram aprovados e ajustados ao perfil legítimo dos arquivos, sem enfraquecer controles para “fazer passar” um caso suspeito.
- [ ] O resultado sem alertas foi entendido apenas como triagem de metadados, não como certificação de segurança ou autenticidade.
- [ ] Alertas são encaminhados a responsáveis autorizados; o arquivo original é preservado conforme política de evidências e retenção.
- [ ] Nenhum membro foi extraído, executado, enviado a terceiros ou publicado; saídas e relatórios não revelam nomes ou caminhos internos.
- [ ] Qualquer restauração posterior segue procedimento aprovado, com destino isolado, proteção contra sobrescrita, verificação independente e plano de recuperação.
- [ ] Nenhum sistema externo foi acessado e nenhuma ação foi realizada fora do escopo autorizado.

## Limitações e próximos passos

Uma inspeção de metadados não verifica o conteúdo dos arquivos, sua procedência, integridade, autenticidade, comportamento, compatibilidade ou segurança. Formatos ZIP podem incluir colisões de nomes dependentes do sistema de arquivos, dados malformados e outros casos não cobertos. Os limites de tamanho e compressão são heurísticas, e `zipfile` precisa interpretar a estrutura do arquivo. A ferramenta não inspeciona outros formatos, não substitui verificação de assinatura/hash por fonte independente, análise antimalware aprovada, controles de acesso, backups verificados ou um processo formal de restauração.

Se houver alerta, não extraia o arquivo no sistema de produção nem remova o alerta para prosseguir. Preserve-o segundo a política aplicável e solicite avaliação por responsáveis de segurança e operações. Uma restauração só deve ocorrer em destino controlado, com autorização, ferramenta atualizada, isolamento, permissões mínimas, proteção contra sobrescrita e plano testado de reversão.

## Referências de consulta local

- Documentação da biblioteca padrão do Python: `zipfile`, `pathlib`, `stat` e `re`.
- Política interna de gestão de backups, análise de arquivos, resposta a incidentes e restauração.

> O exemplo revisa somente metadados de um ZIP local autorizado. Não extrai, executa, transmite ou prova que o arquivo seja seguro.

<!-- Testado localmente com Python 3 e arquivos ZIP sintéticos; nenhum arquivo foi extraído. -->
