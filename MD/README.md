# Lead Generation System - Documentation Archive

**Дата создания:** 20.11.2025 00:49


This folder contains all project documentation organized by version.

## Version Structure

### 📁 v0.1 - Planning & Architecture
Initial project setup, architecture design, and technical decisions.
- Architecture & Design
- Database Schema
- API Documentation
- Technology Stack

### 📁 v0.2 - Implementation
Core module implementation and platform parsers.
- Competitor Parser
- Platform Modules (OLX, SATU)
- Implementation Reports
- Module Guides

### 📁 v0.3 - Current (Guides & Operations)
Current operational guides, deployment instructions, and status reports.
- Quick Start Guides
- Deployment Guides
- Status Reports
- Analysis & Planning

## Versioning Rules

**Important:** All new `.md` files (except README.md in project root) should be placed in the appropriate version folder:

1. **Planning documents** → `MD/v0.X/` (where X is the planning version)
2. **Implementation reports** → `MD/v0.X/` (where X is the implementation version)
3. **Guides & instructions** → `MD/v0.X/` (current version)

### Current Version: v0.3

All new documentation should go to `MD/v0.3/` unless it's related to future planning (v0.4+).

## Quick Navigation

- 🏠 [Project Root README](../README.md) - Main project documentation
- 📖 [v0.1 Docs](./v0.1/README.md) - Architecture & Planning
- 🔧 [v0.2 Docs](./v0.2/README.md) - Implementation
- 🚀 [v0.3 Docs](./v0.3/README.md) - Current Guides (Start here!)

## File Naming Convention

Use descriptive UPPERCASE names with underscores:
- ✅ `FEATURE_IMPLEMENTATION_GUIDE.md`
- ✅ `PLATFORM_COMPARISON_REPORT.md`
- ✅ `DEPLOYMENT_CHECKLIST.md`
- ❌ `guide.md`
- ❌ `notes.md`

## Version Upgrade

When creating a new version (e.g., v0.4):

```bash
mkdir -p MD/v0.4
# Create README.md describing the version focus
# Update this file with v0.4 information
# Update .cursorrules with new version
```

---

**Last Updated:** v0.3
**Maintained by:** Nikolai & AI Assistant

