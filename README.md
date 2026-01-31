
## 1. Setting Up a Virtual Environment

To keep project dependencies isolated and avoid conflicts with your global Python installation, **using a virtual environment is required**.

---

### Prerequisites
- **Python 3.x** installed  
- **pip** (Python package manager)

---

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

---