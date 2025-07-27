#!/usr/bin/env python3
"""
Poe.com Conversation Manager - Main Launcher
Clean root-level entry point that delegates to organized scripts
"""

import os
import sys
import subprocess
import argparse

def main():
    """Main launcher with clean interface."""
    parser = argparse.ArgumentParser(
        description="Poe.com Conversation Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  setup          - Set up environment and install dependencies  
  gui            - Launch the GUI application
  launch         - Launch GUI with automatic database population
  test           - Run system tests and diagnostics
  test-unique    - Test database uniqueness constraints
  
Examples:
  python main.py setup              # First-time setup
  python main.py launch             # Recommended for daily use
  python main.py gui                # Launch GUI directly
  python main.py test               # Verify system health
        """
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'gui', 'launch', 'test', 'test-unique'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--limit', '-l', type=int, default=10,
        help='Number of conversations for launch command (default: 10)'
    )
    
    parser.add_argument(
        '--skip-populate', action='store_true',
        help='Skip database population for launch command'
    )
    
    parser.add_argument(
        '--force-populate', action='store_true', 
        help='Force database population even if data exists'
    )
    
    args = parser.parse_args()
    
    # Map commands to script paths
    script_map = {
        'setup': 'scripts/setup/create_environment.py',
        'gui': 'scripts/development/launch_gui.py', 
        'launch': 'scripts/development/launch_with_data.py',
        'test': 'scripts/testing/test_system.py',
        'test-unique': 'scripts/testing/test_uniqueness.py'
    }
    
    script_path = script_map[args.command]
    
    # Build command arguments
    cmd_args = [sys.executable, script_path]
    
    if args.command == 'launch':
        if args.skip_populate:
            cmd_args.append('--skip-populate')
        if args.force_populate:
            cmd_args.append('--force-populate')
        cmd_args.extend(['--limit', str(args.limit)])
    
    # Execute the appropriate script
    try:
        result = subprocess.run(cmd_args, cwd=os.path.dirname(__file__))
        return result.returncode
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Error running {args.command}: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())