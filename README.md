# TeachCARE Prototype

A research prototype for **TeachCARE: A Constraint-Based Mathematical and Computational Framework for Teacher Workload Management**.

This prototype is intentionally limited to the research scope. It demonstrates teacher/qualification data, curriculum requirements, JHS/SHS eligibility, scheduling periods, binary assignment variables, hard constraints, workload calculation against a 6-hour target, workload balancing, independent validation, and feasibility detection.

It is **not** a full school management system.

## Technology
- Python 3.x
- Flask
- Flask-SQLAlchemy / SQLAlchemy
- SQLite
- PuLP (integer optimization)
- Flask-Migrate
- Bootstrap 5
- HTML/CSS

## Run on Windows

Open PowerShell in this folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
python app.py
```

Then open `http://127.0.0.1:5000`.

If PowerShell blocks activation:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe seed.py
venv\Scripts\python.exe app.py
```

## Mathematical model

The core binary variable is:

`x[t,s,c,d,p] = 1` if teacher `t` teaches subject `s` to section `c` on day `d` at period `p`; otherwise `0`.

The prototype applies hard constraints for:
- curriculum coverage
- teacher qualification
- JHS/SHS eligibility
- teacher schedule conflicts
- section schedule conflicts

For each teacher:

`W_t = total contact-teaching hours assigned to teacher t`

Target:

`T = 6 hours`

Deviation:

`D_t = |W_t - 6|`

Optimization objective:

`minimize sum(D_t)`

subject to the hard constraints.

The validator independently checks the generated schedule rather than relying only on the optimizer.

## Research boundary

The 6-hour target is implemented as a study assumption from the research plan; it is not presented as a universal workload policy.

The prototype uses researcher-prepared demonstration data. Replace these with approved datasets for actual research experiments.
