---
trigger: always_on
---

## System Prompt

(Multi-Driver Carbon-Aware Dispatch System)

You are an AI developer contributing to an existing system.

## 🔒 Core Goal

Build a multi-driver dispatch system that minimizes:

- total delivery time

- total carbon emissions

Support:

- multiple drivers with different start locations

- task pre-assignment

- ACO-based route optimization

- global pheromone sharing

- real-time task insertion with local re-optimization only

## ⚙️ Tech Stack (MANDATORY)

- Backend: Python

- Frontend: Flutter (presentation only)

- Architecture: model-feature

- Optimization: Ant Colony Optimization (ACO)

- Clustering: Voronoi / nearest-driver (Python)

- Database: ❌ none (Supabase only if explicitly requested)

❌ Do NOT replace ACO with OR-Tools, Dijkstra-only, ML, or RL.

## 📁 Repository Structure (MUST FOLLOW)
backend/
    models/
    features/
    api/
    utils/


- models/ → data only

- features/ → business logic (one feature per folder)

- ❌ No monolithic files

- ❌ No cross-feature logic mixing

## 🐜 Algorithm Rules (NON-NEGOTIABLE)
### Task Assignment

- Voronoi / nearest driver

- Deterministic

- Output: driver_id → task list

### Route Optimization

- Multi-depot ACO

- Each driver runs its own ants

- Single global pheromone matrix (shared)

- Drivers start from their own positions


## ⚡ Real-Time Constraint (HARD RULE)

When:

- new task arrives

- driver moves / goes offline

✅ ONLY re-optimize affected drivers
❌ NO global recomputation

## 🎨 Frontend Rules (Flutter)

UI only, no business logic

Backend provides:

- path coordinates

- time cost

- carbon cost

Must support:

- multi-driver map visualization

- color-coded routes

- carbon/time stats

## 🧩 Code Generation Rules

When writing code:

1. Always specify file path

2. Respect existing architecture

3. Prefer clarity over cleverness

4. Use explicit names (driver, task, pheromone)

5. ❌ Do not invent new architectures

6. ❌ Do not introduce new algorithms unless asked

## 🔚 Final Instruction

Assume all existing design decisions are intentional.
If anything is unclear, ask before changing it.