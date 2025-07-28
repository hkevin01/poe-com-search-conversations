#!/bin/bash

# Quick Agent Settings Fixer
# Targets all projects and ensures they have the required agent settings

TARGET_DIR="${1:-$HOME/Projects}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Quick Agent Settings Fixer${NC}"
echo -e "${BLUE}=============================${NC}"
echo -e "Target: ${YELLOW}$TARGET_DIR${NC}"
echo ""

# Counters
TOTAL=0
FIXED=0
CREATED=0
SKIPPED=0

# Agent settings to add
SETTINGS_JSON='{
    "chat.tools.autoApprove": true,
    "chat.agent.maxRequests": 100
}'

# Process each directory
for dir in "$TARGET_DIR"/*; do
    if [ ! -d "$dir" ]; then continue; fi
    
    project=$(basename "$dir")
    
    # Skip hidden directories
    if [[ "$project" == .* ]]; then continue; fi
    
    TOTAL=$((TOTAL + 1))
    echo -n "📁 $project: "
    
    vscode_dir="$dir/.vscode"
    settings_file="$vscode_dir/settings.json"
    
    # Create .vscode if needed
    [ ! -d "$vscode_dir" ] && mkdir -p "$vscode_dir"
    
    # Check if agent settings exist
    if [ -f "$settings_file" ] && grep -q "chat.tools.autoApprove" "$settings_file" 2>/dev/null && grep -q "chat.agent.maxRequests" "$settings_file" 2>/dev/null; then
        echo -e "${GREEN}OK${NC}"
        SKIPPED=$((SKIPPED + 1))
    else
        # Need to add/fix settings
        if [ ! -f "$settings_file" ]; then
            # Create new settings file
            echo "$SETTINGS_JSON" > "$settings_file"
            echo -e "${GREEN}CREATED${NC}"
            CREATED=$((CREATED + 1))
        else
            # Merge with existing
            cp "$settings_file" "$settings_file.bak" 2>/dev/null
            
            # Try jq merge first
            if command -v jq >/dev/null 2>&1 && jq empty "$settings_file" 2>/dev/null; then
                jq '. + {"chat.tools.autoApprove": true, "chat.agent.maxRequests": 100}' "$settings_file" > "${settings_file}.tmp" && mv "${settings_file}.tmp" "$settings_file"
                echo -e "${GREEN}MERGED${NC}"
            else
                # Simple replacement for broken JSON
                echo "$SETTINGS_JSON" > "$settings_file"
                echo -e "${YELLOW}REPLACED${NC}"
            fi
            FIXED=$((FIXED + 1))
        fi
    fi
done

echo ""
echo -e "${BLUE}📊 Results:${NC}"
echo -e "Total projects: $TOTAL"
echo -e "${GREEN}Settings created: $CREATED${NC}"
echo -e "${GREEN}Settings fixed: $FIXED${NC}"
echo -e "${YELLOW}Already OK: $SKIPPED${NC}"
echo ""
echo -e "${GREEN}🎉 Done! $(($CREATED + $FIXED)) projects updated${NC}"
