#!/bin/bash
# Script to create a new release tag
# Usage: ./scripts/create-release.sh <version> [message]
# Example: ./scripts/create-release.sh 1.2.0 "Add new features"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if version is provided
if [ -z "$1" ]; then
  echo -e "${RED}Error: Version number required${NC}"
  echo "Usage: $0 <version> [message]"
  echo "Example: $0 1.2.0 'Add new features'"
  exit 1
fi

VERSION=$1
MESSAGE=${2:-"Release version $VERSION"}

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo -e "${RED}Error: Invalid version format${NC}"
  echo "Version must follow semantic versioning: MAJOR.MINOR.PATCH"
  echo "Example: 1.2.0"
  exit 1
fi

# Check if tag already exists
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
  echo -e "${RED}Error: Tag v$VERSION already exists${NC}"
  exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
  echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
  read -p "Do you want to continue? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Get current branch
BRANCH=$(git branch --show-current)

echo -e "${GREEN}Creating release v$VERSION${NC}"
echo "Branch: $BRANCH"
echo "Message: $MESSAGE"
echo

# Confirm
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  exit 1
fi

# Update version in pyproject.toml
echo -e "${YELLOW}Updating version in pyproject.toml...${NC}"
sed -i "s/^version = .*/version = \"$VERSION\"/" pyproject.toml

# Update version in config.py
echo -e "${YELLOW}Updating version in src/config.py...${NC}"
sed -i "s/version: str = .*/version: str = \"$VERSION\"/" src/config.py

# Commit version bump
git add pyproject.toml src/config.py
git commit -m "chore: bump version to $VERSION" || echo "No changes to commit"

# Create annotated tag
echo -e "${YELLOW}Creating tag v$VERSION...${NC}"
git tag -a "v$VERSION" -m "$MESSAGE"

echo -e "${GREEN}✓ Tag v$VERSION created successfully${NC}"
echo
echo "Next steps:"
echo "1. Review the tag: git show v$VERSION"
echo "2. Push the tag: git push origin v$VERSION"
echo "3. GitHub Actions will automatically:"
echo "   - Create a GitHub Release"
echo "   - Build and deploy backend to Cloud Run"
echo "   - Tag Docker image with version"
echo
echo -e "${YELLOW}To push now, run:${NC}"
echo "git push origin $BRANCH && git push origin v$VERSION"
