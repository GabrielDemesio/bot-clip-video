import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple

from app.cli.menu import choose_from_list
from app.services.s3_sync import S3Syncer, S3SyncError


def _prompt_text(label: str, default: Optional[str] = None) -> str:
    if default:
        value = input(f"{label} [{default}]: ").strip()
        return value if value else default
    return input(f"{label}: ").strip()

def _is_yes(value: str) -> bool:
    v = (value or "").strip().lower()
    return v in {"y", "yes", "s", "sim"}


def _split_prefix(prefix: str) -> Tuple[str, str]:
    normalized = prefix.strip().lstrip('/')
    if not normalized:
        return "", ""
    if normalized.endswith('/'):
        normalized = normalized[:-1]
    parent, _, leaf = normalized.rpartition('/')
    if parent:
        parent += '/'
    return parent, leaf + '/'


def browse_local(start_dir: Path) -> Optional[Path]:
    current = start_dir.resolve()

    while True:
        print("\n" + "=" * 60)
        print(f"📁 Navegador local: {current}")
        print("=" * 60)
        print("Opções: [0] selecionar ESTA pasta  [u] voltar  [q] cancelar")
        print("Dica: número = entrar, s<num> = selecionar item, 0 = selecionar a pasta atual.")

        try:
            entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            print("✗ Permission denied.")
            entries = []

        visible: List[Path] = [p for p in entries if not p.name.startswith(".")]

        if visible:
            print("\nItens:")
            for idx, p in enumerate(visible, start=1):
                suffix = "/" if p.is_dir() else ""
                print(f"  [{idx}] {p.name}{suffix}")

        choice = input("\nDigite um número, s<num>, ou 0/u/q: ").strip().lower()
        if choice == "q":
            return None
        if choice == "u":
            current = current.parent
            continue
        if choice == "0":
            return current
        if choice.startswith("s") and choice[1:].isdigit() and visible:
            idx = int(choice[1:])
            if 1 <= idx <= len(visible):
                picked = visible[idx - 1]
                return picked
            print("Opção inválida.")
            continue
        if choice.isdigit() and visible:
            idx = int(choice)
            if 1 <= idx <= len(visible):
                picked = visible[idx - 1]
                if picked.is_dir():
                    current = picked.resolve()
                    continue
                return picked
        print("Opção inválida.")


def browse_s3_prefix(syncer: S3Syncer, aws_profile: Optional[str], start_prefix: str = "") -> Optional[str]:
    current = start_prefix.lstrip('/')
    if current and not current.endswith('/'):
        current += '/'

    while True:
        print("\n" + "=" * 60)
        shown = f"s3://{syncer.bucket_name}/{current}" if current else f"s3://{syncer.bucket_name}/"
        print(f"🪣 Navegador S3: {shown}")
        print("=" * 60)
        print("Opções: [0] usar este prefixo (enviar aqui)  [u] voltar  [q] cancelar")

        try:
            prefixes, objects = syncer.list_prefix_children(prefix=current, aws_profile=aws_profile)
        except S3SyncError as e:
            print(f"✗ Failed to list prefix: {e}")
            choice = input("\nType 'u' to go up or 'q' to cancel: ").strip().lower()
            if choice == "u":
                parent, _ = _split_prefix(current)
                current = parent
                continue
            return None

        # Show "folders" first
        display_dirs: List[str] = [
            (p[len(current):] if current and p.startswith(current) else p)
            for p in prefixes
        ]

        if display_dirs:
            print("\nPastas:")
            for idx, d in enumerate(display_dirs, start=1):
                print(f"  [{idx}] {d}")

        if objects and not display_dirs:
            print(f"\nEncontrado(s) {len(objects)} arquivo(s) neste prefixo.")
        print("Dica: digite 0 para enviar arquivos para esta pasta.")

        choice = input("\nDigite o número da pasta, ou 0/u/q: ").strip().lower()
        if choice == "q":
            return None
        if choice == "u":
            parent, _ = _split_prefix(current)
            current = parent
            continue
        if choice == "0":
            return current
        if choice.isdigit() and display_dirs:
            idx = int(choice)
            if 1 <= idx <= len(display_dirs):
                current = (current + display_dirs[idx - 1]).lstrip('/')
                continue
        print("Opção inválida.")


def main() -> None:
    print("\n" + "=" * 60)
    print("📤 AWS S3 Sync (interativo)")
    print("=" * 60)

    aws_profile = _prompt_text("AWS profile (vazio para padrão)", default="").strip()
    if not aws_profile:
        aws_profile = None

    default_bucket = os.getenv("S3_BUCKET", "").strip()
    bucket_input = _prompt_text("Bucket S3 (digite '?' para listar)", default=default_bucket or None).strip()

    if bucket_input == "?":
        # Temporary syncer just to list buckets; bucket_name value doesn't matter here.
        tmp = S3Syncer(bucket_name="__dummy__")
        try:
            buckets = tmp.list_buckets(aws_profile=aws_profile)
        except S3SyncError as e:
            print(f"✗ Não foi possível listar buckets: {e}")
            bucket_input = _prompt_text("Bucket S3", default=default_bucket or None).strip()
        else:
            if not buckets:
                print("Nenhum bucket encontrado para essas credenciais.")
                bucket_input = _prompt_text("Bucket S3", default=default_bucket or None).strip()
            else:
                chosen = choose_from_list(
                    buckets,
                    title="Buckets:",
                    prompt="Digite o número do bucket",
                )
                if chosen is None:
                    print("Cancelado.")
                    return
                bucket_input = chosen

    if not bucket_input:
        print("Bucket é obrigatório.")
        return

    default_prefix = os.getenv("S3_PREFIX", "go/")
    prefix_input = _prompt_text("Pasta/prefixo no S3 (digite '?' para navegar)", default=default_prefix).strip()

    syncer = S3Syncer(bucket_name=bucket_input, s3_prefix="")

    if prefix_input == "?":
        selected = browse_s3_prefix(syncer, aws_profile=aws_profile, start_prefix="")
        if selected is None:
            print("Cancelado.")
            return
        prefix_input = selected or ""

    print("\nO que você quer sincronizar?")
    print("  [1] Informar um caminho (arquivo ou pasta)")
    print("  [2] Navegar e escolher (arquivo ou pasta)")
    source_choice = input("Escolha [1/2] (padrão 1): ").strip()

    local_default = os.getenv("S3_LOCAL_PATH", ".")
    if source_choice in {"", "1"}:
        local_input = _prompt_text("Caminho local (arquivo ou pasta)", default=local_default).strip()
    elif source_choice == "2":
        selected_path = browse_local(Path.cwd())
        if selected_path is None:
            print("Cancelado.")
            return
        local_input = str(selected_path)
    else:
        print("Opção inválida, informe um caminho.")
        local_input = _prompt_text("Caminho local (arquivo ou pasta)", default=local_default).strip()

    local_path = Path(local_input).expanduser()

    # Ajuste de prefixo: se for pasta local, incluir o nome da pasta no destino
    dest_prefix = prefix_input.strip("/")
    if local_path.is_dir():
        base = local_path.name
        parent_name = local_path.parent.name if local_path.parent else ""
        # Não inclui "lessons_output" como pasta de topo no S3; inclui subpastas
        if base != "lessons_output":
            if not dest_prefix.endswith(base):
                dest_prefix = f"{dest_prefix}/{base}" if dest_prefix else base
    syncer.s3_prefix = dest_prefix.rstrip("/") if dest_prefix else ""

    print("\n📋 Configuração do sync:")
    print(f"   Local:   {local_path}")
    print(f"   Bucket:  {bucket_input}")
    print(f"   Prefixo: {syncer.s3_prefix or '(raiz)'}")
    print(f"   Profile: {aws_profile or 'padrão'}")

    confirm = input("\nConfirmar e executar? (s/n): ").strip()
    if not _is_yes(confirm):
        print("Cancelado.")
        return

    try:
        if local_path.is_file():
            ok = syncer.copy_file(
                local_file=str(local_path),
                aws_profile=aws_profile
            )
        else:
            ok = syncer.sync_directory(
                local_dir=str(local_path),
                aws_profile=aws_profile
            )
    except S3SyncError as e:
        print(f"\n✗ S3 Sync Error: {e}")
        sys.exit(1)

    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
