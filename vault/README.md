# aclarai Vault Directory

This directory serves as the default vault for Obsidian-style Markdown files that aclarai processes.

## Using Your Own Obsidian Vault

**For development and personal use, you'll want to use your own Obsidian vault instead of this directory.**

### Option 1: Symbolic Link (Recommended for development)
Create a symbolic link from this directory to your actual Obsidian vault:

```bash
# Remove the default vault directory
rm -rf vault

# Create a symbolic link to your Obsidian vault
ln -s /path/to/your/obsidian/vault vault
```

### Option 2: Modify Docker Compose Volume Mount
Edit the `docker-compose.yml` file to mount your Obsidian vault directly:

```yaml
volumes:
  - /path/to/your/obsidian/vault:/vault  # Replace with your vault path
```

### Option 3: Environment Variable Configuration
Set the `VAULT_PATH` environment variable in your `.env` file to point to your Obsidian vault, and update the docker-compose.yml volume mount accordingly.

## Structure

- This directory is mounted as `/vault` in the Docker containers
- Files placed here will be watched by the `vault-watcher` service
- The `aclarai-core` service processes files from this directory
- The `scheduler` service performs periodic maintenance on this directory

## Usage

1. Configure your vault path using one of the methods above
2. Place your Markdown files in the configured vault directory
3. The `vault-watcher` service will detect changes and emit dirty block IDs
4. The `aclarai-core` service will process the files for claim extraction, summarization, and concept linking
5. The `scheduler` service will run periodic jobs for concept hygiene and vault sync

## Important Notes

- Ensure your vault directory is readable and writable by the Docker containers
- Files are processed atomically using `.tmp` → `rename` operations
- The system uses `aclarai:id` and `ver=` markers to track file versions
- If using a symbolic link, ensure Docker has access to follow symlinks
- For production deployments, consider using proper volume mounts instead of symbolic links