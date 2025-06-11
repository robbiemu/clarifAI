#!/usr/bin/env python3
"""
Command-line utility for installing default prompt templates.

This script can be used during Docker builds or manual installation to ensure
default prompt files are available for user customization.
"""

import argparse
import importlib.util
import sys
from pathlib import Path

# Add the shared package to the path
shared_dir = Path(__file__).parent.parent.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

# Get the path to the prompt_installer module
installer_path = shared_dir / "clarifai_shared" / "utils" / "prompt_installer.py"
spec = importlib.util.spec_from_file_location("prompt_installer", installer_path)
prompt_installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompt_installer)

install_all_default_prompts = prompt_installer.install_all_default_prompts
install_default_prompt = prompt_installer.install_default_prompt


def main():
    parser = argparse.ArgumentParser(
        description="Install default prompt templates for ClarifAI"
    )
    parser.add_argument(
        "--template",
        help="Specific template to install (without .yaml extension)",
        default=None,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing prompt files",
    )
    parser.add_argument(
        "--prompts-dir",
        type=Path,
        default=None,
        help="Target directory for prompts (defaults to ./prompts/)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Install all available default prompts",
    )

    args = parser.parse_args()

    try:
        if args.all:
            count = install_all_default_prompts(
                force=args.force, prompts_dir=args.prompts_dir
            )
            print(f"Installed {count} default prompt templates")
        elif args.template:
            success = install_default_prompt(
                template_name=args.template,
                force=args.force,
                prompts_dir=args.prompts_dir,
            )
            if success:
                print(f"Installed prompt template: {args.template}")
            else:
                print(f"Prompt template already exists: {args.template}")
        else:
            # Default: install conversation_extraction template
            success = install_default_prompt(
                template_name="conversation_extraction",
                force=args.force,
                prompts_dir=args.prompts_dir,
            )
            if success:
                print("Installed default conversation_extraction prompt")
            else:
                print("Conversation extraction prompt already exists")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
