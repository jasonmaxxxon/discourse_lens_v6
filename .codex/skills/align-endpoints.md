# align-endpoints

**When to run (mandatory)**  
- Before adding/changing frontend fetch/axios calls.  
- Before adding/changing FastAPI routes.  
- Before changing API payload/response shapes.  
- Any request about “endpoint / 404 / 500 / job_id alignment”.

**Command**  
`python .codex/tools/dump_routes.py --root . --out .codex/artifacts/endpoint_map.json`

**How to use in a task**  
1) Run the command above to refresh `.codex/artifacts/endpoint_map.json`.  
2) Section 1 of your plan: list the relevant endpoints from the map (method + path).  
3) Section 2: state the frontend path/method/payload/response you will use.  
4) Section 3: implement code.
