# Dia 024 — Manifesto local de evidências para revisão autorizada

Ao organizar arquivos de um exercício de resposta a incidentes ou de uma auditoria autorizada, um manifesto local com nomes, tamanhos e hashes SHA-256 pode facilitar a conferência posterior de uma cópia de trabalho. Este guia demonstra a geração de um inventário **não recursivo** de arquivos regulares em uma pasta fictícia. O script lê somente os arquivos imediatamente contidos na pasta indicada e grava um manifesto JSON novo em outro caminho local; não imprime conteúdo, não apaga nem modifica os arquivos inventariados e não acessa a rede.

## Uso autorizado e limitações éticas

Use inicialmente apenas os arquivos fictícios criados pelo exemplo. Para dados reais, obtenha autorização explícita, confirme escopo, finalidade, acesso mínimo, retenção e procedimento de custódia com a equipe responsável. Não colete arquivos de dispositivos, contas, diretórios ou organizações fora do escopo autorizado. Manifestos podem revelar nomes de arquivos, tamanhos e horários; hashes também podem permitir correlação ou confirmação de conteúdo conhecido. Trate o manifesto como informação potencialmente sensível e nunca o publique junto com dados reais, segredos, evidências ou caminhos internos.

O manifesto é um auxílio de organização, não uma cadeia de custódia completa nem prova de autoria, horário, origem, integridade histórica ou completude. O código não segue links simbólicos e ignora subdiretórios e itens não regulares. Uma alteração concorrente durante a leitura pode produzir um resultado inconsistente. Preserve originais conforme o procedimento aprovado; para investigações formais, use ferramentas e armazenamento controlados, registre responsável, horário e transferências, e obtenha orientação da equipe de resposta a incidentes. Não tome medidas contra pessoas ou sistemas com base somente neste manifesto.

## Exemplo seguro em Python

Salve como `make_manifest.py`. Requer Python 3. O programa aceita uma pasta local e um caminho de saída que ainda não exista. Não percorre subpastas, não lê links simbólicos, processa cada arquivo em blocos e falha sem substituir um manifesto existente. O próprio manifesto não deve ficar dentro da pasta inventariada.

```python
#!/usr/bin/env python3
"""Create a SHA-256 inventory of immediate regular files in an authorized local directory."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="pasta local autorizada (somente nível imediato)")
    parser.add_argument("output", type=Path, help="novo manifesto JSON fora da pasta inventariada")
    args = parser.parse_args()

    try:
        root = args.directory.resolve(strict=True)
        if not root.is_dir():
            parser.error("a origem deve ser uma pasta local existente")
        output = args.output.absolute()
        if output.exists() or output.is_symlink():
            parser.error("a saída já existe; escolha um caminho novo para evitar sobrescrita")
        if output.parent.resolve(strict=True) == root or root in output.parent.resolve(strict=True).parents:
            parser.error("grave o manifesto fora da pasta inventariada")

        entries = []
        with os.scandir(root) as children:
            for child in sorted(children, key=lambda item: item.name):
                if not child.is_file(follow_symlinks=False):
                    continue
                path = root / child.name
                sha256, size = hash_file(path)
                entries.append({"name": child.name, "size_bytes": size, "sha256": sha256})

        document = {"algorithm": "SHA-256", "scope": "immediate_regular_files_only", "files": entries}
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(output, flags, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(document, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        except Exception:
            try:
                output.unlink()
            except OSError:
                pass
            raise
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"falha local ao criar o manifesto ({type(exc).__name__}); nenhum arquivo de origem foi alterado", file=__import__("sys").stderr)
        return 2

    print(f"manifesto criado: {len(entries)} arquivo(s); proteja o manifesto conforme a política local")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Execute somente com o fixture descartável abaixo:

```bash
mkdir -p /tmp/evidencias-ficticias /tmp/manifestos-ficticios
printf 'registro ficticio A\n' > /tmp/evidencias-ficticias/registro-a.txt
printf 'nota ficticia B\n' > /tmp/evidencias-ficticias/nota-b.txt
python3 make_manifest.py /tmp/evidencias-ficticias /tmp/manifestos-ficticios/manifesto.json
```

O resultado esperado é a criação de um manifesto com dois itens, tamanho em bytes e hash para cada nome. Confirme localmente que `files` contém somente `nota-b.txt` e `registro-a.txt`, em ordem alfabética, e que o comando termina com código `0`. Rode novamente com o mesmo caminho de saída: deve falhar sem substituir o manifesto anterior. O programa não imprime os hashes na saída do terminal, mas os grava no arquivo de manifesto; não compartilhe esse arquivo sem autorização. Remova os fixtures depois do teste.

## Checklist

- [ ] A execução foi testada primeiro com arquivos totalmente fictícios em uma pasta temporária.
- [ ] Há autorização explícita e escopo documentado para qualquer diretório real posteriormente revisado.
- [ ] A pasta de origem contém somente arquivos dentro do escopo; o script não percorre subpastas e ignora links e itens não regulares.
- [ ] O manifesto é gravado fora da origem, em caminho novo, com acesso restrito e retenção aprovada.
- [ ] Nomes, hashes, tamanhos, caminhos internos, dados pessoais, credenciais e segredos não foram publicados ou enviados a serviços externos.
- [ ] Os originais foram preservados conforme a política, e eventuais divergências são encaminhadas a responsáveis autorizados.
- [ ] A equipe não interpreta o manifesto isoladamente como prova de autoria, cronologia, completude ou incidente.
- [ ] Nenhuma rede, conta, máquina de terceiro ou serviço externo foi acessado.

## Limitações e próximos passos

A ordenação e o hash ajudam na comparação, mas não autenticam o manifesto nem impedem sua alteração posterior. O nome, tamanho ou conteúdo de um arquivo pode mudar durante a execução; o script não cria snapshot nem registra horário confiável, identidade do coletor, origem, permissões, ACLs ou transferências. Erros de leitura interrompem a criação; o código tenta remover uma saída parcial. Arquivos grandes podem exigir tempo e leitura proporcional ao tamanho. O algoritmo identifica bytes, não valida formato ou significado.

Armazene o manifesto e os originais em local aprovado com controles de acesso e trilha de auditoria. Para custódia formal, siga o procedimento organizacional e use mecanismos independentes de assinatura, registro de tempo e proteção contra alteração quando aplicáveis. Evite copiar evidências para repositórios públicos ou canais não aprovados.

> Exemplo exclusivamente local: inventário raso de arquivos fictícios, sem transmissão, execução de conteúdo ou alteração dos itens de origem.

<!-- Testado localmente com fixture fictício; não houve conexão de rede. -->
