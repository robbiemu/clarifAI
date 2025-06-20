#!/usr/bin/env python3
"""
Command-line utility for installing default configuration files.
This script can be used during Docker builds or manual installation to ensure
default configuration files are available for user customization.
"""

import argparse
import sys

# Import the config installer from the installed aclarai_shared package
# This assumes the workspace is set up correctly with `pip install -e shared/`
try:
    from aclarai_shared.utils.config_installer import install_default_config
except ImportError as e:
    print(f"Error: Could not import aclarai_shared package: {e}", file=sys.stderr)
    print("Make sure you have installed the shared package with:", file=sys.stderr)
    print("  pip install -e shared/", file=sys.stderr)
    sys.exit(1)


def main():
    """Main entry point for the configuration installer."""
    parser = argparse.ArgumentParser(
        description="Install or restore aclarai configuration files"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration file with defaults",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()
    try:
        success = install_default_config(force=args.force)
        if success:
            print("✅ Configuration installation complete!")
            if args.force:
                print("Your configuration has been restored to defaults.")
            else:
                print("You can now customize settings/aclarai.config.yaml as needed.")
        else:
            print("❌ Configuration installation failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
