
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

## 2. Start Backend Server

````bash
uvicorn backend.main:app --reload
````

---

## Frontend Emulator Setup

The frontend was developed and tested using the Android Studio Emulator with the following AVD configuration:

- Device: Pixel 7
- Android API Level: 34

---

## 3. Demo Accounts
You may self create account but that will be driver acc

### Admin Account

| Email | Password |
| --- | --- |
| amberng999@gmail.com | Abcd1234@ |

### Driver Accounts

| Email | Password |
| --- | --- |
| honger1206@gmail.com | Abcd1234. |
| jwchow1412@gmail.com | Abcd1234@ |
| a04041121@gmail.com | Cjunxi1121. |
| chin1121@1utar.my | Abcd1234. |

---

## 4. Environment Variables

Please add the following keys to the `.env` file in both the `frontend` and `backend` folders.  
Note: These secret keys will be deactivated within 7 days.

```env
MAPBOX_ACCESS_TOKEN=pk.eyJ1IjoiY2hpbjExMjExIiwiYSI6ImNtazc0MnV2ajAwb2EzZHIybXg2czFodnEifQ.0yWAnhvBMlynUDlqrZqYOg
SUPABASE_URL=https://wmviaqwmumymwycxypfn.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndtdmlhcXdtdW15bXd5Y3h5cGZuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjEzNzM0OCwiZXhwIjoyMDg3NzEzMzQ4fQ.obinERH_C9B2N-1QnRNGK_Lqgo64lK46ws1UjYOCfJ0
MOCK_MODE=true
```



