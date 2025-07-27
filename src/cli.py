#!/usr/bin/env python3
"""
Poe Search CLI - Command Line Interface for Phase 2
Provides search and analytics functionality for extracted conversations.
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from database import ConversationDatabase, Conversation
import logging

def setup_logging():
    """Set up logging for CLI operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    return logging.getLogger(__name__)

def format_conversation_summary(conv: Conversation, highlight_terms: List[str] = None) -> str:
    """Format a conversation for display in search results."""
    # Truncate title if too long
    title = conv.title[:60] + "..." if len(conv.title) > 60 else conv.title
    
    # Format dates
    created = conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "Unknown"
    
    # Bot info
    bot_info = f" [{conv.bot_name}]" if conv.bot_name and conv.bot_name != "Unknown" else ""
    
    # Message count
    msg_info = f" ({conv.message_count} messages)" if conv.message_count > 0 else ""
    
    return f"{conv.id:3d}. {title}{bot_info}{msg_info}\n     Created: {created} | URL: {conv.url[:50]}..."

def search_command(args, db: ConversationDatabase, logger):
    """Handle search command."""
    logger.info(f"🔍 Searching for: '{args.query}'")
    
    # Build filters
    filters = {}
    if args.bot:
        filters['bot_name'] = args.bot
    if args.start_date:
        filters['start_date'] = args.start_date
    if args.end_date:
        filters['end_date'] = args.end_date
    
    # Perform search
    results = db.search_conversations(args.query, filters)
    
    if not results:
        print("❌ No conversations found matching your criteria.")
        return
    
    # Display results
    print(f"\n✅ Found {len(results)} conversations:\n" + "="*70)
    
    for conv in results[:args.limit]:
        print(format_conversation_summary(conv))
        
        if args.show_content and conv.content:
            try:
                messages = json.loads(conv.content)
                print(f"     Preview: {messages[0]['content'][:100]}..." if messages else "")
            except:
                print(f"     Content: {conv.content[:100]}...")
        print()
    
    if len(results) > args.limit:
        print(f"... and {len(results) - args.limit} more results (use --limit to see more)")

def stats_command(args, db: ConversationDatabase, logger):
    """Handle stats command."""
    logger.info("📊 Generating statistics...")
    
    stats = db.get_stats()
    
    print("\n📊 Database Statistics")
    print("=" * 50)
    print(f"Total Conversations: {stats['total_conversations']}")
    print(f"Unique Bots: {stats['unique_bots']}")
    print(f"Total Messages: {stats['total_messages']}")
    print(f"Average Messages per Conversation: {stats['avg_messages_per_conversation']}")
    
    if stats['earliest_conversation']:
        print(f"Earliest Conversation: {stats['earliest_conversation']}")
    if stats['latest_activity']:
        print(f"Latest Activity: {stats['latest_activity']}")
    
    # Bot distribution
    if stats['bot_distribution']:
        print(f"\n🤖 Bot Distribution (Top 10):")
        sorted_bots = sorted(stats['bot_distribution'].items(), key=lambda x: x[1], reverse=True)
        for bot, count in sorted_bots[:10]:
            print(f"  {bot}: {count} conversations")

def export_command(args, db: ConversationDatabase, logger):
    """Handle export command."""
    logger.info(f"💾 Exporting to {args.format} format...")
    
    filename = db.export_conversations(args.format, args.output)
    print(f"✅ Exported to: {filename}")

def list_command(args, db: ConversationDatabase, logger):
    """Handle list command - show recent conversations."""
    logger.info("📋 Listing recent conversations...")
    
    # Get recent conversations
    results = db.search_conversations("", {})[:args.limit]
    
    if not results:
        print("❌ No conversations found in database.")
        return
    
    print(f"\n📋 Recent Conversations (showing {len(results)}):\n" + "="*70)
    
    for conv in results:
        print(format_conversation_summary(conv))

def main():
    parser = argparse.ArgumentParser(description="Poe Search CLI")
    parser.add_argument(
        "--database", "-d",
        default="conversations.db",
        help="SQLite database path"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search conversations")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--bot", help="Filter by bot name")
    search_parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    search_parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results to show")
    search_parser.add_argument("--show-content", action="store_true", help="Show content preview")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export conversations")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
    export_parser.add_argument("--output", help="Output filename")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent conversations")
    list_parser.add_argument("--limit", type=int, default=20, help="Number of conversations to show")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Set up logging
    logger = setup_logging()
    
    try:
        # Initialize database
        db = ConversationDatabase(args.database)
        
        # Execute command
        if args.command == "search":
            search_command(args, db, logger)
        elif args.command == "stats":
            stats_command(args, db, logger)
        elif args.command == "export":
            export_command(args, db, logger)
        elif args.command == "list":
            list_command(args, db, logger)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()