
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
pip install --upgrade pip
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

## 3. Branching Strategy

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

## 4. Commit Message Convention

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

## 5. To Setup File Structure
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