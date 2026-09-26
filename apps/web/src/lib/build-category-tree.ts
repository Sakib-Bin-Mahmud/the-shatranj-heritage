import type { Category, CategoryTree } from "@/lib/api/catalog";

export function buildCategoryTree(categories: Category[]): CategoryTree[] {
  const byId = new Map<string, CategoryTree>();
  categories.forEach((c) => byId.set(c.id, { ...c, children: [] }));

  const roots: CategoryTree[] = [];
  byId.forEach((node) => {
    const parent = node.parent_category_id
      ? byId.get(node.parent_category_id)
      : undefined;
    if (parent) {
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  });

  function sortTree(nodes: CategoryTree[]) {
    nodes.sort(
      (a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name),
    );
    nodes.forEach((n) => sortTree(n.children));
  }
  sortTree(roots);
  return roots;
}

export function descendantIds(node: CategoryTree): string[] {
  return node.children.flatMap((child) => [child.id, ...descendantIds(child)]);
}

// Used to exclude a category (and everything under it) from its own
// "parent" picker when editing — the backend only rejects a category
// being its own direct parent, not a deeper cycle.
export function descendantIdsOf(
  categories: Category[],
  categoryId: string,
): string[] {
  const childrenOf = new Map<string, string[]>();
  for (const c of categories) {
    if (!c.parent_category_id) continue;
    const list = childrenOf.get(c.parent_category_id) ?? [];
    list.push(c.id);
    childrenOf.set(c.parent_category_id, list);
  }

  const result: string[] = [];
  const stack = [...(childrenOf.get(categoryId) ?? [])];
  while (stack.length > 0) {
    const id = stack.pop()!;
    result.push(id);
    stack.push(...(childrenOf.get(id) ?? []));
  }
  return result;
}
