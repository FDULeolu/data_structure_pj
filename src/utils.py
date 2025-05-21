def print_header(title):
    print("\n" + "="*10 + f" {title} " + "="*10)

def print_product_list(products, context=""):
    if context:
        print(f"\n--- {context} ---")
    if not products:
        print("  (无结果)")
        return
    for p in products:
        print(f"  {p}")

def print_task_list(tasks, context=""):
    if context:
        print(f"\n--- {context} ---")
    if not tasks:
        print("  (无结果)")
        return
    for t in tasks:
        print(f"  {t}")