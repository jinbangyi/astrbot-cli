# CLAUDE.md

## Project Overview

TODO: Add a brief project description here.

## Repository Structure

```
.
├── .ai/summaries/                              # AI-generated summaries (date-based: YY-MM-DD/)
│   └── 26-01-09/                               # summaries for Jan 9, 2026
├── .claude/                                    # Claude Code configuration (agents, commands, skills)
├── .devcontainer/                              # Development container runtime configuration
│   ├── .env.example                            # Example environment variables file
│   └── docker-compose.yaml                     # Docker Compose file for devcontainer
├── debug/                                      # Temporary debugging files ONLY
├── data/                                       # persistent data storage for the workspace
├── code-repo/                                  # Storage for cloned code repositories
│   └── github/                                 # Public GitHub repositories
│       ├── helloworld/                         # Example repository for AstrBot plugin development
│       └── AstrBot/                            # AstrBot repository cloned from GitHub
│           └── docs/en/                        # English documentation for AstrBot
├── docs/                                       # Project documentation
│   ├── AI-external-context/                    # External system context for AI agents
│   │   ├── local.md                            # Local running environment info, local env which can upload to git
│   │   └── dev.md                              # Development environment info(vercel,loki,database,hosting,ci/cd etc)
│   ├── blogs/                                  # Blog posts and articles (best practices, tutorials, solutions)
│   ├── development/                            # Date-based development plans (YY-MM-DD/)
│   │   ├── template/                           # Template for development notes
│   │   │   └── user.md                         # Template for user requirements/tasks
│   │   └── 26-01-09/                           # development notes for Jan 9, 2026
│   │       └── user.md                         # user requirements/tasks for the day
│   ├── requirements/                           # Requirements documentation, specs, and user stories
│   │   └── feature-xx/                         # Feature-specific requirements
│   ├── rules/                                  # Repository rules and guidelines
│   │   └── project.md                          # Project-specific rules and guidelines
│   ├── user-guide/                             # User guides and manuals
│   └── TODO.md                                 # Active TODO list (unfinished tasks only)
├── scripts/                                    # Repository scripts (to be implemented)
├── src/                                        # All source code (to be implemented)
├── .dockerignore                               # Docker ignore file
├── .env.local                                  # Local environment variables file (to be created by user)
├── .env.dev                                    # Development environment variables file (to be created by user)
├── .gitignore                                  # Git ignore file
├── CLAUDE.md                                   # Project overview and guidelines for AI agents
├── Dockerfile                                  # Dockerfile for containerizing the application
├── .env.example                                # Example environment variables file
├── main.py                                     # Main application entry point (to be implemented)
├── pyproject.toml                              # Python project configuration (to be implemented)
├── README.md                                   # Project README file (to be implemented)
└── uv.lock                                     # Python dependency lock file (to be implemented)
```

## Development Workflow

### Date-Based Organization

- Development notes: `docs/development/YY-MM-DD/`
- AI summaries: `.ai/summaries/YY-MM-DD/`
- Use this format for all new development work

### Context Sources (in priority order)

1. `docs/development/` - Current plans and architecture
2. `docs/TODO.md` - Pending work
3. `.ai/summaries/` - Past AI work and decisions
4. `docs/AI-external-context/` - External system context

### File Organization Rules

- All source code → `src/`
- All scripts → `scripts/`
- Temporary debugging → `debug/` (never commit this)
- Documentation → `docs/development/YY-MM-DD/`

## Important Notes

2. **Always check `docs/development/`** for current plans before implementing
3. **Date-based file organization** for all new documentation
4. **TODO.md is for unfinished tasks only** - remove completed items
