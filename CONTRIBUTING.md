
## 1. Repository Structure
### Backend (Python)
- `models/` → data models only
- `features/` → feature-based logic (ACO, carbon, realtime, etc.)
- `api/` → API routes & request/response schemas
- `utils/` → shared utilities

### Frontend (Flutter)
- `models/` → frontend data models
- `features/` → feature-based UI pages
- `services/` → backend API calls
- `widgets/` → reusable UI components

---

## 2. Branching Strategy

### Main branches
- `main`
  - Stable, runnable version only
  - **No direct commits**
- `dev`
  - Active integration branch

### Feature branches
Create branches from `dev`:

- Naming format: `feature/<feature-name>`

Examples:
- `feature/task-assignment`
- `feature/aco-optimization`
- `feature/carbon-model`
- `feature/realtime-dispatch`
- `feature/frontend-map`

---

## 3. Commit Message Convention

Use clear, descriptive commit messages:

- Format: `<type>: <short description>`

Types:
- `feat`: new feature
- `fix`: bug fix
- `refactor`: refactor (no behavior change)
- `docs`: documentation only
- `test`: tests only
- `chore`: tooling / config

Examples:
- `feat: add Voronoi-based task assignment`
- `fix: correct carbon calculation for EV`
- `refactor: simplify ACO path construction`
- `docs: update PRD and diagrams`

---