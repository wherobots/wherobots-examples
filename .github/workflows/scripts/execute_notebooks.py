#!/usr/bin/env python3
"""
Notebook Executor for Wherobots Cloud

This script runs inside Wherobots Cloud via the Runs API.
It executes Jupyter notebooks using papermill and saves the executed
notebooks (with outputs) back to S3.

Usage:
    python execute_notebooks.py \
        --s3-input-prefix s3://bucket/notebooks/input/ \
        --s3-output-prefix s3://bucket/notebooks/output/ \
        --timeout 900

Requirements (installed via Runs API dependencies):
    - papermill>=2.6.0
    - boto3 (pre-installed in Wherobots)
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import boto3
import papermill as pm

# NOTE: This script assumes it is running within Wherobots Cloud via the Runs API.
# In Wherobots Cloud, access to Managed Storage (S3) is automatic via IAM roles
# assigned to the runtime environment. No explicit AWS keys are needed here.


def parse_s3_path(s3_path: str) -> tuple:
    """Parse an S3 path into bucket and key.

    Args:
        s3_path: S3 URI in format s3://bucket/key/path

    Returns:
        Tuple of (bucket, key)
    """
    parsed = urlparse(s3_path)
    if parsed.scheme != "s3":
        raise ValueError(f"Invalid S3 path: {s3_path}")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return bucket, key


def list_s3_notebooks(s3_client, bucket: str, prefix: str) -> list:
    """List all .ipynb files under an S3 prefix.

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        prefix: S3 key prefix to search under

    Returns:
        List of S3 keys for notebook files
    """
    notebooks = []
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".ipynb"):
                # Exclude Raster_Inference notebooks
                filename = os.path.basename(key)
                if not filename.startswith("Raster_Inference"):
                    notebooks.append(key)

    return sorted(notebooks)


def download_notebook(
    s3_client, bucket: str, key: str, local_dir: Path, input_prefix: str
) -> Path:
    """Download a notebook from S3 to local directory, preserving structure.

    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        key: S3 key of the notebook
        local_dir: Local directory to download to
        input_prefix: The S3 prefix to strip for relative path calculation

    Returns:
        Path to the downloaded local file
    """
    # Calculate relative path from the input prefix
    relative_path = key[len(input_prefix) :].lstrip("/")
    local_path = local_dir / relative_path
    local_path.parent.mkdir(parents=True, exist_ok=True)

    s3_client.download_file(bucket, key, str(local_path))
    return local_path


def upload_notebook(
    s3_client, local_path: Path, bucket: str, output_prefix: str, relative_path: str
) -> str:
    """Upload an executed notebook to S3.

    Args:
        s3_client: Boto3 S3 client
        local_path: Path to local notebook file
        bucket: S3 bucket name
        output_prefix: S3 prefix for output
        relative_path: Relative path to preserve in S3

    Returns:
        The S3 key where the file was uploaded
    """
    output_key = output_prefix.rstrip("/") + "/" + relative_path.lstrip("/")
    s3_client.upload_file(str(local_path), bucket, output_key)
    return output_key


def execute_notebook(input_path: Path, output_path: Path, timeout: int) -> dict:
    """Execute a notebook using papermill.

    Args:
        input_path: Path to input notebook
        output_path: Path to save executed notebook
        timeout: Execution timeout in seconds

    Returns:
        Dict with execution results including status and any errors
    """
    result = {
        "input": str(input_path),
        "output": str(output_path),
        "status": "pending",
        "error": None,
        "start_time": datetime.utcnow().isoformat(),
        "end_time": None,
    }

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Execute notebook with papermill
        pm.execute_notebook(
            str(input_path),
            str(output_path),
            kernel_name="python3",
            progress_bar=False,
            request_save_on_cell_execute=True,
            execution_timeout=timeout,
        )

        result["status"] = "success"

    except pm.PapermillExecutionError as e:
        # Notebook executed but a cell failed
        # The output notebook still contains partial outputs up to the failure
        result["status"] = "cell_error"
        result["error"] = f"Cell execution error: {e.ename}: {e.evalue}"
        print(f"  Cell error in {input_path.name}: {e.ename}")

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        print(f"  Failed to execute {input_path.name}: {e}")
        traceback.print_exc()

        # If execution failed completely, copy input as output
        # so the conversion pipeline still has the notebook (without outputs)
        if not output_path.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(input_path, output_path)

    result["end_time"] = datetime.utcnow().isoformat()
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Execute Jupyter notebooks in Wherobots Cloud"
    )
    parser.add_argument(
        "--s3-input-prefix",
        required=True,
        help="S3 prefix containing input notebooks (e.g., s3://bucket/input/)",
    )
    parser.add_argument(
        "--s3-output-prefix",
        required=True,
        help="S3 prefix for output notebooks (e.g., s3://bucket/output/)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Timeout per notebook in seconds (default: 900 = 15 minutes)",
    )
    parser.add_argument(
        "--manifest-key",
        default="manifest.json",
        help="S3 key suffix for execution manifest (default: manifest.json)",
    )

    args = parser.parse_args()

    # Parse S3 paths
    input_bucket, input_prefix = parse_s3_path(args.s3_input_prefix)
    output_bucket, output_prefix = parse_s3_path(args.s3_output_prefix)

    # Initialize S3 client
    s3 = boto3.client("s3")

    # Create temp directories
    work_dir = Path(tempfile.mkdtemp(prefix="notebook_exec_"))
    input_dir = work_dir / "input"
    output_dir = work_dir / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    print("=" * 60)
    print("WHEROBOTS NOTEBOOK EXECUTOR")
    print("=" * 60)
    print(f"Working directory: {work_dir}")
    print(f"Input: s3://{input_bucket}/{input_prefix}")
    print(f"Output: s3://{output_bucket}/{output_prefix}")
    print(f"Timeout per notebook: {args.timeout}s")
    print()

    # List notebooks
    notebook_keys = list_s3_notebooks(s3, input_bucket, input_prefix)
    print(f"Found {len(notebook_keys)} notebooks to execute")
    print()

    if len(notebook_keys) == 0:
        print("WARNING: No notebooks found. Check the S3 input prefix.")
        # Write empty manifest
        manifest = {
            "start_time": datetime.utcnow().isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total": 0,
            "success": 0,
            "cell_error": 0,
            "failed": 0,
            "notebooks": [],
        }
        manifest_path = work_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        manifest_key = output_prefix.rstrip("/") + "/" + args.manifest_key
        s3.upload_file(str(manifest_path), output_bucket, manifest_key)
        print(f"Empty manifest uploaded: s3://{output_bucket}/{manifest_key}")
        return

    # Track results
    manifest = {
        "start_time": datetime.utcnow().isoformat(),
        "end_time": None,
        "total": len(notebook_keys),
        "success": 0,
        "cell_error": 0,
        "failed": 0,
        "notebooks": [],
    }

    # Process each notebook
    for i, key in enumerate(notebook_keys, 1):
        filename = os.path.basename(key)
        relative_path = key[len(input_prefix) :].lstrip("/")

        print(f"[{i}/{len(notebook_keys)}] Processing: {relative_path}")

        # Download
        local_input = download_notebook(s3, input_bucket, key, input_dir, input_prefix)
        print(f"  Downloaded to: {local_input}")

        # Compute output path (same relative structure)
        local_output = output_dir / relative_path

        # Execute
        print(f"  Executing...")
        result = execute_notebook(local_input, local_output, args.timeout)

        # Upload if output exists
        if local_output.exists():
            output_key = upload_notebook(
                s3, local_output, output_bucket, output_prefix, relative_path
            )
            result["s3_output"] = f"s3://{output_bucket}/{output_key}"
            print(f"  Uploaded: {output_key}")
        else:
            print(f"  WARNING: No output file generated")

        # Update manifest
        manifest["notebooks"].append(
            {"name": filename, "relative_path": relative_path, "s3_key": key, **result}
        )

        if result["status"] == "success":
            manifest["success"] += 1
            print(f"  Status: SUCCESS")
        elif result["status"] == "cell_error":
            manifest["cell_error"] += 1
            print(f"  Status: CELL_ERROR (partial outputs saved)")
        else:
            manifest["failed"] += 1
            print(f"  Status: FAILED")

        print()

    # Finalize manifest
    manifest["end_time"] = datetime.utcnow().isoformat()

    # Upload manifest
    manifest_path = work_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    manifest_key = output_prefix.rstrip("/") + "/" + args.manifest_key
    s3.upload_file(str(manifest_path), output_bucket, manifest_key)
    print(f"Manifest uploaded: s3://{output_bucket}/{manifest_key}")

    # Summary
    print()
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total notebooks:  {manifest['total']}")
    print(f"  Success:        {manifest['success']}")
    print(f"  Cell error:     {manifest['cell_error']} (partial outputs saved)")
    print(f"  Failed:         {manifest['failed']}")
    print()

    # Calculate duration
    start = datetime.fromisoformat(manifest["start_time"])
    end = datetime.fromisoformat(manifest["end_time"])
    duration = end - start
    print(f"Total duration: {duration}")
    print()

    # Exit with error only if ALL notebooks failed
    if (
        manifest["success"] == 0
        and manifest["cell_error"] == 0
        and manifest["total"] > 0
    ):
        print("ERROR: All notebooks failed to execute")
        sys.exit(1)

    print("Execution complete!")


if __name__ == "__main__":
    main()
