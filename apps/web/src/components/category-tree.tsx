"use client";

import Link from "next/link";
import type { CategoryTree as CategoryTreeNode } from "@/lib/api/catalog";
import styles from "./category-tree.module.css";

export type CategoryTreeProps = {
  categories: CategoryTreeNode[];
  activeSlug?: string;
  linkTo: (slug: string) => string;
};

function CategoryNode({
  category,
  activeSlug,
  linkTo,
}: {
  category: CategoryTreeNode;
  activeSlug?: string;
  linkTo: (slug: string) => string;
}) {
  return (
    <div className={styles.item}>
      <Link
        href={linkTo(category.slug)}
        className={`${styles.link} ${activeSlug === category.slug ? styles.active : ""}`}
      >
        {category.name}
      </Link>
      {category.children.length > 0 && (
        <div className={styles.children}>
          {category.children.map((child) => (
            <CategoryNode
              key={child.id}
              category={child}
              activeSlug={activeSlug}
              linkTo={linkTo}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function CategoryTree({
  categories,
  activeSlug,
  linkTo,
}: CategoryTreeProps) {
  return (
    <nav className={styles.tree} aria-label="Categories">
      {categories.map((category) => (
        <CategoryNode
          key={category.id}
          category={category}
          activeSlug={activeSlug}
          linkTo={linkTo}
        />
      ))}
    </nav>
  );
}
