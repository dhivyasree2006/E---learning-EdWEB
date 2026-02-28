from main import app

print("Registered Routes:")
for route in app.routes:
    methods = getattr(route, "methods", None)
    path = getattr(route, "path", None)
    print(f"{methods} {path}")
