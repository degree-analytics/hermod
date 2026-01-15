# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-11-17

### Added
- Initial stable release of hermod as standalone CLI
- `collect` command for AI usage data collection from ccusage/ccusage-codex
- `submit` command for triggering GitHub Actions ingestion workflow
- Auto-detection of developer name from git
- Comprehensive test suite with 80%+ coverage
- GitHub Actions CI/CD pipeline
- Automated publishing to AWS CodeArtifact

### Breaking Changes
- Extracted from heimdall as standalone package
- New installation method via CodeArtifact (see README)
