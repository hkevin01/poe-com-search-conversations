#!/bin/bash

# VS Code Agent Settings Installer - Robust Version
# Adds chat.tools.autoApprove and chat.agent.maxRequests settings to all project folders

# Default target directory (current directory if not specified)
TARGET_DIR="${1:-.}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 VS Code Agent Settings Installer (Robust Version)${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "Target directory: ${YELLOW}$(realpath "$TARGET_DIR")${NC}"
echo ""

# Settings to add
AGENT_SETTINGS='{
    "chat.tools.autoApprove": true,
    "chat.agent.maxRequests": 100
}'

# Counter variables
PROCESSED=0
CREATED=0
UPDATED=0
SKIPPED=0
ERRORS=0

# Function to safely merge JSON settings
merge_json_settings() {
    local existing_file="$1"
    local output_file="$2"
    
    # Try jq first (if available)
    if command -v jq &> /dev/null; then
        if jq '. + {"chat.tools.autoApprove": true, "chat.agent.maxRequests": 100}' "$existing_file" > "$output_file" 2>/dev/null; then
            return 0
        fi
    fi
    
    # Fallback: manual JSON merging
    echo "Attempting manual JSON merge..."
    
    # Read existing content and remove closing brace
    local content=$(sed '$ s/}$//' "$existing_file" | sed '/^[[:space:]]*$/d')
    
    # Check if we need a comma
    local needs_comma=""
    if [[ "$content" =~ [^[:space:]\{] ]]; then
        needs_comma=","
    fi
    
    # Create merged content
    {
        echo "$content$needs_comma"
        echo '    "chat.tools.autoApprove": true,'
        echo '    "chat.agent.maxRequests": 100'
        echo '}'
    } > "$output_file"
    
    return 0
}

# Function to process a single directory
process_directory() {
    local dir="$1"
    local project_name=$(basename "$dir")
    
    echo -e "${BLUE}📁 Processing: ${project_name}${NC}"
    
    # Skip if not a directory
    if [ ! -d "$dir" ]; then
        echo -e "  ${YELLOW}⚠️  Skipping: Not a directory${NC}"
        ((SKIPPED++))
        return
    fi
    
    # Skip hidden directories (like .git, .vscode, etc.)
    if [[ "$project_name" == .* ]]; then
        echo -e "  ${YELLOW}⚠️  Skipping: Hidden directory${NC}"
        ((SKIPPED++))
        return
    fi
    
    local vscode_dir="$dir/.vscode"
    local settings_file="$vscode_dir/settings.json"
    
    # Create .vscode directory if it doesn't exist
    if [ ! -d "$vscode_dir" ]; then
        echo -e "  ${GREEN}📂 Creating .vscode directory${NC}"
        if mkdir -p "$vscode_dir" 2>/dev/null; then
            ((CREATED++))
        else
            echo -e "  ${RED}❌ Failed to create .vscode directory${NC}"
            ((ERRORS++))
            return
        fi
    fi
    
    # Handle settings.json file
    if [ ! -f "$settings_file" ]; then
        # Create new settings.json
        echo -e "  ${GREEN}📄 Creating new settings.json${NC}"
        if echo "$AGENT_SETTINGS" > "$settings_file" 2>/dev/null; then
            echo -e "  ${GREEN}✅ Added agent settings${NC}"
            ((UPDATED++))
        else
            echo -e "  ${RED}❌ Failed to create settings.json${NC}"
            ((ERRORS++))
        fi
    else
        # Check if settings already exist
        if grep -q "chat.tools.autoApprove" "$settings_file" 2>/dev/null && grep -q "chat.agent.maxRequests" "$settings_file" 2>/dev/null; then
            echo -e "  ${YELLOW}⚠️  Agent settings already exist - skipping${NC}"
            ((SKIPPED++))
        else
            # Backup existing file
            if cp "$settings_file" "$settings_file.backup" 2>/dev/null; then
                echo -e "  ${BLUE}💾 Created backup: settings.json.backup${NC}"
                
                # Try to merge settings
                echo -e "  ${GREEN}🔄 Merging agent settings with existing settings${NC}"
                
                # Create temporary file
                temp_file=$(mktemp)
                
                if merge_json_settings "$settings_file" "$temp_file"; then
                    if mv "$temp_file" "$settings_file" 2>/dev/null; then
                        echo -e "  ${GREEN}✅ Successfully merged settings${NC}"
                        ((UPDATED++))
                    else
                        echo -e "  ${RED}❌ Failed to save merged settings${NC}"
                        ((ERRORS++))
                        rm -f "$temp_file"
                    fi
                else
                    echo -e "  ${RED}❌ Failed to merge settings - creating fresh file${NC}"
                    echo "$AGENT_SETTINGS" > "$settings_file"
                    echo -e "  ${YELLOW}⚠️  Original settings backed up${NC}"
                    ((UPDATED++))
                    rm -f "$temp_file"
                fi
            else
                echo -e "  ${RED}❌ Failed to create backup${NC}"
                ((ERRORS++))
            fi
        fi
    fi
    
    ((PROCESSED++))
    echo ""
}

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}❌ Error: Directory '$TARGET_DIR' does not exist${NC}"
    exit 1
fi

# Process all subdirectories
echo -e "${BLUE}🔍 Scanning for project directories...${NC}"
echo ""

# Process directories one by one (more reliable than find with while loop)
for dir in "$TARGET_DIR"/*; do
    if [ -d "$dir" ]; then
        process_directory "$dir"
    fi
done

# Summary
echo -e "${BLUE}📊 SUMMARY${NC}"
echo -e "${BLUE}==========${NC}"
echo -e "📁 Directories processed: ${GREEN}$PROCESSED${NC}"
echo -e "📂 .vscode folders created: ${GREEN}$CREATED${NC}"
echo -e "🔄 Settings files updated: ${GREEN}$UPDATED${NC}"
echo -e "⚠️  Directories skipped: ${YELLOW}$SKIPPED${NC}"
echo -e "❌ Errors encountered: ${RED}$ERRORS${NC}"
echo ""

if [ $PROCESSED -gt 0 ]; then
    echo -e "${GREEN}🎉 VS Code agent settings installation complete!${NC}"
    echo -e "${BLUE}💡 Settings added/updated:${NC}"
    echo -e "   • ${GREEN}chat.tools.autoApprove: true${NC}"
    echo -e "   • ${GREEN}chat.agent.maxRequests: 100${NC}"
    echo ""
    echo -e "${BLUE}📈 Success Rate: ${GREEN}$(( (UPDATED + CREATED) * 100 / PROCESSED ))%${NC}"
else
    echo -e "${YELLOW}⚠️  No directories were processed${NC}"
fi

echo ""
echo -e "${BLUE}🚀 Your projects are now ready for enhanced AI agent workflows!${NC}"

if [ $ERRORS -gt 0 ]; then
    echo -e "${YELLOW}💡 Some projects had errors - you may want to check them manually${NC}"
fi
