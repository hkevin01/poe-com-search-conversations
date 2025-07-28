#!/bin/bash

# Verification script to check if agent settings were applied correctly
# Usage: ./verify-agent-settings.sh ~/Projects

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

BASE_DIR="${1:-$HOME/Projects}"

if [ ! -d "$BASE_DIR" ]; then
    echo -e "${RED}❌ Directory $BASE_DIR not found${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Verifying agent settings in: $BASE_DIR${NC}"
echo ""

# Track statistics
total_projects=0
projects_with_vscode=0
projects_with_settings=0
projects_with_auto_approve=0
projects_with_max_requests=0

# Function to check a project directory
check_project() {
    local dir="$1"
    local project_name=$(basename "$dir")
    
    # Skip hidden directories
    if [[ "$project_name" == .* ]]; then
        return
    fi
    
    # Only check directories that look like projects
    if [ ! -d "$dir" ]; then
        return
    fi
    
    total_projects=$((total_projects + 1))
    
    echo -e "${BLUE}📁 Checking: ${project_name}${NC}"
    
    # Check if .vscode folder exists
    if [ -d "$dir/.vscode" ]; then
        projects_with_vscode=$((projects_with_vscode + 1))
        echo -e "  ${GREEN}✓${NC} .vscode folder exists"
        
        # Check if settings.json exists
        if [ -f "$dir/.vscode/settings.json" ]; then
            projects_with_settings=$((projects_with_settings + 1))
            echo -e "  ${GREEN}✓${NC} settings.json exists"
            
            # Check for autoApprove setting
            if grep -q '"chat.tools.autoApprove"' "$dir/.vscode/settings.json"; then
                auto_approve_value=$(grep '"chat.tools.autoApprove"' "$dir/.vscode/settings.json" | sed 's/.*: *\([^,}]*\).*/\1/' | tr -d ' ')
                if [[ "$auto_approve_value" == "true" ]]; then
                    projects_with_auto_approve=$((projects_with_auto_approve + 1))
                    echo -e "  ${GREEN}✓${NC} chat.tools.autoApprove: true"
                else
                    echo -e "  ${YELLOW}⚠${NC} chat.tools.autoApprove: $auto_approve_value (expected: true)"
                fi
            else
                echo -e "  ${RED}✗${NC} chat.tools.autoApprove: not found"
            fi
            
            # Check for maxRequests setting
            if grep -q '"chat.agent.maxRequests"' "$dir/.vscode/settings.json"; then
                max_requests_value=$(grep '"chat.agent.maxRequests"' "$dir/.vscode/settings.json" | sed 's/.*: *\([^,}]*\).*/\1/' | tr -d ' ')
                if [[ "$max_requests_value" == "100" ]]; then
                    projects_with_max_requests=$((projects_with_max_requests + 1))
                    echo -e "  ${GREEN}✓${NC} chat.agent.maxRequests: 100"
                else
                    echo -e "  ${YELLOW}⚠${NC} chat.agent.maxRequests: $max_requests_value (expected: 100)"
                fi
            else
                echo -e "  ${RED}✗${NC} chat.agent.maxRequests: not found"
            fi
            
        else
            echo -e "  ${RED}✗${NC} settings.json not found"
        fi
    else
        echo -e "  ${RED}✗${NC} .vscode folder not found"
    fi
    
    echo ""
}

# Process all directories in the base directory
for dir in "$BASE_DIR"/*; do
    check_project "$dir"
done

# Show summary
echo -e "${BLUE}📊 SUMMARY:${NC}"
echo -e "Total projects checked: $total_projects"
echo -e "${GREEN}Projects with .vscode folder: $projects_with_vscode${NC}"
echo -e "${GREEN}Projects with settings.json: $projects_with_settings${NC}"
echo -e "${GREEN}Projects with autoApprove=true: $projects_with_auto_approve${NC}"
echo -e "${GREEN}Projects with maxRequests=100: $projects_with_max_requests${NC}"

if [ $projects_with_auto_approve -eq $total_projects ] && [ $projects_with_max_requests -eq $total_projects ]; then
    echo -e "\n${GREEN}🎉 All projects are properly configured for agent mode!${NC}"
elif [ $projects_with_vscode -gt 0 ]; then
    echo -e "\n${YELLOW}⚠ Some projects may need configuration updates${NC}"
else
    echo -e "\n${RED}❌ No VS Code configurations found - script may not have run correctly${NC}"
fi
