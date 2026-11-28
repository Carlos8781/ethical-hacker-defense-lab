# Dia 070 — Revisão local da configuração de core dumps

Core dumps podem conter dados da memória de um processo, inclusive informação sensível. Uma revisão preventiva deve confirmar se o sistema e o processo atual limitam sua geração de forma compatível com a política da organização. Este guia apenas lê duas configurações do kernel e o limite do processo Python em execução; não cria, abre, remove nem altera core dumps.

## Exemplo seguro em Python

O exemplo é destinado a Linux com Python 3. Ele lê `kernel/core_pattern` e `fs/suid_dumpable` sob `/proc/sys`, e consulta o limite `RLIMIT_CORE` do processo atual. A função permite fornecer uma raiz alternativa para que os testes usem arquivos sintéticos, sem depender das configurações reais do host.

```python
from pathlib import Path
import resource


def inspect_core_dump_policy(proc_sys: Path, soft_limit: int) -> dict[str, str]:
    """Leia somente configurações locais; não acessa arquivos de dump."""
    core_pattern = (proc_sys / "kernel/core_pattern").read_text(encoding="utf-8").strip()
    suid_value = (proc_sys / "fs/suid_dumpable").read_text(encoding="ascii").strip()

    if suid_value not in {"0", "1", "2"}:
        raise ValueError("valor suid_dumpable inesperado")

    if core_pattern.startswith("|"):
        pattern_kind = "handler_pipe"
    elif core_pattern:
        pattern_kind = "file_pattern"
    else:
        pattern_kind = "empty"

    if soft_limit == resource.RLIM_INFINITY:
        limit = "unlimited"
    elif soft_limit == 0:
        limit = "disabled_for_this_process"
    else:
        limit = "finite"

    return {
        "core_pattern_kind": pattern_kind,
        "suid_dumpable": suid_value,
        "process_soft_limit": limit,
    }


if __name__ == "__main__":
    try:
        soft_limit, _ = resource.getrlimit(resource.RLIMIT_CORE)
        result = inspect_core_dump_policy(Path("/proc/sys"), soft_limit)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Não foi possível ler a configuração ({type(exc).__name__}).")

    for key, value in result.items():
        print(f"{key}={value}")
```

O resultado classifica o padrão sem exibir seu conteúdo, que pode conter caminhos ou comandos configurados localmente. Interprete os valores segundo a política aprovada: `suid_dumpable=0` restringe dumps de processos privilegiados; outros valores requerem revisão cuidadosa. Um limite finito ou desabilitado para este processo não determina os limites de outros serviços.

## Teste local com dados fictícios

Salve o código em `inspect_core_dumps.py` e execute o teste abaixo. Ele cria apenas arquivos temporários sintéticos e confirma as classificações, incluindo rejeição de configuração fora do conjunto documentado. Nenhum arquivo do sistema é alterado.

```bash
python3 - <<'PY'
import tempfile
from pathlib import Path
import resource
from inspect_core_dumps import inspect_core_dump_policy

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    (root / "kernel").mkdir()
    (root / "fs").mkdir()
    (root / "kernel/core_pattern").write_text("core.%p\n", encoding="utf-8")
    (root / "fs/suid_dumpable").write_text("0\n", encoding="ascii")
    result = inspect_core_dump_policy(root, 1024 * 1024)
    assert result == {
        "core_pattern_kind": "file_pattern",
        "suid_dumpable": "0",
        "process_soft_limit": "finite",
    }

    (root / "kernel/core_pattern").write_text("|handler\n", encoding="utf-8")
    assert inspect_core_dump_policy(root, 0)["core_pattern_kind"] == "handler_pipe"
    assert inspect_core_dump_policy(root, 0)["process_soft_limit"] == "disabled_for_this_process"

    (root / "fs/suid_dumpable").write_text("9\n", encoding="ascii")
    try:
        inspect_core_dump_policy(root, resource.RLIM_INFINITY)
    except ValueError:
        pass
    else:
        raise AssertionError("valor inesperado deveria ser rejeitado")
print("Testes sintéticos aprovados.")
PY
```

## Limitações éticas e técnicas

- Execute a inspeção apenas em equipamentos que você administra ou tem autorização explícita para revisar. O exemplo não faz chamadas de rede, varredura, exploração nem alteração de configuração.
- Core dumps podem conter segredos, dados pessoais e material de autenticação. Não os abra, colete ou publique como parte deste exercício; siga políticas aprovadas de retenção e acesso.
- `/proc/sys` mostra parâmetros do kernel, enquanto `RLIMIT_CORE` consultado aqui aplica-se somente ao processo Python atual. Serviços podem ter limites próprios, namespaces ou configurações de systemd diferentes.
- A classificação do padrão evita imprimir seu conteúdo, mas não determina se um handler configurado é confiável ou seguro. Revise-o por processo formal e com responsáveis autorizados.
- Este script é uma verificação informativa, não altera a política nem prova que nenhum dump possa ser criado. Ausência de leitura ou valor inesperado deve ser encaminhado ao administrador, não contornado.
- Os valores recomendados dependem do sistema operacional, requisitos de diagnóstico e política organizacional. Não mude controles de produção sem aprovação e plano de reversão.

## Checklist

- [ ] Confirme autorização, equipamento, finalidade e política aplicável antes da inspeção.
- [ ] Teste primeiro com os arquivos sintéticos em diretório temporário.
- [ ] Verifique que o resultado não imprime o padrão bruto nem dados de dumps.
- [ ] Compare os valores com a política e revise separadamente limites de serviços e configurações systemd.
- [ ] Não leia, colete ou compartilhe core dumps; trate qualquer achado conforme as regras internas de dados sensíveis.
- [ ] Encaminhe divergências ao responsável autorizado; não altere controles de produção sem aprovação documentada.
