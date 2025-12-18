import os
import subprocess
from typing import Optional, List, Tuple, Dict, Any

from app.core.logger import get_logger
from app.core.exceptions import VideoProcessingError

logger = get_logger(__name__)


class S3SyncError(VideoProcessingError):
    """Exception raised when S3 sync fails."""
    pass


class S3Syncer:
    """
    Service to sync lesson videos to AWS S3 using AWS CLI.
    """

    def __init__(self, bucket_name: str, s3_prefix: str = ""):
        """
        Initialize S3 syncer.

        Args:
            bucket_name: S3 bucket name
            s3_prefix: S3 prefix/folder path
        """
        self.bucket_name = bucket_name
        self.s3_prefix = s3_prefix.rstrip('/') if s3_prefix else ""

        # Validate AWS CLI is installed
        if not self._check_aws_cli():
            raise S3SyncError(
                "AWS CLI is not installed. Install it with:\n"
                "  Ubuntu/Debian: sudo apt install awscli\n"
                "  macOS: brew install awscli\n"
                "  Or follow: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
            )

    def _check_aws_cli(self) -> bool:
        """Check if AWS CLI is installed."""
        try:
            result = subprocess.run(
                ['aws', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_aws_credentials(self, aws_profile: Optional[str] = None) -> Tuple[bool, str]:
        """Check if AWS credentials are configured (optionally for a profile)."""
        try:
            cmd = ['aws', 'sts', 'get-caller-identity']
            if aws_profile:
                cmd.extend(['--profile', aws_profile])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, ""
            return False, (result.stderr or result.stdout or "").strip()
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            return False, str(exc)

    def _ensure_credentials(self, aws_profile: Optional[str] = None) -> None:
        ok, err = self._check_aws_credentials(aws_profile=aws_profile)
        if ok:
            return
        suffix = f" --profile {aws_profile}" if aws_profile else ""
        hint = f"Run: aws configure{suffix}" if not err else err
        if aws_profile:
            raise S3SyncError(
                f"AWS credentials not configured (ou inválidas) para o profile '{aws_profile}'.\n{hint}"
            )
        raise S3SyncError(
            f"AWS credentials not configured (ou inválidas).\n{hint}\n"
            "Ou defina AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN."
        )

    def _run_aws(
        self,
        args: List[str],
        aws_profile: Optional[str] = None,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        cmd = ['aws', *args]
        if aws_profile:
            cmd.extend(['--profile', aws_profile])
        return subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout
        )

    def sync_directory(
        self,
        local_dir: str,
        aws_profile: Optional[str] = None,
        dry_run: bool = False,
        delete: bool = False
    ) -> bool:
        """
        Sync a local directory to S3 using AWS CLI.

        Args:
            local_dir: Local directory path to sync
            aws_profile: AWS profile name ()
            dry_run: If True, only show what would be synced without uploading
            delete: If True, delete files in S3 that don't exist locally

        Returns:
            True if sync was successful, False otherwise

        Raises:
            S3SyncError: If sync fails
        """
        if not os.path.isdir(local_dir):
            raise S3SyncError(f"Directory not found: {local_dir}")

        self._ensure_credentials(aws_profile=aws_profile)

        # Build S3 URI
        if self.s3_prefix:
            s3_uri = f"s3://{self.bucket_name}/{self.s3_prefix}/"
        else:
            s3_uri = f"s3://{self.bucket_name}/"

        # Build command
        cmd = ['aws', 's3', 'sync', local_dir, s3_uri]

        # Add profile if specified
        if aws_profile:
            cmd.extend(['--profile', aws_profile])

        # Add options
        if dry_run:
            cmd.append('--dryrun')
        if delete:
            cmd.append('--delete')

        print(f"\n📤 Syncing to S3...")
        print(f"   Local:  {local_dir}")
        print(f"   S3:     {s3_uri}")
        if aws_profile:
            print(f"   Profile: {aws_profile}")
        if dry_run:
            print(f"   Mode:   DRY RUN (no files will be uploaded)")
        print()

        try:
            # Run sync command
            result = subprocess.run(
                cmd,
                cwd=local_dir,
                text=True,
                capture_output=False  # Show output in real-time
            )

            if result.returncode == 0:
                print(f"\n✓ Sync completed successfully!")
                logger.info(f"Synced {local_dir} to {s3_uri}")
                return True
            else:
                print(f"\n✗ Sync failed with exit code {result.returncode}")
                logger.error(f"Sync failed: {local_dir} -> {s3_uri}")
                return False

        except subprocess.TimeoutExpired:
            raise S3SyncError("Sync operation timed out")
        except Exception as e:
            raise S3SyncError(f"Sync failed: {e}")

    def copy_file(
        self,
        local_file: str,
        aws_profile: Optional[str] = None,
        s3_key: Optional[str] = None,
        dry_run: bool = False
    ) -> bool:
        """
        Copy a single file to S3 using AWS CLI (aws s3 cp).

        Args:
            local_file: Local file path
            aws_profile: AWS profile name
            s3_key: Optional destination key (defaults to prefix + filename)
            dry_run: If True, only show what would be uploaded
        """
        if not os.path.isfile(local_file):
            raise S3SyncError(f"File not found: {local_file}")

        self._ensure_credentials(aws_profile=aws_profile)

        filename = os.path.basename(local_file)
        if s3_key is None:
            if self.s3_prefix:
                s3_key = f"{self.s3_prefix}/{filename}"
            else:
                s3_key = filename

        s3_uri = f"s3://{self.bucket_name}/{s3_key.lstrip('/')}"

        cmd = ['aws', 's3', 'cp', local_file, s3_uri]
        if aws_profile:
            cmd.extend(['--profile', aws_profile])
        if dry_run:
            cmd.append('--dryrun')

        print(f"\n📤 Uploading to S3...")
        print(f"   Local:  {local_file}")
        print(f"   S3:     {s3_uri}")
        if aws_profile:
            print(f"   Profile: {aws_profile}")
        if dry_run:
            print(f"   Mode:   DRY RUN (no files will be uploaded)")
        print()

        try:
            result = subprocess.run(cmd, text=True, capture_output=False)
            if result.returncode == 0:
                print(f"\n✓ Upload completed successfully!")
                logger.info(f"Uploaded {local_file} to {s3_uri}")
                return True
            print(f"\n✗ Upload failed with exit code {result.returncode}")
            logger.error(f"Upload failed: {local_file} -> {s3_uri}")
            return False
        except Exception as e:
            raise S3SyncError(f"Upload failed: {e}")

    def list_buckets(self, aws_profile: Optional[str] = None) -> List[str]:
        """
        List bucket names using AWS CLI (aws s3api list-buckets).
        """
        self._ensure_credentials(aws_profile=aws_profile)
        result = self._run_aws(
            ['s3api', 'list-buckets', '--query', 'Buckets[].Name', '--output', 'text'],
            aws_profile=aws_profile,
            timeout=30
        )
        if result.returncode != 0:
            raise S3SyncError(result.stderr.strip() or "Failed to list buckets")
        # Output is tab-separated bucket names (or empty string)
        buckets = [b for b in result.stdout.strip().split() if b]
        return buckets

    def list_prefix_children(
        self,
        prefix: str = "",
        aws_profile: Optional[str] = None,
        max_keys: int = 200
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        List "folders" (CommonPrefixes) and objects directly under a prefix.

        Returns:
            (prefixes, objects) where prefixes are full prefix strings (ending in '/')
            and objects are dicts with at least Key/Size/LastModified when available.
        """
        self._ensure_credentials(aws_profile=aws_profile)

        normalized = prefix.lstrip('/')
        if normalized and not normalized.endswith('/'):
            normalized += '/'

        args = [
            's3api', 'list-objects-v2',
            '--bucket', self.bucket_name,
            '--delimiter', '/',
            '--max-keys', str(max_keys),
            '--output', 'json'
        ]
        if normalized:
            args.extend(['--prefix', normalized])

        result = self._run_aws(args, aws_profile=aws_profile, timeout=30)
        if result.returncode != 0:
            raise S3SyncError(result.stderr.strip() or "Failed to list S3 prefix")

        import json

        payload = json.loads(result.stdout or "{}")
        prefixes = [p['Prefix'] for p in payload.get('CommonPrefixes', []) if 'Prefix' in p]
        objects = payload.get('Contents', []) or []
        objects = [o for o in objects if o.get('Key') != normalized]
        return prefixes, objects

    def list_bucket_contents(
        self,
        aws_profile: Optional[str] = None
    ) -> None:
        """
        List contents of S3 bucket.

        Args:
            aws_profile: AWS profile name
        """
        # Build S3 URI
        if self.s3_prefix:
            s3_uri = f"s3://{self.bucket_name}/{self.s3_prefix}/"
        else:
            s3_uri = f"s3://{self.bucket_name}/"

        # Build command
        cmd = ['aws', 's3', 'ls', s3_uri, '--recursive', '--human-readable']

        if aws_profile:
            cmd.extend(['--profile', aws_profile])

        try:
            self._ensure_credentials(aws_profile=aws_profile)
            print(f"\n📋 Listing S3 contents: {s3_uri}\n")
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise S3SyncError(f"Failed to list bucket contents: {e}")
