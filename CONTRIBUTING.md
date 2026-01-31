
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

## 2. Setting Up a Virtual Environment

To keep project dependencies isolated and avoid conflicts with your global Python installation, **using a virtual environment is required**.

### Prerequisites
- **Python 3.x** installed  
- **pip** (Python package manager)

### Installation Steps

#### 1. Create the virtual environment
Navigate to the project root directory and run:
```bash
python -m venv .venv
```
#### 2. Activate the environment
* Windows:

```bash
.venv\Scripts\activate
```
* macOS / Linux:

```bash
source .venv/bin/activate
```
#### 3. Install dependencies Once the environment is activated, install the required packages:

````bash
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
````

### Managing Dependencies
* Adding new packages: If you install a new library during development, please update the requirements file:

```bash
pip freeze > requirements.txt
```
* Leaving the environment: To exit the virtual environment, simply type:

```bash
deactivate
```
Note: Do not commit the .venv folder to the repository. Ensure it is listed in your .gitignore.

---
## 3. Core Rules (READ THIS FIRST)

**DO NOT**
- Directly push to `main`
- Directly push to `dev`
- Merge your own PR without review
- Commit broken or untested code
- Mix multiple unrelated features in one PR

**DO**
- Always work on feature branches
- Always create PRs into `dev`
- Keep PRs small and focused
- Rebase or resolve conflicts before requesting review
- Pull latest `dev` before starting new work
---

## 4. Branching Strategy

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
## 5. Feature Development Flow

All development must follow this flow.  
#### **Direct pushes to `main` or `dev` are *NOT* availabbel.**

### Step 1: Sync with `dev`
Always start from the latest `dev` branch.

```bash
git checkout dev
git pull origin dev
```

### Step 2: Create a Feature Branch
Create a new branch from dev.
```bash
git checkout -b feature/<feature-name>
```

### Step 3: Develop & Commit
* Keep commits small, logical, and focused
* Do not mix unrelated changes
* Follow the commit message convention

```bash
git add .
git commit -m "feat: short and clear description"
```
### Step 4: Push Feature Branch

Push only your feature branch to the remote repository.

```bash
git push origin feature/<feature-name>
```
**Do NOT** push to dev
**Do NOT** push to main

### Step 5: Open a Pull Request (PR)
* When your feature are **completely done** you may open a PR
* Run to check "Up to Date" status, make sure your Up to Date with `dev`
``` bash
git fetch origin
git status
```
* Base branch: dev
* One feature or fix per PR
* Provide a clear description of what was changed and why

### Step 6: Review & Update
Reviewers should check:
* Logic correctness
* Code readability
* Architecture consistency
* Potential side effects
* Performance red flags

### Step 7: Merge & Clean Up
* Merge only after approval
* Prefer Squash Merge
* Delete the feature branch after merging

---

## 6. Commit Message Convention

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

## 7. To Setup File Structure
- Open a terminal (PowerShell / VS Code Terminal)
- Make sure you are in the project root directory (e.g. `...\program`)
- Run the following command:
``` bash
$dirs = @(
    "backend/models",
    "backend/features/task_assignment",
    "backend/features/path_optimization",
    "backend/features/carbon",
    "backend/features/realtime",
    "backend/features/visualization",
    "backend/api",
    "backend/utils",

    "frontend/lib/config",
    "frontend/lib/models",
    "frontend/lib/features/task_assignment",
    "frontend/lib/features/path_optimization",
    "frontend/lib/features/carbon",
    "frontend/lib/features/realtime",
    "frontend/lib/features/visualization",
    "frontend/lib/services",
    "frontend/lib/widgets",

    "docs",
    "tests"
)

foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path $d
}
```

---